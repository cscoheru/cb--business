# config/subscriptions.py
from enum import Enum
from typing import Dict, Any


class PlanTier(str, Enum):
    """订阅计划层级"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    """计费周期"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


# 订阅计划配置
SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "免费版",
        "price_monthly": 0,
        "price_yearly": 0,
        "features": {
            "api_calls_per_day": 5,
            "ai_analysis": False,
            "cost_calculator": False,  # 基础版可用
            "data_export": False,
            "supplier_database": False,
            "support": "community",
        },
    },
    "pro": {
        "name": "专业版",
        "price_monthly": 99,
        "price_yearly": 990,
        "features": {
            "api_calls_per_day": -1,  # 无限
            "ai_analysis": True,
            "cost_calculator": True,  # 精确版
            "data_export": True,
            "supplier_database": True,
            "support": "email",
        },
    },
    "enterprise": {
        "name": "企业版",
        "price_monthly": None,  # 定制
        "price_yearly": None,
        "features": {
            "api_calls_per_day": -1,
            "ai_analysis": True,
            "cost_calculator": True,
            "data_export": True,
            "supplier_database": True,
            "support": "dedicated",
            "api_access": True,
        },
    },
}


def get_plan_features(plan_tier: str) -> Dict[str, Any]:
    """获取订阅计划的功能配置"""
    plan = SUBSCRIPTION_PLANS.get(plan_tier, SUBSCRIPTION_PLANS["free"])
    return plan["features"]


def can_access_feature(user_tier: str, feature: str) -> bool:
    """检查用户是否有权限访问某个功能"""
    features = get_plan_features(user_tier)
    return features.get(feature, False)


def get_plan_pricing(plan_tier: str, billing_cycle: BillingCycle) -> int:
    """获取订阅计划价格"""
    plan = SUBSCRIPTION_PLANS.get(plan_tier, SUBSCRIPTION_PLANS["free"])
    if billing_cycle == BillingCycle.YEARLY:
        return plan.get("price_yearly", 0)
    return plan.get("price_monthly", 0)


def get_plan_info(plan_tier: str) -> Dict[str, Any]:
    """获取订阅计划完整信息"""
    return SUBSCRIPTION_PLANS.get(plan_tier, SUBSCRIPTION_PLANS["free"])


def get_required_plan_for_feature(feature: str) -> str | None:
    """获取访问某个功能所需的最低计划"""
    # 按优先级检查计划（从免费版开始）
    for tier in ["free", "pro", "enterprise"]:
        if can_access_feature(tier, feature):
            return tier
    return None
