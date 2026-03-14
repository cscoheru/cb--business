# services/data_fusion.py
"""数据融合服务 - 打通数据孤岛核心实现

将爬虫AI分析结果与Card生成融合：
1. 从articles表获取AI分析的文章（包含content_theme, opportunity_score等）
2. 基于文章内容识别相关产品品类
3. 将AI洞察融入到Card生成过程中
4. 生成包含多源数据的综合商机卡片
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from config.database import AsyncSessionLocal
from models.article import Article

logger = logging.getLogger(__name__)


class DataFusionService:
    """数据融合服务 - 连接爬虫AI分析与Card生成"""

    def __init__(self):
        self.category_keywords = {
            'wireless_earbuds': ['耳机', 'earbuds', 'headphones', 'audio', '音频'],
            'smart_plugs': ['智能插座', 'smart plug', 'outlet', '插座', '智能'],
            'fitness_trackers': ['健身', 'fitness', 'tracker', 'watch', '健康', '运动'],
            'phone_chargers': ['充电器', 'charger', 'charging', '充电', '电源'],
            'desk_lamps': ['台灯', 'desk lamp', 'lighting', '灯具', '照明'],
            'phone_cases': ['手机壳', 'phone case', 'case', '保护壳', 'case'],
            'yoga_mats': ['瑜伽垫', 'yoga mat', 'fitness', '瑜伽', '运动'],
            'coffee_makers': ['咖啡机', 'coffee maker', '咖啡', 'coffeemaker'],
            'bluetooth_speakers': ['音箱', 'speakers', 'audio', '音响', '扬声器'],
            'webcams': ['摄像头', 'webcam', 'camera', '相机', '摄像头'],
            'keyboards': ['键盘', 'keyboard', '输入设备', '机械键盘'],
            'mouse': ['鼠标', 'mouse', '输入设备', '无线鼠标']
        }

    async def get_relevant_ai_insights(
        self,
        category_key: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        获取与特定品类相关的AI分析洞察

        Args:
            category_key: 品类key
            days_back: 查询最近几天的数据

        Returns:
            AI洞察数据聚合
        """
        keywords = self.category_keywords.get(category_key, [])

        if not keywords:
            logger.warning(f"品类 {category_key} 没有配置关键词")
            return self._get_empty_insights()

        async with AsyncSessionLocal() as db:
            # 查询最近的相关文章
            cutoff_date = datetime.now() - timedelta(days=days_back)

            # 构建关键词匹配条件
            conditions = []
            for keyword in keywords[:5]:  # 限制关键词数量
                conditions.append(Article.title.ilike(f'%{keyword}%'))
                conditions.append(Article.summary.ilike(f'%{keyword}%'))

            query = select(Article).where(
                and_(
                    Article.published_at >= cutoff_date,
                    or_(*conditions) if conditions else True,
                    Article.is_processed == True
                )
            ).order_by(Article.published_at.desc()).limit(20)

            result = await db.execute(query)
            articles = result.scalars().all()

            if not articles:
                logger.info(f"品类 {category_key} 暂无相关AI分析文章")
                return self._get_empty_insights()

            # 聚合AI分析结果
            insights = self._aggregate_insights(articles, category_key)
            logger.info(f"✅ {category_key}: 融合了 {len(articles)} 篇AI分析文章")
            return insights

    def _aggregate_insights(self, articles: List[Article], category_key: str) -> Dict[str, Any]:
        """聚合多篇文章的AI分析结果"""
        total_opportunity_score = 0
        high_opportunity_articles = []
        themes_count = {}
        regions_count = {}
        platforms_count = {}
        risk_levels = {'low': 0, 'medium': 0, 'high': 0}

        for article in articles:
            # 累加机会分数
            if article.opportunity_score:
                total_opportunity_score += article.opportunity_score

            # 高机会文章 (降低阈值以包含更多相关文章)
            if article.opportunity_score and article.opportunity_score >= 0.5:
                high_opportunity_articles.append({
                    'id': str(article.id),
                    'title': article.title,
                    'summary': article.summary,
                    'opportunity_score': article.opportunity_score,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'source': article.source,
                    'region': article.region,
                    'country': article.country
                })

            # 统计主题
            if article.content_theme:
                themes_count[article.content_theme] = themes_count.get(article.content_theme, 0) + 1

            # 统计地区
            if article.region:
                regions_count[article.region] = regions_count.get(article.region, 0) + 1

            # 统计平台
            if article.platform:
                platforms_count[article.platform] = platforms_count.get(article.platform, 0) + 1

            # 统计风险等级
            if article.risk_level:
                risk_levels[article.risk_level] = risk_levels.get(article.risk_level, 0) + 1

        # 计算平均机会分数
        avg_opportunity_score = total_opportunity_score / len(articles) if articles else 0

        return {
            'total_articles': len(articles),
            'avg_opportunity_score': round(avg_opportunity_score, 3),
            'high_opportunity_count': len(high_opportunity_articles),
            'high_opportunity_articles': high_opportunity_articles[:5],  # 只返回前5个
            'themes': themes_count,
            'regions': regions_count,
            'platforms': platforms_count,
            'risk_levels': risk_levels,
            'fusion_metadata': {
                'category': category_key,
                'fusion_time': datetime.now().isoformat(),
                'data_sources': ['crawler_ai_analysis']
            }
        }

    def _get_empty_insights(self) -> Dict[str, Any]:
        """返回空的洞察结构"""
        return {
            'total_articles': 0,
            'avg_opportunity_score': 0,
            'high_opportunity_count': 0,
            'high_opportunity_articles': [],
            'themes': {},
            'regions': {},
            'platforms': {},
            'risk_levels': {'low': 0, 'medium': 0, 'high': 0},
            'fusion_metadata': {
                'fusion_time': datetime.now().isoformat(),
                'data_sources': []
            }
        }

    def enrich_card_content(
        self,
        base_content: Dict[str, Any],
        ai_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将AI洞察融入Card内容

        Args:
            base_content: CardGenerator生成的基础内容 (实际上是analysis dict本身)
            ai_insights: 爬虫AI分析结果

        Returns:
            融合后的内容
        """
        # 直接在base_content中添加AI洞察 (base_content就是analysis dict)
        base_content['ai_insights_fusion'] = {
            'article_count': ai_insights['total_articles'],
            'avg_opportunity_score': ai_insights['avg_opportunity_score'],
            'trending_themes': dict(list(ai_insights['themes'].items())[:3]),
            'hot_regions': dict(list(ai_insights['regions'].items())[:3]),
            'platform_signals': dict(list(ai_insights['platforms'].items())[:3])
        }

        # 如果有高机会文章，添加到推荐理由中
        if ai_insights['high_opportunity_articles']:
            base_content['ai_evidence'] = [
                {
                    'title': art['title'],
                    'score': art['opportunity_score'],
                    'source': art['source']
                }
                for art in ai_insights['high_opportunity_articles'][:3]
            ]

        return base_content


# 全局单例
data_fusion_service = DataFusionService()
