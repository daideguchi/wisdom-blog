#!/bin/bash
# シンプル自動化セットアップ（軽量版）

echo "🚀 シンプル自動化セットアップ開始..."

PROJECT_DIR="/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool"

# 1. ログディレクトリ作成
mkdir -p "$PROJECT_DIR/logs"

# 2. 既存の重いシステム完全停止
echo "🛑 既存システム停止中..."
launchctl stop com.dev-system-health 2>/dev/null || true
launchctl stop com.dev-log-monitor 2>/dev/null || true
launchctl unload "$HOME/Library/LaunchAgents/com.dev-system-health.plist" 2>/dev/null || true
launchctl unload "$HOME/Library/LaunchAgents/com.dev-log-monitor.plist" 2>/dev/null || true
pkill -f "dev_log_watcher.py" 2>/dev/null || true
pkill -f "system_health_monitor.py" 2>/dev/null || true

# 3. 既存のcron設定削除
echo "🧹 既存cron設定クリア..."
crontab -l 2>/dev/null | grep -v "article_generator.py" | grep -v "simple_dev_monitor.py" | crontab - 2>/dev/null || true

# 4. シンプルcron設定（軽量版）
echo "⏰ シンプルcron設定中..."

# 開発監視: 10分ごと（軽量）
DEV_MONITOR_CRON="*/10 * * * * cd $PROJECT_DIR && source venv/bin/activate && timeout 30 python automation/simple_dev_monitor.py >> logs/simple_monitor.log 2>&1 &"

# AI記事生成: 2時間ごと（頻度を下げて軽量化）
ARTICLE_CRON="0 */2 * * * cd $PROJECT_DIR && source venv/bin/activate && timeout 60 python automation/smart_article_generator.py >> logs/smart_article.log 2>&1"

# cron設定追加
{
    crontab -l 2>/dev/null || true
    echo "$DEV_MONITOR_CRON"
    echo "$ARTICLE_CRON"
} | crontab -

# 5. 頭脳ディレクトリからAPIキー確認
echo "🔑 頭脳ディレクトリAPI確認..."
BRAIN_ENV="/Users/dd/Desktop/1_dev/coding-rule2/.env"
if [ -f "$BRAIN_ENV" ]; then
    API_COUNT=$(grep -c "API_KEY" "$BRAIN_ENV" 2>/dev/null || echo "0")
    echo "✅ 頭脳にAPIキー $API_COUNT 個発見"
else
    echo "❌ 頭脳ディレクトリの.envファイルなし"
fi

# 6. 設定確認
echo "✅ 設定完了確認中..."
sleep 2

if crontab -l | grep -q "simple_dev_monitor.py"; then
    echo "✅ 開発監視: cron設定済み（10分間隔）"
else
    echo "❌ 開発監視: cron設定失敗"
fi

if crontab -l | grep -q "smart_article_generator.py"; then
    echo "✅ AI記事生成: cron設定済み（2時間間隔）"
else
    echo "❌ AI記事生成: cron設定失敗"
fi

echo ""
echo "🎊 シンプル自動化セットアップ完了！"
echo ""
echo "📊 軽量システム構成:"
echo "   📝 開発監視 (simple_dev_monitor.py)"
echo "      - 10分間隔で軽量監視"
echo "      - 30秒でタイムアウト（重くならない）"
echo "      - ファイル変更をObsidian INBOXに記録"
echo ""
echo "   🤖 AI記事生成 (smart_article_generator.py)"
echo "      - 2時間間隔で実行（軽量化）"
echo "      - 頭脳ディレクトリのAPIキー自動読み込み"
echo "      - 60秒でタイムアウト"
echo ""
echo "📋 ログファイル:"
echo "   - 開発監視: $PROJECT_DIR/logs/simple_monitor.log"
echo "   - AI記事生成: $PROJECT_DIR/logs/smart_article.log"
echo ""
echo "🔧 管理コマンド:"
echo "   cron確認: crontab -l"
echo "   手動実行: cd $PROJECT_DIR && source venv/bin/activate && python automation/smart_article_generator.py"
echo "   ログ確認: tail -f $PROJECT_DIR/logs/simple_monitor.log"
echo ""
echo "✨ これで重くならない軽量自動化システムが稼働します！"