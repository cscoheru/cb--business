# services/cache.py
"""Redis缓存服务 - 减少数据库和API调用压力"""

import json
import logging
from typing import Optional, Any
from datetime import timedelta
import hashlib

from redis.asyncio import Redis
from config.settings import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis缓存服务"""

    def __init__(self):
        self.redis: Optional[Redis] = None

    async def connect(self):
        """连接Redis"""
        if not self.redis:
            self.redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            await self.redis.ping()
            logger.info("✅ Redis缓存服务已连接")

    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None

    def _generate_key(self, prefix: str, identifier: str) -> str:
        """生成缓存键"""
        # 使用hash避免键过长
        hash_obj = hashlib.md5(f"{prefix}:{identifier}".encode())
        return f"{prefix}:{hash_obj.hexdigest()[:8]}"

    async def get(self, prefix: str, identifier: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            prefix: 键前缀 (如: 'amazon_product', 'api_response')
            identifier: 标识符 (如: ASIN, URL参数)

        Returns:
            缓存的数据，不存在返回None
        """
        if not self.redis:
            await self.connect()

        key = self._generate_key(prefix, identifier)
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug(f"✅ 缓存命中: {key}")
                return json.loads(data)
            else:
                logger.debug(f"❌ 缓存未命中: {key}")
                return None
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
            return None

    async def set(
        self,
        prefix: str,
        identifier: str,
        value: Any,
        ttl: int = 3600
    ):
        """
        设置缓存

        Args:
            prefix: 键前缀
            identifier: 标识符
            value: 要缓存的数据
            ttl: 过期时间(秒)，默认1小时
        """
        if not self.redis:
            await self.connect()

        key = self._generate_key(prefix, identifier)
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False)
            )
            logger.debug(f"💾 已缓存: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")

    async def delete(self, prefix: str, identifier: str):
        """删除缓存"""
        if not self.redis:
            await self.connect()

        key = self._generate_key(prefix, identifier)
        try:
            await self.redis.delete(key)
            logger.debug(f"🗑️ 已删除缓存: {key}")
        except Exception as e:
            logger.warning(f"缓存删除失败: {e}")

    async def invalidate_pattern(self, pattern: str):
        """批量删除匹配模式的缓存"""
        if not self.redis:
            await self.connect()

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"🗑️ 已批量删除缓存: {len(keys)}个")
        except Exception as e:
            logger.warning(f"批量删除缓存失败: {e}")


# 全局缓存服务实例
cache_service = CacheService()


async def get_cached_or_fetch(
    prefix: str,
    identifier: str,
    fetch_func: callable,
    ttl: int = 3600
) -> Any:
    """
    获取缓存或调用函数获取数据

    Args:
        prefix: 缓存键前缀
        identifier: 标识符
        fetch_func: 数据获取函数 (async)
        ttl: 缓存时间(秒)

    Returns:
        数据 (来自缓存或fetch_func)
    """
    # 尝试从缓存获取
    cached_data = await cache_service.get(prefix, identifier)
    if cached_data is not None:
        return cached_data

    # 缓存未命中，调用函数获取
    logger.info(f"🔄 缓存未命中，调用函数: {prefix}:{identifier}")
    data = await fetch_func()

    # 存入缓存
    if data is not None:
        await cache_service.set(prefix, identifier, data, ttl)

    return data
