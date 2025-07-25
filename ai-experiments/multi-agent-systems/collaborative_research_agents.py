#!/usr/bin/env python3
"""
Collaborative Research Agents - AI実験実装例
azukiazusa1スタイルの実用的デモコード

複数のAIエージェントが協調して技術研究を行うシステム
- Research Agent: 論文・記事調査
- Analysis Agent: 技術分析・評価
- Synthesis Agent: 知識統合・洞察生成
- Writer Agent: 記事作成・品質チェック
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp
import openai
from enum import Enum

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentRole(Enum):
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    SYNTHESIZER = "synthesizer"
    WRITER = "writer"


@dataclass
class ResearchTask:
    """研究タスク定義"""
    id: str
    topic: str
    research_questions: List[str]
    target_domains: List[str]
    deadline: str
    priority: int
    status: str = "pending"


@dataclass
class ResearchResult:
    """研究結果"""
    agent_id: str
    task_id: str
    result_type: str  # "literature", "analysis", "synthesis", "article"
    content: Dict[str, Any]
    confidence_score: float
    created_at: str


class BaseAgent:
    """基底エージェントクラス"""
    
    def __init__(self, agent_id: str, role: AgentRole, api_key: str):
        self.agent_id = agent_id
        self.role = role
        self.api_key = api_key
        self.openai_client = openai.AsyncOpenAI(api_key=api_key)
        self.results_history: List[ResearchResult] = []
    
    async def process_task(self, task: ResearchTask) -> ResearchResult:
        """タスク処理 - サブクラスで実装"""
        raise NotImplementedError
    
    async def _call_llm(self, system_prompt: str, user_prompt: str, 
                       model: str = "gpt-4") -> str:
        """LLM API呼び出し"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return ""
    
    def save_result(self, result: ResearchResult):
        """結果保存"""
        self.results_history.append(result)
        
        # ファイルにも保存
        results_dir = Path(f"results/{self.agent_id}")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = results_dir / f"{result.task_id}_{result.result_type}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)


