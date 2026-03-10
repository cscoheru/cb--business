# api/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta, date
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

from models.user import User, PlanTier, PlanStatus
from models.subscription import Subscription, UserUsage
from config.database import get_db
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ============ 权限验证 ============
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """验证用户是否为管理员"""
    # TODO: 添加真正的管理员验证逻辑
    # 目前临时使用 plan_tier == "enterprise" 作为管理员标识
    if current_user.plan_tier != PlanTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_ADMIN", "message": "需要管理员权限"}
        )
    return current_user


# ============ 数据模型 ============
class UserListResponse(BaseModel):
    users: List[dict]
    total: int


class UserFilter(BaseModel):
    status: Optional[str] = None
    plan_tier: Optional[str] = None
    search: Optional[str] = None


class SubscriptionListResponse(BaseModel):
    subscriptions: List[dict]
    stats: dict


class FinanceDataResponse(BaseModel):
    monthlyRevenue: List[dict]
    subscriptionTrend: List[dict]
    paymentMethods: List[dict]
    totalRevenue: float
    revenueGrowth: float
    activeSubscriptions: int
    subscriptionGrowth: float


class AnalyticsDataResponse(BaseModel):
    totalUsers: int
    userGrowth: float
    activeUsers: int
    averageApiCalls: float
    apiCallsGrowth: float
    topMarkets: List[dict]
    topCategories: List[dict]


# ============ 用户管理 ============
@router.post("/users", response_model=UserListResponse)
async def get_users(
    filters: UserFilter,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表（管理员）"""
    query = select(User)

    # 应用筛选
    if filters.status:
        query = query.where(User.plan_status == filters.status)
    if filters.plan_tier:
        query = query.where(User.plan_tier == filters.plan_tier)
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.where(
            (User.email.ilike(search_term)) | (User.name.ilike(search_term))
        )

    # 执行查询
    result = await db.execute(query.order_by(desc(User.created_at)))
    users = result.scalars().all()

    # 转换为响应格式
    users_data = []
    for user in users:
        # 获取今日API使用量
        today = date.today()
        usage_result = await db.execute(
            select(func.sum(UserUsage.quantity))
            .where(
                and_(
                    UserUsage.user_id == str(user.id),
                    UserUsage.period_date == today,
                )
            )
        )
        api_used = usage_result.scalar() or 0

        # 获取套餐限额
        from config.subscriptions import get_plan_features
        features = get_plan_features(user.plan_tier.value)
        api_limit = features.get("api_calls_per_day", -1)

        users_data.append({
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "subscription": user.plan_tier.value,
            "status": user.plan_status.value,
            "createdAt": user.created_at.strftime("%Y-%m-%d"),
            "lastActiveAt": user.last_active_at.strftime("%Y-%m-%d") if user.last_active_at else user.created_at.strftime("%Y-%m-%d"),
            "apiUsage": {
                "limit": api_limit,
                "used": api_used,
            }
        })

    # 获取总数
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar() or 0

    return UserListResponse(users=users_data, total=total)


@router.get("/users/stats")
async def get_users_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户统计（管理员）"""
    # 总用户数
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0

    # 活跃用户数（30天内登录）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_result = await db.execute(
        select(func.count(User.id)).where(User.last_active_at >= thirty_days_ago)
    )
    active_users = active_result.scalar() or 0

    # 付费用户数
    paid_result = await db.execute(
        select(func.count(User.id)).where(User.plan_tier != PlanTier.FREE)
    )
    paid_users = paid_result.scalar() or 0

    # 月增长率（简化计算，对比上月）
    last_month = datetime.utcnow() - timedelta(days=30)
    growth_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= last_month)
    )
    new_users = growth_result.scalar() or 0
    growth_rate = (new_users / total_users * 100) if total_users > 0 else 0

    return {
        "total": total_users,
        "active": active_users,
        "paid": paid_users,
        "growthRate": round(growth_rate, 1),
    }


