#!/usr/bin/env python3
"""
AI特化ツェッテルカステンシステム
azukiazusa1スタイルの知識管理 + 最新AI技術統合

原則:
- 原子性: 1ノート = 1AI概念/実験結果
- 連結性: AI概念間の自動リンク生成
- 継続性: 日々のAI実験からの継続的知識蓄積  
- 創発性: AI技術組み合わせによる新洞察発見
"""

import json
import os
import re
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import hashlib
import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class AIKnowledgeNote:
    """AI特化知識ノート"""
    id: str
    title: str
    content: str
    ai_domain: str  # "llm", "agent", "rag", "prompt-engineering", etc.
    experiment_id: Optional[str]
    concepts: List[str]
    connections: List[str]
    created_at: str
    updated_at: str
    permanence_score: float  # 恒久性スコア (0-1)
    emergence_potential: float  # 創発可能性スコア (0-1)


class ZettelkastenAISystem:
    """AI特化ツェッテルカステンシステム"""
    
    def __init__(self, base_path: str = "knowledge-graph"):
        self.base_path = Path(base_path)
        self.db_path = self.base_path / "knowledge_graph.db"
        self.permanent_notes_path = self.base_path / "permanent-notes"
        self.connections_path = self.base_path / "connections"
        self.concepts_path = self.base_path / "concepts"
        self.emergence_path = self.base_path / "emergence"
        
        # ディレクトリ作成
        for path in [self.permanent_notes_path, self.connections_path, 
                     self.concepts_path, self.emergence_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.setup_database()
        self.knowledge_graph = nx.DiGraph()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def setup_database(self):
        """SQLiteデータベースセットアップ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_notes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                ai_domain TEXT NOT NULL,
                experiment_id TEXT,
                concepts TEXT,  -- JSON array
                connections TEXT,  -- JSON array
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                permanence_score REAL DEFAULT 0.0,
                emergence_potential REAL DEFAULT 0.0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_connections (
                source_concept TEXT,
                target_concept TEXT,
                connection_strength REAL,
                connection_type TEXT,
                created_at TEXT,
                PRIMARY KEY (source_concept, target_concept)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emergence_insights (
                id TEXT PRIMARY KEY,
                insight_title TEXT NOT NULL,
                connected_concepts TEXT,  -- JSON array
                ai_domains TEXT,  -- JSON array
                insight_content TEXT NOT NULL,
                confidence_score REAL,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_note(self, title: str, content: str, ai_domain: str, 
                   experiment_id: Optional[str] = None) -> str:
        """新しいAI知識ノート作成"""
        note_id = self._generate_note_id(title)
        concepts = self._extract_ai_concepts(content, ai_domain)
        
        note = AIKnowledgeNote(
            id=note_id,
            title=title,
            content=content,
            ai_domain=ai_domain,
            experiment_id=experiment_id,
            concepts=concepts,
            connections=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            permanence_score=self._calculate_permanence_score(content, concepts),
            emergence_potential=self._calculate_emergence_potential(concepts, ai_domain)
        )
        
        self._save_note_to_db(note)
        self._save_note_to_file(note)
        self._update_knowledge_graph(note)
        self._discover_connections(note)
        
        return note_id
    
    def _generate_note_id(self, title: str) -> str:
        """ノートID生成 (ツェッテルカステン形式)"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        return f"AI{timestamp}{title_hash}"
    
    def _extract_ai_concepts(self, content: str, ai_domain: str) -> List[str]:
        """AI技術概念抽出"""
        ai_concept_patterns = {
            "llm": ["transformer", "attention", "gpt", "claude", "llama", "bert", 
                   "fine-tuning", "prompt", "token", "embedding"],
            "agent": ["multi-agent", "reasoning", "planning", "tool-use", "memory",
                     "reflection", "coordination", "autonomy"],
            "rag": ["retrieval", "vector-database", "semantic-search", "chunking",
                   "embedding", "reranking", "context-window"],
            "prompt-engineering": ["few-shot", "chain-of-thought", "self-consistency",
                                 "tree-of-thought", "prompt-template", "instruction-tuning"]
        }
        
        concepts = []
        domain_patterns = ai_concept_patterns.get(ai_domain, [])
        
        for pattern in domain_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                concepts.append(pattern)
        
        # 一般的なAI概念も抽出
        general_ai_concepts = ["artificial-intelligence", "machine-learning", "deep-learning",
                              "neural-network", "optimization", "evaluation", "benchmark"]
        
        for concept in general_ai_concepts:
            if re.search(concept.replace("-", "[-_\\s]?"), content, re.IGNORECASE):
                concepts.append(concept)
        
        return list(set(concepts))
    
    def _calculate_permanence_score(self, content: str, concepts: List[str]) -> float:
        """恒久性スコア計算"""
        factors = {
            "length": min(len(content) / 1000, 1.0),  # 内容の充実度
            "concepts": min(len(concepts) / 5, 1.0),  # 概念の豊富さ
            "depth": len(re.findall(r'(例|実装|詳細|具体|詳しく)', content)) / 10,  # 深度
            "references": len(re.findall(r'(論文|研究|実験|結果)', content)) / 5  # 参考性
        }
        
        return sum(factors.values()) / len(factors)
    
    def _calculate_emergence_potential(self, concepts: List[str], ai_domain: str) -> float:
        """創発可能性スコア計算"""
        # 複数のAI領域に跨る概念ほど創発性が高い
        cross_domain_concepts = 0
        all_domains = ["llm", "agent", "rag", "prompt-engineering"]
        
        for domain in all_domains:
            if domain != ai_domain:
                domain_concepts = self._get_domain_concepts(domain)
                if any(concept in domain_concepts for concept in concepts):
                    cross_domain_concepts += 1
        
        novelty_score = len(set(concepts)) / 10  # 新規概念数
        cross_domain_score = cross_domain_concepts / len(all_domains)
        
        return (novelty_score + cross_domain_score) / 2
    
    def _get_domain_concepts(self, domain: str) -> List[str]:
        """ドメイン固有概念取得"""
        domain_concepts = {
            "llm": ["transformer", "attention", "gpt", "claude"],
            "agent": ["multi-agent", "reasoning", "planning", "tool-use"],
            "rag": ["retrieval", "vector-database", "semantic-search"],
            "prompt-engineering": ["few-shot", "chain-of-thought"]
        }
        return domain_concepts.get(domain, [])
    
    def _save_note_to_db(self, note: AIKnowledgeNote):
        """ノートをデータベースに保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO knowledge_notes 
            (id, title, content, ai_domain, experiment_id, concepts, connections,
             created_at, updated_at, permanence_score, emergence_potential)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            note.id, note.title, note.content, note.ai_domain, note.experiment_id,
            json.dumps(note.concepts), json.dumps(note.connections),
            note.created_at, note.updated_at, note.permanence_score, note.emergence_potential
        ))
        
        conn.commit()
        conn.close()
    
    def _save_note_to_file(self, note: AIKnowledgeNote):
        """ノートをMarkdownファイルに保存"""
        file_path = self.permanent_notes_path / f"{note.id}.md"
        
        markdown_content = f"""---
id: {note.id}
title: "{note.title}"
ai_domain: {note.ai_domain}
experiment_id: {note.experiment_id}
concepts: {json.dumps(note.concepts)}
permanence_score: {note.permanence_score:.3f}
emergence_potential: {note.emergence_potential:.3f}
created_at: {note.created_at}
updated_at: {note.updated_at}
---

# {note.title}

## AI Domain: {note.ai_domain.upper()}

{note.content}

## 関連概念
{', '.join(f'`{concept}`' for concept in note.concepts)}

## 接続ノート
{chr(10).join(f'- [[{conn}]]' for conn in note.connections)}
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    def _update_knowledge_graph(self, note: AIKnowledgeNote):
        """知識グラフ更新"""
        self.knowledge_graph.add_node(note.id, **asdict(note))
        
        # 概念ベースの接続
        for concept in note.concepts:
            concept_nodes = [n for n, d in self.knowledge_graph.nodes(data=True)
                           if concept in d.get('concepts', [])]
            
            for other_node in concept_nodes:
                if other_node != note.id:
                    self.knowledge_graph.add_edge(note.id, other_node, 
                                                 connection_type='concept',
                                                 weight=0.7)
    
    def _discover_connections(self, note: AIKnowledgeNote):
        """自動的な関連性発見"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, title, content, concepts FROM knowledge_notes WHERE id != ?', 
                      (note.id,))
        existing_notes = cursor.fetchall()
        
        connections = []
        for existing_id, existing_title, existing_content, existing_concepts in existing_notes:
            similarity = self._calculate_semantic_similarity(note.content, existing_content)
            concept_overlap = len(set(note.concepts) & set(json.loads(existing_concepts)))
            
            if similarity > 0.3 or concept_overlap >= 2:
                connections.append(existing_id)
                
                # 双方向接続をデータベースに記録
                cursor.execute('''
                    INSERT OR REPLACE INTO concept_connections
                    (source_concept, target_concept, connection_strength, connection_type, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (note.id, existing_id, similarity, 'semantic', datetime.now().isoformat()))
        
        # ノートの接続を更新
        note.connections = connections
        self._save_note_to_db(note)
        
        conn.commit()
        conn.close()
    
    def _calculate_semantic_similarity(self, content1: str, content2: str) -> float:
        """セマンティック類似度計算"""
        try:
            tfidf_matrix = self.vectorizer.fit_transform([content1, content2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0.0
    
    def discover_emergent_insights(self) -> List[Dict]:
        """創発的洞察発見"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, concepts, ai_domain, emergence_potential, title, content
            FROM knowledge_notes 
            WHERE emergence_potential > 0.5
            ORDER BY emergence_potential DESC
        ''')
        
        high_potential_notes = cursor.fetchall()
        insights = []
        
        for note_id, concepts_json, ai_domain, emergence_potential, title, content in high_potential_notes:
            concepts = json.loads(concepts_json)
            
            # 異なるドメインとの接続を探す
            cursor.execute('''
                SELECT DISTINCT ai_domain, COUNT(*) as count
                FROM knowledge_notes 
                WHERE id IN (
                    SELECT target_concept FROM concept_connections WHERE source_concept = ?
                )
                AND ai_domain != ?
                GROUP BY ai_domain
            ''', (note_id, ai_domain))
            
            cross_domain_connections = cursor.fetchall()
            
            if len(cross_domain_connections) >= 2:
                insight_id = f"INSIGHT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                insight = {
                    'id': insight_id,
                    'title': f"Cross-domain insight: {title}",
                    'connected_concepts': concepts,
                    'ai_domains': [ai_domain] + [domain for domain, count in cross_domain_connections],
                    'insight_content': self._generate_insight_content(note_id, concepts, cross_domain_connections),
                    'confidence_score': emergence_potential,
                    'created_at': datetime.now().isoformat()
                }
                
                insights.append(insight)
                self._save_emergence_insight(insight)
        
        conn.close()
        return insights
    
    def _generate_insight_content(self, note_id: str, concepts: List[str], 
                                cross_domain_connections: List[Tuple[str, int]]) -> str:
        """創発的洞察コンテンツ生成"""
        domains = [domain for domain, count in cross_domain_connections]
        
        insight_content = f"""
# 創発的洞察: {note_id}

## 関連概念
{', '.join(concepts)}

## 接続ドメイン
{', '.join(domains)}

## 洞察内容
この知識ノートは複数のAI領域（{', '.join(domains)}）と接続を持ち、
新しい研究方向や実装アイデアの源泉となる可能性があります。

## 研究提案
- {concepts[0] if concepts else 'Core concept'}と{domains[0] if domains else 'related domain'}の組み合わせ
- 複数ドメインの統合による新しいAI手法
- 実験的実装による概念実証

## Next Steps
1. 関連論文調査
2. プロトタイプ実装
3. 実験結果記録
4. 新しい知識ノート作成
"""
        return insight_content
    
    def _save_emergence_insight(self, insight: Dict):
        """創発的洞察保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO emergence_insights
            (id, insight_title, connected_concepts, ai_domains, insight_content, confidence_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            insight['id'], insight['title'], 
            json.dumps(insight['connected_concepts']),
            json.dumps(insight['ai_domains']),
            insight['insight_content'],
            insight['confidence_score'],
            insight['created_at']
        ))
        
        # ファイルにも保存
        file_path = self.emergence_path / f"{insight['id']}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(insight['insight_content'])
        
        conn.commit()
        conn.close()
    
    def get_knowledge_stats(self) -> Dict:
        """知識ベース統計"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # ノート数
        cursor.execute('SELECT COUNT(*) FROM knowledge_notes')
        stats['total_notes'] = cursor.fetchone()[0]
        
        # ドメイン別分布
        cursor.execute('SELECT ai_domain, COUNT(*) FROM knowledge_notes GROUP BY ai_domain')
        stats['domain_distribution'] = dict(cursor.fetchall())
        
        # 高恒久性ノート
        cursor.execute('SELECT COUNT(*) FROM knowledge_notes WHERE permanence_score > 0.7')
        stats['high_permanence_notes'] = cursor.fetchone()[0]
        
        # 創発可能性ノート
        cursor.execute('SELECT COUNT(*) FROM knowledge_notes WHERE emergence_potential > 0.5')
        stats['high_emergence_notes'] = cursor.fetchone()[0]
        
        # 接続数
        cursor.execute('SELECT COUNT(*) FROM concept_connections')
        stats['total_connections'] = cursor.fetchone()[0]
        
        # 洞察数
        cursor.execute('SELECT COUNT(*) FROM emergence_insights')
        stats['total_insights'] = cursor.fetchone()[0]
        
        conn.close()
        return stats


def main():
    """メイン実行"""
    zk_system = ZettelkastenAISystem()
    
    # サンプルAI知識ノート作成
    note_id = zk_system.create_note(
        title="Multi-Agent RAG System Architecture",
        content="""
        マルチエージェントRAGシステムは、複数のLLMエージェントが協調して
        情報検索と生成を行うアーキテクチャです。

        ## 主要コンポーネント
        1. Retrieval Agent: Vector database から関連文書を検索
        2. Reasoning Agent: 検索結果を分析し推論
        3. Generation Agent: 最終回答を生成
        4. Coordination Agent: エージェント間の調整

        ## 実装例
        - Claude API を使った協調エージェント
        - Semantic search による高精度検索
        - Chain-of-thought reasoning の統合
        """,
        ai_domain="agent",
        experiment_id="EXP_20250724_001"
    )
    
    print(f"Created note: {note_id}")
    
    # 統計表示
    stats = zk_system.get_knowledge_stats()
    print(f"\nKnowledge Base Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 創発的洞察発見
    insights = zk_system.discover_emergent_insights()
    print(f"\nDiscovered {len(insights)} emergent insights")


if __name__ == "__main__":
    main()