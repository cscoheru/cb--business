# api/public/dependencies.py
"""公共 API 认证依赖

提供 API Key 认证、限流检查、用量记录功能
"""

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
from datetime import datetime, timezone
from typing import Optional
import logging
import time

from config.database import get_db
from models.api_key import APIKey, APIUsage
from services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


async def get_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    """
    验证 API Key

    从 X-API-Key Header 获取密钥并验证

    Returns:
        APIKey: 验证通过的 API Key 对象

    Raises:
        HTTPException: 401 无效密钥, 403 过期, 429 超限
    """
    # 从 Header 获取
    api_key_value = request.headers.get("X-API-Key")
    if not api_key_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_api_key",
                "message": "Missing API Key. Include X-API-Key header."
            }
        )

    # 计算 hash
    key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()

    # 查询数据库
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API Key"
            }
        )

    # 检查过期
    if api_key_obj.expires_at:
        expires_at = api_key_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "api_key_expired",
                    "message": "API Key expired. Please renew subscription.",
                    "expired_at": expires_at.isoformat()
                }
            )

    # 限流检查
    allowed, rate_info = await rate_limiter.check_rate_limit(
        api_key_obj.id,
        api_key_obj.rate_limit_per_minute,
        api_key_obj.rate_limit_per_day
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "API rate limit exceeded",
                "rate_info": rate_info
            },
            headers={
                "X-RateLimit-Limit-Minute": str(rate_info.get("minute_limit", 0)),
                "X-RateLimit-Remaining-Minute": str(rate_info.get("minute_remaining", 0)),
                "X-RateLimit-Limit-Day": str(rate_info.get("day_limit", 0)),
                "X-RateLimit-Remaining-Day": str(rate_info.get("day_remaining", 0)),
            }
        )

    # 更新最后使用时间
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    # 存储限流信息到 request state
    request.state.api_key = api_key_obj
    request.state.rate_info = rate_info

    return api_key_obj


async def get_api_key_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[APIKey]:
    """
    可选的 API Key 验证

    如果提供了 X-API-Key 则验证，否则返回 None
    用于同时支持公开和认证访问的端点
    """
    api_key_value = request.headers.get("X-API-Key")
    if not api_key_value:
        return None

    return await get_api_key(request, db)


async def record_api_usage(
    request: Request,
    response_status: int,
    response_time_ms: int,
    tokens_used: int = 0,
    error_message: str = None
):
    """
    记录 API 使用情况

    在请求完成后调用，记录到数据库
    """
    if not hasattr(request.state, "api_key"):
        return

    api_key = request.state.api_key

    # 异步记录，不阻塞响应
    try:
        from config.database import async_session_factory

        async with async_session_factory() as db:
            usage = APIUsage(
                api_key_id=api_key.id,
                endpoint=request.url.path,
                method=request.method,
                status_code=response_status,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                error_message=error_message[:500] if error_message else None,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", "")[:255]
            )
            db.add(usage)
            await db.commit()

    except Exception as e:
        logger.error(f"Failed to record API usage: {e}")


class UsageTracker:
    """
    用量跟踪器 - 用于记录 API 调用

    Usage:
        tracker = UsageTracker(request)
        # ... do work ...
        await tracker.record(200, response_time_ms=150)
    """

    def __init__(self, request: Request):
        self.request = request
        self.start_time = time.time()

    async def record(
        self,
        status_code: int,
        tokens_used: int = 0,
        error_message: str = None
    ):
        """记录使用情况"""
        response_time_ms = int((time.time() - self.start_time) * 1000)

        await record_api_usage(
            self.request,
            response_status=status_code,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            error_message=error_message
        )
