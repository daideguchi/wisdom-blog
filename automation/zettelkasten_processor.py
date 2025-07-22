"""
ツェッテルカステン自動整理システム
Obsidianノートの完全自動化処理
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
import frontmatter

class ZettelkastenProcessor:
    def __init__(self):
        self.obsidian_vault = "/Users/dd/Library/Mobile Documents/iCloud~md~obsidian/Documents"
        self.inbox_path = os.path.join(self.obsidian_vault, "00_INBOX")
        self.literature_path = os.path.join(self.obsidian_vault, "01_LITERATURE")
        self.permanent_path = os.path.join(self.obsidian_vault, "02_PERMANENT")
        self.moc_path = os.path.join(self.obsidian_vault, "03_MOC")
        self.output_path = os.path.join(self.obsidian_vault, "04_OUTPUT")
        
        self.ensure_folders()
    
    def ensure_folders(self):
        """ツェッテルカステン フォルダ構造を作成"""
        folders = [
            self.inbox_path,
            self.literature_path, 
            self.permanent_path,
            self.moc_path,
            self.output_path,
            os.path.join(self.output_path, "zenn_drafts"),
            os.path.join(self.output_path, "published")
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
            
        print("✅ ツェッテルカステン フォルダ構造を確認")
    
    def generate_zettel_id(self):
        """ユニークなツェッテルIDを生成"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"Z{timestamp}"
    
    def create_permanent_note_template(self, title, concept, links=None):
        """恒久ノートテンプレートを生成"""
        zettel_id = self.generate_zettel_id()
        created_date = datetime.now().strftime("%Y-%m-%d")
        
        template = f"""---
id: {zettel_id}
title: "{title}"
type: permanent
created: {created_date}
tags: [zettelkasten, concept]
---

# {title}

## 核心概念
{concept}

## 詳細説明


## 関連するアイデア
{self._format_links(links)}

## 応用・実例


## 参考文献


## 更新履歴
- {created_date}: 初回作成

---
*ツェッテルID: {zettel_id}*
"""
        return template, zettel_id
    
    def _format_links(self, links):
        """リンクをマークダウン形式にフォーマット"""
        if not links:
            return "- [[]]"
        
        formatted = []
        for link in links:
            formatted.append(f"- [[{link}]]")
        return "\n".join(formatted)
    
    def process_inbox_notes(self):
        """受信箱のノートを処理"""
        if not os.path.exists(self.inbox_path):
            return
        
        processed_count = 0
        
        for filename in os.listdir(self.inbox_path):
            if filename.endswith('.md'):
                file_path = os.path.join(self.inbox_path, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        post = frontmatter.load(f)
                    
                    # フローティングノートを分析
                    content = post.content
                    title = post.metadata.get('title', filename[:-3])
                    
                    # 原子性チェック：複数のアイデアが含まれているか
                    if self._contains_multiple_ideas(content):
                        suggestions = self._suggest_note_split(content, title)
                        print(f"📝 分割推奨: {filename}")
                        for i, suggestion in enumerate(suggestions, 1):
                            print(f"   {i}. {suggestion}")
                    
                    # 恒久ノート候補判定
                    if self._is_permanent_note_candidate(content):
                        self._promote_to_permanent(file_path, post)
                        processed_count += 1
                        
                except Exception as e:
                    print(f"❌ 処理エラー ({filename}): {e}")
        
        print(f"✅ 受信箱処理完了: {processed_count}件処理")
    
    def _contains_multiple_ideas(self, content):
        """複数のアイデアが含まれているかチェック"""
        # 見出しの数で判定（簡易版）
        headers = re.findall(r'^#{1,6}\s+', content, re.MULTILINE)
        return len(headers) > 3
    
    def _suggest_note_split(self, content, title):
        """ノート分割の提案"""
        suggestions = []
        
        # 見出しベースの分割提案
        headers = re.findall(r'^(#{1,6})\s+(.+)', content, re.MULTILINE)
        for level, header_text in headers:
            if len(level) <= 2:  # H1, H2レベルの見出し
                suggestions.append(f"{title} - {header_text}")
        
        return suggestions[:3]  # 最大3つまで
    
    def _is_permanent_note_candidate(self, content):
        """恒久ノート候補かどうか判定"""
        # 文字数チェック
        if len(content) < 200:
            return False
        
        # リンクの存在チェック
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        if len(links) < 1:
            return False
        
        # 概念的内容のキーワードチェック
        concept_keywords = ['原則', '法則', 'パターン', '理論', '概念', '手法', 'メソッド']
        for keyword in concept_keywords:
            if keyword in content:
                return True
        
        return False
    
    def _promote_to_permanent(self, inbox_path, post):
        """恒久ノートに昇格"""
        title = post.metadata.get('title', 'Untitled')
        zettel_id = self.generate_zettel_id()
        
        # メタデータ更新
        post.metadata.update({
            'id': zettel_id,
            'type': 'permanent',
            'promoted_date': datetime.now().strftime("%Y-%m-%d"),
            'tags': post.metadata.get('tags', []) + ['zettelkasten', 'permanent']
        })
        
        # 恒久ノートフォルダに移動
        new_filename = f"{zettel_id}_{title.replace(' ', '_')}.md"
        new_path = os.path.join(self.permanent_path, new_filename)
        
        with open(new_path, 'w', encoding='utf-8') as f:
            frontmatter.dump(post, f)
        
        # 元ファイル削除
        os.remove(inbox_path)
        
        print(f"✅ 恒久ノートに昇格: {new_filename}")
    
    def discover_missing_links(self):
        """欠落しているリンクを発見"""
        permanent_notes = {}
        
        # 恒久ノートを全て読み込み
        for filename in os.listdir(self.permanent_path):
            if filename.endswith('.md'):
                file_path = os.path.join(self.permanent_path, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    permanent_notes[filename] = content
        
        # 潜在的なリンクを発見
        suggestions = []
        
        for note1, content1 in permanent_notes.items():
            for note2, content2 in permanent_notes.items():
                if note1 != note2:
                    # 共通キーワード検出
                    similarity = self._calculate_content_similarity(content1, content2)
                    if similarity > 0.3:  # 閾値
                        suggestions.append({
                            'note1': note1,
                            'note2': note2,
                            'similarity': similarity
                        })
        
        return suggestions
    
    def _calculate_content_similarity(self, content1, content2):
        """コンテンツ類似度を計算（簡易版）"""
        # 単語セットベースの類似度
        words1 = set(re.findall(r'\w+', content1.lower()))
        words2 = set(re.findall(r'\w+', content2.lower()))
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0
    
    def generate_moc_suggestions(self):
        """MOC作成提案を生成"""
        # タグベースのクラスター分析
        tag_clusters = {}
        
        for filename in os.listdir(self.permanent_path):
            if filename.endswith('.md'):
                file_path = os.path.join(self.permanent_path, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                    tags = post.metadata.get('tags', [])
                    
                    for tag in tags:
                        if tag not in tag_clusters:
                            tag_clusters[tag] = []
                        tag_clusters[tag].append(filename)
        
        # 大きなクラスターをMOC候補として提案
        moc_suggestions = []
        for tag, notes in tag_clusters.items():
            if len(notes) >= 5:  # 5つ以上のノートがあるタグ
                moc_suggestions.append({
                    'topic': tag,
                    'note_count': len(notes),
                    'notes': notes
                })
        
        return sorted(moc_suggestions, key=lambda x: x['note_count'], reverse=True)
    
    def run_daily_maintenance(self):
        """日次メンテナンス実行"""
        print("🧠 ツェッテルカステン日次メンテナンス開始")
        
        # 1. 受信箱処理
        self.process_inbox_notes()
        
        # 2. 欠落リンク発見
        missing_links = self.discover_missing_links()
        if missing_links:
            print(f"🔗 潜在的リンク {len(missing_links)}件発見")
            for link in missing_links[:5]:  # 上位5件表示
                print(f"   {link['note1']} ↔ {link['note2']} (類似度: {link['similarity']:.2f})")
        
        # 3. MOC提案
        moc_suggestions = self.generate_moc_suggestions()
        if moc_suggestions:
            print(f"📋 MOC作成提案 {len(moc_suggestions)}件")
            for suggestion in moc_suggestions[:3]:  # 上位3件表示
                print(f"   {suggestion['topic']}: {suggestion['note_count']}ノート")
        
        print("✅ 日次メンテナンス完了")

def main():
    processor = ZettelkastenProcessor()
    processor.run_daily_maintenance()

if __name__ == "__main__":
    main()