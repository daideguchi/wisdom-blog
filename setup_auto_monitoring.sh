#!/bin/bash
# 完全自動化セットアップスクリプト - 死活監視付き

echo "🚀 開発ログ監視完全自動化セットアップ開始..."

PROJECT_DIR="/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool"
HEALTH_PLIST="com.dev-system-health.plist"
HOME_HEALTH_PLIST="$HOME/Library/LaunchAgents/$HEALTH_PLIST"

# 1. ログディレクトリ作成
mkdir -p "$PROJECT_DIR/logs"

# 2. 既存の監視プロセス停止
echo "🛑 既存プロセス停止中..."
launchctl stop com.dev-log-monitor 2>/dev/null || true
launchctl stop com.dev-system-health 2>/dev/null || true
launchctl unload "$HOME/Library/LaunchAgents/com.dev-log-monitor.plist" 2>/dev/null || true
launchctl unload "$HOME_HEALTH_PLIST" 2>/dev/null || true

# 3. システム健全性監視をlaunchdに登録
echo "🔧 システム健全性監視を登録中..."
cp "$PROJECT_DIR/$HEALTH_PLIST" "$HOME_HEALTH_PLIST"
launchctl load "$HOME_HEALTH_PLIST"
launchctl start com.dev-system-health

# 4. crontab設定（記事生成を1時間ごと）
echo "⏰ cron設定中..."
CRON_JOB="0 * * * * cd $PROJECT_DIR && source venv/bin/activate && python automation/article_generator.py >> logs/article_generation.log 2>&1"

# 既存のcron設定を削除してから追加
crontab -l 2>/dev/null | grep -v "article_generator.py" | crontab - 2>/dev/null || true
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# 5. APIキー設定確認
echo "🔑 APIキー設定確認..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY環境変数が設定されていません"
    echo "   以下をターミナルで実行してください:"
    echo "   export ANTHROPIC_API_KEY='your_actual_api_key'"
    echo "   echo 'export ANTHROPIC_API_KEY=\"your_actual_api_key\"' >> ~/.zshrc"
fi

# 6. 起動確認
echo "✅ 設定完了確認中..."
sleep 5

if launchctl list | grep -q "com.dev-system-health"; then
    echo "✅ システム健全性監視: 起動中"
else
    echo "❌ システム健全性監視: 起動失敗"
fi

if crontab -l | grep -q "article_generator.py"; then
    echo "✅ AI記事生成: cron設定済み"
else
    echo "❌ AI記事生成: cron設定失敗"
fi

# 7. 監視対象プロセス起動確認
sleep 10
if ps aux | grep -q "dev_log_watcher.py" && ! ps aux | grep "dev_log_watcher.py" | grep -q grep; then
    echo "✅ 開発ログ監視プロセス: 起動中"
else
    echo "⏳ 開発ログ監視プロセス: 起動準備中（システム健全性監視が自動起動します）"
fi

echo ""
echo "🎉 完全自動化セットアップ完了！"
echo ""
echo "📊 監視システム構成:"
echo "   📱 システム健全性監視 (com.dev-system-health)"
echo "      - Mac起動時に自動開始"
echo "      - 開発ログ監視プロセスの死活監視・自動復旧"
echo "      - 5分間隔でプロセス状況チェック"
echo ""
echo "   📝 開発ログ監視 (dev_log_watcher.py)"
echo "      - /Users/dd/Desktop/1_dev/ 配下を監視"
echo "      - ファイル変更・Git操作を自動記録"
echo "      - 健全性監視により自動復旧"
echo ""
echo "   🤖 AI記事生成 (cron)"
echo "      - 毎時0分に自動実行"
echo "      - 蓄積ログからAI記事生成"
echo ""
echo "📋 ログファイル:"
echo "   - システム健全性: $PROJECT_DIR/logs/system_health.log"
echo "   - 開発ログ監視: $PROJECT_DIR/logs/dev_monitor.log"
echo "   - AI記事生成: $PROJECT_DIR/logs/article_generation.log"
echo ""
echo "🔧 管理コマンド:"
echo "   状況確認: ./check_monitoring_status.sh"
echo "   システム再起動: launchctl stop com.dev-system-health && launchctl start com.dev-system-health"
echo "   手動記事生成: cd $PROJECT_DIR && source venv/bin/activate && python automation/article_generator.py"
echo ""
echo "✨ これでMac再起動後も自動で監視システムが立ち上がります！"