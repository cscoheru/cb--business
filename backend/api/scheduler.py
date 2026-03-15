# api/scheduler.py
"""调度器管理API - 手动触发和监控定时任务

提供手动触发定时任务的端点，方便调试和测试。
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


# ============================================================================
# Models
# ============================================================================

class JobTriggerResponse(BaseModel):
    """任务触发响应"""
    success: bool
    job_id: str
    message: str
    execution_time: float = 0.0


class SchedulerStatusResponse(BaseModel):
    """调度器状态响应"""
    success: bool
    is_running: bool
    jobs: List[Dict[str, Any]]
    uptime_seconds: float


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """
    获取调度器状态

    返回:
        调度器运行状态和所有注册的任务信息
    """
    try:
        from scheduler.opportunity_tasks import scheduler
        import time

        # 检查调度器是否运行
        is_running = scheduler.running

        # 获取所有任务
        jobs = scheduler.get_jobs()

        job_list = []
        for job in jobs:
            job_list.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "enabled": True  # APScheduler jobs are always enabled
            })

        # 计算运行时间
        uptime = time.time()

        return SchedulerStatusResponse(
            success=True,
            is_running=is_running,
            jobs=job_list,
            uptime_seconds=uptime
        )

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/funnel-management", response_model=JobTriggerResponse)
async def trigger_funnel_management(
    background_tasks: BackgroundTasks
):
    """
    手动触发漏斗管理任务

    通常由调度器自动执行，此端点用于手动触发。

    功能:
    - 检查所有商机状态
    - 执行自动演进
    - 处理超时商机
    """
    try:
        from scheduler.opportunity_tasks import funnel_management_job
        import time

        start_time = time.time()

        # 在后台执行任务
        logger.info("🔄 [手动触发] 漏斗管理任务")

        await funnel_management_job()

        execution_time = time.time() - start_time

        logger.info("✅ [手动触发] 漏斗管理任务完成")

        return JobTriggerResponse(
            success=True,
            job_id="funnel_management",
            message="漏斗管理任务执行成功",
            execution_time=round(execution_time, 2)
        )

    except Exception as e:
        logger.error(f"Failed to trigger funnel management: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/signal-discovery", response_model=JobTriggerResponse)
async def trigger_signal_discovery(
    background_tasks: BackgroundTasks
):
    """
    手动触发信号发现任务

    功能:
    - 从Articles表发现新商机
    - AI分析文章内容
    - 创建BusinessOpportunity记录
    """
    try:
        from scheduler.opportunity_tasks import signal_discovery_job
        import time

        start_time = time.time()

        logger.info("🔍 [手动触发] 信号发现任务")

        await signal_discovery_job()

        execution_time = time.time() - start_time

        logger.info("✅ [手动触发] 信号发现任务完成")

        return JobTriggerResponse(
            success=True,
            job_id="signal_discovery",
            message="信号发现任务执行成功",
            execution_time=round(execution_time, 2)
        )

    except Exception as e:
        logger.error(f"Failed to trigger signal discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/grade-monitoring", response_model=JobTriggerResponse)
async def trigger_grade_monitoring(
    background_tasks: BackgroundTasks
):
    """
    手动触发等级监控任务

    功能:
    - 查询所有用户收藏的商机
    - 重新计算C-P-I分数
    - 更新等级（自动升降）
    - 记录等级变更历史
    """
    try:
        from scheduler.opportunity_tasks import grade_monitoring_job
        import time

        start_time = time.time()

        logger.info("📊 [手动触发] 等级监控任务")

        await grade_monitoring_job()

        execution_time = time.time() - start_time

        logger.info("✅ [手动触发] 等级监控任务完成")

        return JobTriggerResponse(
            success=True,
            job_id="grade_monitoring",
            message="等级监控任务执行成功",
            execution_time=round(execution_time, 2)
        )

    except Exception as e:
        logger.error(f"Failed to trigger grade monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/all")
async def trigger_all_jobs(
    background_tasks: BackgroundTasks
):
    """
    按顺序触发所有定时任务

    用于测试或数据同步。
    """
    try:
        import time
        start_time = time.time()

        results = []

        # 1. 漏斗管理
        try:
            funnel_result = await trigger_funnel_management(background_tasks)
            results.append({
                "job": "funnel_management",
                "success": funnel_result.success,
                "time": funnel_result.execution_time
            })
        except Exception as e:
            results.append({
                "job": "funnel_management",
                "success": False,
                "error": str(e)
            })

        # 2. 信号发现
        try:
            signal_result = await trigger_signal_discovery(background_tasks)
            results.append({
                "job": "signal_discovery",
                "success": signal_result.success,
                "time": signal_result.execution_time
            })
        except Exception as e:
            results.append({
                "job": "signal_discovery",
                "success": False,
                "error": str(e)
            })

        # 3. 等级监控
        try:
            grade_result = await trigger_grade_monitoring(background_tasks)
            results.append({
                "job": "grade_monitoring",
                "success": grade_result.success,
                "time": grade_result.execution_time
            })
        except Exception as e:
            results.append({
                "job": "grade_monitoring",
                "success": False,
                "error": str(e)
            })

        total_time = time.time() - start_time

        success_count = sum(1 for r in results if r.get("success"))

        return {
            "success": True,
            "total_jobs": len(results),
            "successful": success_count,
            "failed": len(results) - success_count,
            "total_time": round(total_time, 2),
            "results": results
        }

    except Exception as e:
        logger.error(f"Failed to trigger all jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
