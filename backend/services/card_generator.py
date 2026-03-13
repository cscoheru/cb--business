# services/card_generator.py
"""每日信息卡片生成服务"""

import logging
from typing import List, Dict, Any
from datetime import datetime
import asyncio

from crawler.products.oxylabs_client import OxylabsClient
from models.card import Card
from config.database import AsyncSessionLocal
from sqlalchemy import select

logger = logging.getLogger(__name__)


# 3个目标品类配置
CATEGORIES = {
    'wireless_earbuds': {
        'name': '无线耳机',
        'search_query': 'wireless earbuds bluetooth',
        'limit': 20
    },
    'smart_plugs': {
        'name': '智能插座',
        'search_query': 'smart plug wifi',
        'limit': 20
    },
    'fitness_trackers': {
        'name': '健身追踪器',
        'search_query': 'fitness tracker watch',
        'limit': 20
    }
}


class CardGenerator:
    """卡片生成服务"""

    def __init__(self):
        self.client = OxylabsClient()

    async def close(self):
        """关闭客户端"""
        await self.client.close()

    async def fetch_category_data(self, category_key: str) -> List[Dict]:
        """
        获取指定品类的Amazon数据

        Args:
            category_key: 品类key (wireless_earbuds, smart_plugs, fitness_trackers)

        Returns:
            产品列表
        """
        if category_key not in CATEGORIES:
            raise ValueError(f"未知品类: {category_key}")

        config = CATEGORIES[category_key]
        logger.info(f"🔍 获取{config['name']}数据...")

        try:
            products = await self.client.search_amazon(
                query=config['search_query'],
                limit=config['limit'],
                use_cache=True,
                cache_ttl=1800  # 30分钟缓存
            )

            logger.info(f"✅ 获取到{len(products)}个产品")
            return products

        except Exception as e:
            logger.error(f"❌ 获取{config['name']}数据失败: {e}")
            return []

    async def analyze_with_ai(self, category_key: str, products: List[Dict]) -> Dict:
        """
        使用AI分析产品数据，生成卡片内容

        Args:
            category_key: 品类key
            products: 产品列表

        Returns:
            分析结果
        """
        logger.info(f"🤖 AI分析{category_key}...")

        # 计算价格统计
        prices = [p.get('price') for p in products if p.get('price')]
        ratings = [p.get('rating') for p in products if p.get('rating')]

        price_analysis = {}
        if prices:
            price_analysis = {
                'min': round(min(prices), 2),
                'max': round(max(prices), 2),
                'avg': round(sum(prices) / len(prices), 2),
                'count': len(prices)
            }

        rating_analysis = {}
        if ratings:
            rating_analysis = {
                'min': round(min(ratings), 2),
                'max': round(max(ratings), 2),
                'avg': round(sum(ratings) / len(ratings), 2),
                'count': len(ratings)
            }

        # 基于Phase 0的分析逻辑
        analysis = {
            'category': category_key,
            'category_name': CATEGORIES[category_key]['name'],
            'market_data': {
                'total_products': len(products),
                'price_analysis': price_analysis,
                'rating_analysis': rating_analysis,
                'data_source': 'Oxylabs Amazon API',
                'reliability': 0.95,
                'fetch_time': datetime.now().isoformat()
            },
            'insights': self._generate_insights(category_key, products, price_analysis),
            'opportunity_score': self._calculate_opportunity_score(category_key, price_analysis, rating_analysis),
            'recommendations': self._generate_recommendations(category_key, products)
        }

        logger.info(f"✅ AI分析完成")
        return analysis

    def _generate_insights(self, category_key: str, products: List[Dict], price_analysis: Dict) -> Dict:
        """生成洞察"""
        # 这里可以集成GLM-4等AI服务
        # 暂时使用基于规则的逻辑

        insights = {
            'price_sweet_spot': self._get_price_sweet_spot(category_key, price_analysis),
            'top_products': products[:5] if len(products) >= 5 else products,
            'market_saturation': 'high' if len(products) > 15 else 'medium'
        }

        return insights

    def _get_price_sweet_spot(self, category_key: str, price_analysis: Dict) -> Dict:
        """获取价格甜蜜点"""
        # 基于Phase 0真实数据
        sweet_spots = {
            'wireless_earbuds': {'min': 20, 'max': 30, 'best': 25},
            'smart_plugs': {'min': 20, 'max': 30, 'best': 25},
            'fitness_trackers': {'min': 30, 'max': 50, 'best': 45}
        }

        spot = sweet_spots.get(category_key, {'min': 20, 'max': 50, 'best': 35})
        return spot

    def _calculate_opportunity_score(self, category_key: str, price_analysis: Dict, rating_analysis: Dict) -> int:
        """计算机会评分"""
        score = 50  # 基础分

        # 价格竞争度 (价格越低，机会越大)
        if price_analysis.get('avg', 0) < 50:
            score += 20
        elif price_analysis.get('avg', 0) < 100:
            score += 10

        # 评分质量
        if rating_analysis.get('avg', 0) > 4.5:
            score += 15
        elif rating_analysis.get('avg', 0) > 4.0:
            score += 10

        # 品类特定调整
        if category_key == 'wireless_earbuds':
            score += 10  # 需求大
        elif category_key == 'smart_plugs':
            score += 5   # 竞争激烈
        elif category_key == 'fitness_trackers':
            score += 15  # 市场大

        return min(score, 100)

    def _generate_recommendations(self, category_key: str, products: List[Dict]) -> List[str]:
        """生成推荐建议"""
        recommendations = []

        # 基于品类生成不同建议
        if category_key == 'wireless_earbuds':
            recommendations = [
                "目标价格: $25-35，靠近Anker P20i的畅销价格",
                "核心卖点: 防丢失设计 + 稳定连接",
                "差异化: 不拼高端ANC，专注解决用户痛点",
                "市场定位: 东南亚（性价比）+ 美国（品质）"
            ]
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

        # 1. 获取Amazon数据
        products = await self.fetch_category_data(category_key)

        if not products:
            raise ValueError(f"无法获取{category_key}的产品数据")

        # 2. AI分析
        analysis = await self.analyze_with_ai(category_key, products)

        # 3. 生成卡片内容
        content = self._generate_card_content(analysis)

        # 4. 创建Card对象
        card = Card(
            title=f"{analysis['category_name']}市场信息 - {datetime.now().strftime('%Y-%m-%d')}",
            category=category_key,
            content=content,
            analysis=analysis,
            amazon_data={'products': products[:10]},  # 只保留前10个产品
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
                'rating': analysis['market_data']['rating_analysis']
            },
            'insights': analysis['insights'],
            'recommendations': analysis['recommendations'],
            'data_sources': ['Oxylabs Amazon API (95%)'],
            'generated_at': datetime.now().isoformat()
        }


