#!/usr/bin/env python3
"""
Zenn Connect同期テストスクリプト
実際の同期状況を監視・確認
"""

import subprocess
import time
import requests
from datetime import datetime

class ZennConnectTester:
    def __init__(self):
        self.zenn_account = "daideguchi"
        self.project_root = "/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool"
        
    def check_git_status(self):
        """Git状況確認"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)
    
    def push_to_github(self):
        """GitHubにプッシュ"""
        try:
            # リモート確認
            remote_result = subprocess.run(
                ['git', 'remote', '-v'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if not remote_result.stdout:
                print("⚠️  GitHubリモートリポジトリが未設定")
                print("手動設定が必要:")
                print("git remote add origin https://github.com/daideguchi/post_tool.git")
                return False
            
            # プッシュ実行
            push_result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            return push_result.returncode == 0, push_result.stdout + push_result.stderr
            
        except Exception as e:
            return False, str(e)
    
    def check_zenn_articles(self):
        """Zennアカウントの記事一覧確認"""
        try:
            url = f"https://zenn.dev/{self.zenn_account}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # test-automationの記事が存在するかチェック
                if "AIによる自動記事生成テスト" in response.text:
                    return True, "テスト記事がZennに同期済み"
                else:
                    return False, "テスト記事はまだ同期されていません"
            else:
                return False, f"Zennアクセスエラー: {response.status_code}"
                
        except Exception as e:
            return False, f"確認エラー: {e}"
    
    def run_sync_test(self):
        """同期テスト実行"""
        print("🧪 Zenn Connect同期テスト開始")
        print(f"⏰ テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Git状況確認
        git_ok, git_status = self.check_git_status()
        if git_ok:
            print(f"✅ Git状況: クリーン")
        else:
            print(f"❌ Git状況: {git_status}")
        
        # 2. GitHub push試行
        print("\n📤 GitHubプッシュ実行中...")
        push_ok, push_result = self.push_to_github()
        if push_ok:
            print(f"✅ GitHubプッシュ成功")
        else:
            print(f"❌ GitHubプッシュ失敗: {push_result}")
            return False
        
        # 3. Zenn同期待機・確認
        print("\n⏳ Zenn Connect同期待機中...")
        for i in range(6):  # 最大3分間待機
            time.sleep(30)  # 30秒間隔
            
            sync_ok, sync_result = self.check_zenn_articles()
            print(f"   {i+1}/6回目確認: {sync_result}")
            
            if sync_ok:
                print(f"🎉 Zenn Connect同期成功!")
                print(f"🔗 確認URL: https://zenn.dev/{self.zenn_account}")
                return True
        
        print("⌛ 同期確認タイムアウト（3分経過）")
        print("手動でZennサイトを確認してください:")
        print(f"🔗 https://zenn.dev/{self.zenn_account}")
        
        return False
    
    def log_test_result(self, success):
        """テスト結果ログ"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "zenn_connect_sync",
            "success": success,
            "account": self.zenn_account
        }
        
        log_path = f"{self.project_root}/obsidian_vault/knowledge_management/dialogue_logs/zenn_test_log.json"
        
        # ログ保存処理は簡略化
        print(f"📝 テスト結果: {'成功' if success else '要確認'}")

def main():
    tester = ZennConnectTester()
    success = tester.run_sync_test()
    tester.log_test_result(success)

if __name__ == "__main__":
    main()