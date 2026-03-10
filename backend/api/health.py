# api/health.py
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check():
    """简单健康检查 - 用于 Railway 等平台"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cb-business-api"
    }


@router.get("/health/extended", tags=["health"])
async def extended_health_check():
    """扩展健康检查 - 包含数据库和Redis状态"""
    # 延迟导入以避免启动时阻塞
    from config.database import engine
    from config.redis import redis_client

    # 检查数据库（非阻塞）
    db_status = "not_checked"
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 检查Redis（非阻塞）
    redis_status = "not_checked"
    try:
        if redis_client.client and await redis_client.ping():
            redis_status = "connected"
        else:
            redis_status = "not_initialized"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cb-business-api",
        "database": db_status,
        "redis": redis_status
    }
