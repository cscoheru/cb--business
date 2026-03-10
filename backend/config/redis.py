# config/redis.py
import redis.asyncio as aioredis
from .settings import settings


class RedisClient:
    """Redis客户端"""
    def __init__(self):
        self.client = None

    async def connect(self):
        """连接Redis"""
        self.client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> str | None:
        """获取值"""
        if self.client:
            return await self.client.get(key)
        return None

    async def set(self, key: str, value: str, ex: int = None):
        """设置值"""
        if self.client:
            await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        """删除值"""
        if self.client:
            await self.client.delete(key)

    async def ping(self) -> bool:
        """检查连接"""
        if self.client:
            try:
                return await self.client.ping()
            except Exception:
                return False
        return False


# 全局Redis客户端实例
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """获取Redis客户端依赖"""
    if not redis_client.client:
        await redis_client.connect()
    return redis_client
