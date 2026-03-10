# api/__init__.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from config.settings import settings
from config.database import engine
from config.redis import redis_client
from api.health import router as health_router
from api.auth import router as auth_router
from api.users import router as users_router
from api.subscriptions import router as subscriptions_router
from api.usage import router as usage_router
from api.admin import router as admin_router
from api.payments import router as payments_router
from api.crawler import router as crawler_router
import logging
import json

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
origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.headers.get("X-Error-Code", "HTTP_ERROR") if hasattr(exc, "headers") and exc.headers else "HTTP_ERROR"
        }
    )

# 注册路由
app.include_router(health_router, tags=["health"])
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(subscriptions_router)
app.include_router(usage_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(crawler_router)

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
