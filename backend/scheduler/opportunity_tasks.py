# scheduler/opportunity_tasks.py
"""智能商机跟踪系统 - 定时任务"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.database import AsyncSessionLocal, get_db
from services.smart_orchestrator import get_orchestrator

logger = logging.getLogger(__name__)

# 创建调度器
scheduler = AsyncIOScheduler()


async def funnel_management_job():
    """
    漏斗管理定时任务

    每小时执行一次，检查商机状态并执行自动演进
    """
    logger.info("🔄 [定时任务] 开始漏斗管理")

    try:
        async with AsyncSessionLocal() as db:
            orchestrator = get_orchestrator()
            await orchestrator.manage_funnel(db)

        logger.info("✅ [定时任务] 漏斗管理完成")

    except Exception as e:
        logger.error(f"❌ [定时任务] 漏斗管理失败: {e}")


async def signal_discovery_job():
    """
    信号发现定时任务

    每30分钟执行一次，从Articles表发现新商机
    """
    logger.info("🔍 [定时任务] 开始信号发现")

    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from models.article import Article
            from models.business_opportunity import BusinessOpportunity
            from services.signal_adapters import DatabaseArticleSignalAdapter
            from services.smart_orchestrator import get_orchestrator

            orchestrator = get_orchestrator()
            adapter = DatabaseArticleSignalAdapter(db)

            # 查找最近未处理的文章
            result = await db.execute(
                select(Article)
                .where(Article.is_processed == True)
                .order_by(Article.published_at.desc())
                .limit(20)
            )
            articles = result.scalars().all()

            logger.info(f"📰 找到 {len(articles)} 篇文章")

            for article in articles:
                try:
                    # 转换为信号
                    signal = await adapter.to_signal(article)

                    # 处理信号
                    await orchestrator.process_signal(signal, db, auto_collect=False)

                except Exception as e:
                    logger.error(f"处理文章 {article.id} 失败: {e}")
                    continue

        logger.info("✅ [定时任务] 信号发现完成")

    except Exception as e:
        logger.error(f"❌ [定时任务] 信号发现失败: {e}")


async def grade_monitoring_job():
    """
    等级监控定时任务

    每6小时执行一次，重新计算用户收藏商机的C-P-I分数并更新等级
    支持自动升降级和等级变更历史记录
    """
    logger.info("📊 [定时任务] 开始等级监控")

    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from models.business_opportunity import BusinessOpportunity, OpportunityGrade
            from services.grade_manager import GradeManager

            # 查询所有用户收藏的商机（有user_id的商机）
            result = await db.execute(
                select(BusinessOpportunity)
                .where(BusinessOpportunity.user_id.isnot(None))
                .where(BusinessOpportunity.card_id.isnot(None))  # 必须有关联卡片才能计算CPI
                .order_by(BusinessOpportunity.last_cpi_recalc_at.asc())  # 优先更新最久未重算的
            )
            opportunities = result.scalars().all()

            if not opportunities:
                logger.info("📊 没有需要监控的商机")
                return

            logger.info(f"📊 找到 {len(opportunities)} 个需要监控的商机")

            # 批量更新等级
            results = await GradeManager.batch_update_grades(opportunities, db)

            # 统计结果
            grade_changes = sum(1 for r in results if r.get('grade_changed'))
            errors = sum(1 for r in results if r.get('error'))

            logger.info(f"✅ [定时任务] 等级监控完成")
            logger.info(f"  - 处理商机数: {len(results)}")
            logger.info(f"  - 等级变更数: {grade_changes}")
            if errors > 0:
                logger.warning(f"  - 错误数: {errors}")

            # 记录等级变更详情
            for result in results:
                if result.get('grade_changed'):
                    history = result.get('history_entry', {})
                    logger.info(
                        f"  🔄 商机 {result.get('title', 'N/A')[:30]}: "
                        f"{history.get('from_grade')} → {history.get('to_grade')} "
                        f"({history.get('old_score'):.1f} → {history.get('new_score'):.1f})"
                    )

    except Exception as e:
        logger.error(f"❌ [定时任务] 等级监控失败: {e}", exc_info=True)


def setup_opportunity_scheduler():
    """设置商机定时任务"""

    # 漏斗管理：每小时执行
    scheduler.add_job(
        funnel_management_job,
        'interval',
        hours=1,
        id='funnel_management',
        name='漏斗管理任务'
    )

    # 信号发现：每30分钟执行
    scheduler.add_job(
        signal_discovery_job,
        'interval',
        minutes=30,
        id='signal_discovery',
        name='信号发现任务'
    )

    # 等级监控：每6小时执行
    scheduler.add_job(
        grade_monitoring_job,
        'interval',
        hours=6,
        id='grade_monitoring',
        name='等级监控任务'
    )

    logger.info("✅ 商机定时任务已设置")
    logger.info("  - 漏斗管理: 每小时")
    logger.info("  - 信号发现: 每30分钟")
    logger.info("  - 等级监控: 每6小时")


def start_opportunity_scheduler():
    """启动商机定时任务调度器"""
    if not scheduler.running:
        setup_opportunity_scheduler()
        scheduler.start()
        logger.info("🚀 商机定时任务调度器已启动")
    else:
        logger.warning("⚠️ 商机定时任务调度器已在运行")


def stop_opportunity_scheduler():
    """停止商机定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 商机定时任务调度器已停止")


# 导出供main.py使用
__all__ = [
    'start_opportunity_scheduler',
    'stop_opportunity_scheduler',
    'setup_opportunity_scheduler'
]
