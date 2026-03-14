# api/dependencies.py
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
from typing import Callable, Awaitable
from config.database import AsyncSessionLocal
from config.redis import redis_client
from models.user import User
from utils.auth import verify_access_token
from config.subscriptions import can_access_feature, get_required_plan_for_feature
import uuid


async def get_db():
    """获取数据库会话依赖"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis():
    """获取Redis客户端依赖"""
    if not redis_client.client:
        await redis_client.connect()
    return redis_client


# 安全认证
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    token = credentials.credentials
    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )

    # 将字符串转换为 UUID
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID格式"
        )

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if current_user.plan_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已停用"
        )
    return current_user


def require_feature(feature: str):
    """要求用户有访问某个功能的权限（装饰器依赖工厂）"""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not can_access_feature(current_user.plan_tier, feature):
            required_plan = get_required_plan_for_feature(feature)

            if required_plan == "pro":
                message = "此功能需要专业版订阅"
                required_plan = "pro"
            elif required_plan == "enterprise":
                message = "此功能需要企业版订阅"
                required_plan = "enterprise"
            else:
                message = "此功能需要升级订阅"

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FEATURE_LOCKED",
                    "feature": feature,
                    "required_plan": required_plan,
                    "current_plan": current_user.plan_tier,
                    "message": message
                }
            )
        return current_user
    return dependency


def require_pro_user(current_user: User = Depends(get_current_user)) -> User:
    """快捷方法：要求专业版或企业版用户"""
    if current_user.plan_tier == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "UPGRADE_REQUIRED",
                "message": "此功能需要专业版或企业版订阅",
                "required_plan": "pro",
                "current_plan": current_user.plan_tier
            }
        )
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> dict | None:
    """获取当前用户（可选）- 用于不需要认证但需要用户信息的场景"""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_access_token(token)

    if payload is None:
        return None

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return None

    user = await db.get(User, user_id)
    if user is None:
        return None

    return {
        "id": str(user.id),
        "email": user.email,
        "plan_tier": user.plan_tier,
        "plan_status": user.plan_status,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "is_trial_expired": user.is_trial_expired() if hasattr(user, 'is_trial_expired') else False
    }
