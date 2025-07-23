#!/usr/bin/env python3
"""
シンプル開発ログ監視システム
軽量・最小限の機能のみ実装
"""

import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

class SimpleDevMonitor:
    def __init__(self):
        self.project_dir = Path("/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool")
        self.brain_dir = Path("/Users/dd/Desktop/1_dev/coding-rule2")
        self.log_file = self.project_dir / "logs" / "simple_dev.log"
        self.log_file.parent.mkdir(exist_ok=True)
        
        # 頭脳からAPIキー読み込み
        self.load_api_keys()
        
    def load_api_keys(self):
        """頭脳ディレクトリからAPIキー読み込み"""
        env_file = self.brain_dir / ".env"
        self.api_keys = {}
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        self.api_keys[key] = value
            
            # 環境変数に設定
            for key, value in self.api_keys.items():
                os.environ[key] = value
            
            self.log_event("INFO", f"APIキー読み込み完了: {len(self.api_keys)}個")
        else:
            self.log_event("WARNING", "頭脳ディレクトリの.envファイルが見つかりません")
    
    def log_event(self, level, message):
        """シンプルログ記録"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} [{level}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"[{level}] {message}")
    
    def check_git_changes(self):
        """Git変更チェック（軽量版）"""
        watch_dirs = [
            "/Users/dd/Desktop/1_dev/coding-rule2/projects",
            "/Users/dd/Desktop/1_dev/post_tool"  # 他のプロジェクトがあれば追加
        ]
        
        changes = []
        for watch_dir in watch_dirs:
            if os.path.exists(watch_dir):
                try:
                    # 最近の変更を確認（軽量）
                    result = subprocess.run(
                        ['find', watch_dir, '-name', '*.py', '-o', '-name', '*.js', '-o', '-name', '*.ts', '-o', '-name', '*.md', '-newer', str(self.log_file)],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if result.stdout.strip():
                        files = result.stdout.strip().split('\n')[:5]  # 最大5ファイルまで
                        changes.extend(files)
                        
                except Exception as e:
                    self.log_event("DEBUG", f"ディレクトリ監視エラー ({watch_dir}): {e}")
        
        return changes
    
    def collect_dev_log(self):
        """開発ログ収集（軽量版）"""
        changes = self.check_git_changes()
        
        if changes:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "file_changes",
                "changes": changes[:3],  # 最大3ファイル
                "count": len(changes)
            }
            
            self.log_event("INFO", f"ファイル変更検出: {len(changes)}件")
            return log_entry
        
        return None
    
    def run_simple_monitoring(self):
        """シンプル監視実行"""
        self.log_event("INFO", "シンプル開発監視開始")
        
        while True:
            try:
                log_entry = self.collect_dev_log()
                if log_entry:
                    # ログをObsidianに保存（軽量）
                    self.save_to_obsidian(log_entry)
                
                time.sleep(300)  # 5分間隔（軽量化）
                
            except KeyboardInterrupt:
                self.log_event("INFO", "監視停止")
                break
            except Exception as e:
                self.log_event("ERROR", f"監視エラー: {e}")
                time.sleep(60)
    
    def save_to_obsidian(self, log_entry):
        """Obsidianに軽量ログ保存"""
        obsidian_vault = Path("/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents")
        obsidian_log = obsidian_vault / "00_INBOX" / f"dev_log_{datetime.now().strftime('%Y%m%d')}.md"
        
        content = f"## {log_entry['timestamp']}\n\n"
        if log_entry['type'] == 'file_changes':
            content += f"ファイル変更: {log_entry['count']}件\n\n"
            for file_path in log_entry['changes']:
                content += f"- {os.path.basename(file_path)}\n"
        
        content += "\n---\n\n"
        
        with open(obsidian_log, 'a', encoding='utf-8') as f:
            f.write(content)

def main():
    monitor = SimpleDevMonitor()
    monitor.run_simple_monitoring()

if __name__ == "__main__":
    main()