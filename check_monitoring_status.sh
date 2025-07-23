#!/bin/bash
# 監視システム状況確認スクリプト

echo "📊 開発ログ監視システム状況確認"
echo "================================"

PROJECT_DIR="/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool"

# 1. launchd状況確認
echo "🔧 launchd監視プロセス:"
if launchctl list | grep -q "com.dev-log-monitor"; then
    echo "   ✅ 起動中"
    launchctl list | grep "com.dev-log-monitor"
else
    echo "   ❌ 停止中"
fi

# 2. プロセス確認
echo ""
echo "🔍 実行中プロセス:"
DEV_PROCESSES=$(ps aux | grep "dev_log_watcher.py" | grep -v grep)
if [ -n "$DEV_PROCESSES" ]; then
    echo "   ✅ 開発ログ監視プロセス発見"
    echo "$DEV_PROCESSES"
else
    echo "   ❌ 開発ログ監視プロセスなし"
fi

# 3. cron設定確認
echo ""
echo "⏰ cron設定:"
if crontab -l 2>/dev/null | grep -q "article_generator.py"; then
    echo "   ✅ AI記事生成cron設定済み"
    crontab -l | grep "article_generator.py"
else
    echo "   ❌ AI記事生成cron未設定"
fi

# 4. ログファイル確認
echo ""
echo "📋 ログファイル状況:"
LOG_FILES=(
    "$PROJECT_DIR/logs/dev_monitor.log"
    "$PROJECT_DIR/logs/dev_monitor_error.log"
    "$PROJECT_DIR/logs/article_generation.log"
)

for log_file in "${LOG_FILES[@]}"; do
    if [ -f "$log_file" ]; then
        size=$(stat -f%z "$log_file" 2>/dev/null || echo "0")
        mod_time=$(stat -f%Sm "$log_file" 2>/dev/null || echo "不明")
        echo "   ✅ $(basename "$log_file"): ${size}bytes, 更新: $mod_time"
    else
        echo "   ❌ $(basename "$log_file"): ファイル不存在"
    fi
done

# 5. 監視対象フォルダ確認
echo ""
echo "📁 監視対象フォルダ:"
WATCH_FOLDERS=(
    "/Users/dd/Desktop/1_dev"
    "/Users/dd/Desktop/dev"
)

for folder in "${WATCH_FOLDERS[@]}"; do
    if [ -d "$folder" ]; then
        file_count=$(find "$folder" -name "*.py" -o -name "*.js" -o -name "*.ts" | wc -l | tr -d ' ')
        echo "   ✅ $folder: ${file_count}個の監視対象ファイル"
    else
        echo "   ⚠️  $folder: フォルダ不存在"
    fi
done

# 6. 最新のログエントリ
echo ""
echo "📝 最新ログエントリ（直近5行）:"
if [ -f "$PROJECT_DIR/logs/dev_monitor.log" ]; then
    tail -5 "$PROJECT_DIR/logs/dev_monitor.log"
else
    echo "   ログファイルがありません"
fi

echo ""
echo "🎯 管理コマンド:"
echo "   完全自動化設定: ./setup_auto_monitoring.sh"
echo "   監視再起動: launchctl stop com.dev-log-monitor && launchctl start com.dev-log-monitor"
echo "   手動記事生成: cd $PROJECT_DIR && source venv/bin/activate && python automation/article_generator.py"