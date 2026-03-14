# services/migration_service.py
"""Cards系统集成服务

实现新旧系统的平滑集成和迁移
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import select
from config.database import AsyncSessionLocal
from models.card import Card as OldCard
from models.business_opportunity import BusinessOpportunity, OpportunityType, OpportunityStatus

logger = logging.getLogger(__name__)


class CardsIntegrationService:
    """Cards系统集成服务"""

    async def migrate_card_to_opportunity(
        self,
        card: OldCard,
        db: AsyncSessionLocal
    ) -> Optional[BusinessOpportunity]:
        """
        将旧Card迁移为BusinessOpportunity

        Args:
            card: 旧的Card对象
            db: 数据库session

        Returns:
            新创建的BusinessOpportunity，如果已存在则返回None
        """
        try:
            # 检查是否已迁移
            existing = await db.execute(
                select(BusinessOpportunity).where(
                    BusinessOpportunity.title == card.title
                )
            )
            if existing.scalar_one_or_none():
                logger.info(f"Card {card.id} 已迁移，跳过")
                return None

            # 确定商机类型
            opp_type = self._determine_opportunity_type(card)

            # 创建BusinessOpportunity
            opportunity = BusinessOpportunity(
                title=f"{card.title} (从Card迁移)",
                description=card.content.get('summary', {}).get('title', ''),
                opportunity_type=opp_type,
                status=OpportunityStatus.POTENTIAL,  # 旧Card需要重新验证
                elements=self._extract_elements(card),
                ai_insights=self._build_ai_insights(card),
                confidence_score=self._calculate_initial_confidence(card)
            )

            db.add(opportunity)
            await db.commit()
            await db.refresh(opportunity)

            logger.info(f"✅ 迁移Card {card.id} → Opportunity {opportunity.id}")

            return opportunity

        except Exception as e:
            logger.error(f"迁移Card {card.id} 失败: {e}")
            await db.rollback()
            return None

    def _determine_opportunity_type(self, card: OldCard) -> OpportunityType:
        """根据Card确定商机类型"""
        category = card.category

        # 根据category映射到商机类型
        if 'electronics' in category or 'wireless' in category or 'phone' in category:
            return OpportunityType.PRODUCT
        elif 'policy' in category or 'tax' in category:
            return OpportunityType.POLICY
        elif 'platform' in category or 'tiktok' in category or 'shopee' in category:
            return OpportunityType.PLATFORM
        elif 'brand' in category:
            return OpportunityType.BRAND
        else:
            return OpportunityType.PRODUCT  # 默认

    def _extract_elements(self, card: OldCard) -> Dict[str, Any]:
        """从Card提取商机要素"""
        elements = {}

        # 从amazon_data提取产品信息
        if card.amazon_data:
            products = card.amazon_data.get('products', [])
            if products:
                elements['product'] = {
                    'focus': ', '.join([p.get('title', 'N/A') for p in products[:3]]),
                    'opportunity_reason': '来自Card的产品数据'
                }

        # 从category推断地区信息
        category = card.category.lower()
        region_keywords = {
            'us': '美国', 'eu': '欧洲', 'asia': '亚洲',
            'sea': '东南亚', 'my': '马来西亚', 'th': '泰国'
        }
        for kw, name in region_keywords.items():
            if kw in category:
                elements['region'] = {
                    'focus': name,
                    'opportunity_reason': '从Card类别推断'
                }
                break

        return elements

    def _build_ai_insights(self, card: OldCard) -> Dict[str, Any]:
        """从Card构建AI洞察"""
        analysis = card.analysis or {}
        content = card.content or {}

        return {
            'why_opportunity': content.get('summary', {}).get('opportunity_score', '从旧Card迁移'),
            'key_assumptions': ['从Card迁移的数据，需要重新验证'],
            'verification_needs': ['需要AI重新分析', '需要更新产品数据'],
            'missing_information': ['使用Card的历史数据'],
            'data_requirements': [],
            'migration_metadata': {
                'original_card_id': str(card.id),
                'migrated_at': datetime.utcnow().isoformat(),
                'original_confidence': content.get('summary', {}).get('opportunity_score', 0)
            }
        }

    def _calculate_initial_confidence(self, card: OldCard) -> float:
        """计算初始置信度"""
        content = card.content or {}
        summary = content.get('summary', {})

        # 使用Card的opportunity_score作为参考
        card_score = summary.get('opportunity_score', 50)

        # 转换为0-1范围
        return min(card_score / 100, 0.7)  # 旧数据打折

    async def batch_migrate_cards(
        self,
        limit: int = 100,
        db: AsyncSessionLocal = None
    ) -> List[BusinessOpportunity]:
        """
        批量迁移Cards

        Args:
            limit: 迁移数量限制
            db: 数据库session

        Returns:
            迁移的BusinessOpportunity列表
        """
        if db is None:
            db = AsyncSessionLocal()

        try:
            # 查找已发布的Cards
            result = await db.execute(
                select(OldCard)
                .where(OldCard.is_published == True)
                .order_by(OldCard.created_at.desc())
                .limit(limit)
            )
            cards = result.scalars().all()

            logger.info(f"📦 找到 {len(cards)} 个Card待迁移")

            migrated = []
            for card in cards:
                opportunity = await self.migrate_card_to_opportunity(card, db)
                if opportunity:
                    migrated.append(opportunity)

            logger.info(f"✅ 批量迁移完成: {len(migrated)}/{len(cards)}")

            return migrated

        except Exception as e:
            logger.error(f"批量迁移失败: {e}")
            return []


# 双轨运行支持
class DualModeService:
    """双轨运行服务 - 同时支持新旧系统"""

    async def get_cards_and_opportunities(
        self,
        limit: int = 20,
        db: AsyncSessionLocal = None
    ) -> Dict[str, Any]:
        """
        同时获取旧Cards和新BusinessOpportunities

        Returns:
            合并的结果
        """
        if db is None:
            db = AsyncSessionLocal()

        try:
            # 获取旧Cards
            cards_result = await db.execute(
                select(OldCard)
                .where(OldCard.is_published == True)
                .order_by(OldCard.created_at.desc())
                .limit(limit)
            )
            cards = cards_result.scalars().all()

            # 获取新Opportunities
            opps_result = await db.execute(
                select(BusinessOpportunity)
                .where(BusinessOpportunity.status != OpportunityStatus.ARCHIVED)
                .order_by(BusinessOpportunity.created_at.desc())
                .limit(limit)
            )
            opportunities = opps_result.scalars().all()

            # 合并结果
            return {
                'legacy_cards': [card.to_dict() for card in cards],
                'opportunities': [opp.to_dict() for opp in opportunities],
                'total': len(cards) + len(opportunities),
                'mode': 'dual_track'
            }

        except Exception as e:
            logger.error(f"双轨查询失败: {e}")
            return {
                'legacy_cards': [],
                'opportunities': [],
                'total': 0,
                'mode': 'dual_track',
                'error': str(e)
            }

    async def sync_card_updates_to_opportunity(
        self,
        card_id: str,
        db: AsyncSessionLocal
    ):
        """
        当Card更新时，同步到关联的Opportunity

        Args:
            card_id: Card ID
            db: 数据库session
        """
        try:
            # 查找Card
            card_result = await db.execute(
                select(OldCard).where(OldCard.id == card_id)
            )
            card = card_result.scalar_one_or_none()

            if not card:
                logger.warning(f"Card {card_id} 不存在")
                return

            # 查找关联的Opportunity
            opp_result = await db.execute(
                select(BusinessOpportunity).where(
                    BusinessOpportunity.title == card.title
                )
            )
            opportunity = opp_result.scalar_one_or_none()

            if not opportunity:
                # 没有关联的Opportunity，创建一个
                integration = CardsIntegrationService()
                await integration.migrate_card_to_opportunity(card, db)
                return

            # 更新Opportunity
            opportunity.elements = self._extract_elements(card)
            opportunity.updated_at = datetime.utcnow()

            await db.commit()

            logger.info(f"🔄 同步Card {card_id} → Opportunity {opportunity.id}")

        except Exception as e:
            logger.error(f"同步Card更新失败: {e}")
            await db.rollback()
