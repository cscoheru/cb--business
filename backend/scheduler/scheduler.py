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


async def start_scheduler():
    """启动调度器"""
    # 导入任务函数
    from scheduler.tasks import crawl_retail_dive, crawl_shopify_blog, crawl_cifnews, crawl_techcrunch, cleanup_old_articles

    # 添加定时任务
    # Retail Dive - 每30分钟爬取一次
    scheduler.add_job(
        crawl_retail_dive,
        trigger=IntervalTrigger(minutes=30),
        id='retail_dive_crawl',
        name='Retail Dive 定时爬取',
        replace_existing=True,
    )

    # Shopify Blog - 每30分钟爬取一次
    scheduler.add_job(
        crawl_shopify_blog,
        trigger=IntervalTrigger(minutes=30),
        id='shopify_blog_crawl',
        name='Shopify Blog 定时爬取',
        replace_existing=True,
    )

    # 雨果网 - 每30分钟爬取一次
    scheduler.add_job(
        crawl_cifnews,
        trigger=IntervalTrigger(minutes=30),
        id='cifnews_crawl',
        name='雨果网定时爬取',
        replace_existing=True,
    )

    # TechCrunch - 每30分钟爬取一次
    scheduler.add_job(
        crawl_techcrunch,
        trigger=IntervalTrigger(minutes=30),
        id='techcrunch_crawl',
        name='TechCrunch 定时爬取',
        replace_existing=True,
    )

    # 每天凌晨3点清理过期数据
    scheduler.add_job(
        cleanup_old_articles,
        trigger=CronTrigger(hour=3, minute=0),
        id='cleanup_old_data',
        name='清理过期文章',
        replace_existing=True,
    )

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
