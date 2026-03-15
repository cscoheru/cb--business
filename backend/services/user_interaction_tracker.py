# services/user_interaction_tracker.py
"""用户交互追踪服务 - 记录和分析用户行为"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID
import logging

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_interaction import (
    UserInteraction, UserSession, UserEngagement, ConversionEvent,
    InteractionEventType
)
from models.user import User

logger = logging.getLogger(__name__)


class UserInteractionTracker:
    """用户交互追踪服务

    记录用户行为，分析用户旅程，支持转化漏斗优化
    """

    async def track_event(
        self,
        db: AsyncSession,
        user_id: UUID,
        event_type: InteractionEventType,
        event_name: Optional[str] = None,
        category: str = "general",
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        funnel_stage: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        properties: Optional[Dict[str, Any]] = None,
        attribution: Optional[Dict[str, Any]] = None
    ) -> UserInteraction:
        """
        记录用户交互事件

        Args:
            db: 数据库session
            user_id: 用户ID
            event_type: 事件类型枚举
            event_name: 自定义事件名称
            category: 事件分类 (browsing, engagement, conversion, etc.)
            target_type: 目标对象类型
            target_id: 目标对象ID
            session_id: 会话ID
            funnel_stage: 转化漏斗阶段
            metadata: 事件元数据
            properties: 事件属性
            attribution: 归因数据

        Returns:
            创建的UserInteraction记录
        """
        try:
            interaction = UserInteraction(
                user_id=user_id,
                event_type=event_type,
                event_name=event_name or event_type.value,
                category=category,
                target_type=target_type,
                target_id=target_id,
                session_id=session_id,
                funnel_stage=funnel_stage,
                event_metadata=metadata or {},
                properties=properties or {},
                attribution=attribution or {},
                created_at=datetime.now(timezone.utc)
            )

            db.add(interaction)
            await db.commit()
            await db.refresh(interaction)

            logger.info(f"📊 Tracked event: {event_type.value} for user {user_id}")

            return interaction

        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            await db.rollback()
            raise

    async def track_page_view(
        self,
        db: AsyncSession,
        user_id: UUID,
        page: str,
        session_id: str,
        referrer: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserInteraction:
        """追踪页面浏览"""
        return await self.track_event(
            db=db,
            user_id=user_id,
            event_type=InteractionEventType.VIEW_CARD,  # 默认类型
            event_name=f"view_{page}",
            category="browsing",
            session_id=session_id,
            funnel_stage=self._get_funnel_stage_from_page(page),
            event_metadata={**(metadata or {}), "referrer": referrer, "page": page}
        )

    async def track_card_view(
        self,
        db: AsyncSession,
        user_id: UUID,
        card_id: UUID,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserInteraction:
        """追踪卡片查看"""
        return await self.track_event(
            db=db,
            user_id=user_id,
            event_type=InteractionEventType.VIEW_CARD,
            category="browsing",
            target_type="card",
            target_id=card_id,
            session_id=session_id,
            funnel_stage="awareness",
            event_metadata=metadata
        )

    async def track_favorite(
        self,
        db: AsyncSession,
        user_id: UUID,
        target_type: str,
        target_id: UUID,
        session_id: str,
        is_favorite: bool = True
    ) -> UserInteraction:
        """追踪收藏/取消收藏"""
        event_type = InteractionEventType.FAVORITE_CARD if is_favorite else InteractionEventType.UNFAVORITE_CARD

        return await self.track_event(
            db=db,
            user_id=user_id,
            event_type=event_type,
            category="engagement",
            target_type=target_type,
            target_id=target_id,
            session_id=session_id,
            funnel_stage="consideration"
        )

    async def track_report_generation(
        self,
        db: AsyncSession,
        user_id: UUID,
        report_type: str,
        report_id: UUID,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserInteraction:
        """追踪报告生成"""
        return await self.track_event(
            db=db,
            user_id=user_id,
            event_type=InteractionEventType.GENERATE_REPORT,
            category="engagement",
            target_type="report",
            target_id=report_id,
            session_id=session_id,
            funnel_stage="consideration",
            properties={"report_type": report_type},
            event_metadata=metadata
        )

    async def track_conversion(
        self,
        db: AsyncSession,
        user_id: UUID,
        conversion_type: str,
        conversion_stage: str,
        conversion_value: Optional[float] = None,
        session_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        attribution: Optional[Dict[str, Any]] = None
    ) -> ConversionEvent:
        """
        记录转化事件

        Args:
            db: 数据库session
            user_id: 用户ID
            conversion_type: 转化类型 (trial_start, subscription, upgrade, renewal)
            conversion_stage: 转化阶段
            conversion_value: 转化价值
            session_id: 会话ID
            event_data: 事件数据
            attribution: 归因数据

        Returns:
            创建的ConversionEvent记录
        """
        try:
            conversion = ConversionEvent(
                user_id=user_id,
                conversion_type=conversion_type,
                conversion_stage=conversion_stage,
                conversion_value=conversion_value,
                event_data=event_data or {},
                attribution=attribution or {},
                occurred_at=datetime.now(timezone.utc)
            )

            db.add(conversion)
            await db.commit()
            await db.refresh(conversion)

            logger.info(f"💰 Conversion tracked: {conversion_type} for user {user_id}")

            return conversion

        except Exception as e:
            logger.error(f"Failed to track conversion: {e}")
            await db.rollback()
            raise

    async def get_user_events(
        self,
        db: AsyncSession,
        user_id: UUID,
        event_type: Optional[InteractionEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[UserInteraction]:
        """获取用户事件列表"""
        query = select(UserInteraction).where(UserInteraction.user_id == user_id)

        if event_type:
            query = query.where(UserInteraction.event_type == event_type)

        if start_date:
            query = query.where(UserInteraction.created_at >= start_date)

        if end_date:
            query = query.where(UserInteraction.created_at <= end_date)

        query = query.order_by(desc(UserInteraction.created_at)).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def get_user_funnel_stage(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[str]:
        """获取用户当前所处的转化漏斗阶段"""
        # 获取最近的转化事件
        result = await db.execute(
            select(ConversionEvent)
            .where(ConversionEvent.user_id == user_id)
            .order_by(desc(ConversionEvent.occurred_at))
            .limit(1)
        )
        latest_conversion = result.scalar_one_or_none()

        if latest_conversion:
            return latest_conversion.conversion_stage

        # 如果没有转化事件，根据最近的交互事件判断
        result = await db.execute(
            select(UserInteraction)
            .where(UserInteraction.user_id == user_id)
            .order_by(desc(UserInteraction.created_at))
            .limit(1)
        )
        latest_interaction = result.scalar_one_or_none()

        if latest_interaction:
            return latest_interaction.funnel_stage

        return None

    def _get_funnel_stage_from_page(self, page: str) -> str:
        """根据页面路径推断漏斗阶段"""
        page_mapping = {
            "cards": "awareness",
            "opportunities": "awareness",
            "favorites": "consideration",
            "reports": "consideration",
            "pricing": "consideration",
            "checkout": "conversion",
            "dashboard": "retention"
        }
        return page_mapping.get(page, "awareness")


class UserEngagementAnalyzer:
    """用户参与度分析服务

    计算用户参与度分数，分析用户行为模式
    """

    async def calculate_daily_engagement(
        self,
        db: AsyncSession,
        user_id: UUID,
        date: datetime
    ) -> UserEngagement:
        """
        计算用户每日参与度

        Args:
            db: 数据库session
            user_id: 用户ID
            date: 统计日期

        Returns:
            用户参与度记录
        """
        # 获取当天的事件
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # 查询当天的事件
        result = await db.execute(
            select(UserInteraction)
            .where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.created_at >= start_of_day,
                    UserInteraction.created_at < end_of_day
                )
            )
        )
        events = result.scalars().all()

        # 统计各类事件
        cards_viewed = sum(1 for e in events if e.event_type == InteractionEventType.VIEW_CARD)
        favorites_count = sum(1 for e in events if e.event_type in [
            InteractionEventType.FAVORITE_CARD,
            InteractionEventType.FAVORITE_OPPORTUNITY
        ])
        reports_generated = sum(1 for e in events if e.event_type == InteractionEventType.GENERATE_REPORT)
        searches_performed = sum(1 for e in events if e.event_type == InteractionEventType.SEARCH_KEYWORDS)

        # 计算参与度分数 (0-100)
        engagement_score = await self._calculate_engagement_score(
            db, user_id, events, cards_viewed, favorites_count, reports_generated
        )

        # 获取历史数据
        total_favorites = await self._get_total_favorites(db, user_id)
        total_reports = await self._get_total_reports(db, user_id)
        total_days_active = await self._get_total_days_active(db, user_id)

        # 创建或更新参与度记录
        engagement = UserEngagement(
            user_id=user_id,
            date=start_of_day,
            is_active=len(events) > 0,
            session_count=len(set(e.session_id for e in events if e.session_id)),
            page_views=sum(1 for e in events if e.category == "browsing"),
            events_count=len(events),
            cards_viewed=cards_viewed,
            opportunities_viewed=sum(1 for e in events if e.event_type == InteractionEventType.VIEW_OPPORTUNITY),
            favorites_count=favorites_count,
            reports_generated=reports_generated,
            searches_performed=searches_performed,
            engagement_score=engagement_score,
            total_favorites=total_favorites,
            total_reports=total_reports,
            total_days_active=total_days_active + (1 if len(events) > 0 else 0),
            meta_data={"calculated_at": datetime.now(timezone.utc).isoformat()}
        )

        db.merge(engagement)
        await db.commit()

        return engagement

    async def _calculate_engagement_score(
        self,
        db: AsyncSession,
        user_id: UUID,
        events: List[UserInteraction],
        cards_viewed: int,
        favorites_count: int,
        reports_generated: int
    ) -> float:
        """计算参与度分数 (0-100)"""
        # 活跃度分数 (30%权重) - 基于事件数量
        activity_score = min(len(events) / 20 * 30, 30)

        # 深度分数 (40%权重) - 基于收藏和报告
        depth_score = min((favorites_count * 5 + reports_generated * 10) / 40 * 40, 40)

        # 增长分数 (30%权重) - 基于多样化行为
        unique_categories = len(set(e.category for e in events))
        growth_score = min(unique_categories / 4 * 30, 30)

        return min(activity_score + depth_score + growth_score, 100.0)

    async def _get_total_favorites(self, db: AsyncSession, user_id: UUID) -> int:
        """获取总收藏数"""
        result = await db.execute(
            select(func.count(UserInteraction.id))
            .where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.event_type.in_([
                        InteractionEventType.FAVORITE_CARD,
                        InteractionEventType.FAVORITE_OPPORTUNITY
                    ])
                )
            )
        )
        return result.scalar() or 0

    async def _get_total_reports(self, db: AsyncSession, user_id: UUID) -> int:
        """获取总报告数"""
        result = await db.execute(
            select(func.count(UserInteraction.id))
            .where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.event_type == InteractionEventType.GENERATE_REPORT
                )
            )
        )
        return result.scalar() or 0

    async def _get_total_days_active(self, db: AsyncSession, user_id: UUID) -> int:
        """获取总活跃天数"""
        result = await db.execute(
            select(func.count(func.distinct(func.date(UserInteraction.created_at))))
            .where(UserInteraction.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_user_journey(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户旅程数据

        Args:
            db: 数据库session
            user_id: 用户ID
            days: 查询天数

        Returns:
            用户旅程数据
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # 获取事件
        result = await db.execute(
            select(UserInteraction)
            .where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.created_at >= start_date
                )
            )
            .order_by(UserInteraction.created_at)
        )
        events = result.scalars().all()

        # 获取参与度数据
        engagement_result = await db.execute(
            select(UserEngagement)
            .where(
                and_(
                    UserEngagement.user_id == user_id,
                    UserEngagement.date >= start_date
                )
            )
            .order_by(UserEngagement.date)
        )
        engagement_data = engagement_result.scalars().all()

        # 获取转化事件
        conversion_result = await db.execute(
            select(ConversionEvent)
            .where(
                and_(
                    ConversionEvent.user_id == user_id,
                    ConversionEvent.occurred_at >= start_date
                )
            )
            .order_by(ConversionEvent.occurred_at)
        )
        conversions = conversion_result.scalars().all()

        return {
            "user_id": str(user_id),
            "period_days": days,
            "total_events": len(events),
            "events": [
                {
                    "type": e.event_type.value,
                    "category": e.category,
                    "timestamp": e.created_at.isoformat(),
                    "target_type": e.target_type,
                    "funnel_stage": e.funnel_stage
                }
                for e in events
            ],
            "engagement": [
                {
                    "date": e.date.isoformat(),
                    "score": e.engagement_score,
                    "is_active": e.is_active,
                    "favorites": e.favorites_count,
                    "reports": e.reports_generated
                }
                for e in engagement_data
            ],
            "conversions": [
                {
                    "type": c.conversion_type,
                    "stage": c.conversion_stage,
                    "value": c.conversion_value,
                    "timestamp": c.occurred_at.isoformat()
                }
                for c in conversions
            ]
        }

    async def get_funnel_analysis(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取转化漏斗分析

        Args:
            db: 数据库session
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            漏斗分析数据
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # 统计各阶段的用户数
        funnel_stages = ["awareness", "consideration", "conversion", "retention"]

        funnel_data = {}
        for stage in funnel_stages:
            result = await db.execute(
                select(func.count(func.distinct(UserInteraction.user_id)))
                .where(
                    and_(
                        UserInteraction.funnel_stage == stage,
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date
                    )
                )
            )
            count = result.scalar() or 0
            funnel_data[stage] = count

        # 统计转化事件
        conversion_result = await db.execute(
            select(ConversionEvent.conversion_type, func.count(ConversionEvent.id))
            .where(
                and_(
                    ConversionEvent.occurred_at >= start_date,
                    ConversionEvent.occurred_at <= end_date
                )
            )
            .group_by(ConversionEvent.conversion_type)
        )
        conversions = {row[0]: row[1] for row in conversion_result.all()}

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "funnel": funnel_data,
            "conversions": conversions,
            "conversion_rates": {
                stage: self._calculate_conversion_rate(funnel_data, stage)
                for stage in funnel_stages[1:]
            }
        }

    def _calculate_conversion_rate(self, funnel_data: Dict[str, int], stage: str) -> float:
        """计算转化率"""
        stage_order = ["awareness", "consideration", "conversion", "retention"]
        stage_index = stage_order.index(stage)

        if stage_index == 0:
            return 0.0

        previous_stage = stage_order[stage_index - 1]
        previous_count = funnel_data.get(previous_stage, 0)

        if previous_count == 0:
            return 0.0

        current_count = funnel_data.get(stage, 0)
        return round(current_count / previous_count * 100, 2)
