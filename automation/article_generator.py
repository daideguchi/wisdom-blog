#!/usr/bin/env python3
"""
AI記事生成スクリプト
蓄積された開発ログからClaude AIが技術記事を自動生成します
"""

import os
import json
import frontmatter
from datetime import datetime, timedelta
from pathlib import Path
from anthropic import Anthropic
import re

# 設定
OBSIDIAN_VAULT_PATH = "/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents"
DEV_LOGS_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "01_Dev_Logs")
ARTICLES_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "02_Generated_Articles")
PROJECT_ARTICLES_PATH = "/Users/dd/Desktop/1_dev/post_tool/articles"

# 記事生成設定
MIN_LOG_ENTRIES = 5
TARGET_WORD_COUNT = 800
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class ArticleGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
        self.ensure_folders()
        
    def ensure_folders(self):
        """必要なフォルダを作成"""
        os.makedirs(ARTICLES_PATH, exist_ok=True)
        os.makedirs(PROJECT_ARTICLES_PATH, exist_ok=True)
        
    def get_recent_logs(self, days=7):
        """最近のログを取得"""
        all_logs = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            log_file = os.path.join(DEV_LOGS_PATH, f"dev_log_{date.strftime('%Y-%m-%d')}.json")
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        daily_logs = json.load(f)
                        all_logs.extend(daily_logs)
                except Exception as e:
                    print(f"ログ読み込みエラー ({log_file}): {e}")
        
        return all_logs
    
    def analyze_logs(self, logs):
        """ログを分析してテーマを抽出"""
        themes = {
            "git_commits": [],
            "file_changes": [],
            "errors": [],
            "technologies": set(),
            "patterns": []
        }
        
        for log in logs:
            log_type = log.get("type")
            message = log.get("message", "")
            details = log.get("details", {})
            
            if log_type == "git_commit":
                themes["git_commits"].append(log)
                
            elif log_type == "file_modified":
                themes["file_changes"].append(log)
                extension = details.get("extension", "")
                if extension in [".py", ".js", ".ts", ".tsx", ".jsx"]:
                    themes["technologies"].add(self.get_tech_from_extension(extension))
                    
            elif "error" in message.lower():
                themes["errors"].append(log)
        
        return themes
    
    def get_tech_from_extension(self, ext):
        """ファイル拡張子から技術名を取得"""
        tech_map = {
            ".py": "Python",
            ".js": "JavaScript", 
            ".ts": "TypeScript",
            ".tsx": "React/TypeScript",
            ".jsx": "React",
            ".vue": "Vue.js",
            ".go": "Go",
            ".rs": "Rust"
        }
        return tech_map.get(ext, ext)
    
    def generate_article_prompt(self, themes, logs):
        """記事生成用のプロンプトを作成"""
        
        # ログの要約
        log_summary = []
        for log in logs[-10:]:  # 最新10件
            timestamp = log.get("timestamp", "")
            log_type = log.get("type", "")
            message = log.get("message", "")
            log_summary.append(f"{timestamp}: [{log_type}] {message}")
        
        technologies = ", ".join(themes["technologies"])
        commit_count = len(themes["git_commits"])
        file_changes = len(themes["file_changes"])
        
        prompt = f"""
あなたは技術ブログライターです。以下の開発ログを分析して、技術記事を生成してください。

## 開発活動の概要
- 使用技術: {technologies}
- Gitコミット数: {commit_count}
- ファイル変更数: {file_changes}

## 開発ログ（最新10件）
{chr(10).join(log_summary)}

## 記事生成の要件
1. タイトルは魅力的で具体的にする
2. 実際の開発体験に基づいた内容にする
3. 技術的な学びや解決したことを中心にする
4. コードブロックがある場合は含める
5. 文字数は{TARGET_WORD_COUNT}文字程度
6. Zenn記事形式で出力

## 出力形式
以下のJSON形式で出力してください：

{{
    "title": "記事タイトル",
    "emoji": "適切な絵文字",
    "type": "tech",
    "topics": ["関連トピック1", "関連トピック2"],
    "published": false,
    "content": "記事本文（Markdown形式）"
}}

記事本文は以下の構成にしてください：
- 導入（何について書くか）
- 問題・課題の説明
- 解決方法・実装内容
- 学んだこと・ポイント
- まとめ

実際の開発体験から得られた知見を重視し、読者の役に立つ実用的な内容にしてください。
"""
        
        return prompt
    
    def generate_article(self, logs):
        """AIを使って記事を生成"""
        if not self.client:
            print("❌ Claude APIキーが設定されていません")
            print("環境変数 ANTHROPIC_API_KEY を設定してください")
            return None
            
        if len(logs) < MIN_LOG_ENTRIES:
            print(f"❌ ログが不足しています（最低{MIN_LOG_ENTRIES}件必要、現在{len(logs)}件）")
            return None
        
        print("🤖 AIが記事を生成中...")
        
        themes = self.analyze_logs(logs)
        prompt = self.generate_article_prompt(themes, logs)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # JSONを抽出
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                article_data = json.loads(json_match.group())
                return article_data
            else:
                print("❌ AIの出力からJSONを抽出できませんでした")
                return None
                
        except Exception as e:
            print(f"❌ AI記事生成エラー: {e}")
            return None
    
    def save_article(self, article_data):
        """記事をファイルに保存"""
        if not article_data:
            return None
            
        title = article_data.get("title", "Untitled")
        safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Obsidianに保存
        obsidian_filename = f"{timestamp}_{safe_title}.md"
        obsidian_path = os.path.join(ARTICLES_PATH, obsidian_filename)
        
        # Zenn記事用ファイル名（slug生成）
        slug = f"{datetime.now().strftime('%Y%m%d')}_{safe_title.lower()}"
        zenn_filename = f"{slug}.md"
        zenn_path = os.path.join(PROJECT_ARTICLES_PATH, zenn_filename)
        
        # フロントマターを作成
        post = frontmatter.Post(
            content=article_data.get("content", ""),
            title=title,
            emoji=article_data.get("emoji", "📝"),
            type=article_data.get("type", "tech"),
            topics=article_data.get("topics", []),
            published=False,  # 手動確認後にpublish
            generated_at=datetime.now().isoformat(),
            source="dev_log_ai"
        )
        
        # 両方の場所に保存
        for file_path in [obsidian_path, zenn_path]:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    frontmatter.dump(post, f)
                print(f"✅ 記事を保存: {file_path}")
            except Exception as e:
                print(f"❌ 保存エラー ({file_path}): {e}")
        
        return zenn_path
    
    def generate_and_save(self):
        """記事生成と保存のメイン処理"""
        print("📊 開発ログを分析中...")
        
        logs = self.get_recent_logs(days=7)
        
        if not logs:
            print("❌ ログが見つかりません")
            print("先に dev_log_watcher.py を実行してログを蓄積してください")
            return False
        
        print(f"📝 {len(logs)}件のログを発見")
        
        article_data = self.generate_article(logs)
        if article_data:
            saved_path = self.save_article(article_data)
            if saved_path:
                print(f"🎉 記事生成完了!")
                print(f"   タイトル: {article_data.get('title')}")
                print(f"   ファイル: {saved_path}")
                print(f"")
                print(f"📝 次のステップ:")
                print(f"1. 生成された記事を確認・編集")
                print(f"2. published: true に変更")
                print(f"3. git push で自動投稿")
                return True
        
        return False

def main():
    print("🚀 AI記事生成を開始...")
    
    generator = ArticleGenerator()
    success = generator.generate_and_save()
    
    if not success:
        print("❌ 記事生成に失敗しました")
        print("トラブルシューティング:")
        print("- APIキーが設定されているか確認")
        print("- 十分なログが蓄積されているか確認")
        print("- dev_log_watcher.py を先に実行")

if __name__ == "__main__":
    main()