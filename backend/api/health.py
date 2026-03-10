# api/health.py
from fastapi import APIRouter
from schemas.common import HealthResponse
from config.database import engine
from config.redis import redis_client
from datetime import datetime

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """健康检查"""
    # 检查数据库
    try:
        async with engine.begin() as conn:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 检查Redis
    try:
        if redis_client.client and await redis_client.ping():
            redis_status = "connected"
        else:
            redis_status = "not initialized"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        database=db_status,
        redis=redis_status
    )
