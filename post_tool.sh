#!/bin/bash
# POST_TOOL 統合管理スクリプト
# 全機能を一つのスクリプトに統合

PROJECT_DIR="/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool"
BRAIN_LOGS="/Users/dd/Desktop/1_dev/coding-rule2/runtime/logs"
OBSIDIAN_INBOX="/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents/00_INBOX"

case "$1" in
    # ========== 自動化管理 ==========
    "start")
        echo "🚀 自動化システム開始中（軽量版）..."
        # 既存のpost_tool設定を削除
        crontab -l 2>/dev/null | grep -v "post_tool" | crontab - 2>/dev/null
        # 現実的な頻度で設定を追加
        {
            crontab -l 2>/dev/null || true
            echo "0 9,15,21 * * * cd $PROJECT_DIR && source venv/bin/activate && python automation/zettelkasten_processor.py >> logs/zettelkasten.log 2>&1"
            echo "0 20 * * * cd $PROJECT_DIR && source venv/bin/activate && python automation/smart_article_generator.py >> logs/smart_article.log 2>&1"
        } | crontab -
        echo "✅ 軽量自動化システム開始完了"
        echo "📅 スケジュール:"
        echo "   🧠 ツェッテルカステン整理: 朝9時、午後3時、夜9時"
        echo "   🤖 AI記事生成: 毎日夜8時"
        ;;
    
    "stop")
        echo "⏸️  自動化システム停止中..."
        crontab -l > ~/post_tool_cron_backup.txt 2>/dev/null
        crontab -l 2>/dev/null | grep -v "post_tool" | crontab - 2>/dev/null
        echo "✅ 停止完了（バックアップ: ~/post_tool_cron_backup.txt）"
        ;;
    
    "status")
        echo "📊 現在の自動化設定:"
        echo "===================="
        crontab -l 2>/dev/null | grep -E "(zettelkasten_processor|smart_article_generator)" || echo "❌ 自動化設定なし"
        ;;
    
    # ========== 手動実行 ==========
    "zettel")
        echo "🧠 ツェッテルカステン整理を今すぐ実行中..."
        cd "$PROJECT_DIR"
        source venv/bin/activate
        python automation/zettelkasten_processor.py
        echo "✅ 実行完了"
        ;;
    
    "article")
        echo "🤖 AI記事生成を今すぐ実行中..."
        cd "$PROJECT_DIR"
        source venv/bin/activate
        python automation/smart_article_generator.py
        echo "✅ 実行完了"
        ;;
    
    "monitor")
        echo "📝 開発監視を今すぐ実行中..."
        cd "$PROJECT_DIR"
        source venv/bin/activate
        python automation/simple_dev_monitor.py &
        MONITOR_PID=$!
        echo "📊 開発監視開始（PID: $MONITOR_PID）"
        echo "⏹️  停止: kill $MONITOR_PID"
        ;;
    
    # ========== ログ確認 ==========
    "logs")
        echo "📊 全開発ログ統合確認"
        echo "===================="
        echo ""
        echo "🧠 頭脳ディレクトリログ（システム全体）"
        echo "====================================="
        if [ -d "$BRAIN_LOGS" ]; then
            echo "📁 場所: $BRAIN_LOGS"
            echo "📋 最新3件:"
            ls -t "$BRAIN_LOGS"/*.log 2>/dev/null | head -3 | while read file; do
                echo "   📄 $(basename "$file") - $(stat -f%Sm "$file" 2>/dev/null)"
            done
        else
            echo "❌ 頭脳ログディレクトリが見つかりません"
        fi
        
        echo ""
        echo "🎯 post_toolプロジェクトログ（プロジェクト専用）"
        echo "==========================================="
        if [ -d "$PROJECT_DIR/logs" ]; then
            echo "📁 場所: $PROJECT_DIR/logs"
            echo "📋 最新3件:"
            ls -t "$PROJECT_DIR/logs"/*.log 2>/dev/null | head -3 | while read file; do
                echo "   📄 $(basename "$file") - $(stat -f%Sm "$file" 2>/dev/null)"
                tail -1 "$file" 2>/dev/null | sed 's/^/      /'
            done
        fi
        
        echo ""
        echo "🔍 今日の活動サマリー"
        echo "=================="
        TODAY=$(date '+%Y-%m-%d')
        echo "🧠 システム活動:"
        grep -h "$TODAY" "$BRAIN_LOGS"/*.log 2>/dev/null | tail -2 | sed 's/^/   /' || echo "   今日の活動なし"
        echo "🎯 プロジェクト活動:"
        grep -h "$TODAY" "$PROJECT_DIR/logs"/*.log 2>/dev/null | tail -2 | sed 's/^/   /' || echo "   今日の活動なし"
        ;;
    
    # ========== メモ作成 ==========
    "memo")
        TIMESTAMP=$(date '+%Y-%m-%d_%H%M%S')
        MEMO_FILE="$OBSIDIAN_INBOX/memo_$TIMESTAMP.md"
        
        if [ "$2" ]; then
            TITLE="$2"
        else
            TITLE="クイックメモ"
        fi
        
        cat > "$MEMO_FILE" << EOF
## $TITLE

**作成日時**: $(date '+%Y-%m-%d %H:%M:%S')

### 内容
<!-- ここにメモを書く -->

### 参考リンク
<!-- URLやリンクがあれば -->

### タグ
#memo #inbox

EOF
        echo "✅ メモ作成: $MEMO_FILE"
        ;;
    
    # ========== Git管理 ==========
    "push")
        echo "📤 Git自動プッシュ中..."
        cd "$PROJECT_DIR"
        
        # 変更があるかチェック
        if git diff --quiet && git diff --cached --quiet; then
            echo "📋 変更なし - プッシュ不要"
            exit 0
        fi
        
        # 自動コミット
        git add .
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        git commit -m "📝 POST_TOOL自動更新 - $TIMESTAMP

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
        
        # プッシュ
        git push
        echo "✅ Git プッシュ完了"
        ;;
    
    "status-git")
        echo "📊 Git状況確認"
        echo "=============="
        cd "$PROJECT_DIR"
        echo "🔄 Git Status:"
        git status --short
        echo ""
        echo "📝 最新コミット:"
        git log --oneline -3
        ;;
    
    # ========== セットアップ ==========
    "setup")
        echo "🔧 POST_TOOL初期セットアップ"
        echo "=========================="
        
        # 必要ディレクトリ作成
        mkdir -p "$PROJECT_DIR/logs"
        
        # 仮想環境確認
        if [ ! -d "$PROJECT_DIR/venv" ]; then
            echo "📦 仮想環境作成中..."
            cd "$PROJECT_DIR"
            python3 -m venv venv
            source venv/bin/activate
            pip install anthropic watchdog python-frontmatter
        fi
        
        echo "✅ セットアップ完了"
        echo "💡 次のステップ: ./post_tool.sh start"
        ;;
    
    *)
        echo "🎛️  POST_TOOL 統合管理システム"
        echo "=============================="
        echo ""
        echo "🚀 自動化制御:"
        echo "  ./post_tool.sh start     - 自動化開始"
        echo "  ./post_tool.sh stop      - 自動化停止"
        echo "  ./post_tool.sh status    - 設定確認"
        echo ""
        echo "🎮 手動実行:"
        echo "  ./post_tool.sh zettel    - ツェッテルカステン整理"
        echo "  ./post_tool.sh article   - AI記事生成"
        echo "  ./post_tool.sh monitor   - 開発監視開始"
        echo ""
        echo "📊 ログ・情報:"
        echo "  ./post_tool.sh logs      - 全ログ確認"
        echo ""
        echo "📝 メモ作成:"
        echo "  ./post_tool.sh memo      - クイックメモ"
        echo "  ./post_tool.sh memo 'タイトル' - タイトル付きメモ"
        echo ""
        echo "📤 Git管理:"
        echo "  ./post_tool.sh push      - 自動コミット&プッシュ"
        echo "  ./post_tool.sh status-git - Git状況確認"
        echo ""
        echo "🔧 セットアップ:"
        echo "  ./post_tool.sh setup     - 初期セットアップ"
        echo ""
        echo "例:"
        echo "  ./post_tool.sh start         # 自動化開始"
        echo "  ./post_tool.sh memo '面白いURL発見' # メモ作成"
        echo "  ./post_tool.sh push          # Git自動プッシュ"
        echo "  ./post_tool.sh logs          # 全ログ確認"
        ;;
esac