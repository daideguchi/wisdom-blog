#!/bin/bash
# 開発ログ監視システム起動スクリプト

echo "🚀 開発ログ監視システム起動中..."

cd "/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool"

# 仮想環境アクティベート
source venv/bin/activate

# バックグラウンドで監視開始
nohup python automation/dev_log_watcher.py > dev_monitor.log 2>&1 &

MONITOR_PID=$!
echo "📊 監視システム起動完了 (PID: $MONITOR_PID)"
echo "   ログファイル: dev_monitor.log"
echo "   停止コマンド: kill $MONITOR_PID"

# 自動記事生成の定期実行（1時間ごと）
while true; do
    sleep 3600  # 1時間待機
    echo "🤖 AI記事生成チェック中..."
    python automation/article_generator.py
done &

ARTICLE_PID=$!
echo "📝 記事生成システム起動完了 (PID: $ARTICLE_PID)"

# プロセスIDを保存
echo "MONITOR_PID=$MONITOR_PID" > .monitoring_pids
echo "ARTICLE_PID=$ARTICLE_PID" >> .monitoring_pids

echo ""
echo "✅ システム起動完了！"
echo "   あなたのコーディング作業がすべて監視・記録されます"
echo "   AIが自動で技術記事を生成します"