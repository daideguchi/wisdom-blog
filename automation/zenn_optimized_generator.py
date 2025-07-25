#!/usr/bin/env python3
"""
Zenn最適化AI記事生成スクリプト
Zenn特化の記事生成・品質チェック・自動投稿システム
"""

import os
import json
import frontmatter
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from anthropic import Anthropic
from typing import Dict, List, Optional, Any

# 設定
OBSIDIAN_VAULT_PATH = "/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents"
DEV_LOGS_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "01_Dev_Logs")
PROJECT_ARTICLES_PATH = "/Users/dd/Desktop/1_dev/coding-rule2/projects/post_tool/articles"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Zenn最適化設定
ZENN_OPTIMAL_CONFIG = {
    "min_word_count": 800,
    "max_word_count": 4000,
    "optimal_word_count": 1500,
    "max_topics": 5,
    "min_topics": 2,
    "supported_types": ["tech", "idea"],
    "quality_threshold": 0.8
}

# Zenn人気Topicマッピング
ZENN_POPULAR_TOPICS = {
    "python": ["python", "fastapi", "django", "flask", "pandas"],
    "javascript": ["javascript", "nodejs", "react", "vue", "nextjs"],
    "typescript": ["typescript", "react", "nodejs", "frontend"],
    "ai": ["machinelearning", "ai", "python", "tensorflow", "pytorch"],
    "web": ["frontend", "backend", "webdev", "css", "html"],
    "cloud": ["aws", "gcp", "azure", "docker", "kubernetes"],
    "mobile": ["flutter", "reactnative", "ios", "android"],
    "data": ["data", "sql", "analytics", "visualization"]
}

# 技術別最適emoji
TECH_EMOJIS = {
    "python": "🐍", "javascript": "🟨", "typescript": "🔷", "react": "⚛️",
    "vue": "💚", "ai": "🤖", "ml": "🧠", "data": "📊", "web": "🌐",
    "cloud": "☁️", "docker": "🐳", "git": "📝", "api": "🔌",
    "database": "🗄️", "security": "🔒", "performance": "⚡", "testing": "🧪"
}

class ZennOptimizedGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
        self.ensure_folders()
        
    def ensure_folders(self):
        """必要なフォルダを作成"""
        os.makedirs(PROJECT_ARTICLES_PATH, exist_ok=True)
        
    def get_recent_logs(self, days: int = 7) -> List[Dict[str, Any]]:
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
    
    def analyze_technical_domains(self, logs: List[Dict]) -> Dict[str, Any]:
        """技術ドメインを分析してZenn最適なトピックを抽出"""
        tech_analysis = {
            "primary_tech": set(),
            "secondary_tech": set(),
            "frameworks": set(),
            "tools": set(),
            "patterns": [],
            "complexity_level": "beginner"
        }
        
        tech_indicators = {
            "python": ["python", ".py", "pip", "venv", "django", "flask", "fastapi"],
            "javascript": ["javascript", ".js", "npm", "node", "yarn"],
            "typescript": ["typescript", ".ts", ".tsx", "tsc"],
            "react": ["react", "jsx", "useState", "useEffect", "component"],
            "ai": ["ai", "ml", "model", "training", "tensorflow", "pytorch", "claude", "openai"],
            "web": ["html", "css", "frontend", "backend", "api", "server"],
            "cloud": ["aws", "docker", "kubernetes", "deployment", "cloud"],
            "data": ["database", "sql", "pandas", "analytics", "visualization"]
        }
        
        # ログから技術を抽出
        all_text = " ".join([
            log.get("message", "") + " " + str(log.get("details", {}))
            for log in logs
        ]).lower()
        
        for tech, keywords in tech_indicators.items():
            matches = sum(1 for keyword in keywords if keyword in all_text)
            if matches >= 3:
                tech_analysis["primary_tech"].add(tech)
            elif matches >= 1:
                tech_analysis["secondary_tech"].add(tech)
        
        # 複雑度レベル判定
        advanced_indicators = ["architecture", "optimization", "performance", "scale", "system"]
        if any(indicator in all_text for indicator in advanced_indicators):
            tech_analysis["complexity_level"] = "advanced"
        elif len(tech_analysis["primary_tech"]) > 2:
            tech_analysis["complexity_level"] = "intermediate"
        
        return tech_analysis
    
    def select_optimal_emoji(self, tech_analysis: Dict[str, Any]) -> str:
        """技術分析に基づいて最適なemojiを選択"""
        primary_techs = tech_analysis["primary_tech"]
        
        # 優先度の高い技術から選択
        for tech in ["ai", "python", "react", "typescript", "javascript"]:
            if tech in primary_techs:
                return TECH_EMOJIS.get(tech, "📝")
        
        return "🚀"  # デフォルト
    
    def generate_zenn_topics(self, tech_analysis: Dict[str, Any]) -> List[str]:
        """Zenn人気トピックから最適なトピックリストを生成"""
        topics = []
        primary_techs = tech_analysis["primary_tech"]
        secondary_techs = tech_analysis["secondary_tech"]
        
        # 主要技術から必須トピック
        for tech in primary_techs:
            if tech in ZENN_POPULAR_TOPICS:
                topics.extend(ZENN_POPULAR_TOPICS[tech][:2])
        
        # 副次技術から補完
        for tech in secondary_techs:
            if tech in ZENN_POPULAR_TOPICS and len(topics) < 4:
                topics.append(ZENN_POPULAR_TOPICS[tech][0])
        
        # 重複削除・優先度ソート
        unique_topics = list(dict.fromkeys(topics))
        
        # Zenn人気度に基づく優先度
        priority_topics = ["python", "javascript", "react", "ai", "typescript", "nodejs"]
        sorted_topics = sorted(unique_topics, key=lambda x: 
                             priority_topics.index(x) if x in priority_topics else 100)
        
        return sorted_topics[:ZENN_OPTIMAL_CONFIG["max_topics"]]
    
    def create_zenn_optimized_prompt(self, logs: List[Dict], tech_analysis: Dict) -> str:
        """Zenn最適化プロンプト生成"""
        
        log_summary = []
        for log in logs[-15:]:  # 最新15件
            timestamp = log.get("timestamp", "")
            log_type = log.get("type", "")
            message = log.get("message", "")
            log_summary.append(f"{timestamp}: [{log_type}] {message}")
        
        primary_techs = ", ".join(tech_analysis["primary_tech"])
        complexity = tech_analysis["complexity_level"]
        suggested_topics = self.generate_zenn_topics(tech_analysis)
        suggested_emoji = self.select_optimal_emoji(tech_analysis)
        
        prompt = f"""
あなたはZenn特化の技術記事ライターです。以下の開発ログを分析して、Zennで人気が出る高品質な技術記事を生成してください。

## 技術分析結果
- 主要技術: {primary_techs}
- 複雑度レベル: {complexity}
- 推奨topics: {suggested_topics}
- 推奨emoji: {suggested_emoji}

## 開発ログ（最新15件）
{chr(10).join(log_summary)}

## Zenn記事最適化要件
1. **タイトル**: SEO最適化・具体的・魅力的（30-60文字）
2. **文字数**: {ZENN_OPTIMAL_CONFIG["optimal_word_count"]}文字程度
3. **構成**: 導入→問題→解決→コード例→学び→まとめ
4. **実用性**: 読者が実際に試せる内容
5. **独自性**: 実体験に基づく知見・ハマった点・解決法
6. **可読性**: 見出し・箇条書き・コードブロック適切使用

## 高品質記事の特徴
- 具体的なコード例とその説明
- 実際にハマった問題と解決過程
- なぜその方法を選んだかの理由
- 他の手法との比較・検討
- 読者への明確なメリット

## 出力形式（JSON）
```json
{{
    "title": "実践的で魅力的なタイトル（30-60文字）",
    "emoji": "{suggested_emoji}",
    "type": "tech",
    "topics": {json.dumps(suggested_topics, ensure_ascii=False)},
    "published": false,
    "content": "記事本文（Markdown形式）",
    "estimated_reading_time": "3-5分",
    "target_audience": "初心者|中級者|上級者",
    "key_takeaways": ["学習ポイント1", "学習ポイント2", "学習ポイント3"]
}}
```

記事本文の構成例：
# タイトル

## はじめに
なぜこの記事を書くか・読者にどんなメリットがあるか

## 問題・課題
実際に遭遇した問題・なぜその問題が重要か

## 解決方法
具体的な実装・コード例・手順

```python
# 実際のコード例
def example_function():
    return "具体的で動作する例"
```

## ハマったポイント
実際にハマった点・解決に時間がかかった理由

## 他の方法との比較
なぜこの方法を選んだか・他の選択肢

## 学んだこと・ポイント
今回の体験から得られた知見・注意点

## まとめ
要点の整理・次のステップ・読者へのアドバイス

実体験に基づき、読者が実際に実装できる具体的で実用的な内容にしてください。
"""
        return prompt
    
    def generate_article(self, logs: List[Dict]) -> Optional[Dict[str, Any]]:
        """Zenn最適化AI記事生成"""
        if not self.client:
            print("❌ Claude APIキーが設定されていません")
            return None
            
        if len(logs) < 5:
            print(f"❌ ログが不足しています（最低5件必要、現在{len(logs)}件）")
            return None
        
        print("🤖 Zenn最適化AI記事生成中...")
        
        tech_analysis = self.analyze_technical_domains(logs)
        prompt = self.create_zenn_optimized_prompt(logs, tech_analysis)
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            print(f"📄 AI応答長: {len(content)}文字")
            
            # JSON抽出（より堅牢）
            json_matches = re.findall(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if not json_matches:
                json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            
            if json_matches:
                try:
                    article_data = json.loads(json_matches[0])
                    return self.validate_article_quality(article_data)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析エラー: {e}")
                    return None
            else:
                print("❌ AIの出力からJSONを抽出できませんでした")
                print("デバッグ用出力:")
                print(content[:500] + "...")
                return None
                
        except Exception as e:
            print(f"❌ AI記事生成エラー: {e}")
            return None
    
    def validate_article_quality(self, article_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """記事品質バリデーション"""
        quality_issues = []
        
        # 必須フィールドチェック
        required_fields = ["title", "emoji", "type", "topics", "content"]
        for field in required_fields:
            if not article_data.get(field):
                quality_issues.append(f"必須フィールド不足: {field}")
        
        # 文字数チェック
        content = article_data.get("content", "")
        word_count = len(content)
        if word_count < ZENN_OPTIMAL_CONFIG["min_word_count"]:
            quality_issues.append(f"文字数不足: {word_count}文字（最低{ZENN_OPTIMAL_CONFIG['min_word_count']}文字）")
        elif word_count > ZENN_OPTIMAL_CONFIG["max_word_count"]:
            quality_issues.append(f"文字数過多: {word_count}文字（最大{ZENN_OPTIMAL_CONFIG['max_word_count']}文字）")
        
        # トピック数チェック
        topics = article_data.get("topics", [])
        if len(topics) < ZENN_OPTIMAL_CONFIG["min_topics"]:
            quality_issues.append(f"トピック不足: {len(topics)}個（最低{ZENN_OPTIMAL_CONFIG['min_topics']}個）")
        
        # コードブロックの存在チェック（技術記事の場合）
        if article_data.get("type") == "tech" and "```" not in content:
            quality_issues.append("技術記事にコード例がありません")
        
        if quality_issues:
            print("⚠️ 品質問題を検出:")
            for issue in quality_issues:
                print(f"   - {issue}")
            
            # 致命的な問題がある場合は記事を破棄
            if len(quality_issues) > 2:
                print("❌ 品質問題が多すぎるため記事を破棄")
                return None
        
        # 品質スコア計算
        quality_score = 1.0 - (len(quality_issues) * 0.2)
        article_data["quality_score"] = max(quality_score, 0.0)
        
        print(f"✅ 記事品質スコア: {quality_score:.2f}")
        return article_data
    
    def save_zenn_article(self, article_data: Dict[str, Any]) -> Optional[Path]:
        """Zenn最適化記事保存"""
        if not article_data:
            return None
            
        title = article_data.get("title", "Untitled")
        safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Zenn記事用ファイル名（SEO最適化）
        slug = f"{timestamp}_{safe_title.lower()}"
        filename = f"{slug}.md"
        file_path = Path(PROJECT_ARTICLES_PATH) / filename
        
        # Zenn最適化フロントマター
        post = frontmatter.Post(
            content=article_data.get("content", ""),
            title=title,
            emoji=article_data.get("emoji", "📝"),
            type=article_data.get("type", "tech"),
            topics=article_data.get("topics", []),
            published=False,  # 品質確認後に手動でtrue
            created_at=datetime.now().isoformat(),
            quality_score=article_data.get("quality_score", 0.0),
            estimated_reading_time=article_data.get("estimated_reading_time", "3-5分"),
            target_audience=article_data.get("target_audience", "中級者"),
            key_takeaways=article_data.get("key_takeaways", []),
            source="zenn_optimized_ai",
            slug=slug
        )
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                frontmatter.dump(post, f)
            print(f"✅ Zenn最適化記事を保存: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            return None
    
    def generate_and_save(self) -> bool:
        """メイン処理：記事生成と保存"""
        print("🚀 Zenn最適化AI記事生成を開始...")
        
        logs = self.get_recent_logs(days=7)
        
        if not logs:
            print("❌ ログが見つかりません")
            print("先に dev_log_watcher.py を実行してログを蓄積してください")
            return False
        
        print(f"📊 {len(logs)}件のログを分析中...")
        
        article_data = self.generate_article(logs)
        if article_data:
            saved_path = self.save_zenn_article(article_data)
            if saved_path:
                print(f"\n🎉 Zenn最適化記事生成完了!")
                print(f"   📝 タイトル: {article_data.get('title')}")
                print(f"   {article_data.get('emoji')} Topics: {', '.join(article_data.get('topics', []))}")
                print(f"   📊 品質スコア: {article_data.get('quality_score', 0.0):.2f}")
                print(f"   📁 ファイル: {saved_path}")
                print(f"\n📋 次のステップ:")
                print(f"1. 生成された記事の内容を確認・編集")
                print(f"2. published: true に変更")
                print(f"3. git add articles/ && git commit -m '📝 新記事追加'")
                print(f"4. git push origin main で自動投稿")
                print(f"5. Zenn: https://zenn.dev/daideguchi で確認")
                return True
        
        return False

def main():
    print("🚀 Zenn最適化AI記事生成システム")
    print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    generator = ZennOptimizedGenerator()
    success = generator.generate_and_save()
    
    if not success:
        print("\n❌ 記事生成に失敗しました")
        print("🔧 トラブルシューティング:")
        print("- ANTHROPIC_API_KEY環境変数が設定されているか確認")
        print("- 十分なログが蓄積されているか確認（最低5件）")
        print("- python3 automation/dev_log_watcher.py を先に実行")
        print("- インターネット接続を確認")

if __name__ == "__main__":
    main()