class ResearchAgent(BaseAgent):
    """文献調査エージェント"""
    
    def __init__(self, agent_id: str, api_key: str):
        super().__init__(agent_id, AgentRole.RESEARCHER, api_key)
    
    async def process_task(self, task: ResearchTask) -> ResearchResult:
        """文献調査実行"""
        logger.info(f"[{self.agent_id}] Starting literature research: {task.topic}")
        
        # 1. 検索キーワード生成
        keywords = await self._generate_search_keywords(task)
        
        # 2. 論文検索 (arXiv API使用)
        papers = await self._search_arxiv_papers(keywords, limit=10)
        
        # 3. GitHub リポジトリ検索
        repos = await self._search_github_repos(keywords, limit=5)
        
        # 4. 技術記事検索
        articles = await self._search_tech_articles(keywords, limit=10)
        
        # 5. 結果統合
        literature_review = {
            "keywords": keywords,
            "papers": papers,
            "repositories": repos,
            "articles": articles,
            "summary": await self._generate_literature_summary(papers, repos, articles)
        }
        
        result = ResearchResult(
            agent_id=self.agent_id,
            task_id=task.id,
            result_type="literature",
            content=literature_review,
            confidence_score=0.8,
            created_at=datetime.now().isoformat()
        )
        
        self.save_result(result)
        return result
    
    async def _generate_search_keywords(self, task: ResearchTask) -> List[str]:
        """検索キーワード生成"""
        system_prompt = """
        あなたは技術研究のための検索キーワード生成エキスパートです。
        与えられた研究トピックから、効果的な検索キーワードを生成してください。
        """
        
        user_prompt = f"""
        研究トピック: {task.topic}
        対象ドメイン: {', '.join(task.target_domains)}
        研究質問: {', '.join(task.research_questions)}
        
        このトピックを調査するための効果的な検索キーワードを10個生成してください。
        英語キーワードと日本語キーワードの両方を含めてください。
        """
        
        response = await self._call_llm(system_prompt, user_prompt)
        
        # キーワード抽出 (簡易実装)
        keywords = [kw.strip() for kw in response.split('\n') if kw.strip()]
        return keywords[:10]
    
    async def _search_arxiv_papers(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """arXiv論文検索"""
        papers = []
        
        # 実際のarXiv API呼び出し (簡易実装)
        for keyword in keywords[:3]:  # 最初の3つのキーワードで検索
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"http://export.arxiv.org/api/query?search_query=all:{keyword}&start=0&max_results={limit//3}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            # XML解析は簡略化
                            papers.append({
                                "title": f"Sample paper for {keyword}",
                                "authors": ["Author 1", "Author 2"],
                                "abstract": f"Abstract for {keyword} research...",
                                "url": f"https://arxiv.org/abs/sample-{keyword}",
                                "published": "2024-01-01"
                            })
            except Exception as e:
                logger.error(f"arXiv search error: {e}")
        
        return papers
    
    async def _search_github_repos(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """GitHub リポジトリ検索"""
        repos = []
        
        # GitHub API検索 (簡易実装)
        for keyword in keywords[:2]:
            repos.append({
                "name": f"awesome-{keyword}",
                "description": f"Awesome {keyword} resources and implementations",
                "url": f"https://github.com/example/awesome-{keyword}",
                "stars": 1234,
                "language": "Python",
                "topics": [keyword, "ai", "machine-learning"]
            })
        
        return repos
    
    async def _search_tech_articles(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """技術記事検索"""
        articles = []
        
        # 技術記事検索 (Zenn, Qiita等のAPI使用 - 簡易実装)
        for keyword in keywords[:5]:
            articles.append({
                "title": f"{keyword}を使った実装方法",
                "author": "技術者A",
                "url": f"https://zenn.dev/example/{keyword}-implementation",
                "published": "2024-01-15",
                "tags": [keyword, "tutorial", "implementation"]
            })
        
        return articles
    
    async def _generate_literature_summary(self, papers: List[Dict], 
                                         repos: List[Dict], articles: List[Dict]) -> str:
        """文献レビューサマリー生成"""
        system_prompt = """
        あなたは技術文献レビューのエキスパートです。
        収集された論文、リポジトリ、記事から包括的なサマリーを作成してください。
        """
        
        user_prompt = f"""
        収集された文献:
        
        論文: {len(papers)}本
        {json.dumps(papers[:3], ensure_ascii=False, indent=2)}
        
        リポジトリ: {len(repos)}個
        {json.dumps(repos, ensure_ascii=False, indent=2)}
        
        記事: {len(articles)}本
        {json.dumps(articles[:3], ensure_ascii=False, indent=2)}
        
        これらの文献から以下を含む包括的なサマリーを作成してください:
        1. 主要なトレンドと発展
        2. 重要な技術的課題
        3. 実装アプローチの比較
        4. 今後の研究方向
        """
        
        return await self._call_llm(system_prompt, user_prompt)


class AnalysisAgent(BaseAgent):
    """分析エージェント"""
    
    def __init__(self, agent_id: str, api_key: str):
        super().__init__(agent_id, AgentRole.ANALYST, api_key)
    
    async def process_task(self, task: ResearchTask, 
                          literature_result: ResearchResult) -> ResearchResult:
        """技術分析実行"""
        logger.info(f"[{self.agent_id}] Starting technical analysis: {task.topic}")
        
        literature = literature_result.content
        
        # 1. 技術的課題分析
        challenges = await self._analyze_technical_challenges(literature)
        
        # 2. 実装パターン分析
        patterns = await self._analyze_implementation_patterns(literature)
        
        # 3. 性能評価・比較
        performance = await self._analyze_performance_metrics(literature)
        
        # 4. 技術成熟度評価
        maturity = await self._assess_technology_maturity(literature)
        
        analysis_result = {
            "technical_challenges": challenges,
            "implementation_patterns": patterns,
            "performance_analysis": performance,
            "technology_maturity": maturity,
            "recommendations": await self._generate_recommendations(challenges, patterns)
        }
        
        result = ResearchResult(
            agent_id=self.agent_id,
            task_id=task.id,
            result_type="analysis",
            content=analysis_result,
            confidence_score=0.85,
            created_at=datetime.now().isoformat()
        )
        
        self.save_result(result)
        return result
    
    async def _analyze_technical_challenges(self, literature: Dict) -> List[Dict]:
        """技術的課題分析"""
        system_prompt = """
        技術文献から主要な技術的課題を特定し、その重要度と解決の困難さを評価してください。
        """
        
        user_prompt = f"""
        文献情報:
        {json.dumps(literature['summary'], ensure_ascii=False)}
        
        この分野の主要な技術的課題を特定し、以下の形式で回答してください:
        - 課題名
        - 重要度 (1-10)
        - 困難度 (1-10)  
        - 現在のアプローチ
        - 制限事項
        """
        
        response = await self._call_llm(system_prompt, user_prompt)
        
        # 簡易解析 (実際はより精密な構造化が必要)
        return [{"challenge": "Sample Challenge", "importance": 8, "difficulty": 7}]
    
    async def _analyze_implementation_patterns(self, literature: Dict) -> List[Dict]:
        """実装パターン分析"""
        # 実装パターンの分析ロジック
        return [{"pattern": "Sample Pattern", "frequency": 5, "effectiveness": 8}]
    
    async def _analyze_performance_metrics(self, literature: Dict) -> Dict:
        """性能分析"""
        return {"average_accuracy": 0.85, "training_time": "2 hours", "inference_speed": "100ms"}
    
    async def _assess_technology_maturity(self, literature: Dict) -> Dict:
        """技術成熟度評価"""
        return {"maturity_level": "emerging", "adoption_rate": "low", "stability": "experimental"}
    
    async def _generate_recommendations(self, challenges: List[Dict], 
                                      patterns: List[Dict]) -> List[str]:
        """推奨事項生成"""
        return ["Recommendation 1", "Recommendation 2", "Recommendation 3"]


class SynthesisAgent(BaseAgent):
    """統合エージェント"""
    
    def __init__(self, agent_id: str, api_key: str):
        super().__init__(agent_id, AgentRole.SYNTHESIZER, api_key)
    
    async def process_task(self, task: ResearchTask, 
                          literature_result: ResearchResult,
                          analysis_result: ResearchResult) -> ResearchResult:
        """知識統合実行"""
        logger.info(f"[{self.agent_id}] Starting knowledge synthesis: {task.topic}")
        
        # 1. クロスドメイン洞察発見
        cross_insights = await self._discover_cross_domain_insights(
            literature_result.content, analysis_result.content)
        
        # 2. 新規研究方向提案
        research_directions = await self._propose_research_directions(
            analysis_result.content, task.research_questions)
        
        # 3. 実装アイデア生成
        implementation_ideas = await self._generate_implementation_ideas(
            literature_result.content, analysis_result.content)
        
        # 4. 統合サマリー作成
        synthesis_summary = await self._create_synthesis_summary(
            cross_insights, research_directions, implementation_ideas)
        
        synthesis_result = {
            "cross_domain_insights": cross_insights,
            "research_directions": research_directions,
            "implementation_ideas": implementation_ideas,
            "synthesis_summary": synthesis_summary,
            "novelty_score": await self._calculate_novelty_score(cross_insights)
        }
        
        result = ResearchResult(
            agent_id=self.agent_id,
            task_id=task.id,
            result_type="synthesis",
            content=synthesis_result,
            confidence_score=0.75,
            created_at=datetime.now().isoformat()
        )
        
        self.save_result(result)
        return result
    
    async def _discover_cross_domain_insights(self, literature: Dict, analysis: Dict) -> List[Dict]:
        """クロスドメイン洞察発見"""
        system_prompt = """
        あなたは異分野知識統合のエキスパートです。
        文献調査と技術分析の結果から、分野横断的な新しい洞察を発見してください。
        """
        
        user_prompt = f"""
        文献情報: {json.dumps(literature, ensure_ascii=False)[:1000]}
        分析結果: {json.dumps(analysis, ensure_ascii=False)[:1000]}
        
        これらの情報から分野横断的な洞察を発見し、以下を含めてください:
        1. 異分野との共通パターン
        2. 技術の新しい組み合わせ可能性
        3. 未探索の研究領域
        """
        
        response = await self._call_llm(system_prompt, user_prompt)
        
        return [{"insight": "Cross-domain insight example", "confidence": 0.8}]
    
    async def _propose_research_directions(self, analysis: Dict, 
                                         research_questions: List[str]) -> List[Dict]:
        """研究方向提案"""
        return [{"direction": "Novel research direction", "feasibility": 0.7, "impact": 0.9}]
    
    async def _generate_implementation_ideas(self, literature: Dict, analysis: Dict) -> List[Dict]:
        """実装アイデア生成"""
        return [{"idea": "Implementation idea", "complexity": "medium", "novelty": 0.8}]
    
    async def _create_synthesis_summary(self, insights: List[Dict], 
                                      directions: List[Dict], ideas: List[Dict]) -> str:
        """統合サマリー作成"""
        return "Comprehensive synthesis summary..."
    
    async def _calculate_novelty_score(self, insights: List[Dict]) -> float:
        """新規性スコア計算"""
        return 0.8


class WriterAgent(BaseAgent):
    """記事作成エージェント"""
    
    def __init__(self, agent_id: str, api_key: str):
        super().__init__(agent_id, AgentRole.WRITER, api_key)
    
    async def process_task(self, task: ResearchTask, 
                          synthesis_result: ResearchResult) -> ResearchResult:
        """記事作成実行"""
        logger.info(f"[{self.agent_id}] Starting article writing: {task.topic}")
        
        synthesis = synthesis_result.content
        
        # 1. 記事構成作成
        article_structure = await self._create_article_structure(task, synthesis)
        
        # 2. 各セクション執筆
        sections = await self._write_article_sections(article_structure, synthesis)
        
        # 3. 記事統合
        full_article = await self._integrate_article(article_structure, sections)
        
        # 4. 品質チェック
        quality_score = await self._check_article_quality(full_article)
        
        # 5. SEO最適化
        seo_metadata = await self._optimize_seo(full_article, task.topic)
        
        article_result = {
            "article_structure": article_structure,
            "full_article": full_article,
            "quality_score": quality_score,
            "seo_metadata": seo_metadata,
            "word_count": len(full_article.split()),
            "estimated_reading_time": len(full_article.split()) // 200
        }
        
        result = ResearchResult(
            agent_id=self.agent_id,
            task_id=task.id,
            result_type="article",
            content=article_result,
            confidence_score=quality_score,
            created_at=datetime.now().isoformat()
        )
        
        self.save_result(result)
        
        # 記事ファイル保存
        await self._save_article_file(task, full_article, seo_metadata)
        
        return result
    
    async def _create_article_structure(self, task: ResearchTask, synthesis: Dict) -> Dict:
        """記事構成作成"""
        system_prompt = """
        技術記事の効果的な構成を作成してください。
        読者にとって理解しやすく、SEOにも最適化された構成にしてください。
        """
        
        user_prompt = f"""
        記事トピック: {task.topic}
        研究結果サマリー: {synthesis.get('synthesis_summary', '')[:500]}
        
        以下を含む記事構成を作成してください:
        1. タイトル案（3つ）
        2. 導入部の要点
        3. 主要セクションの見出し
        4. 各セクションの概要
        5. 結論部の要点
        """
        
        response = await self._call_llm(system_prompt, user_prompt)
        
        return {
            "titles": ["Sample Title 1", "Sample Title 2", "Sample Title 3"],
            "introduction": "Introduction points...",
            "sections": [
                {"title": "Background", "content": "Background content..."},
                {"title": "Analysis", "content": "Analysis content..."},
                {"title": "Implementation", "content": "Implementation content..."}
            ],
            "conclusion": "Conclusion points..."
        }
    
    async def _write_article_sections(self, structure: Dict, synthesis: Dict) -> Dict:
        """各セクション執筆"""
        sections = {}
        
        for section in structure["sections"]:
            system_prompt = f"""
            技術記事の「{section['title']}」セクションを執筆してください。
            専門的でありながら理解しやすい文章を心がけてください。
            """
            
            user_prompt = f"""
            セクション: {section['title']}
            概要: {section['content']}
            参考情報: {json.dumps(synthesis, ensure_ascii=False)[:1000]}
            
            このセクションの内容を詳しく執筆してください。
            コード例や図表の提案も含めてください。
            """
            
            content = await self._call_llm(system_prompt, user_prompt)
            sections[section['title']] = content
        
        return sections
    
    async def _integrate_article(self, structure: Dict, sections: Dict) -> str:
        """記事統合"""
        article_parts = []
        
        # タイトル
        article_parts.append(f"# {structure['titles'][0]}")
        article_parts.append("")
        
        # 導入
        article_parts.append("## はじめに")
        article_parts.append(structure['introduction'])
        article_parts.append("")
        
        # 各セクション
        for section in structure["sections"]:
            article_parts.append(f"## {section['title']}")
            article_parts.append(sections.get(section['title'], section['content']))
            article_parts.append("")
        
        # 結論
        article_parts.append("## まとめ")
        article_parts.append(structure['conclusion'])
        
        return "\n".join(article_parts)
    
    async def _check_article_quality(self, article: str) -> float:
        """記事品質チェック"""
        # 簡易品質指標
        word_count = len(article.split())
        structure_score = len([line for line in article.split('\n') if line.startswith('#')]) / 10
        content_density = word_count / 2000  # 目標2000語
        
        return min((structure_score + content_density) / 2, 1.0)
    
    async def _optimize_seo(self, article: str, topic: str) -> Dict:
        """SEO最適化"""
        return {
            "meta_title": f"{topic} - 最新AI技術解説",
            "meta_description": f"{topic}の最新動向と実装方法を詳しく解説。AI研究の最前線をお届けします。",
            "keywords": [topic, "AI", "machine learning", "implementation"],
            "og_title": f"{topic} - AI技術解説",
            "og_description": f"{topic}の詳細な技術解説と実装ガイド"
        }
    
    async def _save_article_file(self, task: ResearchTask, article: str, seo: Dict):
        """記事ファイル保存"""
        articles_dir = Path("articles/generated")
        articles_dir.mkdir(parents=True, exist_ok=True)
        
        # Frontmatter付きMarkdown形式で保存
        frontmatter = f"""---
title: "{seo['meta_title']}"
description: "{seo['meta_description']}"
keywords: {json.dumps(seo['keywords'])}
created_at: "{datetime.now().isoformat()}"
task_id: "{task.id}"
topic: "{task.topic}"
published: true
---

"""
        
        file_path = articles_dir / f"{task.id}_generated_article.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + article)
        
        logger.info(f"Article saved: {file_path}")


class CollaborativeResearchSystem:
    """協調研究システム"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.agents = {
            "researcher": ResearchAgent("researcher_001", api_key),
            "analyst": AnalysisAgent("analyst_001", api_key),
            "synthesizer": SynthesisAgent("synthesizer_001", api_key),
            "writer": WriterAgent("writer_001", api_key)
        }
        self.tasks: List[ResearchTask] = []
        self.results: Dict[str, List[ResearchResult]] = {}
    
    def create_research_task(self, topic: str, research_questions: List[str],
                           target_domains: List[str], priority: int = 1) -> str:
        """研究タスク作成"""
        task_id = f"TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = ResearchTask(
            id=task_id,
            topic=topic,
            research_questions=research_questions,
            target_domains=target_domains,
            deadline=(datetime.now().strftime('%Y-%m-%d')),
            priority=priority
        )
        
        self.tasks.append(task)
        self.results[task_id] = []
        
        logger.info(f"Created research task: {task_id} - {topic}")
        return task_id
    
    async def execute_research_pipeline(self, task_id: str) -> Dict[str, ResearchResult]:
        """研究パイプライン実行"""
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        logger.info(f"Starting research pipeline: {task_id}")
        
        # 1. 文献調査
        literature_result = await self.agents["researcher"].process_task(task)
        self.results[task_id].append(literature_result)
        
        # 2. 技術分析
        analysis_result = await self.agents["analyst"].process_task(task, literature_result)
        self.results[task_id].append(analysis_result)
        
        # 3. 知識統合
        synthesis_result = await self.agents["synthesizer"].process_task(
            task, literature_result, analysis_result)
        self.results[task_id].append(synthesis_result)
        
        # 4. 記事作成
        article_result = await self.agents["writer"].process_task(task, synthesis_result)
        self.results[task_id].append(article_result)
        
        # タスク完了
        task.status = "completed"
        
        pipeline_results = {
            "literature": literature_result,
            "analysis": analysis_result,
            "synthesis": synthesis_result,
            "article": article_result
        }
        
        logger.info(f"Research pipeline completed: {task_id}")
        return pipeline_results
    
    def get_system_stats(self) -> Dict:
        """システム統計"""
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks if t.status == "completed"])
        total_results = sum(len(results) for results in self.results.values())
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "total_results": total_results,
            "agents_count": len(self.agents)
        }


async def main():
    """デモ実行"""
    import os
    
    # API Key設定 (環境変数から取得)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return
    
    # システム初期化
    research_system = CollaborativeResearchSystem(api_key)
    
    # 研究タスク作成
    task_id = research_system.create_research_task(
        topic="Multi-Agent Reinforcement Learning",
        research_questions=[
            "What are the latest advances in multi-agent RL?",
            "How do agents coordinate in complex environments?",
            "What are the scalability challenges?"
        ],
        target_domains=["reinforcement-learning", "multi-agent-systems", "game-theory"],
        priority=1
    )
    
    # 研究パイプライン実行
    try:
        results = await research_system.execute_research_pipeline(task_id)
        
        print(f"\n🎉 Research Pipeline Completed!")
        print(f"Task ID: {task_id}")
        print(f"Results Generated:")
        for result_type, result in results.items():
            print(f"  - {result_type}: {result.confidence_score:.2f} confidence")
        
        # システム統計表示
        stats = research_system.get_system_stats()
        print(f"\n📊 System Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Research pipeline failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())