# api/__init__.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from config.database import engine
from config.redis import redis_client
from api.health import router as health_router
from api.auth import router as auth_router
from api.users import router as users_router
from api.subscriptions import router as subscriptions_router
from api.usage import router as usage_router
from api.admin import router as admin_router
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="跨境电商智能信息SaaS平台API",
    version="1.0.0",
    debug=settings.DEBUG
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router, tags=["health"])
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(subscriptions_router)
app.include_router(usage_router)
app.include_router(admin_router)

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"{settings.APP_NAME} starting up...")
    await redis_client.connect()
    logger.info("Redis connected")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Shutting down...")
    await redis_client.disconnect()
    await engine.dispose()
    logger.info("Connections closed")
