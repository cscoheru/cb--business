# api/data_collection_tasks.py
"""数据采集任务 API - Data Collection Tasks API

提供数据采集任务的查询和管理功能。
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from config.database import get_db
from models.business_opportunity import DataCollectionTask, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/data-collection-tasks", tags=["data-collection-tasks"])


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_progress(task: DataCollectionTask) -> float:
    """计算任务进度 (0-1)"""
    if task.status == TaskStatus.PENDING:
        return 0.0
    elif task.status == TaskStatus.RUNNING:
        # 估算运行中任务的进度为50%
        return 0.5
    elif task.status == TaskStatus.COMPLETED:
        return 1.0
    else:  # FAILED, CANCELLED
        return 0.0


def estimate_completion_time(task: DataCollectionTask) -> Optional[str]:
    """估算任务完成时间"""
    if task.status == TaskStatus.COMPLETED:
        return "已完成"
    elif task.status in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
        return "已取消"
    elif task.status == TaskStatus.PENDING:
        return "等待中"
    elif task.status == TaskStatus.RUNNING:
        if task.started_at:
            elapsed = (datetime.utcnow() - task.started_at).total_seconds()
            if elapsed < 60:
                return "约1分钟"
            elif elapsed < 300:
                return "约5分钟"
            else:
                return "进行中"
        return "进行中"
    return None


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("")
async def list_tasks(
    opportunity_id: Optional[str] = Query(None, description="商机ID"),
    status: Optional[str] = Query(None, description="任务状态"),
    task_type: Optional[str] = Query(None, description="任务类型"),
    active_only: bool = Query(True, description="只显示活跃任务"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取数据采集任务列表"""
    try:
        from uuid import UUID

        query = select(DataCollectionTask)

        # 应用筛选
        if opportunity_id:
            try:
                opportunity_uuid = UUID(opportunity_id)
                query = query.where(DataCollectionTask.opportunity_id == opportunity_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid opportunity ID format")

        if status:
            query = query.where(DataCollectionTask.status == status)

        if task_type:
            query = query.where(DataCollectionTask.task_type == task_type)

        if active_only:
            query = query.where(
                DataCollectionTask.status.in_([
                    TaskStatus.PENDING.value,
                    TaskStatus.RUNNING.value
                ])
            )

        # 排序：活跃任务优先，然后按创建时间倒序
        query = query.order_by(
            DataCollectionTask.status.asc(),  # PENDING, RUNNING first
            desc(DataCollectionTask.created_at)
        )

        # 分页
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        tasks = result.scalars().all()

        # 构建响应
        return {
            "success": True,
            "total": len(tasks),
            "tasks": [
                {
                    "id": str(task.id),
                    "opportunity_id": str(task.opportunity_id),
                    "task_type": task.task_type,
                    "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                    "status": task.status.value if hasattr(task.status, 'value') else task.status,
                    "ai_request": task.ai_request,
                    "channel_name": task.channel_name,
                    "error_message": task.error_message,
                    "retry_count": task.retry_count,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "progress": calculate_progress(task),
                    "estimated_completion": estimate_completion_time(task),
                    "result_summary": _summarize_result(task.result) if task.result else None
                }
                for task in tasks
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个任务详情"""
    try:
        from uuid import UUID

        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task ID format")

        result = await db.execute(
            select(DataCollectionTask).where(DataCollectionTask.id == task_uuid)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {
            "success": True,
            "task": task.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunity/{opportunity_id}")
async def get_opportunity_tasks(
    opportunity_id: str,
    include_history: bool = Query(False, description="包含已完成任务"),
    db: AsyncSession = Depends(get_db)
):
    """获取特定商机的所有数据采集任务"""
    try:
        from uuid import UUID

        try:
            opportunity_uuid = UUID(opportunity_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid opportunity ID format")

        query = select(DataCollectionTask).where(
            DataCollectionTask.opportunity_id == opportunity_uuid
        )

        if not include_history:
            query = query.where(
                DataCollectionTask.status.in_([
                    TaskStatus.PENDING.value,
                    TaskStatus.RUNNING.value
                ])
            )

        query = query.order_by(DataCollectionTask.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()

        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "active_count": sum(1 for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.RUNNING]),
            "completed_count": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed_count": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "tasks": [task.to_dict() for task in tasks]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取商机任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_task_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取任务统计摘要"""
    try:
        # 总任务数
        total_result = await db.execute(
            select(DataCollectionTask)
        )
        all_tasks = total_result.scalars().all()

        # 按状态统计
        by_status = {}
        for task in all_tasks:
            status = task.status.value if hasattr(task.status, 'value') else task.status
            by_status[status] = by_status.get(status, 0) + 1

        # 按类型统计
        by_type = {}
        for task in all_tasks:
            by_type[task.task_type] = by_type.get(task.task_type, 0) + 1

        # 活跃任务（最近24小时）
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_tasks = [t for t in all_tasks if t.created_at >= yesterday]

        return {
            "success": True,
            "total": len(all_tasks),
            "by_status": by_status,
            "by_type": by_type,
            "active_24h": len(active_tasks),
            "completion_rate": by_status.get('completed', 0) / len(all_tasks) if all_tasks else 0
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _summarize_result(result: Dict[str, Any]) -> str:
    """摘要结果数据"""
    if not result:
        return "无结果"

    # 根据结果类型生成摘要
    if 'products' in result:
        count = len(result.get('products', []))
        return f"采集到 {count} 个产品"
    elif 'articles' in result:
        count = len(result.get('articles', []))
        return f"采集到 {count} 篇文章"
    elif 'competition_data' in result:
        return "竞争分析完成"
    elif 'price_history' in result:
        return "价格历史采集完成"
    else:
        return "数据采集完成"
