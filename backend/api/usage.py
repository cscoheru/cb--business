# api/usage.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta, date
from typing import Optional
import uuid

from models.user import User
from models.subscription import UserUsage
from schemas.subscription import UsageCheckResponse, FeatureCheckResponse
from config.subscriptions import get_plan_features, can_access_feature, get_required_plan_for_feature
from config.database import get_db
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


async def check_rate_limit(
    user: User,
    usage_type: str,
    db: AsyncSession,
) -> bool:
    """检查使用限额"""
    features = get_plan_features(user.plan_tier.value)
    daily_limit = features.get("api_calls_per_day", -1)

    # 无限额度
    if daily_limit == -1:
        return True

    # 检查今日使用量
    today = date.today()
    result = await db.execute(
        select(func.count(UserUsage.id))
        .where(
            and_(
                UserUsage.user_id == user.id,
                UserUsage.usage_type == usage_type,
                UserUsage.period_date == today,
            )
        )
    )
    usage_count = result.scalar() or 0

    if usage_count >= daily_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"每日{usage_type}调用次数已达上限({daily_limit}次)",
                "limit": daily_limit,
                "reset_at": (datetime.now() + timedelta(days=1)).isoformat(),
            }
        )

    # 记录使用
    new_usage = UserUsage(
        id=uuid.uuid4(),
        user_id=user.id,
        usage_type=usage_type,
        quantity=1,
        period_date=today,
    )
    db.add(new_usage)
    await db.commit()

    return True


async def record_usage(
    user: User,
    usage_type: str,
    db: AsyncSession,
    quantity: int = 1,
) -> UserUsage:
    """记录使用量（不检查限额）"""
    today = date.today()

    new_usage = UserUsage(
        id=uuid.uuid4(),
        user_id=user.id,
        usage_type=usage_type,
        quantity=quantity,
        period_date=today,
    )
    db.add(new_usage)
    await db.commit()
    await db.refresh(new_usage)

    return new_usage


@router.get("/check/{usage_type}", response_model=UsageCheckResponse)
async def check_usage(
    usage_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查指定使用类型的当前配额"""
    features = get_plan_features(current_user.plan_tier)
    daily_limit = features.get("api_calls_per_day", -1)

    # 获取今日使用量
    today = date.today()
    result = await db.execute(
        select(func.count(UserUsage.id))
        .where(
            and_(
                UserUsage.user_id == current_user.id,
                UserUsage.usage_type == usage_type,
                UserUsage.period_date == today,
            )
        )
    )
    current_count = result.scalar() or 0

    # 计算剩余配额
    if daily_limit == -1:
        remaining = -1  # 无限
    else:
        remaining = max(0, daily_limit - current_count)

    # 计算重置时间
    reset_at = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    return UsageCheckResponse(
        usage_type=usage_type,
        current_count=current_count,
        limit=daily_limit,
        remaining=remaining,
        reset_at=reset_at,
    )


@router.get("/feature/{feature_name}", response_model=FeatureCheckResponse)
async def check_feature_access(
    feature_name: str,
    current_user: User = Depends(get_current_user),
):
    """检查用户是否有权限访问某个功能"""
    has_access = can_access_feature(current_user.plan_tier, feature_name)
    required_plan = get_required_plan_for_feature(feature_name)

    message = None
    if not has_access:
        if required_plan == "pro":
            message = "此功能需要专业版订阅"
        elif required_plan == "enterprise":
            message = "此功能需要企业版订阅"

    return FeatureCheckResponse(
        has_access=has_access,
        feature=feature_name,
        current_plan=current_user.plan_tier,
        required_plan=required_plan if not has_access else None,
        message=message,
    )


@router.get("/stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户使用统计"""
    # 获取今日使用量
    today = date.today()
    result = await db.execute(
        select(UserUsage.usage_type, func.sum(UserUsage.quantity).label("total"))
        .where(
            and_(
                UserUsage.user_id == current_user.id,
                UserUsage.period_date == today,
            )
        )
        .group_by(UserUsage.usage_type)
    )
    today_stats = result.all()

    # 获取本周使用量
    week_ago = today - timedelta(days=7)
    result = await db.execute(
        select(UserUsage.usage_type, func.sum(UserUsage.quantity).label("total"))
        .where(
            and_(
                UserUsage.user_id == current_user.id,
                UserUsage.period_date >= week_ago,
            )
        )
        .group_by(UserUsage.usage_type)
    )
    week_stats = result.all()

    return {
        "today": {row.usage_type: row.total for row in today_stats},
        "week": {row.usage_type: row.total for row in week_stats},
        "plan_tier": current_user.plan_tier,
    }


@router.post("/record/{usage_type}")
async def record_usage_endpoint(
    usage_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    quantity: int = 1,
):
    """手动记录使用量"""
    await record_usage(current_user, usage_type, db, quantity)
    return {"success": True, "message": "使用量已记录"}
