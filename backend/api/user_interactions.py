# api/user_interactions.py
"""用户交互追踪API - User Interaction Tracking API (Simplified Version)

提供用户行为追踪、分析和转化漏斗监控功能。
注意: 当前版本为简化版，不包含身份验证。生产环境需要添加JWT认证。
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging

from sqlalchemy import select, and_
from config.database import AsyncSessionLocal, get_db
from models.user_interaction import UserInteraction, UserEngagement, ConversionEvent, InteractionEventType
from models.user import User
from services.user_interaction_tracker import (
    UserInteractionTracker,
    UserEngagementAnalyzer
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/user-interactions", tags=["user-interactions"])

# 全局实例
tracker = UserInteractionTracker()
analyzer = UserEngagementAnalyzer()


# ============================================================================
# Request/Response Models
# ============================================================================

class TrackEventRequest(BaseModel):
    """事件追踪请求"""
    event_type: str = Field(..., description="事件类型")
    event_name: Optional[str] = Field(None, description="自定义事件名称")
    category: str = Field("general", description="事件分类")
    target_type: Optional[str] = Field(None, description="目标类型")
    target_id: Optional[str] = Field(None, description="目标ID (字符串格式)")
    session_id: Optional[str] = Field(None, description="会话ID")
    funnel_stage: Optional[str] = Field(None, description="漏斗阶段")
    event_metadata: Dict[str, Any] = Field(default_factory=dict)
    properties: Dict[str, Any] = Field(default_factory=dict)
    attribution: Dict[str, Any] = Field(default_factory=dict)


class TrackEventResponse(BaseModel):
    """事件追踪响应"""
    success: bool
    event_id: str
    message: str


# ============================================================================
# Helper Functions
# ============================================================================

async def get_demo_user(db: AsyncSessionLocal) -> User:
    """获取演示用户（临时实现，生产环境需使用JWT认证）"""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="No users found")
    return user


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/track", response_model=TrackEventResponse)
async def track_user_event(
    request: TrackEventRequest,
    db: AsyncSessionLocal = Depends(get_db)
):
    """追踪用户交互事件（简化版，无需认证）"""
    try:
        # 获取演示用户
        current_user = await get_demo_user(db)

        # 转换事件类型
        try:
            event_type_enum = InteractionEventType(request.event_type)
        except ValueError:
            event_type_enum = InteractionEventType.VIEW_CARD

        # 处理target_id
        target_uuid = None
        if request.target_id:
            try:
                target_uuid = UUID(request.target_id)
            except ValueError:
                pass

        interaction = await tracker.track_event(
            db=db,
            user_id=current_user.id,
            event_type=event_type_enum,
            event_name=request.event_name,
            category=request.category,
            target_type=request.target_type,
            target_id=target_uuid,
            session_id=request.session_id,
            funnel_stage=request.funnel_stage,
            metadata=request.event_metadata,
            properties=request.properties,
            attribution=request.attribution
        )

        return TrackEventResponse(
            success=True,
            event_id=str(interaction.id),
            message="事件追踪成功"
        )

    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_user_events(
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSessionLocal = Depends(get_db)
):
    """获取用户事件列表"""
    try:
        current_user = await get_demo_user(db)

        event_type_enum = None
        if event_type:
            try:
                event_type_enum = InteractionEventType(event_type)
            except ValueError:
                pass

        events = await tracker.get_user_events(
            db=db,
            user_id=current_user.id,
            event_type=event_type_enum,
            limit=limit
        )

        return {
            "success": True,
            "count": len(events),
            "events": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type.value,
                    "event_name": e.event_name,
                    "category": e.category,
                    "target_type": e.target_type,
                    "target_id": str(e.target_id) if e.target_id else None,
                    "funnel_stage": e.funnel_stage,
                    "created_at": e.created_at.isoformat(),
                    "event_metadata": e.event_metadata
                }
                for e in events
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get user events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journey")
async def get_user_journey(
    days: int = Query(30, ge=1, le=90),
    db: AsyncSessionLocal = Depends(get_db)
):
    """获取用户旅程数据"""
    try:
        current_user = await get_demo_user(db)

        journey = await analyzer.get_user_journey(
            db=db,
            user_id=current_user.id,
            days=days
        )

        return journey

    except Exception as e:
        logger.error(f"Failed to get user journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engagement/daily")
async def get_daily_engagement(
    date: Optional[datetime] = Query(None),
    db: AsyncSessionLocal = Depends(get_db)
):
    """获取用户每日参与度"""
    try:
        current_user = await get_demo_user(db)
        target_date = date or datetime.now()

        engagement = await analyzer.calculate_daily_engagement(
            db=db,
            user_id=current_user.id,
            date=target_date
        )

        return {
            "success": True,
            "date": engagement.date.isoformat(),
            "is_active": engagement.is_active,
            "engagement_score": engagement.engagement_score,
            "activity": {
                "session_count": engagement.session_count,
                "page_views": engagement.page_views,
                "events_count": engagement.events_count
            },
            "usage": {
                "cards_viewed": engagement.cards_viewed,
                "favorites_count": engagement.favorites_count,
                "reports_generated": engagement.reports_generated
            },
            "assets": {
                "total_favorites": engagement.total_favorites,
                "total_reports": engagement.total_reports
            }
        }

    except Exception as e:
        logger.error(f"Failed to get daily engagement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_user_stats_summary(
    db: AsyncSessionLocal = Depends(get_db)
):
    """获取用户统计摘要"""
    try:
        current_user = await get_demo_user(db)

        # 获取最近30天的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # 统计事件
        result = await db.execute(
            select(UserInteraction)
            .where(
                and_(
                    UserInteraction.user_id == current_user.id,
                    UserInteraction.created_at >= start_date
                )
            )
        )
        events = result.scalars().all()

        # 统计各类行为
        stats = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": 30
            },
            "total_events": len(events),
            "cards_viewed": sum(1 for e in events if e.event_type == InteractionEventType.VIEW_CARD),
            "favorites": sum(1 for e in events if e.event_type in [
                InteractionEventType.FAVORITE_CARD,
                InteractionEventType.FAVORITE_OPPORTUNITY
            ]),
            "reports_generated": sum(1 for e in events if e.event_type == InteractionEventType.GENERATE_REPORT),
            "last_activity": events[0].created_at.isoformat() if events else None
        }

        # 获取当前漏斗阶段
        funnel_stage = await tracker.get_user_funnel_stage(db, current_user.id)
        if funnel_stage:
            stats["funnel_stage"] = funnel_stage

        return stats

    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "user-interactions"}
