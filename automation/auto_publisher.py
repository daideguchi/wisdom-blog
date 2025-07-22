"""
自動投稿システム
AIが生成した記事をZennとブログに自動投稿
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

from config import get_config

class AutoPublisher:
    def __init__(self):
        self.config = get_config()
        self.project_root = Path("/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool")
        self.articles_dir = self.project_root / "articles"
        
    def publish_to_zenn(self, article_path):
        """
        Zennに記事を投稿（Zenn Connectによる自動同期）
        """
        try:
            # Zenn記事のメタデータ確認
            with open(article_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'published: false' in content:
                print(f"⏸️  記事 {article_path.name} は非公開設定のためスキップ")
                return False
                
            # Gitに追加・コミット（Zenn Connectが自動同期）
            subprocess.run(['git', 'add', str(article_path)], 
                          cwd=self.project_root, check=True)
            subprocess.run(['git', 'commit', '-m', f'📝 新記事追加: {article_path.stem}'], 
                          cwd=self.project_root, check=True)
            subprocess.run(['git', 'push'], 
                          cwd=self.project_root, check=True)
            
            print(f"✅ Zenn投稿完了: {article_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Zenn投稿失敗: {e}")
            return False
    
    def deploy_blog(self):
        """
        Astroブログをデプロイ
        """
        try:
            blog_dir = self.project_root / "blog-app"
            
            # ブログビルド
            subprocess.run(['npm', 'run', 'build'], 
                          cwd=blog_dir, check=True)
            
            # Vercelデプロイ（設定されている場合）
            if self.config['blog']['auto_deploy']:
                subprocess.run(['npx', 'vercel', '--prod'], 
                              cwd=blog_dir, check=True)
                print("✅ ブログデプロイ完了")
            
            return True
            
        except Exception as e:
            print(f"❌ ブログデプロイ失敗: {e}")
            return False
    
    def publish_new_articles(self):
        """
        新しい記事を検出して自動投稿
        """
        if not self.articles_dir.exists():
            print("📁 articlesフォルダが見つかりません")
            return
        
        # 新しい記事を検出（git statusベース）
        try:
            result = subprocess.run(['git', 'status', '--porcelain', 'articles/'], 
                                  cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            new_articles = []
            for line in result.stdout.split('\n'):
                if line.startswith('??') or line.startswith('A '):
                    filepath = line[3:].strip()
                    if filepath.endswith('.md'):
                        new_articles.append(self.project_root / filepath)
            
            if not new_articles:
                print("📝 新しい記事はありません")
                return
            
            print(f"🔍 {len(new_articles)}個の新記事を検出")
            
            # 各記事を投稿
            for article_path in new_articles:
                print(f"\n📤 投稿処理開始: {article_path.name}")
                
                # Zenn投稿
                if self.publish_to_zenn(article_path):
                    print(f"✅ {article_path.name} Zenn投稿完了")
                
                # ブログ投稿は一括で実行
            
            # ブログデプロイ
            if new_articles:
                self.deploy_blog()
                
        except Exception as e:
            print(f"❌ 自動投稿処理エラー: {e}")

def main():
    """メイン実行関数"""
    print("🚀 AI自動投稿システム開始")
    print(f"📅 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    publisher = AutoPublisher()
    publisher.publish_new_articles()
    
    print("✅ 自動投稿処理完了")

if __name__ == "__main__":
    main()