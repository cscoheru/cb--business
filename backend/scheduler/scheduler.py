# scheduler/scheduler.py
"""定时任务调度器"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from config.settings import settings

logger = logging.getLogger(__name__)

# 任务存储配置（持久化任务状态）
jobstores = {
    'default': SQLAlchemyJobStore(url=f'sqlite:///{settings.BASE_DIR}/scheduler_jobs.sqlite')
}

# 执行器配置
executors = {
    'default': AsyncIOExecutor(),
}

# 调度器配置
scheduler_config = {
    'jobstores': jobstores,
    'executors': executors,
    'job_defaults': {
        'coalesce': True,  # 合并错过的任务
        'max_instances': 1,  # 同一任务最多1个实例
        'misfire_grace_time': 3600,  # 错过任务的时间容忍度（秒）
    },
    'timezone': 'Asia/Shanghai',
}


# 全局调度器实例
scheduler = AsyncIOScheduler(**scheduler_config)


# 模块级任务函数，可以被APScheduler序列化
async def _crawl_job_wrapper(source_name: str, source_display_name: str):
    """包装爬虫任务函数"""
    from scheduler.tasks import execute_crawl
    logger.info(f"🔄 开始爬取 {source_display_name}...")
    result = await execute_crawl(source_name)
    logger.info(f"✅ {source_display_name} 爬取完成: {result.get('new_count', 0)} 篇新文章")
    return result


async def start_scheduler():
    """启动调度器"""
    try:
        # 导入任务函数和配置
        from scheduler.tasks import cleanup_old_articles
        from crawler.config import get_enabled_sources

        # 获取所有启用的数据源
        sources = get_enabled_sources()
        logger.info(f"找到 {len(sources)} 个已启用的数据源")

        # 为每个数据源创建定时任务
        for source_name, config in sources.items():
            try:
                # 使用偏函数传递参数
                from functools import partial
                job_func = partial(_crawl_job_wrapper, source_name, config['name'])

                # 添加定时任务 - 每30分钟爬取一次
                scheduler.add_job(
                    job_func,
                    trigger=IntervalTrigger(minutes=30),
                    id=f'{source_name}_crawl',
                    name=f"{config['name']} 定时爬取",
                    replace_existing=True,
                    misfire_grace_time=3600,  # 错过1小时内的任务
                )
                logger.info(f"  ✓ 已注册: {config['name']} (每30分钟)")
            except Exception as e:
                logger.error(f"  ✗ 注册失败 {config['name']}: {e}")

        # 每天凌晨3点清理过期数据
        scheduler.add_job(
            cleanup_old_articles,
            trigger=CronTrigger(hour=3, minute=0),
            id='cleanup_old_data',
            name='清理过期文章',
            replace_existing=True,
        )
        logger.info("  ✓ 已注册: 清理过期文章 (每天凌晨3点)")

    except ImportError as e:
        logger.warning(f"Scheduler tasks not available: {e}")
        logger.info("Starting scheduler without crawler tasks")

    # 启动调度器
    scheduler.start()
    logger.info("🚀 爬虫调度器已启动")

    # 打印任务列表
    jobs = scheduler.get_jobs()
    logger.info(f"📋 已注册 {len(jobs)} 个定时任务:")
    for job in jobs:
        logger.info(f"  - {job.name} (ID: {job.id}, 下次执行: {job.next_run_time})")


async def stop_scheduler():
    """停止调度器"""
    scheduler.shutdown()
    logger.info("🛑 爬虫调度器已停止")