# ============ 订阅管理 ============
@router.post("/subscriptions", response_model=SubscriptionListResponse)
async def get_subscriptions(
    filters: UserFilter,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取订阅列表（管理员）"""
    query = select(Subscription)

    # 应用筛选
    if filters.status:
        query = query.where(Subscription.status == filters.status)
    if filters.plan_tier:
        query = query.where(Subscription.plan_tier == filters.plan_tier)

    # 执行查询
    result = await db.execute(query.order_by(desc(Subscription.started_at)))
    subscriptions = result.scalars().all()

    # 转换为响应格式
    subscriptions_data = []
    for sub in subscriptions:
        # 获取用户邮箱
        user_result = await db.execute(select(User.email).where(User.id == sub.user_id))
        user_email = user_result.scalar() or ""

        subscriptions_data.append({
            "id": str(sub.id),
            "userId": str(sub.user_id),
            "userEmail": user_email,
            "plan": sub.plan_tier,
            "status": sub.status,
            "amount": float(sub.amount) if sub.amount else 0,
            "currency": sub.currency,
            "period": sub.billing_cycle,
            "startDate": sub.started_at.strftime("%Y-%m-%d"),
            "nextBillingDate": sub.expires_at.strftime("%Y-%m-%d") if sub.expires_at else "",
        })

    # 获取统计数据
    total_result = await db.execute(
        select(func.count(Subscription.id)).where(Subscription.status == "active")
    )
    active_count = total_result.scalar() or 0

    pro_result = await db.execute(
        select(func.count(Subscription.id)).where(
            and_(
                Subscription.status == "active",
                Subscription.plan_tier == "pro"
            )
        )
    )
    pro_count = pro_result.scalar() or 0

    enterprise_result = await db.execute(
        select(func.count(Subscription.id)).where(
            and_(
                Subscription.status == "active",
                Subscription.plan_tier == "enterprise"
            )
        )
    )
    enterprise_count = enterprise_result.scalar() or 0

    # 计算本月收入
    this_month = datetime.utcnow().replace(day=1)
    revenue_result = await db.execute(
        select(func.sum(Subscription.amount)).where(
            and_(
                Subscription.status == "active",
                Subscription.started_at >= this_month
            )
        )
    )
    revenue = revenue_result.scalar() or 0

    stats = {
        "total": active_count,
        "active": active_count,
        "pro": pro_count,
        "enterprise": enterprise_count,
        "revenue": float(revenue),
    }

    return SubscriptionListResponse(subscriptions=subscriptions_data, stats=stats)


# ============ 财务数据 ============
@router.get("/finance", response_model=FinanceDataResponse)
async def get_finance_data(
    period: str = Query("30d", description="时间范围: 7d, 30d, 90d, 365d"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取财务数据（管理员）"""
    # 计算时间范围
    days_map = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}
    days = days_map.get(period, 30)

    # 月度收入数据（模拟6个月数据）
    monthly_revenue = []
    for i in range(6):
        month = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_name = month.strftime("%-m月")
        # 简化计算，实际应该按月统计收入
        revenue = 45000 + (i * 8000) + (i * 5000 if i < 3 else 0)
        monthly_revenue.append({
            "month": month_name,
            "revenue": revenue
        })
    monthly_revenue.reverse()

    # 订阅趋势
    subscription_trend = []
    for i in range(6):
        month = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_name = month.strftime("%-m月")
        # 获取该月订阅数
        result = await db.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.status == "active",
                    Subscription.started_at >= month,
                    Subscription.started_at < month + timedelta(days=32)
                )
            )
        )
        count = result.scalar() or 0
        subscription_trend.append({
            "month": month_name,
            "count": 45 + count * 1.5  # 模拟数据
        })
    subscription_trend.reverse()

    # 支付方式分布（模拟数据）
    payment_methods = [
        {"method": "支付宝", "count": 68, "percentage": 48},
        {"method": "微信支付", "count": 56, "percentage": 40},
        {"method": "信用卡", "count": 18, "percentage": 12},
    ]

    # 计算总收入
    total_revenue_result = await db.execute(
        select(func.sum(Subscription.amount)).where(Subscription.status == "active")
    )
    total_revenue = float(total_revenue_result.scalar() or 0)

    # 活跃订阅数
    active_subs_result = await db.execute(
        select(func.count(Subscription.id)).where(Subscription.status == "active")
    )
    active_subscriptions = active_subs_result.scalar() or 0

    return FinanceDataResponse(
        monthlyRevenue=monthly_revenue,
        subscriptionTrend=subscription_trend,
        paymentMethods=payment_methods,
        totalRevenue=total_revenue,
        revenueGrowth=12.5,
        activeSubscriptions=active_subscriptions,
        subscriptionGrowth=8.3,
    )


# ============ 分析数据 ============
@router.get("/analytics", response_model=AnalyticsDataResponse)
async def get_analytics_data(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分析数据（管理员）"""
    # 总用户数
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0

    # 活跃用户（30天内登录）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_result = await db.execute(
        select(func.count(User.id)).where(User.last_active_at >= thirty_days_ago)
    )
    active_users = active_result.scalar() or 0

    # 月增长率
    last_month = datetime.utcnow() - timedelta(days=30)
    growth_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= last_month)
    )
    new_users = growth_result.scalar() or 0
    user_growth = round((new_users / total_users * 100) if total_users > 0 else 0, 1)

    # 平均API调用
    avg_api_calls = 234  # 模拟数据

    # API调用增长率
    api_calls_growth = 25.3

    # 热门市场（模拟数据）
    top_markets = [
        {"market": "东南亚", "users": 892, "growth": 22.5},
        {"market": "欧盟", "users": 567, "growth": 15.8},
        {"market": "拉美", "users": 445, "growth": 32.1},
        {"market": "中东", "users": 234, "growth": 18.2},
    ]

    # 热门品类（模拟数据）
    top_categories = [
        {"category": "电子产品", "views": 12450, "growth": 28.5},
        {"category": "美妆个护", "views": 8934, "growth": 19.2},
        {"category": "家居用品", "views": 6789, "growth": 15.6},
        {"category": "户外用品", "views": 5432, "growth": 22.8},
    ]

    return AnalyticsDataResponse(
        totalUsers=total_users,
        userGrowth=user_growth,
        activeUsers=active_users,
        averageApiCalls=avg_api_calls,
        apiCallsGrowth=api_calls_growth,
        topMarkets=top_markets,
        topCategories=top_categories,
    )
