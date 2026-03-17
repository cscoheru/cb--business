# services/rate_limiter.py
"""Redis 滑动窗口限流服务

使用 Redis 实现分布式限流，支持分钟级和日级限制
"""

import logging
from typing import Optional, Tuple
from datetime import datetime, timezone
import uuid

from redis.asyncio import Redis
from config.settings import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis 滑动窗口限流器"""

    def __init__(self):
        self.redis: Optional[Redis] = None

    async def connect(self):
        """连接 Redis"""
        if not self.redis:
            self.redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            logger.info("✅ Rate Limiter Redis 已连接")

    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def _ensure_connection(self):
        """确保已连接"""
        if not self.redis:
            await self.connect()

    async def check_rate_limit(
        self,
        api_key_id: uuid.UUID,
        limit_per_minute: int,
        limit_per_day: int
    ) -> Tuple[bool, dict]:
        """
        检查是否在限流范围内

        Args:
            api_key_id: API Key ID
            limit_per_minute: 每分钟限制
            limit_per_day: 每日限制

        Returns:
            (allowed: bool, info: dict)
            - allowed: True 如果请求被允许
            - info: 包含当前计数和限制信息
        """
        await self._ensure_connection()

        now = datetime.now(timezone.utc)
        minute_key = f"ratelimit:{api_key_id}:minute:{now.strftime('%Y%m%d%H%M')}"
        day_key = f"ratelimit:{api_key_id}:day:{now.strftime('%Y%m%d')}"

        try:
            # 使用 pipeline 提高性能
            pipe = self.redis.pipeline()

            # 增加计数
            pipe.incr(minute_key)
            pipe.incr(day_key)

            # 设置过期时间 (只在第一次设置)
            pipe.expire(minute_key, 120)  # 2分钟过期 (留buffer)
            pipe.expire(day_key, 86400 + 3600)  # 25小时过期

            results = await pipe.execute()

            minute_count = results[0]
            day_count = results[1]

            # 检查限制
            minute_exceeded = minute_count > limit_per_minute
            day_exceeded = day_count > limit_per_day

            allowed = not minute_exceeded and not day_exceeded

            info = {
                "minute_count": minute_count,
                "minute_limit": limit_per_minute,
                "minute_remaining": max(0, limit_per_minute - minute_count),
                "day_count": day_count,
                "day_limit": limit_per_day,
                "day_remaining": max(0, limit_per_day - day_count),
                "reset_at": {
                    "minute": (now.replace(second=0, microsecond=0).timestamp() + 60),
                    "day": (now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() + 86400)
                }
            }

            if not allowed:
                logger.warning(
                    f"⚠️ Rate limit exceeded for API Key {api_key_id}: "
                    f"minute={minute_count}/{limit_per_minute}, day={day_count}/{limit_per_day}"
                )

            return allowed, info

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # 出错时允许请求通过 (fail-open)
            return True, {"error": str(e), "fallback": True}

    async def get_usage_stats(
        self,
        api_key_id: uuid.UUID
    ) -> dict:
        """
        获取当前用量统计

        Returns:
            当前分钟和当日的使用量
        """
        await self._ensure_connection()

        now = datetime.now(timezone.utc)
        minute_key = f"ratelimit:{api_key_id}:minute:{now.strftime('%Y%m%d%H%M')}"
        day_key = f"ratelimit:{api_key_id}:day:{now.strftime('%Y%m%d')}"

        try:
            minute_count = await self.redis.get(minute_key)
            day_count = await self.redis.get(day_key)

            return {
                "current_minute": int(minute_count or 0),
                "current_day": int(day_count or 0),
                "period": {
                    "minute": now.strftime('%Y%m%d%H%M'),
                    "day": now.strftime('%Y%m%d')
                }
            }
        except Exception as e:
            logger.error(f"Get usage stats failed: {e}")
            return {"error": str(e)}

    async def reset_limits(
        self,
        api_key_id: uuid.UUID
    ) -> bool:
        """
        重置指定 API Key 的限流计数

        用于测试或特殊管理操作
        """
        await self._ensure_connection()

        try:
            # 查找并删除所有限流键
            pattern = f"ratelimit:{api_key_id}:*"
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis.delete(*keys)
                logger.info(f"🔄 Reset rate limits for API Key {api_key_id}: deleted {len(keys)} keys")

            return True
        except Exception as e:
            logger.error(f"Reset limits failed: {e}")
            return False


# 全局限流器实例
rate_limiter = RateLimiter()


async def check_api_rate_limit(
    api_key_id: uuid.UUID,
    limit_per_minute: int,
    limit_per_day: int
) -> Tuple[bool, dict]:
    """
    便捷函数：检查 API 限流

    Usage:
        allowed, info = await check_api_rate_limit(api_key.id, 60, 1000)
        if not allowed:
            raise HTTPException(429, "Rate limit exceeded")
    """
    return await rate_limiter.check_rate_limit(
        api_key_id,
        limit_per_minute,
        limit_per_day
    )
