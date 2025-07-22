#!/usr/bin/env python3
"""
開発ログ監視スクリプト
あなたの開発作業を監視してAI記事生成の材料を収集します
"""

import os
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import signal
import sys

# 設定
OBSIDIAN_VAULT_PATH = "/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents"
DEV_LOGS_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "01_Dev_Logs")
LOG_FILE = os.path.join(DEV_LOGS_PATH, f"dev_log_{datetime.now().strftime('%Y-%m-%d')}.json")

# 監視対象フォルダ
WATCH_FOLDERS = [
    "/Users/dd/Desktop/1_dev",  # 現在のプロジェクトフォルダ
    "/Users/dd/Desktop/dev",    # 他の開発フォルダがあれば追加
]

class DevLogCollector:
    def __init__(self):
        self.logs = []
        self.ensure_folders()
        
    def ensure_folders(self):
        """必要なフォルダを作成"""
        os.makedirs(DEV_LOGS_PATH, exist_ok=True)
        
    def add_log(self, log_type, message, details=None):
        """ログエントリを追加"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": log_type,
            "message": message,
            "details": details or {}
        }
        self.logs.append(entry)
        self.save_logs()
        print(f"📝 {log_type}: {message}")
        
    def save_logs(self):
        """ログをファイルに保存"""
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)

class DevFileHandler(FileSystemEventHandler):
    def __init__(self, collector):
        self.collector = collector
        self.last_processed = {}
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # 重複処理を防ぐ
        current_time = time.time()
        if file_path in self.last_processed:
            if current_time - self.last_processed[file_path] < 5:  # 5秒以内は無視
                return
        self.last_processed[file_path] = current_time
        
        # ファイル種別による処理
        if file_path.endswith(('.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.md')):
            self.collector.add_log(
                "file_modified",
                f"ファイル編集: {os.path.basename(file_path)}",
                {"file_path": file_path, "extension": Path(file_path).suffix}
            )

class GitWatcher:
    def __init__(self, collector):
        self.collector = collector
        self.last_commit_hash = None
        self.running = True
        
    def watch_git(self):
        """Git操作を監視"""
        while self.running:
            try:
                for folder in WATCH_FOLDERS:
                    if os.path.exists(os.path.join(folder, '.git')):
                        self.check_git_changes(folder)
            except Exception as e:
                print(f"Git監視エラー: {e}")
            time.sleep(10)  # 10秒ごとにチェック
            
    def check_git_changes(self, repo_path):
        """Git変更をチェック"""
        try:
            # 最新コミットハッシュを取得
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'], 
                cwd=repo_path,
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                current_hash = result.stdout.strip()
                
                if self.last_commit_hash and self.last_commit_hash != current_hash:
                    # 新しいコミットが検出された
                    commit_info = self.get_commit_info(repo_path, current_hash)
                    self.collector.add_log(
                        "git_commit",
                        f"新しいコミット: {commit_info['message'][:50]}...",
                        commit_info
                    )
                    
                self.last_commit_hash = current_hash
                
        except Exception as e:
            print(f"Git変更チェックエラー: {e}")
            
    def get_commit_info(self, repo_path, commit_hash):
        """コミット情報を取得"""
        try:
            # コミットメッセージ
            msg_result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%s', commit_hash],
                cwd=repo_path, capture_output=True, text=True
            )
            
            # コミット差分
            diff_result = subprocess.run(
                ['git', 'diff', f'{commit_hash}^', commit_hash, '--stat'],
                cwd=repo_path, capture_output=True, text=True
            )
            
            return {
                "hash": commit_hash,
                "message": msg_result.stdout.strip(),
                "diff_stat": diff_result.stdout.strip(),
                "repo_path": repo_path
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def stop(self):
        self.running = False

def main():
    print("🚀 開発ログ監視を開始します...")
    print("Ctrl+C で停止")
    
    collector = DevLogCollector()
    
    # 初期ログ
    collector.add_log("system", "開発ログ監視開始", {
        "watch_folders": WATCH_FOLDERS,
        "log_file": LOG_FILE
    })
    
    # ファイル監視セットアップ
    event_handler = DevFileHandler(collector)
    observers = []
    
    for folder in WATCH_FOLDERS:
        if os.path.exists(folder):
            observer = Observer()
            observer.schedule(event_handler, folder, recursive=True)
            observer.start()
            observers.append(observer)
            print(f"📁 監視開始: {folder}")
        else:
            print(f"⚠️  フォルダが見つかりません: {folder}")
    
    # Git監視セットアップ
    git_watcher = GitWatcher(collector)
    git_thread = threading.Thread(target=git_watcher.watch_git)
    git_thread.daemon = True
    git_thread.start()
    print("📊 Git監視開始")
    
    # 定期的な記事生成チェック
    def check_article_generation():
        while True:
            time.sleep(3600)  # 1時間ごと
            if len(collector.logs) >= 5:  # 5つ以上のログが蓄積されたら
                print("📝 十分なログが蓄積されました。記事生成を検討してください。")
                print("  → python automation/article_generator.py")
    
    article_thread = threading.Thread(target=check_article_generation)
    article_thread.daemon = True
    article_thread.start()
    
    # 終了シグナルハンドリング
    def signal_handler(sig, frame):
        print("\n🛑 監視を停止しています...")
        git_watcher.stop()
        for observer in observers:
            observer.stop()
            observer.join()
        collector.add_log("system", "開発ログ監視終了")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # メインループ
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()