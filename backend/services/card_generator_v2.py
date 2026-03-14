# services/card_generator_v2.py
"""卡片生成服务 V2 - 多数据源聚合架构

新架构特点：
1. 通过DataSourceRegistry并行获取多个数据源
2. AI分析基于所有数据源的综合数据
3. 每个数据源可独立替换/启用/禁用
4. 单个数据源失败不影响整体

数据流向：
┌─────────────────────────────────────────────────────┐
│  CardGenerator                                     │
│  1. fetch_category_data()                          │
│     └─> data_source_registry.fetch_all()           │
│         └─> 并行调用所有启用的数据源                │
│             ├─> Oxylabs (产品/价格/评分)           │
│             ├─> Google Trends (搜索趋势)           │
│             └─> Reddit (社交讨论)                   │
│                                                     │
│  2. analyze_with_ai()                              │
│     └─> 基于所有数据源的综合分析                   │
│         ├─> 产品数据分析                           │
│         ├─> 趋势分析                               │
│         └─> 综合评分                               │
└─────────────────────────────────────────────────────┘
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from models.card import Card
from config.database import AsyncSessionLocal
from sqlalchemy import select
from services.cache import cache_service
from services.data_source_registry import data_source_registry
from services.data_source_init import initialize_data_sources

logger = logging.getLogger(__name__)


# 3个目标品类配置
CATEGORIES = {
    'wireless_earbuds': {
        'name': '无线耳机',
        'search_queries': ['wireless earbuds', 'bluetooth earbuds'],
        'limit': 20
    },
    'smart_plugs': {
        'name': '智能插座',
        'search_queries': ['smart plug', 'wifi outlet'],
        'limit': 20
    },
    'fitness_trackers': {
        'name': '健身追踪器',
        'search_queries': ['fitness tracker', 'fitness watch'],
        'limit': 20
    }
}


class CardGenerator:
    """卡片生成服务 - 多数据源架构"""

    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """确保数据源已初始化"""
        if not self._initialized:
            await initialize_data_sources()
            self._initialized = True

    async def close(self):
        """关闭资源（如有需要）"""
        pass

    async def fetch_category_data(
        self,
        category_key: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取指定品类的综合市场数据（多数据源聚合）

        Args:
            category_key: 品类key
            use_cache: 是否使用缓存（默认True）

        Returns:
            聚合后的数据：
            {
                "products": [...],      # 来自Oxylabs等电商数据源
                "trends": [...],        # 来自Google Trends等
                "sentiments": [...],     # 来自Reddit等社交数据源
                "sources": {             # 各数据源原始数据
                    "oxylabs": {...},
                    "google_trends": {...}
                },
                "metadata": {            # 元数据
                    "total_sources": 2,
                    "successful_sources": 2,
                    "fetch_time": "...",
                    "data_points": 50
                }
            }
        """
        await self._ensure_initialized()

        if category_key not in CATEGORIES:
            raise ValueError(f"未知品类: {category_key}")

        config = CATEGORIES[category_key]
        cache_key = f"aggregated_data:{category_key}"

        # 尝试从缓存获取
        if use_cache:
            cached_data = await cache_service.get("aggregated", category_key)
            if cached_data:
                logger.info(f"✅ {config['name']} 使用缓存数据")
                return cached_data

        logger.info(f"🔍 获取{config['name']}的综合数据...")

        try:
            # 并行调用所有数据源
            # 使用第一个搜索关键词作为主查询
            primary_query = config['search_queries'][0]

            result = await data_source_registry.fetch_all(
                category=category_key,
                query=primary_query,
                limit=config['limit'],
                timeout=30.0
            )

            if not result["success"]:
                logger.error(f"❌ 所有数据源均失败")
                # 尝试返回过期缓存
                if use_cache:
                    stale_data = await cache_service.get("aggregated", category_key)
                    if stale_data:
                        logger.warning(f"⚠️ 使用过期缓存数据")
                        return stale_data
                return self._get_empty_result()

            # 记录数据源状态
            logger.info(
                f"✅ 数据获取完成: {result['successful_sources']}/{result['total_sources']} 个数据源成功"
            )

            # 缓存30分钟
            if result.get("aggregated"):
                await cache_service.set(
                    "aggregated",
                    category_key,
                    result,
                    ttl=1800  # 30分钟
                )

            return result

        except Exception as e:
            logger.error(f"❌ 获取{config['name']}数据失败: {e}")
            # 如果API失败，尝试返回过期的缓存数据
            if use_cache:
                stale_data = await cache_service.get("aggregated", category_key)
                if stale_data:
                    logger.warning(f"⚠️ 使用过期缓存数据")
                    return stale_data
            return self._get_empty_result()

    def _get_empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "products": [],
            "trends": [],
            "sentiments": [],
            "sources": {},
            "metadata": {
                "total_sources": 0,
                "successful_sources": 0,
                "fetch_time": datetime.now().isoformat(),
                "data_points": 0
            }
        }

    async def analyze_with_ai(
        self,
        category_key: str,
        aggregated_data: Dict[str, Any]
    ) -> Dict:
        """
        使用AI分析多源聚合数据，生成卡片内容

        Args:
            category_key: 品类key
            aggregated_data: 多数据源聚合数据

        Returns:
            分析结果
        """
        logger.info(f"🤖 AI分析{category_key}...")

        # 提取各类型数据
        products = aggregated_data.get("products", [])
        trends = aggregated_data.get("trends", [])
        sentiments = aggregated_data.get("sentiments", [])
        metadata = aggregated_data.get("metadata", {})

        # 1. 产品数据分析（来自Oxylabs等电商数据源）
        price_analysis = self._analyze_prices(products)
        rating_analysis = self._analyze_ratings(products)

        # 2. 趋势分析（来自Google Trends等）
        trend_analysis = self._analyze_trends(trends)

        # 3. 情感分析（来自Reddit等社交数据源）
        sentiment_analysis = self._analyze_sentiments(sentiments)

        # 4. 数据源可靠性分析
        source_reliability = self._calculate_source_reliability(metadata)

        # 综合分析
        analysis = {
            'category': category_key,
            'category_name': CATEGORIES[category_key]['name'],
            'market_data': {
                # 产品数据
                'total_products': len(products),
                'price_analysis': price_analysis,
                'rating_analysis': rating_analysis,

                # 趋势数据
                'trend_analysis': trend_analysis,

                # 情感数据
                'sentiment_analysis': sentiment_analysis,

                # 数据源信息
                'data_sources': metadata.get('sources_called', []),
                'total_sources': metadata.get('total_sources', 0),
                'successful_sources': metadata.get('successful_sources', 0),
                'reliability': source_reliability,
                'fetch_time': metadata.get('fetch_time', datetime.now().isoformat())
            },
            'insights': self._generate_insights(
                category_key,
                products,
                trends,
                price_analysis,
                trend_analysis
            ),
            'opportunity_score': self._calculate_opportunity_score(
                category_key,
                price_analysis,
                rating_analysis,
                trend_analysis,
                sentiment_analysis
            ),
            'recommendations': self._generate_recommendations(
                category_key,
                products,
                trends
            )
        }

        logger.info(f"✅ AI分析完成")
        return analysis

    def _analyze_prices(self, products: List[Dict]) -> Dict:
        """分析价格数据"""
        prices = [p.get('price', 0) for p in products if p.get('price')]

        if not prices:
            return {}

        return {
            'min': round(min(prices), 2),
            'max': round(max(prices), 2),
            'avg': round(sum(prices) / len(prices), 2),
            'median': round(sorted(prices)[len(prices) // 2], 2),
            'count': len(prices)
        }

    def _analyze_ratings(self, products: List[Dict]) -> Dict:
        """分析评分数据"""
        ratings = [p.get('rating', 0) for p in products if p.get('rating')]

        if not ratings:
            return {}

        return {
            'min': round(min(ratings), 2),
            'max': round(max(ratings), 2),
            'avg': round(sum(ratings) / len(ratings), 2),
            'count': len(ratings)
        }

    def _analyze_trends(self, trends: List[Dict]) -> Dict:
        """分析趋势数据"""
        if not trends:
            return {}

        # 提取趋势量级
        volumes = [t.get('volume', 0) for t in trends if t.get('volume')]
        traffic = [t.get('traffic', 0) for t in trends if t.get('traffic')]

        return {
            'total_trends': len(trends),
            'avg_volume': round(sum(volumes) / len(volumes), 2) if volumes else 0,
            'total_traffic_growth': round(sum(traffic), 2) if traffic else 0,
            'top_keywords': [t.get('keyword', '') for t in trends[:5]]
        }

    def _analyze_sentiments(self, sentiments: List[Dict]) -> Dict:
        """分析情感数据"""
        if not sentiments:
            return {}

        positive = sum(1 for s in sentiments if s.get('sentiment') == 'positive')
        negative = sum(1 for s in sentiments if s.get('sentiment') == 'negative')
        neutral = sum(1 for s in sentiments if s.get('sentiment') == 'neutral')

        return {
            'total_mentions': len(sentiments),
            'positive_ratio': round(positive / len(sentiments), 2) if sentiments else 0,
            'negative_ratio': round(negative / len(sentiments), 2) if sentiments else 0,
            'neutral_ratio': round(neutral / len(sentiments), 2) if sentiments else 0
        }

    def _calculate_source_reliability(self, metadata: Dict) -> float:
        """计算综合数据可靠性"""
        total = metadata.get('total_sources', 1)
        successful = metadata.get('successful_sources', 0)

        # 基础可靠性：成功的数据源比例
        base_reliability = successful / total if total > 0 else 0

        # 各数据源权重的加权平均（简化版）
        # Oxylabs: 0.95, Google Trends: 0.85
        sources_called = metadata.get('sources_called', [])
        source_weights = {
            'oxylabs': 0.6,
            'google_trends': 0.4
        }

        weighted_reliability = 0.0
        for source in sources_called:
            if source in source_weights:
                weighted_reliability += source_weights[source]

        # 综合成功率 + 权重可靠性
        final_reliability = (base_reliability * 0.5 + weighted_reliability * 0.5)

        return round(final_reliability, 2)

    def _generate_insights(
        self,
        category_key: str,
        products: List[Dict],
        trends: List[Dict],
        price_analysis: Dict,
        trend_analysis: Dict
    ) -> Dict:
        """生成综合洞察"""
        return {
            'price_sweet_spot': self._get_price_sweet_spot(category_key, price_analysis),
            'top_products': products[:5] if len(products) >= 5 else products,
            'rising_trends': trends[:3] if len(trends) >= 3 else trends,
            'market_saturation': 'high' if len(products) > 15 else 'medium',
            'trend_strength': self._assess_trend_strength(trend_analysis)
        }

    def _get_price_sweet_spot(self, category_key: str, price_analysis: Dict) -> Dict:
        """获取价格甜蜜点"""
        # 基于品类的基础甜蜜点
        base_spots = {
            'wireless_earbuds': {'min': 20, 'max': 30, 'best': 25},
            'smart_plugs': {'min': 20, 'max': 30, 'best': 25},
            'fitness_trackers': {'min': 30, 'max': 50, 'best': 45}
        }

        base_spot = base_spots.get(category_key, {'min': 20, 'max': 50, 'best': 35})

        # 如果有实际价格数据，调整甜蜜点
        if price_analysis and 'avg' in price_analysis:
            avg_price = price_analysis['avg']
            # 甜蜜点在平均价格的80%-120%之间
            base_spot['best'] = round(avg_price, 2)
            base_spot['min'] = round(avg_price * 0.8, 2)
            base_spot['max'] = round(avg_price * 1.2, 2)

        return base_spot

    def _assess_trend_strength(self, trend_analysis: Dict) -> str:
        """评估趋势强度"""
        if not trend_analysis:
            return 'unknown'

        avg_volume = trend_analysis.get('avg_volume', 0)
        traffic_growth = trend_analysis.get('total_traffic_growth', 0)

        if avg_volume > 70 or traffic_growth > 100:
            return 'high'
        elif avg_volume > 40 or traffic_growth > 50:
            return 'medium'
        else:
            return 'low'

    def _calculate_opportunity_score(
        self,
        category_key: str,
        price_analysis: Dict,
        rating_analysis: Dict,
        trend_analysis: Dict,
        sentiment_analysis: Dict
    ) -> int:
        """计算综合机会评分（0-100）

        考虑因素：
        1. 价格竞争度（价格越低，机会越大）
        2. 产品评分质量
        3. 搜索趋势强度
        4. 社交情感正面度
        5. 品类特定因素
        """
        score = 50  # 基础分

        # 1. 价格竞争度 (30分)
        if price_analysis.get('avg', 0) < 50:
            score += 30
        elif price_analysis.get('avg', 0) < 100:
            score += 20
        elif price_analysis.get('avg', 0) < 150:
            score += 10

        # 2. 评分质量 (20分)
        if rating_analysis.get('avg', 0) > 4.5:
            score += 20
        elif rating_analysis.get('avg', 0) > 4.0:
            score += 15
        elif rating_analysis.get('avg', 0) > 3.5:
            score += 10

        # 3. 趋势强度 (15分)
        trend_strength = self._assess_trend_strength(trend_analysis)
        if trend_strength == 'high':
            score += 15
        elif trend_strength == 'medium':
            score += 10
        elif trend_strength == 'low':
            score += 5

        # 4. 情感正面度 (10分)
        positive_ratio = sentiment_analysis.get('positive_ratio', 0)
        if positive_ratio > 0.7:
            score += 10
        elif positive_ratio > 0.5:
            score += 5

        # 5. 品类特定调整 (-25 到 +25)
        category_adjustments = {
            'wireless_earbuds': 10,   # 需求大
            'smart_plugs': 0,         # 竞争激烈
            'fitness_trackers': 15    # 市场大
        }
        score += category_adjustments.get(category_key, 0)

        return min(max(score, 0), 100)  # 限制在0-100

    def _generate_recommendations(
        self,
        category_key: str,
        products: List[Dict],
        trends: List[Dict]
    ) -> List[str]:
        """生成推荐建议"""
        recommendations = []

        if category_key == 'wireless_earbuds':
            recommendations = [
                "目标价格: $25-35，靠近畅销产品价格区间",
                "核心卖点: 防丢失设计 + 稳定连接",
                "差异化: 不拼高端ANC，专注解决用户痛点",
                "市场定位: 东南亚（性价比）+ 美国（品质）"
            ]
            # 添加基于趋势的建议
            if trends:
                top_trend = trends[0].get('keyword', '')
                if top_trend:
                    recommendations.append(f"热门趋势: 关注 '{top_trend}' 相关功能")

        elif category_key == 'smart_plugs':
            recommendations = [
                "目标价格: $20-30",
                "核心功能: 能耗监测 + 多插座设计",
                "差异化: 避免纯价格竞争",
                "市场定位: 美国智能家居市场"
            ]

        elif category_key == 'fitness_trackers':
            recommendations = [
                "目标价格: $40-60 (中端) 或 $20-30 (预算)",
                "核心功能: 长续航 (+2周) + 健康监测",
                "差异化: 避免与Apple/Samsung正面竞争",
                "市场定位: 预算市场 + 特定运动场景"
            ]

        return recommendations

    async def generate_card(self, category_key: str) -> Card:
        """
        生成单个品类的信息卡片

        Args:
            category_key: 品类key

        Returns:
            Card对象
        """
        logger.info(f"🎨 生成{category_key}卡片...")

        # 1. 获取多数据源聚合数据
        aggregated_data = await self.fetch_category_data(category_key, use_cache=True)

        # 检查是否有有效数据
        if (not aggregated_data.get("products") and
            not aggregated_data.get("trends") and
            not aggregated_data.get("sentiments")):
            raise ValueError(f"无法获取{category_key}的有效数据")

        # 2. AI综合分析
        analysis = await self.analyze_with_ai(category_key, aggregated_data)

        # 3. 生成卡片内容
        content = self._generate_card_content(analysis)

        # 4. 创建Card对象
        card = Card(
            title=f"{analysis['category_name']}市场洞察 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            category=category_key,
            content=content,
            analysis=analysis,
            amazon_data={'products': aggregated_data.get("products", [])[:10]},
            is_published=False
        )

        logger.info(f"✅ 卡片生成完成: {card.title}")
        return card

    def _generate_card_content(self, analysis: Dict) -> Dict:
        """生成卡片展示内容"""
        return {
            'summary': {
                'title': analysis['category_name'],
                'opportunity_score': analysis['opportunity_score'],
                'market_size': analysis['market_data']['total_products'],
                'sweet_spot': analysis['insights']['price_sweet_spot'],
                'reliability': analysis['market_data']['reliability']
            },
            'market_data': {
                'price': analysis['market_data']['price_analysis'],
                'rating': analysis['market_data']['rating_analysis'],
                'trends': analysis['market_data'].get('trend_analysis', {}),
                'sentiments': analysis['market_data'].get('sentiment_analysis', {})
            },
            'insights': analysis['insights'],
            'recommendations': analysis['recommendations'],
            'data_sources': analysis['market_data']['data_sources'],
            'generated_at': datetime.now().isoformat()
        }


# ============ 导出函数（保持与旧版本兼容） ============

async def get_or_generate_cards() -> List[Card]:
    """获取或生成卡片（按需生成 + 智能缓存）"""
    cache_key = "daily_cards_v2"
    cache_ttl = 1800  # 30分钟缓存

    # 1. 尝试从缓存获取
    cached_cards = await cache_service.get_json("cards_v2", "daily")
    if cached_cards:
        logger.info("✅ 使用缓存的卡片数据")
        return cached_cards

    # 2. 缓存未命中，生成新卡片
    logger.info("🔄 缓存未命中，生成新卡片...")
    return await generate_and_cache_cards()


async def generate_and_cache_cards() -> List[Card]:
    """生成并缓存卡片"""
    generator = CardGenerator()
    results = []

    try:
        # 为每个品类生成卡片
        for category_key in CATEGORIES.keys():
            try:
                card = await generator.generate_card(category_key)

                # 保存到数据库
                async with AsyncSessionLocal() as session:
                    session.add(card)
                    await session.commit()
                    logger.info(f"💾 已保存: {card.id}")

                results.append(card)

            except Exception as e:
                logger.error(f"❌ 生成{category_key}卡片失败: {e}")
                # 如果某个品类失败，尝试从数据库获取最新的
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(Card)
                        .where(Card.category == category_key)
                        .where(Card.is_published == True)
                        .order_by(Card.created_at.desc())
                        .limit(1)
                    )
                    existing_card = result.scalar_one_or_none()
                    if existing_card:
                        results.append(existing_card)
                        logger.warning(f"⚠️ 使用过期数据替代: {category_key}")

        await generator.close()

        # 缓存结果
        if results:
            card_dicts = [card.to_dict() for card in results]
            await cache_service.set_json("cards_v2", "daily", card_dicts, ttl=1800)
            logger.info(f"💾 已缓存 {len(results)} 张卡片")

        return results

    except Exception as e:
        logger.error(f"❌ 卡片生成失败: {e}")
        await generator.close()
        return []


async def get_cards_for_user() -> Dict[str, Any]:
    """为用户获取卡片（按需生成模式）"""
    try:
        cards = await get_or_generate_cards()

        return {
            "success": True,
            "count": len(cards),
            "cards": [card.to_dict() for card in cards],
            "cache_info": {
                "mode": "实时生成（多数据源）",
                "cache_ttl": "30分钟",
                "data_sources": data_source_registry.list_enabled_sources()
            }
        }
    except Exception as e:
        logger.error(f"获取卡片失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def generate_daily_cards_task():
    """后台定时任务"""
    logger.info("🔄 执行后台数据更新...")
    result = await generate_and_cache_cards()
    logger.info(f"✅ 后台更新完成: {len(result)} 张卡片")
    return result
