# config/subscriptions.py
from enum import Enum
from typing import Dict, Any, Optional


class PlanTier(str, Enum):
    """订阅计划层级"""
    FREE = "free"
    TRIAL = "trial"
    PRO = "pro"


class BillingCycle(str, Enum):
    """计费周期"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class PlanStatus(str, Enum):
    """订阅状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL_ENDED = "trial_ended"


# 订阅计划配置
SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "免费版",
        "price_monthly": 0,
        "price_yearly": 0,
        "duration_days": None,  # 永久
        "features": {
            "api_calls_per_day": 10,
            "cards_per_day": 3,
            "ai_analysis": False,
            "cost_calculator": True,
            "data_export": False,
            "supplier_database": False,
            "market_insights": False,
            "support": "community",
        },
        "description": "基础功能，体验平台核心能力",
        "limits": {
            "daily_card_views": 10,
            "historical_data_days": 7,
        }
    },
    "trial": {
        "name": "试用版",
        "price_monthly": 0,
        "price_yearly": 0,
        "duration_days": 14,  # 14天试用期
        "features": {
            "api_calls_per_day": 50,
            "cards_per_day": 12,
            "ai_analysis": True,
            "cost_calculator": True,
            "data_export": True,
            "supplier_database": True,
            "market_insights": True,
            "support": "email",
        },
        "description": "14天完整体验，了解全部功能",
        "limits": {
            "daily_card_views": 50,
            "historical_data_days": 30,
        }
    },
    "pro": {
        "name": "专业版",
        "price_monthly": 99,
        "price_yearly": 990,
        "duration_days": None,  # 订阅制，按周期续费
        "features": {
            "api_calls_per_day": -1,  # 无限制
            "cards_per_day": -1,
            "ai_analysis": True,
            "cost_calculator": True,
            "data_export": True,
            "supplier_database": True,
            "market_insights": True,
            "api_access": True,
            "support": "priority",
        },
        "description": "完整功能，助力跨境业务增长",
        "limits": {
            "daily_card_views": -1,  # 无限制
            "historical_data_days": -1,  # 全部历史
        }
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


def get_plan_pricing(plan_tier: str, billing_cycle: BillingCycle) -> Optional[int]:
    """
    获取订阅计划价格

    Returns:
        价格（分），如果不需要支付则返回 None
    """
    plan = SUBSCRIPTION_PLANS.get(plan_tier, SUBSCRIPTION_PLANS["free"])

    # Free 和 Trial 不需要支付
    if plan_tier in ["free", "trial"]:
        return None

    # Pro 需要支付
    if plan_tier == "pro":
        if billing_cycle == BillingCycle.YEARLY:
            return plan.get("price_yearly", 0)
        return plan.get("price_monthly", 0)

    return 0


def get_plan_info(plan_tier: str) -> Dict[str, Any]:
    """获取订阅计划完整信息"""
    return SUBSCRIPTION_PLANS.get(plan_tier, SUBSCRIPTION_PLANS["free"])


def get_required_plan_for_feature(feature: str) -> str | None:
    """获取访问某个功能所需的最低计划"""
    # 按优先级检查计划（从免费版开始）
    for tier in ["free", "trial", "pro"]:
        if can_access_feature(tier, feature):
            return tier
    return None


def get_trial_duration_days() -> int:
    """获取试用期天数"""
    return SUBSCRIPTION_PLANS["trial"]["duration_days"]


def is_trial_plan(plan_tier: str) -> bool:
    """检查是否为试用计划"""
    return plan_tier == "trial"


def get_upgrade_target(current_tier: str) -> str:
    """
    获取当前计划的升级目标

    Args:
        current_tier: 当前计划层级

    Returns:
        建议升级到的计划层级
    """
    upgrade_path = {
        "free": "trial",      # 免费用户推荐先试用
        "trial": "pro",       # 试用用户升级到专业版
        "pro": None,          # 专业版已是最高级
    }
    return upgrade_path.get(current_tier)


def get_all_plans_for_display() -> list[Dict[str, Any]]:
    """
    获取所有计划用于前端展示

    Returns:
        包含计划详情的列表，按 free -> trial -> pro 排序
    """
    plans = []
    for tier in ["free", "trial", "pro"]:
        plan_info = get_plan_info(tier)
        plans.append({
            "tier": tier,
            "name": plan_info["name"],
            "description": plan_info["description"],
            "price_monthly": plan_info.get("price_monthly"),
            "price_yearly": plan_info.get("price_yearly"),
            "duration_days": plan_info.get("duration_days"),
            "features": plan_info["features"],
            "limits": plan_info.get("limits", {}),
        })
    return plans
