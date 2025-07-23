#!/usr/bin/env python3
"""
スマート記事生成システム
頭脳ディレクトリのAPIキーを自動活用
"""

import os
import json
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 頭脳ディレクトリからAPIキー読み込み
def load_brain_api_keys():
    """頭脳ディレクトリからAPIキー自動読み込み"""
    brain_dir = Path("/Users/dd/Desktop/1_dev/coding-rule2")
    env_file = brain_dir / ".env"
    
    if env_file.exists():
        api_keys = {}
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    api_keys[key] = value
                    os.environ[key] = value
        
        print(f"✅ 頭脳からAPIキー読み込み完了: {len(api_keys)}個")
        return api_keys
    else:
        print("❌ 頭脳ディレクトリの.envファイルが見つかりません")
        return {}

class SmartArticleGenerator:
    def __init__(self):
        self.project_dir = Path("/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool")
        self.api_keys = load_brain_api_keys()
        
        # Claude API確認
        self.anthropic_api_key = self.api_keys.get('ANTHROPIC_API_KEY')
        if not self.anthropic_api_key:
            print("❌ Claude APIキーが見つかりません")
            sys.exit(1)
        
        self.log_file = self.project_dir / "logs" / "smart_article.log"
        self.log_file.parent.mkdir(exist_ok=True)
    
    def log_event(self, message):
        """ログ記録"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        print(message)
    
    def get_recent_dev_logs(self):
        """最近の開発ログ取得"""
        log_files = []
        
        # シンプル監視ログ
        simple_log = self.project_dir / "logs" / "simple_dev.log"
        if simple_log.exists():
            log_files.append(simple_log)
        
        # Obsidianログ（iCloud同期版）
        obsidian_inbox = Path("/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents/00_INBOX")
        if obsidian_inbox.exists():
            dev_logs = list(obsidian_inbox.glob("dev_log_*.md"))
            log_files.extend(dev_logs[-3:])  # 最新3日分
        
        return log_files
    
    def analyze_logs_for_article(self):
        """ログ分析して記事生成判断"""
        log_files = self.get_recent_dev_logs()
        
        if not log_files:
            self.log_event("ログファイルなし - 記事生成スキップ")
            return None
        
        # 簡単な活動量チェック
        total_content = ""
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    total_content += content
            except Exception as e:
                self.log_event(f"ログ読み込みエラー: {e}")
        
        # 最小限の活動量チェック
        if len(total_content) < 200:  # 200文字未満は記事生成しない
            self.log_event("活動量不足 - 記事生成スキップ")
            return None
        
        return total_content
    
    def generate_simple_article(self):
        """シンプル記事生成"""  
        log_content = self.analyze_logs_for_article()
        if not log_content:
            return False
        
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=self.anthropic_api_key)
            
            # 開発ログから記事生成プロンプト
            prompt = f"""
最近の開発活動から技術記事を生成してください。

開発ログ情報：
{log_content}

以下の要件でZenn記事を作成：
1. タイトルは具体的で魅力的に
2. 実際の開発体験に基づく内容
3. 文字数は800-1200文字程度
4. Zenn Markdown形式で直接出力

以下の形式で出力：
---
title: "記事タイトル"
emoji: "適切な絵文字"
type: "tech"
topics: ["適切なトピック1", "適切なトピック2"]
published: false
published_at: "{datetime.now().strftime('%Y-%m-%d')}"
---

# 記事タイトル

## はじめに
(開発背景・動機)

## 実装・解決内容
(具体的な技術内容)

## 学んだこと・ポイント
(重要なポイントや注意事項)

## まとめ
(締めくくり)
"""
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            self.log_event("✅ AI記事生成完了")
            
            # 記事保存
            self.save_article(content)
            return True
            
        except Exception as e:
            self.log_event(f"❌ 記事生成エラー: {e}")
            return False
    
    def save_article(self, article_content):
        """記事保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        article_file = self.project_dir / "articles" / f"auto_generated_{timestamp}.md"
        
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(article_content)
        
        self.log_event(f"📝 記事保存: {article_file}")

def main():
    generator = SmartArticleGenerator()
    success = generator.generate_simple_article()
    
    if success:
        print("🎉 記事生成完了")
    else:
        print("⏭️  記事生成スキップ")

if __name__ == "__main__":
    main()