# TASK-005: 订阅管理系统实现

> **所属会话**: 会话2（后端开发线）
> **优先级**: P0（最高）
> **预计工期**: 3天
> **依赖任务**: TASK-004（认证系统）
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

实现订阅管理系统，包括订阅计划配置、订阅创建/查询/取消、付费功能解锁检测、使用限额控制等核心功能。

---

## 验收标准

- [ ] 订阅计划配置（免费版、专业版、企业版）
- [ ] 创建订阅API (`POST /api/v1/subscriptions`)
- [ ] 查询订阅API (`GET /api/v1/subscriptions`)
- [ ] 取消订阅API (`DELETE /api/v1/subscriptions`)
- [ ] 付费功能检测中间件
- [ ] 使用限额追踪（API调用次数）
- [ ] 付费触发检测服务

---

## 订阅计划配置

```python
# backend/config/subscriptions.py
from enum import Enum
from typing import Dict, Any

class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

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
    return SUBSCRIPTION_PLANS.get(plan_tier, SUBSCRIPTION_PLANS["free"])["features"]

def can_access_feature(user_tier: str, feature: str) -> bool:
    """检查用户是否有权限访问某个功能"""
    features = get_plan_features(user_tier)
    return features.get(feature, False)
```

---

## API规范

### 创建订阅
```
POST /api/v1/subscriptions
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "plan_tier": "pro",
  "billing_cycle": "monthly"
}

Response 200:
{
  "success": true,
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "plan_tier": "pro",
    "status": "active",
    "billing_cycle": "monthly",
    "amount": 99.00,
    "currency": "CNY",
    "started_at": "2025-03-10T...",
    "expires_at": "2025-04-10T..."
  }
}
```

### 查询当前订阅
```
GET /api/v1/subscriptions
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "id": "uuid",
    "plan_tier": "pro",
    "status": "active",
    "expires_at": "2025-04-10T...",
    "auto_renew": true,
    "features": {...}
  }
}
```

### 取消订阅
```
DELETE /api/v1/subscriptions
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "message": "订阅已取消"
}
```

---

## 付费功能检测

### 中间件实现

```python
# backend/api/dependencies.py
from functools import wraps
from fastapi import HTTPException, status
from models.user import User
from config.subscriptions import can_access_feature

def require_feature(feature: str):
    """要求用户有访问某个功能的权限"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User, **kwargs):
            if not can_access_feature(current_user.plan_tier.value, feature):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "FEATURE_LOCKED",
                        "feature": feature,
                        "required_plan": "pro",
                        "message": "此功能需要专业版订阅"
                    }
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.get("/api/v1/suppliers")
@require_feature("supplier_database")
async def get_suppliers(
    current_user: User = Depends(get_current_user)
):
    # 只有专业版用户可以访问
    pass
```

### 付费触发检测服务

```python
# backend/services/upsell_detector.py
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.user import User
from models.user_usage import UserUsage

class UpsellDetector:
    """付费触发检测器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_user_actions(self, user_id: str) -> Dict[str, bool]:
        """分析用户行为，判断是否应该触发付费推荐"""
        signals = {
            "cost_calculator_needed": False,
            "supplier_needed": False,
            "ai_analysis_needed": False,
            "community_needed": False
        }

        # 检测成本计算器使用频率
        today = datetime.utcnow().date()
        result = await self.db.execute(
            select(func.count(UserUsage.id))
            .where(UserUsage.user_id == user_id)
            .where(UserUsage.usage_type == "cost_calculator")
            .where(UserUsage.period_date == today)
        )
        usage_count = result.scalar() or 0

        if usage_count >= 3:
            signals["cost_calculator_needed"] = True

        # 检测品类浏览频率
        result = await self.db.execute(
            select(func.count(UserUsage.id))
            .where(UserUsage.user_id == user_id)
            .where(UserUsage.usage_type == "view_category")
            .where(UserUsage.period_date >= today - timedelta(days=7))
        )
        category_views = result.scalar() or 0

        if category_views >= 5:
            signals["supplier_needed"] = True

        return signals

    async def get_recommended_upgrade(self, user: User) -> dict | None:
        """获取推荐的升级方案"""
        if user.plan_tier == "free":
            signals = await self.analyze_user_actions(user.id)

            if signals["cost_calculator_needed"] or signals["supplier_needed"]:
                return {
                    "message": "您正在深入调研，专业版可以提供更精确的数据",
                    "features": ["精确成本计算器", "供应商数据库", "深度市场分析"],
                    "price": "¥99/月",
                    "action_url": "/pricing"
                }

        return None
```

---

## 使用限额追踪

```python
# backend/api/usage.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.user import User
from models.user_usage import UserUsage
from config.subscriptions import get_plan_features
from config.database import get_db
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])

async def check_rate_limit(
    user: User,
    usage_type: str,
    db: AsyncSession
):
    """检查使用限额"""
    features = get_plan_features(user.plan_tier.value)
    daily_limit = features.get("api_calls_per_day", -1)

    if daily_limit == -1:
        return True  # 无限

    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.count(UserUsage.id))
        .where(UserUsage.user_id == user.id)
        .where(UserUsage.usage_type == usage_type)
        .where(UserUsage.period_date == today)
    )
    usage_count = result.scalar() or 0

    if usage_count >= daily_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"每日{usage_type}调用次数已达上限({daily_limit}次)",
                "limit": daily_limit,
                "reset_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
            }
        )

    # 记录使用
    new_usage = UserUsage(
        user_id=user.id,
        usage_type=usage_type,
        quantity=1,
        period_date=today
    )
    db.add(new_usage)
    await db.commit()

    return True
```

---

## 提交规范

```bash
git commit -m "feat(TASK-005): 实现订阅管理系统

- 实现订阅计划配置（免费版/专业版/企业版）
- 实现创建订阅API
- 实现查询订阅API
- 实现取消订阅API
- 创建付费功能检测中间件
- 实现使用限额追踪
- 实现付费触发检测服务

API端点:
- POST /api/v1/subscriptions
- GET /api/v1/subscriptions
- DELETE /api/v1/subscriptions
- GET /api/v1/usage/check

功能特性:
- 订阅计划配置
- 付费功能权限控制
- API调用限额追踪
- 付费触发检测

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

*本任务书由主会话（项目经理）创建和维护*
