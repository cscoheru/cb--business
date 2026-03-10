# schemas/subscription.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from config.subscriptions import PlanTier, BillingCycle


class SubscriptionCreate(BaseModel):
    """创建订阅请求"""
    plan_tier: PlanTier = Field(..., description="订阅计划层级")
    billing_cycle: BillingCycle = Field(default=BillingCycle.MONTHLY, description="计费周期")


class SubscriptionResponse(BaseModel):
    """订阅响应"""
    id: str
    user_id: str
    plan_tier: str
    status: str
    billing_cycle: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "CNY"
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    auto_renew: bool = True
    features: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class FeatureCheckResponse(BaseModel):
    """功能检查响应"""
    has_access: bool
    feature: str
    current_plan: str
    required_plan: Optional[str] = None
    message: Optional[str] = None


class UsageCheckResponse(BaseModel):
    """使用量检查响应"""
    usage_type: str
    current_count: int
    limit: int
    remaining: int
    reset_at: datetime


class PlanInfoResponse(BaseModel):
    """计划信息响应"""
    tier: str
    name: str
    price_monthly: Optional[int]
    price_yearly: Optional[int]
    features: Dict[str, Any]


class UpsellSuggestionResponse(BaseModel):
    """付费升级建议响应"""
    should_upgrade: bool
    message: Optional[str] = None
    recommended_plan: Optional[str] = None
    features: Optional[list[str]] = None
    price: Optional[str] = None
    action_url: Optional[str] = None
