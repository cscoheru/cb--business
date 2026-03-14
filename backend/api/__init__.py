# api/__init__.py
import logging
import json

# 配置日志（必须在最前面）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
from api.assessments import router as assessments_router
from api.search import router as search_router
from api.products import router as products_router
from api.lazada import router as lazada_router
from api.trends import router as trends_router
from api.opportunities import router as opportunities_router
from api.social import router as social_router
from api.keywords import router as keywords_router
from api.products_real import router as products_real_router
from api.cards import router as cards_router
from api.favorites import router as favorites_router
from api.unified_favorites import router as unified_favorites_router
from api.batch_operations import router as batch_operations_router
from api.openclaw_integration import router as openclaw_router
from api.notifications import router as notifications_router
from api.migrate import router as migrate_router


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="跨境电商智能信息SaaS平台API",
    version="1.0.0",
    debug=settings.DEBUG
)

# 配置CORS
# 默认允许 zenconsult.top 域名，确保生产环境CORS正常工作
default_origins = [
    "https://www.zenconsult.top",
    "https://admin.zenconsult.top",
    "http://localhost:3000",  # 开发环境
    "http://localhost:3001",  # 备用开发端口
]

# 检查环境变量是否有效（非空且不是通配符）
if settings.ALLOWED_ORIGINS and settings.ALLOWED_ORIGINS.strip() and settings.ALLOWED_ORIGINS != "*":
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    logger.info(f"Using ALLOWED_ORIGINS from environment: {origins}")
else:
    origins = default_origins
    logger.info(f"Using default CORS origins: {origins}")

# 去重（避免重复值导致CORS错误）
seen = set()
unique_origins = []
for origin in origins:
    if origin not in seen:
        unique_origins.append(origin)
        seen.add(origin)
origins = unique_origins

logger.info(f"Final CORS allowed origins: {origins}")

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


# 根路径端点（Railway 和其他平台默认检查）
@app.get("/")
async def root():
    """根路径 - 用于快速健康检查"""
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/test")
async def test():
    """测试端点 - 验证路由是否正常工作"""
    return {
        "message": "Routes are working!",
        "timestamp": "2026-03-12"
    }


# 注册路由
app.include_router(health_router, tags=["health"])
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(subscriptions_router)
app.include_router(usage_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(assessments_router)
app.include_router(search_router)
# app.include_router(products_router)  # Disabled - using products_real_router instead
app.include_router(products_real_router)
app.include_router(lazada_router)
app.include_router(trends_router)
app.include_router(opportunities_router)
app.include_router(social_router)
app.include_router(keywords_router)
app.include_router(cards_router)
app.include_router(favorites_router)
app.include_router(unified_favorites_router)  # ✅ 统一收藏API

# OpenClaw集成路由
app.include_router(batch_operations_router)
app.include_router(openclaw_router)

# 通知路由
app.include_router(notifications_router)

# 数据库迁移路由（需要admin权限）
app.include_router(migrate_router)

# 可选的 crawler 路由（依赖可能未安装）
try:
    from api.crawler import router as crawler_router
    app.include_router(crawler_router)
    logger.info("Crawler router loaded")
except ImportError as e:
    logger.warning(f"Crawler router not available: {e}")

# 添加同步版本的爬虫路由（作为备用）
try:
    from api.crawler_sync import router as crawler_sync_router
    app.include_router(crawler_sync_router)
    logger.info("Crawler sync router loaded")
except ImportError as e:
    logger.warning(f"Crawler sync router not available: {e}")

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"{settings.APP_NAME} starting up...")

    # 启动爬虫调度器
    try:
        from scheduler.scheduler import start_scheduler
        await start_scheduler()
        logger.info("🚀 爬虫调度器已启动")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

    # 启动智能商机跟踪定时任务
    try:
        from scheduler.opportunity_tasks import start_opportunity_scheduler
        start_opportunity_scheduler()
        logger.info("🎯 智能商机定时任务已启动")
    except Exception as e:
        logger.error(f"Failed to start opportunity scheduler: {e}")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Shutting down...")

    # 停止爬虫调度器
    try:
        from scheduler.scheduler import stop_scheduler
        await stop_scheduler()
    except Exception as e:
        logger.warning(f"Scheduler shutdown failed: {e}")

    # 停止智能商机定时任务
    try:
        from scheduler.opportunity_tasks import stop_opportunity_scheduler
        stop_opportunity_scheduler()
        logger.info("🎯 智能商机定时任务已停止")
    except Exception as e:
        logger.warning(f"Opportunity scheduler shutdown failed: {e}")

    # 关闭连接（忽略错误）
    try:
        await redis_client.disconnect()
    except Exception:
        pass

    try:
        await engine.dispose()
    except Exception:
        pass

    logger.info("Shutdown complete")


# 启动服务器 - 当使用 "python -m api" 时执行
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", 8000))

    # 在后台启动调度器（非阻塞）
    import threading

    def run_scheduler_async():
        try:
            asyncio.run(start_scheduler())
        except Exception as e:
            logger.error(f"Scheduler startup failed: {e}")

    scheduler_thread = threading.Thread(target=run_scheduler_async, daemon=True)
    scheduler_thread.start()

    logger.info(f"🚀 Starting server on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
