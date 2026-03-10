# api/subscriptions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Optional
import uuid

from models.user import User
from models.subscription import Subscription
from schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    PlanInfoResponse,
)
from config.subscriptions import (
    SUBSCRIPTION_PLANS,
    get_plan_features,
    get_plan_pricing,
    get_plan_info,
)
from config.database import get_db
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建订阅"""
    # 检查用户是否已有活跃订阅
    existing = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.status == "active",
            )
        )
    )
    existing_subscription = existing.scalar_one_or_none()

    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ACTIVE_SUBSCRIPTION_EXISTS",
                "message": "您已有活跃订阅，请先取消现有订阅后再创建新订阅"
            }
        )

    # 获取定价
    amount = get_plan_pricing(subscription_data.plan_tier.value, subscription_data.billing_cycle)

    # 计算过期时间
    if subscription_data.billing_cycle.value == "monthly":
        expires_at = datetime.utcnow() + timedelta(days=30)
    else:  # yearly
        expires_at = datetime.utcnow() + timedelta(days=365)

    # 创建订阅
    new_subscription = Subscription(
        id=uuid.uuid4(),
        user_id=current_user.id,
        plan_tier=subscription_data.plan_tier.value,
        status="active",
        billing_cycle=subscription_data.billing_cycle.value,
        amount=amount,
        currency="CNY",
        started_at=datetime.utcnow(),
        expires_at=expires_at,
        auto_renew=True,
    )

    db.add(new_subscription)
    await db.commit()
    await db.refresh(new_subscription)

    # 获取功能列表
    features = get_plan_features(new_subscription.plan_tier)

    return SubscriptionResponse(
        id=str(new_subscription.id),
        user_id=str(new_subscription.user_id),
        plan_tier=new_subscription.plan_tier,
        status=new_subscription.status,
        billing_cycle=new_subscription.billing_cycle,
        amount=float(new_subscription.amount) if new_subscription.amount else None,
        currency=new_subscription.currency,
        started_at=new_subscription.started_at,
        expires_at=new_subscription.expires_at,
        canceled_at=new_subscription.canceled_at,
        auto_renew=new_subscription.auto_renew,
        features=features,
    )


@router.get("/me", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的订阅信息"""
    result = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.status == "active",
            )
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        # 返回免费版信息
        return SubscriptionResponse(
            id="",
            user_id=str(current_user.id),
            plan_tier="free",
            status="active",
            billing_cycle=None,
            amount=0,
            currency="CNY",
            started_at=current_user.created_at,
            expires_at=None,
            canceled_at=None,
            auto_renew=False,
            features=get_plan_features("free"),
        )

    features = get_plan_features(subscription.plan_tier)

    return SubscriptionResponse(
        id=str(subscription.id),
        user_id=str(subscription.user_id),
        plan_tier=subscription.plan_tier,
        status=subscription.status,
        billing_cycle=subscription.billing_cycle,
        amount=float(subscription.amount) if subscription.amount else None,
        currency=subscription.currency,
        started_at=subscription.started_at,
        expires_at=subscription.expires_at,
        canceled_at=subscription.canceled_at,
        auto_renew=subscription.auto_renew,
        features=features,
    )


@router.delete("", response_model=dict)
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消订阅"""
    result = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.status == "active",
            )
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NO_ACTIVE_SUBSCRIPTION", "message": "没有找到活跃的订阅"}
        )

    # 更新订阅状态
    subscription.status = "canceled"
    subscription.canceled_at = datetime.utcnow()
    subscription.auto_renew = False

    await db.commit()

    return {
        "success": True,
        "message": "订阅已取消",
        "expires_at": subscription.expires_at,
    }


@router.get("/plans", response_model=list[PlanInfoResponse])
async def list_plans():
    """获取所有订阅计划"""
    plans = []
    for tier, info in SUBSCRIPTION_PLANS.items():
        plans.append(
            PlanInfoResponse(
                tier=tier,
                name=info["name"],
                price_monthly=info.get("price_monthly"),
                price_yearly=info.get("price_yearly"),
                features=info["features"],
            )
        )
    return plans


@router.get("/plans/{tier}", response_model=PlanInfoResponse)
async def get_plan_details(tier: str):
    """获取指定订阅计划详情"""
    plan_info = get_plan_info(tier)
    if not plan_info or tier not in SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PLAN_NOT_FOUND", "message": f"未找到计划: {tier}"}
        )

    return PlanInfoResponse(
        tier=tier,
        name=plan_info["name"],
        price_monthly=plan_info.get("price_monthly"),
        price_yearly=plan_info.get("price_yearly"),
        features=plan_info["features"],
    )
