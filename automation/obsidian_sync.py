#!/usr/bin/env python3
"""
Obsidian同期システム
post_toolプロジェクト ↔ Obsidian Vault の双方向同期
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

class ObsidianSync:
    def __init__(self):
        self.project_root = Path("/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool")
        self.obsidian_vault = Path("/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents")
        self.project_vault = self.project_root / "obsidian_vault"
        
        # 同期設定
        self.sync_config = {
            "vault_to_project": {
                "04_OUTPUT/zenn_drafts": "articles",
                "04_OUTPUT/published": "published_articles",
                "knowledge_management": "knowledge_base"
            },
            "project_to_vault": {
                "articles": "04_OUTPUT/zenn_drafts",
                "automation": "06_AUTOMATION",
                "51_Udemy_AI副業講座": "51_Udemy_AI副業講座"
            }
        }
        
    def ensure_structure(self):
        """プロジェクト内Obsidianフォルダ構造を確保"""
        folders = [
            "00_INBOX",
            "01_LITERATURE", 
            "02_PERMANENT",
            "03_MOC",
            "04_OUTPUT/zenn_drafts",
            "04_OUTPUT/published",
            "knowledge_management/dialogue_logs",
            "06_AUTOMATION"
        ]
        
        for folder in folders:
            (self.project_vault / folder).mkdir(parents=True, exist_ok=True)
            
        print("✅ Obsidianフォルダ構造確保完了")
    
    def sync_to_obsidian(self):
        """プロジェクト → Obsidian Vault同期"""
        if not self.obsidian_vault.exists():
            print("❌ ObsidianVaultが見つかりません")
            return False
            
        synced_files = 0
        
        for project_path, vault_path in self.sync_config["project_to_vault"].items():
            source = self.project_root / project_path
            target = self.obsidian_vault / vault_path
            
            if source.exists():
                target.mkdir(parents=True, exist_ok=True)
                
                # .mdファイルのみ同期
                for md_file in source.rglob("*.md"):
                    relative_path = md_file.relative_to(source)
                    target_file = target / relative_path
                    
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(md_file, target_file)
                    synced_files += 1
                    
        print(f"✅ プロジェクト→Obsidian同期完了: {synced_files}ファイル")
        return True
    
    def sync_from_obsidian(self):
        """Obsidian Vault → プロジェクト同期"""
        if not self.obsidian_vault.exists():
            print("❌ ObsidianVaultが見つかりません")
            return False
            
        synced_files = 0
        
        for vault_path, project_path in self.sync_config["vault_to_project"].items():
            source = self.obsidian_vault / vault_path
            target = self.project_root / project_path
            
            if source.exists():
                target.mkdir(parents=True, exist_ok=True)
                
                # .mdファイルのみ同期
                for md_file in source.rglob("*.md"):
                    relative_path = md_file.relative_to(source)
                    target_file = target / relative_path
                    
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(md_file, target_file)
                    synced_files += 1
                    
        print(f"✅ Obsidian→プロジェクト同期完了: {synced_files}ファイル")
        return True
    
    def create_sync_log(self):
        """同期ログ作成"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "sync_status": "completed",
            "project_vault_exists": self.project_vault.exists(),
            "obsidian_vault_exists": self.obsidian_vault.exists()
        }
        
        log_path = self.project_vault / "knowledge_management/dialogue_logs/sync_log.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 既存ログ読み込み
        logs = []
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        
        logs.append(log_entry)
        
        # 最新10件のみ保持
        logs = logs[-10:]
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
        print(f"📝 同期ログ記録: {log_path}")
    
    def run_full_sync(self):
        """完全同期実行"""
        print("🔄 Obsidian同期開始...")
        
        # 1. フォルダ構造確保
        self.ensure_structure()
        
        # 2. 双方向同期
        self.sync_to_obsidian()
        self.sync_from_obsidian()
        
        # 3. ログ記録
        self.create_sync_log()
        
        print("✅ Obsidian同期完了")

def main():
    sync = ObsidianSync()
    sync.run_full_sync()

if __name__ == "__main__":
    main()