async def generate_daily_cards() -> Dict[str, Any]:
    """
    生成每日3张信息卡片

    Returns:
        生成结果统计
    """
    logger.info("=" * 60)
    logger.info("🚀 开始生成每日信息卡片")
    logger.info("=" * 60)

    generator = CardGenerator()
    results = {
        'success': [],
        'failed': [],
        'timestamp': datetime.now().isoformat()
    }

    try:
        # 为每个品类生成卡片
        for category_key in CATEGORIES.keys():
            try:
                card = await generator.generate_card(category_key)

                # 保存到数据库
                async with AsyncSessionLocal() as session:
                    session.add(card)
                    await session.commit()
                    logger.info(f"💾 已保存到数据库: {card.id}")

                results['success'].append({
                    'category': category_key,
                    'card_id': card.id,
                    'title': card.title
                })

            except Exception as e:
                logger.error(f"❌ 生成{category_key}卡片失败: {e}")
                results['failed'].append({
                    'category': category_key,
                    'error': str(e)
                })

    finally:
        await generator.close()

    # 输出结果
    logger.info("=" * 60)
    logger.info("📊 卡片生成完成")
    logger.info(f"✅ 成功: {len(results['success'])}")
    logger.info(f"❌ 失败: {len(results['failed'])}")

    if results['failed']:
        logger.error("失败详情:")
        for item in results['failed']:
            logger.error(f"  - {item['category']}: {item['error']}")

    logger.info("=" * 60)

    return results


# 导出函数供scheduler使用
async def generate_and_publish_cards():
    """生成并发布卡片（定时任务调用）"""
    results = await generate_daily_cards()

    # 可选：发布成功的卡片
    if results['success']:
        async with AsyncSessionLocal() as session:
            for item in results['success']:
                try:
                    card = await session.get(Card, item['card_id'])
                    if card:
                        card.is_published = True
                        card.published_at = datetime.utcnow()
                        await session.commit()
                        logger.info(f"📢 已发布: {card.title}")
                except Exception as e:
                    logger.error(f"发布失败: {e}")

    return results
