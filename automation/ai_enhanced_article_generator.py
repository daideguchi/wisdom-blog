#!/usr/bin/env python3
"""
AI強化記事生成システム - 高度化版
azukiazusa1スタイル × ツェッテルカステン × AI実験統合

機能:
1. AI実験結果自動記事化
2. ツェッテルカステン知識統合
3. SEO最適化記事生成
4. 品質保証システム
5. GitHub自動デプロイ
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import yaml
import hashlib
import re
from dataclasses import dataclass, asdict

# 外部ライブラリ
import openai
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 内部モジュール
import sys
sys.path.append(str(Path(__file__).parent.parent))
from knowledge_graph.zettelkasten_ai_system import ZettelkastenAISystem, AIKnowledgeNote
from ai_experiments.multi_agent_systems.collaborative_research_agents import CollaborativeResearchSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ArticleMetadata:
    """記事メタデータ"""
    id: str
    title: str
    description: str
    keywords: List[str]
    ai_domain: str
    experiment_id: Optional[str]
    knowledge_notes: List[str]
    quality_score: float
    seo_score: float
    estimated_reading_time: int
    created_at: str
    published: bool = False


@dataclass
class ContentAnalytics:
    """コンテンツ分析結果"""
    readability_score: float
    technical_depth: float
    novelty_score: float
    practical_value: float
    engagement_potential: float


class AIEnhancedArticleGenerator:
    """AI強化記事生成システム"""
    
    def __init__(self, config_path: str = "config/article_generator.yaml"):
        self.config = self._load_config(config_path)
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # システム統合
        self.zettelkasten_system = ZettelkastenAISystem("knowledge-graph")
        self.research_system = CollaborativeResearchSystem(os.getenv("OPENAI_API_KEY"))
        
        # 記事生成設定
        self.articles_path = Path("blog-app/articles")
        self.articles_path.mkdir(parents=True, exist_ok=True)
        
        # 品質チェッカー
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # テンプレート
        self.article_templates = self._load_templates()
        
    def _load_config(self, config_path: str) -> Dict:
        """設定ファイル読み込み"""
        default_config = {
            "generation": {
                "target_word_count": 2000,
                "min_quality_score": 0.7,
                "seo_optimization": True,
                "include_code_examples": True,
                "max_articles_per_day": 3
            },
            "content_strategy": {
                "primary_domains": ["llm", "agent", "rag", "prompt-engineering"],
                "content_types": ["tutorial", "analysis", "experiment-report", "concept-explanation"],
                "target_audience": ["researchers", "engineers", "students"],
                "tone": "technical-accessible"
            },
            "seo": {
                "target_keywords_per_article": 5,
                "meta_description_length": 160,
                "title_optimization": True,
                "internal_linking": True
            }
        }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
        
        return default_config
    
    def _load_templates(self) -> Dict[str, str]:
        """記事テンプレート読み込み"""
        return {
            "tutorial": """# {title}

## はじめに
{introduction}

## 背景・基礎知識
{background}

## 実装方法
{implementation}

## 実例・デモ
{examples}

## 応用・発展
{applications}

## まとめ
{conclusion}

## 参考資料
{references}
""",
            "experiment-report": """# {title}

## 実験概要
{experiment_overview}

## 仮説・目的
{hypothesis}

## 実験方法
{methodology}

## 結果・分析
{results}

## 考察・洞察
{discussion}

## 今後の展開
{future_work}

## 関連知識・参考文献
{related_knowledge}
""",
            "concept-explanation": """# {title}

## 概念の定義
{definition}

## 重要性・背景
{importance}

## 技術的詳細
{technical_details}

## 実装パターン
{implementation_patterns}

## 使用例・ケーススタディ
{use_cases}

## 他の概念との関係
{relationships}

