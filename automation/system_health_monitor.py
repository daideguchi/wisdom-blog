#!/usr/bin/env python3
"""
システム健全性監視スクリプト
プロセス死活監視・自動復旧機能
"""

import os
import subprocess
import time
import json
import signal
import sys
from datetime import datetime
from pathlib import Path

class SystemHealthMonitor:
    def __init__(self):
        self.project_dir = Path("/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool")
        self.log_dir = self.project_dir / "logs"
        self.health_log = self.log_dir / "health_monitor.log"
        self.running = True
        
        # 監視対象プロセス
        self.monitored_processes = {
            "dev_log_watcher": "automation/dev_log_watcher.py",
        }
        
        self.log_dir.mkdir(exist_ok=True)
        
    def log_event(self, level, message):
        """イベントログ記録"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} [{level}] {message}\n"
        
        with open(self.health_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"[{level}] {message}")
    
    def is_process_running(self, script_name):
        """プロセス実行確認"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', script_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False
    
    def start_process(self, script_name):
        """プロセス起動"""
        try:
            script_path = self.project_dir / script_name
            venv_python = self.project_dir / "venv" / "bin" / "python"
            
            if not script_path.exists():
                self.log_event("ERROR", f"スクリプトが見つかりません: {script_path}")
                return False
            
            if not venv_python.exists():
                self.log_event("ERROR", f"仮想環境が見つかりません: {venv_python}")
                return False
            
            # バックグラウンドでプロセス起動
            subprocess.Popen(
                [str(venv_python), str(script_path)],
                cwd=str(self.project_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(3)  # 起動確認のための待機
            
            if self.is_process_running(script_name):
                self.log_event("INFO", f"プロセス起動成功: {script_name}")
                return True
            else:
                self.log_event("ERROR", f"プロセス起動失敗: {script_name}")
                return False
                
        except Exception as e:
            self.log_event("ERROR", f"プロセス起動エラー ({script_name}): {e}")
            return False
    
    def check_and_restart_processes(self):
        """プロセス監視・自動復旧"""
        for process_name, script_path in self.monitored_processes.items():
            if not self.is_process_running(script_path):
                self.log_event("WARNING", f"プロセス停止検出: {process_name}")
                
                # 自動復旧試行
                if self.start_process(script_path):
                    self.log_event("INFO", f"プロセス自動復旧成功: {process_name}")
                else:
                    self.log_event("ERROR", f"プロセス自動復旧失敗: {process_name}")
            else:
                self.log_event("DEBUG", f"プロセス正常稼働: {process_name}")
    
    def check_system_health(self):
        """システム全体健全性チェック"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "processes": {},
            "disk_space": self.get_disk_usage(),
            "log_file_sizes": self.get_log_sizes()
        }
        
        for process_name, script_path in self.monitored_processes.items():
            health_status["processes"][process_name] = {
                "running": self.is_process_running(script_path),
                "script_path": script_path
            }
        
        return health_status
    
    def get_disk_usage(self):
        """ディスク使用量確認"""
        try:
            result = subprocess.run(['df', '-h', str(self.project_dir)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    fields = lines[1].split()
                    return {
                        "total": fields[1],
                        "used": fields[2], 
                        "available": fields[3],
                        "usage_percent": fields[4]
                    }
        except Exception:
            pass
        return {"error": "取得失敗"}
    
    def get_log_sizes(self):
        """ログファイルサイズ確認"""
        sizes = {}
        for log_file in self.log_dir.glob("*.log"):
            try:
                size_bytes = log_file.stat().st_size
                sizes[log_file.name] = f"{size_bytes / 1024:.1f}KB"
            except Exception:
                sizes[log_file.name] = "アクセス不可"
        return sizes
    
    def run_health_check(self):
        """健全性チェック実行"""
        self.log_event("INFO", "システム健全性チェック開始")
        
        # 初回起動時にプロセス確認
        for process_name, script_path in self.monitored_processes.items():
            if not self.is_process_running(script_path):
                self.log_event("INFO", f"初回起動: {process_name}")
                self.start_process(script_path)
        
        # 定期監視ループ
        while self.running:
            try:
                self.check_and_restart_processes()
                
                # システム状況を1時間ごとにログ
                if datetime.now().minute == 0:
                    health_status = self.check_system_health()
                    self.log_event("INFO", f"システム状況: {json.dumps(health_status, ensure_ascii=False)}")
                
                time.sleep(300)  # 5分間隔で監視
                
            except KeyboardInterrupt:
                self.log_event("INFO", "システム健全性監視を停止します")
                break
            except Exception as e:
                self.log_event("ERROR", f"監視エラー: {e}")
                time.sleep(60)  # エラー時は1分待機
    
    def stop(self):
        """監視停止"""
        self.running = False

def signal_handler(sig, frame):
    """シグナルハンドラー"""
    print("\n監視を停止中...")
    monitor.stop()
    sys.exit(0)

if __name__ == "__main__":
    monitor = SystemHealthMonitor()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    monitor.run_health_check()