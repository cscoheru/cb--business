# main.py
import uvicorn
import os
import asyncio
from api import app
from scheduler.scheduler import start_scheduler, stop_scheduler

async def main():
    """启动应用：API服务器 + 爬虫调度器"""
    port = int(os.getenv("PORT", 8000))

    # 启动爬虫调度器
    await start_scheduler()

    # 创建FastAPI服务器配置
    config = uvicorn.Config(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
    server = uvicorn.Server(config)

    try:
        # 启动API服务器
        await server.serve()
    finally:
        # 停止调度器
        await stop_scheduler()

if __name__ == "__main__":
    # 使用简单模式（兼容性更好）
    port = int(os.getenv("PORT", 8000))

    # 在后台启动调度器
    import threading

    def run_scheduler():
        asyncio.run(start_scheduler())

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    print("🚀 爬虫调度器已在后台启动")

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