## まとめ・今後の発展
{summary}
"""
        }
    
    async def generate_article_from_experiment(self, experiment_id: str) -> Optional[ArticleMetadata]:
        """実験結果から記事生成"""
        logger.info(f"Generating article from experiment: {experiment_id}")
        
        # 1. 実験結果取得
        experiment_data = await self._get_experiment_data(experiment_id)
        if not experiment_data:
            logger.error(f"No experiment data found for: {experiment_id}")
            return None
        
        # 2. 関連知識ノート取得
        related_notes = await self._get_related_knowledge_notes(experiment_data)
        
        # 3. 記事構成決定
        article_type = self._determine_article_type(experiment_data)
        template = self.article_templates[article_type]
        
        # 4. コンテンツ生成
        content_sections = await self._generate_content_sections(
            experiment_data, related_notes, article_type)
        
        # 5. 記事統合
        full_article = self._integrate_article_content(template, content_sections)
        
        # 6. 品質チェック・改善
        quality_score = await self._assess_article_quality(full_article)
        if quality_score < self.config["generation"]["min_quality_score"]:
            full_article = await self._improve_article_quality(full_article, quality_score)
            quality_score = await self._assess_article_quality(full_article)
        
        # 7. SEO最適化
        seo_metadata = await self._optimize_for_seo(full_article, experiment_data)
        
        # 8. メタデータ作成
        article_metadata = await self._create_article_metadata(
            experiment_data, related_notes, quality_score, seo_metadata)
        
        # 9. ファイル保存
        await self._save_article_with_metadata(full_article, article_metadata)
        
        # 10. 知識グラフ更新
        await self._update_knowledge_graph_with_article(article_metadata, related_notes)
        
        logger.info(f"Article generated successfully: {article_metadata.id}")
        return article_metadata
    
    async def _get_experiment_data(self, experiment_id: str) -> Optional[Dict]:
        """実験データ取得"""
        results_path = Path(f"results/synthesizer_001/{experiment_id}_synthesis.json")
        
        if results_path.exists():
            with open(results_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 実験が完了していない場合は待機
        logger.info(f"Experiment data not found, checking research system...")
        
        # 研究システムから直接取得を試行
        try:
            stats = self.research_system.get_system_stats()
            if stats["completed_tasks"] > 0:
                # 最新完了タスクの結果を取得 (実装簡略化)
                return {
                    "experiment_id": experiment_id,
                    "topic": "Multi-Agent AI Systems",
                    "results": {"summary": "Experimental AI research results..."},
                    "insights": ["Insight 1", "Insight 2"],
                    "implementation": {"code": "# Sample implementation code"},
                    "evaluation": {"accuracy": 0.85, "performance": "good"}
                }
        except Exception as e:
            logger.error(f"Error getting experiment data: {e}")
        
        return None
    
    async def _get_related_knowledge_notes(self, experiment_data: Dict) -> List[AIKnowledgeNote]:
        """関連知識ノート取得"""
        topic = experiment_data.get("topic", "")
        
        # ツェッテルカステンシステムから関連ノート検索
        stats = self.zettelkasten_system.get_knowledge_stats()
        
        if stats["total_notes"] > 0:
            # 実際の実装では、セマンティック検索を使用
            return [
                AIKnowledgeNote(
                    id="NOTE_001",
                    title="Multi-Agent Coordination",
                    content="Multi-agent systems coordination mechanisms...",
                    ai_domain="agent",
                    experiment_id=experiment_data.get("experiment_id"),
                    concepts=["coordination", "multi-agent", "consensus"],
                    connections=["NOTE_002", "NOTE_003"],
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                    permanence_score=0.8,
                    emergence_potential=0.7
                )
            ]
        
        return []
    
    def _determine_article_type(self, experiment_data: Dict) -> str:
        """記事タイプ決定"""
        topic = experiment_data.get("topic", "").lower()
        
        if "implementation" in experiment_data or "code" in str(experiment_data):
            return "tutorial"
        elif "experiment" in topic or "evaluation" in experiment_data:
            return "experiment-report"
        else:
            return "concept-explanation"
    
    async def _generate_content_sections(self, experiment_data: Dict, 
                                       related_notes: List[AIKnowledgeNote], 
                                       article_type: str) -> Dict[str, str]:
        """コンテンツセクション生成"""
        sections = {}
        
        if article_type == "experiment-report":
            sections = await self._generate_experiment_report_sections(experiment_data, related_notes)
        elif article_type == "tutorial":
            sections = await self._generate_tutorial_sections(experiment_data, related_notes)
        else:  # concept-explanation
            sections = await self._generate_concept_sections(experiment_data, related_notes)
        
        return sections
    
    async def _generate_experiment_report_sections(self, experiment_data: Dict,
                                                 related_notes: List[AIKnowledgeNote]) -> Dict[str, str]:
        """実験レポートセクション生成"""
        sections = {}
        
        # 実験概要
        sections["experiment_overview"] = await self._generate_section_content(
            "実験概要",
            f"実験データ: {json.dumps(experiment_data, ensure_ascii=False)[:500]}",
            "この実験の目的、対象技術、期待される成果について詳しく説明してください。"
        )
        
        # 仮説・目的
        sections["hypothesis"] = await self._generate_section_content(
            "仮説・目的",
            f"トピック: {experiment_data.get('topic', '')}",
            "この実験で検証したい仮説と具体的な目的を明確に述べてください。"
        )
        
        # 実験方法
        sections["methodology"] = await self._generate_section_content(
            "実験方法",
            f"実装詳細: {experiment_data.get('implementation', {})}",
            "実験の手順、使用したツール、評価指標について詳しく説明してください。コード例も含めてください。"
        )
        
        # 結果・分析
        sections["results"] = await self._generate_section_content(
            "結果・分析",
            f"評価結果: {experiment_data.get('evaluation', {})}",
            "実験結果を定量的・定性的に分析し、グラフや表を用いて視覚化してください。"
        )
        
        # 考察・洞察
        related_context = "\n".join([f"関連知識: {note.title} - {note.content[:200]}" 
                                   for note in related_notes])
        sections["discussion"] = await self._generate_section_content(
            "考察・洞察",
            f"実験洞察: {experiment_data.get('insights', [])}\n{related_context}",
            "結果から得られる洞察、既存研究との比較、発見された新しい知見について考察してください。"
        )
        
        # 今後の展開
        sections["future_work"] = await self._generate_section_content(
            "今後の展開",
            f"実験結果: {experiment_data.get('results', {})}",
            "この実験結果を受けて、今後の研究方向や改善点について提案してください。"
        )
        
        # 関連知識・参考文献
        sections["related_knowledge"] = self._generate_related_knowledge_section(related_notes)
        
        return sections
    
    async def _generate_tutorial_sections(self, experiment_data: Dict,
                                        related_notes: List[AIKnowledgeNote]) -> Dict[str, str]:
        """チュートリアルセクション生成"""
        sections = {}
        
        sections["introduction"] = await self._generate_section_content(
            "導入",
            f"トピック: {experiment_data.get('topic', '')}",
            "このチュートリアルで学習する内容、前提知識、期待される学習成果を説明してください。"
        )
        
        sections["background"] = await self._generate_section_content(
            "背景・基礎知識",
            "\n".join([note.content[:300] for note in related_notes]),
            "必要な背景知識、基礎概念を初学者にも分かりやすく説明してください。"
        )
        
        sections["implementation"] = await self._generate_section_content(
            "実装方法",
            f"実装: {experiment_data.get('implementation', {})}",
            "ステップバイステップの実装手順、重要なポイント、注意事項を含めてください。完全なコード例も提供してください。"
        )
        
        sections["examples"] = await self._generate_section_content(
            "実例・デモ",
            f"評価結果: {experiment_data.get('evaluation', {})}",
            "実際の使用例、デモンストレーション、期待される出力結果を示してください。"
        )
        
        sections["applications"] = await self._generate_section_content(
            "応用・発展",
            f"洞察: {experiment_data.get('insights', [])}",
            "基本実装からの発展方法、実際のプロジェクトでの応用例を提案してください。"
        )
        
        sections["conclusion"] = await self._generate_section_content(
            "まとめ",
            f"実験結果全体: {json.dumps(experiment_data, ensure_ascii=False)[:300]}",
            "学習した内容のまとめ、重要ポイントの再確認、次のステップを提示してください。"
        )
        
        sections["references"] = self._generate_references_section(experiment_data, related_notes)
        
        return sections
    
    async def _generate_concept_sections(self, experiment_data: Dict,
                                       related_notes: List[AIKnowledgeNote]) -> Dict[str, str]:
        """概念解説セクション生成"""
        sections = {}
        
        sections["definition"] = await self._generate_section_content(
            "概念の定義",
            f"トピック: {experiment_data.get('topic', '')}",
            "この概念の正確な定義、類似概念との違い、技術的特徴を明確に説明してください。"
        )
        
        sections["importance"] = await self._generate_section_content(
            "重要性・背景",
            f"実験背景: {experiment_data.get('results', {})}",
            "なぜこの概念が重要なのか、現在の技術トレンドにおける位置づけを説明してください。"
        )
        
        sections["technical_details"] = await self._generate_section_content(
            "技術的詳細",
            f"実装詳細: {experiment_data.get('implementation', {})}",
            "技術的な仕組み、アルゴリズム、数学的基礎について詳しく解説してください。"
        )
        
        sections["implementation_patterns"] = await self._generate_section_content(
            "実装パターン",
            "\n".join([note.content[:200] for note in related_notes]),
            "一般的な実装パターン、ベストプラクティス、避けるべきアンチパターンを紹介してください。"
        )
        
        sections["use_cases"] = await self._generate_section_content(
            "使用例・ケーススタディ",
            f"評価事例: {experiment_data.get('evaluation', {})}",
            "実際の使用例、成功事例、失敗事例から学べる教訓を提示してください。"
        )
        
        sections["relationships"] = await self._generate_section_content(
            "他の概念との関係",
            "\n".join([f"{note.title}: {', '.join(note.concepts)}" for note in related_notes]),
            "関連する概念、上位・下位概念との関係、技術的な依存関係を図解してください。"
        )
        
        sections["summary"] = await self._generate_section_content(
            "まとめ・今後の発展",
            f"今後の洞察: {experiment_data.get('insights', [])}",
            "概念の重要ポイント整理、今後の発展方向、研究・開発の展望を述べてください。"
        )
        
        return sections
    
    async def _generate_section_content(self, section_title: str, context: str, 
                                      instruction: str) -> str:
        """セクションコンテンツ生成"""
        system_prompt = f"""
        あなたは技術記事執筆のエキスパートです。
        azukiazusa1のような高品質で実用的な技術記事を執筆してください。
        
        記事の特徴:
        - 実装例とコードを重視
        - 初学者にも理解しやすい説明
        - 最新技術トレンドを反映
        - SEOを意識した構成
        """
        
        user_prompt = f"""
        セクション: {section_title}
        
        コンテキスト:
        {context}
        
        指示:
        {instruction}
        
        この技術記事のセクションを、以下の点を考慮して執筆してください:
        1. 具体例とコード例を含める
        2. 図表や箇条書きで理解しやすくする
        3. 2-3段落、500-800語程度
        4. マークダウン形式で出力
        5. 実用性を重視した内容
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating section content: {e}")
            return f"## {section_title}\n\n[Content generation error]"
    
    def _generate_related_knowledge_section(self, related_notes: List[AIKnowledgeNote]) -> str:
        """関連知識セクション生成"""
        if not related_notes:
            return "## 参考資料\n\n- [AI技術の最新動向](https://example.com/ai-trends)\n- [実装ガイド](https://example.com/implementation-guide)"
        
        content = ["## 関連知識・参考文献\n"]
        
        for note in related_notes:
            content.append(f"### {note.title}")
            content.append(f"{note.content[:200]}...")
            content.append(f"**関連概念**: {', '.join(note.concepts)}")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_references_section(self, experiment_data: Dict, 
                                   related_notes: List[AIKnowledgeNote]) -> str:
        """参考文献セクション生成"""
        references = ["## 参考資料\n"]
        
        # 実験関連の参考文献
        if "sources" in experiment_data:
            references.extend([f"- {source}" for source in experiment_data["sources"]])
        
        # 知識ノートからの参考文献
        for note in related_notes:
            references.append(f"- [{note.title}](knowledge-graph/{note.id}.md)")
        
        # デフォルト参考文献
        references.extend([
            "- [OpenAI API Documentation](https://platform.openai.com/docs)",
            "- [Multi-Agent Systems Research](https://arxiv.org/list/cs.MA/recent)",
            "- [AI実装ベストプラクティス](https://github.com/topics/artificial-intelligence)"
        ])
        
        return "\n".join(references)
    
    def _integrate_article_content(self, template: str, sections: Dict[str, str]) -> str:
        """記事コンテンツ統合"""
        try:
            return template.format(**sections)
        except KeyError as e:
            logger.error(f"Template formatting error: {e}")
            # フォールバック: セクションを順番に結合
            content_parts = []
            for section_name, section_content in sections.items():
                content_parts.append(section_content)
                content_parts.append("")
            return "\n".join(content_parts)
    
    async def _assess_article_quality(self, article: str) -> float:
        """記事品質評価"""
        analytics = await self._analyze_content(article)
        
        # 品質スコア計算 (0-1)
        quality_factors = {
            "length": min(len(article.split()) / 2000, 1.0),  # 目標2000語
            "structure": len(re.findall(r'^##?\s', article, re.MULTILINE)) / 8,  # 目標8見出し
            "code_examples": len(re.findall(r'```', article)) / 4,  # 目標2コードブロック
            "readability": analytics.readability_score,
            "technical_depth": analytics.technical_depth,
            "practical_value": analytics.practical_value
        }
        
        weighted_score = (
            quality_factors["length"] * 0.2 +
            quality_factors["structure"] * 0.15 +
            quality_factors["code_examples"] * 0.2 +
            quality_factors["readability"] * 0.15 +
            quality_factors["technical_depth"] * 0.15 +
            quality_factors["practical_value"] * 0.15
        )
        
        return min(weighted_score, 1.0)
    
    async def _analyze_content(self, article: str) -> ContentAnalytics:
        """コンテンツ分析"""
        # 簡易分析実装
        word_count = len(article.split())
        sentence_count = len(re.findall(r'[.!?]+', article))
        
        # 読みやすさスコア (Flesch Reading Ease簡易版)
        avg_sentence_length = word_count / max(sentence_count, 1)
        readability_score = max(0, min(1, (20 - avg_sentence_length) / 20))
        
        # 技術的深度 (技術用語の密度)
        tech_terms = len(re.findall(r'\b(API|algorithm|implementation|framework|system|model|data|function|class|method)\b', article, re.IGNORECASE))
        technical_depth = min(tech_terms / 20, 1.0)
        
        # 実用価値 (コード例、実例の有無)
        code_blocks = len(re.findall(r'```', article))
        examples = len(re.findall(r'(例|example|実装|implementation)', article, re.IGNORECASE))
        practical_value = min((code_blocks + examples) / 5, 1.0)
        
        # 新規性スコア (新しい概念や手法の言及)
        novelty_indicators = len(re.findall(r'(新しい|最新|革新|breakthrough|novel|cutting-edge)', article, re.IGNORECASE))
        novelty_score = min(novelty_indicators / 3, 1.0)
        
        # エンゲージメント可能性 (問いかけ、呼びかけの有無)
        engagement_indicators = len(re.findall(r'(\?|どう|いかが|試して|挑戦|考えて)', article, re.IGNORECASE))
        engagement_potential = min(engagement_indicators / 5, 1.0)
        
        return ContentAnalytics(
            readability_score=readability_score,
            technical_depth=technical_depth,
            novelty_score=novelty_score,
            practical_value=practical_value,
            engagement_potential=engagement_potential
        )
    
    async def _improve_article_quality(self, article: str, current_score: float) -> str:
        """記事品質改善"""
        improvement_prompt = f"""
        以下の技術記事の品質を向上させてください。
        現在の品質スコア: {current_score:.2f}
        
        改善点:
        1. より具体的なコード例を追加
        2. 実用的な実装手順を詳細化
        3. 読みやすさの向上
        4. 技術的深度の向上
        
        記事:
        {article}
        
        改善された記事を出力してください。
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": improvement_prompt}],
                temperature=0.5,
                max_tokens=3000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error improving article quality: {e}")
            return article
    
    async def _optimize_for_seo(self, article: str, experiment_data: Dict) -> Dict:
        """SEO最適化"""
        topic = experiment_data.get("topic", "AI技術")
        
        # キーワード抽出
        keywords = await self._extract_seo_keywords(article, topic)
        
        # メタ情報生成
        meta_title = f"{topic} - 実装ガイドと実験結果"
        meta_description = f"{topic}の詳細な実装方法と実験結果を解説。最新AI技術の実用的活用法をコード例付きで紹介します。"
        
        return {
            "meta_title": meta_title,
            "meta_description": meta_description[:160],  # 160文字制限
            "keywords": keywords,
            "og_title": meta_title,
            "og_description": meta_description[:200],
            "twitter_card": "summary_large_image",
            "canonical_url": f"https://blog-app-kappa-sand.vercel.app/blog/{self._generate_slug(topic)}"
        }
    
    async def _extract_seo_keywords(self, article: str, main_topic: str) -> List[str]:
        """SEOキーワード抽出"""
        # 主要キーワード
        keywords = [main_topic.lower()]
        
        # 技術用語抽出
        tech_patterns = [
            r'\b(AI|machine\s+learning|deep\s+learning|neural\s+network)\b',
            r'\b(API|framework|library|implementation)\b',
            r'\b(Python|JavaScript|TypeScript|React|Node\.js)\b',
            r'\b(algorithm|model|data|training|evaluation)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, article, re.IGNORECASE)
            keywords.extend([match.lower() for match in matches if isinstance(match, str)])
        
        # 重複除去・頻度順ソート
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, freq in sorted_keywords[:self.config["seo"]["target_keywords_per_article"]]]
    
    def _generate_slug(self, title: str) -> str:
        """URL slug生成"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    async def _create_article_metadata(self, experiment_data: Dict, 
                                     related_notes: List[AIKnowledgeNote],
                                     quality_score: float, seo_metadata: Dict) -> ArticleMetadata:
        """記事メタデータ作成"""
        article_id = f"AI_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ArticleMetadata(
            id=article_id,
            title=seo_metadata["meta_title"],
            description=seo_metadata["meta_description"],
            keywords=seo_metadata["keywords"],
            ai_domain=experiment_data.get("domain", "general"),
            experiment_id=experiment_data.get("experiment_id"),
            knowledge_notes=[note.id for note in related_notes],
            quality_score=quality_score,
            seo_score=await self._calculate_seo_score(seo_metadata),
            estimated_reading_time=len(seo_metadata["meta_description"].split()) // 200 * 60,  # 概算
            created_at=datetime.now().isoformat(),
            published=quality_score >= self.config["generation"]["min_quality_score"]
        )
    
    async def _calculate_seo_score(self, seo_metadata: Dict) -> float:
        """SEOスコア計算"""
        score_factors = {
            "title_length": 1.0 if 30 <= len(seo_metadata["meta_title"]) <= 60 else 0.5,
            "description_length": 1.0 if 120 <= len(seo_metadata["meta_description"]) <= 160 else 0.5,
            "keywords_count": min(len(seo_metadata["keywords"]) / 5, 1.0),
            "has_og_tags": 1.0 if "og_title" in seo_metadata else 0.0
        }
        
        return sum(score_factors.values()) / len(score_factors)
    
    async def _save_article_with_metadata(self, article: str, metadata: ArticleMetadata):
        """記事とメタデータ保存"""
        # Frontmatter作成
        frontmatter = f"""---
id: "{metadata.id}"
title: "{metadata.title}"
description: "{metadata.description}"
keywords: {json.dumps(metadata.keywords)}
ai_domain: "{metadata.ai_domain}"
experiment_id: "{metadata.experiment_id}"
knowledge_notes: {json.dumps(metadata.knowledge_notes)}
quality_score: {metadata.quality_score:.3f}
seo_score: {metadata.seo_score:.3f}
estimated_reading_time: {metadata.estimated_reading_time}
created_at: "{metadata.created_at}"
published: {str(metadata.published).lower()}
emoji: "🧠"
type: "tech"
topics: {json.dumps(metadata.keywords[:3])}
published_at: "{datetime.now().strftime('%Y-%m-%d')}"
---

"""
        
        # 記事ファイル保存
        article_file = self.articles_path / f"{metadata.id}.md"
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter + article)
        
        # メタデータファイル保存
        metadata_file = self.articles_path / f"{metadata.id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Article saved: {article_file}")
    
    async def _update_knowledge_graph_with_article(self, metadata: ArticleMetadata, 
                                                 related_notes: List[AIKnowledgeNote]):
        """知識グラフ更新"""
        # 記事を新しい知識ノートとして追加
        article_note_id = self.zettelkasten_system.create_note(
            title=metadata.title,
            content=f"Generated article about {metadata.ai_domain}",
            ai_domain=metadata.ai_domain,
            experiment_id=metadata.experiment_id
        )
        
        logger.info(f"Knowledge graph updated with article: {article_note_id}")
    
    async def auto_generate_daily_articles(self, max_articles: int = None) -> List[ArticleMetadata]:
        """日次自動記事生成"""
        if max_articles is None:
            max_articles = self.config["generation"]["max_articles_per_day"]
        
        logger.info(f"Starting daily article generation (max: {max_articles})")
        
        generated_articles = []
        
        # 1. 新しい実験結果をチェック
        experiment_ids = await self._get_new_experiment_results()
        
        # 2. 各実験から記事生成
        for i, experiment_id in enumerate(experiment_ids[:max_articles]):
            try:
                article_metadata = await self.generate_article_from_experiment(experiment_id)
                if article_metadata:
                    generated_articles.append(article_metadata)
                    logger.info(f"Generated article {i+1}/{min(len(experiment_ids), max_articles)}")
                    
                    # レート制限を考慮して待機
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error generating article for {experiment_id}: {e}")
        
        # 3. GitHub自動コミット (オプション)
        if generated_articles and os.getenv("AUTO_COMMIT", "false").lower() == "true":
            await self._auto_commit_articles(generated_articles)
        
        logger.info(f"Daily article generation completed: {len(generated_articles)} articles")
        return generated_articles
    
    async def _get_new_experiment_results(self) -> List[str]:
        """新しい実験結果取得"""
        # 過去24時間の実験結果を検索
        results_dir = Path("results")
        if not results_dir.exists():
            return ["DEMO_EXPERIMENT_001"]  # デモ用
        
        cutoff_time = datetime.now() - timedelta(days=1)
        new_experiments = []
        
        for result_file in results_dir.rglob("*_synthesis.json"):
            if result_file.stat().st_mtime > cutoff_time.timestamp():
                experiment_id = result_file.stem.replace("_synthesis", "")
                new_experiments.append(experiment_id)
        
        return new_experiments[:5]  # 最大5実験
    
    async def _auto_commit_articles(self, generated_articles: List[ArticleMetadata]):
        """自動Git コミット"""
        try:
            # Git add
            subprocess.run(["git", "add", "blog-app/articles/"], check=True, cwd=".")
            
            # Commit message作成
            article_titles = [metadata.title[:50] for metadata in generated_articles]
            commit_message = f"🤖 Auto-generated {len(generated_articles)} AI articles\n\n" + \
                           "\n".join([f"- {title}" for title in article_titles])
            
            # Git commit
            subprocess.run(["git", "commit", "-m", commit_message], check=True, cwd=".")
            
            # Git push (オプション)
            if os.getenv("AUTO_PUSH", "false").lower() == "true":
                subprocess.run(["git", "push"], check=True, cwd=".")
            
            logger.info(f"Articles committed to Git: {len(generated_articles)} articles")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operations failed: {e}")


async def main():
    """メイン実行"""
    generator = AIEnhancedArticleGenerator()
    
    # デモ: 実験結果から記事生成
    article_metadata = await generator.generate_article_from_experiment("DEMO_EXPERIMENT_001")
    
    if article_metadata:
        print(f"✅ Article generated successfully!")
        print(f"ID: {article_metadata.id}")
        print(f"Title: {article_metadata.title}")
        print(f"Quality Score: {article_metadata.quality_score:.3f}")
        print(f"SEO Score: {article_metadata.seo_score:.3f}")
        print(f"Published: {article_metadata.published}")
    else:
        print("❌ Failed to generate article")


if __name__ == "__main__":
    asyncio.run(main())