# api/openclaw_integration.py
"""OpenClaw集成API - FastAPI与OpenClaw的双向通信

提供FastAPI与OpenClaw Gateway之间的集成接口：
1. 手动触发OpenClaw Channel执行
2. 查询OpenClaw Channels状态
3. 获取OpenClaw执行日志
4. 健康检查

部署信息:
- OpenClaw Gateway: http://103.59.103.85:18789
- 认证Token: VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import httpx
from enum import Enum

from config.database import AsyncSessionLocal, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/openclaw", tags=["openclaw"])

# OpenClaw配置
OPENCLAW_BASE_URL = "http://103.59.103.85:18789"
OPENCLAW_AUTH_TOKEN = "VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30"
OPENCLAW_TIMEOUT = 300.0  # 5分钟超时


# ============================================================================
# Enums and Models
# ============================================================================

class ChannelStatus(str, Enum):
    """Channel状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    DISABLED = "disabled"


class ChannelInfo(BaseModel):
    """Channel信息"""
    id: str
    name: str
    status: ChannelStatus
    enabled: bool
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    last_result: Optional[Dict[str, Any]] = None


class TriggerChannelRequest(BaseModel):
    """触发Channel请求"""
    channel_id: str = Field(..., description="Channel ID")
    params: Dict[str, Any] = Field(
        default={},
        description="传递给Channel的参数"
    )


class TriggerChannelResponse(BaseModel):
    """触发Channel响应"""
    success: bool
    channel_id: str
    execution_id: str
    message: str


class ChannelsStatusResponse(BaseModel):
    """Channels状态响应"""
    success: bool
    total_channels: int
    active_channels: int
    channels: List[ChannelInfo]


# ============================================================================
# Internal Helper Functions
# ============================================================================

async def _call_openclaw_api(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    内部函数: 调用OpenClaw API

    Args:
        method: HTTP方法 (GET, POST, etc.)
        endpoint: API端点路径
        data: 请求体数据
        params: URL查询参数

    Returns:
        API响应数据

    Raises:
        HTTPException: 如果API调用失败
    """
    url = f"{OPENCLAW_BASE_URL}{endpoint}"

    headers = {
        "Authorization": f"Bearer {OPENCLAW_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=OPENCLAW_TIMEOUT) as client:
            if method.upper() == "GET":
                response = await client.get(
                    url,
                    headers=headers,
                    params=params
                )
            elif method.upper() == "POST":
                response = await client.post(
                    url,
                    headers=headers,
                    json=data
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported HTTP method: {method}"
                )

            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException:
        logger.error(f"OpenClaw API timeout: {url}")
        raise HTTPException(
            status_code=504,
            detail="OpenClaw API request timed out"
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"OpenClaw API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"OpenClaw API error: {e.response.text}"
        )

    except Exception as e:
        logger.error(f"Failed to call OpenClaw API: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to communicate with OpenClaw: {str(e)}"
        )


# ============================================================================
# Public API Endpoints
# ============================================================================

@router.post("/trigger/{channel_id}", response_model=TriggerChannelResponse)
async def trigger_openclaw_channel(
    channel_id: str,
    request: TriggerChannelRequest = None
):
    """
    手动触发OpenClaw Channel执行

    用途:
    - 立即执行某个Channel (不等待下次调度)
    - 传递自定义参数给Channel
    - 测试Channel功能

    示例:
        POST /api/v1/openclaw/trigger/rss-crawler
        POST /api/v1/openclaw/trigger/oxylabs-monitor
        POST /api/v1/openclaw/trigger/trend-discovery

    Args:
        channel_id: Channel ID (如 rss-crawler, oxylabs-monitor)
        request: 可选的触发参数

    Returns:
        执行结果和execution_id
    """
    try:
        logger.info(f"Manually triggering OpenClaw channel: {channel_id}")

        # 如果没有提供request，创建一个默认的
        if request is None:
            request = TriggerChannelRequest(channel_id=channel_id)

        # 调用OpenClaw API触发Channel
        response_data = await _call_openclaw_api(
            method="POST",
            endpoint="/api/channels/trigger",
            data={
                "channel": channel_id,
                "params": request.params
            }
        )

        logger.info(f"Channel {channel_id} triggered: {response_data.get('execution_id')}")

        return TriggerChannelResponse(
            success=response_data.get("success", True),
            channel_id=channel_id,
            execution_id=response_data.get("execution_id", ""),
            message=response_data.get("message", "Channel triggered successfully")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger channel {channel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger channel: {str(e)}"
        )


@router.get("/channels/status", response_model=ChannelsStatusResponse)
async def get_channels_status():
    """
    获取所有OpenClaw Channels的状态

    用途:
    - 监控Channels健康状态
    - 查看最近执行结果
    - 检查下次执行时间

    Returns:
        所有Channels的状态信息
    """
    try:
        response_data = await _call_openclaw_api(
            method="GET",
            endpoint="/api/channels"
        )

        channels_data = response_data.get("channels", [])

        # 转换为ChannelInfo对象列表
        channels = []
        active_count = 0

        for ch in channels_data:
            status = ChannelStatus.IDLE
            if ch.get("running"):
                status = ChannelStatus.RUNNING
            elif ch.get("last_result", {}).get("success"):
                status = ChannelStatus.SUCCESS
            elif ch.get("last_result", {}).get("error"):
                status = ChannelStatus.FAILED
            elif not ch.get("enabled"):
                status = ChannelStatus.DISABLED

            if status not in [ChannelStatus.DISABLED, ChannelStatus.FAILED]:
                active_count += 1

            channels.append(ChannelInfo(
                id=ch.get("id", ""),
                name=ch.get("name", ""),
                status=status,
                enabled=ch.get("enabled", True),
                last_run=ch.get("last_run"),
                next_run=ch.get("next_run"),
                last_result=ch.get("last_result")
            ))

        return ChannelsStatusResponse(
            success=True,
            total_channels=len(channels),
            active_channels=active_count,
            channels=channels
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get channels status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get channels status: {str(e)}"
        )


@router.get("/channels/{channel_id}/logs")
async def get_channel_logs(
    channel_id: str,
    limit: int = Query(50, ge=1, le=500, description="日志条数限制")
):
    """
    获取指定Channel的执行日志

    Args:
        channel_id: Channel ID
        limit: 返回的日志条数

    Returns:
        Channel日志数据
    """
    try:
        response_data = await _call_openclaw_api(
            method="GET",
            endpoint=f"/api/channels/{channel_id}/logs",
            params={"limit": limit}
        )

        return {
            "success": True,
            "channel_id": channel_id,
            "logs": response_data.get("logs", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get channel logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get channel logs: {str(e)}"
        )


@router.get("/health")
async def check_openclaw_health():
    """
    检查OpenClaw Gateway健康状态

    Returns:
        OpenClaw服务健康信息
    """
    try:
        response_data = await _call_openclaw_api(
            method="GET",
            endpoint="/health"
        )

        return {
            "success": True,
            "openclaw_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "openclaw_info": response_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OpenClaw health check failed: {e}")
        return {
            "success": False,
            "openclaw_status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/sync/now")
async def trigger_immediate_sync():
    """
    触发立即同步所有启用的Channels

    用途:
    - 立即更新数据
    - 手动触发数据刷新
    - 测试所有Channels

    Returns:
        同步任务ID和状态
    """
    try:
        # 先获取所有Channels状态
        status_response = await get_channels_status()
        enabled_channels = [
            ch for ch in status_response.channels
            if ch.enabled
        ]

        logger.info(f"Triggering immediate sync for {len(enabled_channels)} channels")

        # 触发所有启用的Channel
        results = []
        for channel in enabled_channels:
            try:
                result = await trigger_openclaw_channel(
                    channel_id=channel.id,
                    request=TriggerChannelRequest(channel_id=channel.id)
                )
                results.append({
                    "channel": channel.id,
                    "success": result.success,
                    "execution_id": result.execution_id
                })
            except Exception as e:
                logger.error(f"Failed to trigger channel {channel.id}: {e}")
                results.append({
                    "channel": channel.id,
                    "success": False,
                    "error": str(e)
                })

        success_count = sum(1 for r in results if r.get("success"))

        return {
            "success": True,
            "total_channels": len(enabled_channels),
            "successful_triggers": success_count,
            "failed_triggers": len(enabled_channels) - success_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"Failed to trigger immediate sync: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger immediate sync: {str(e)}"
        )


@router.get("/config")
async def get_openclaw_config():
    """
    获取OpenClaw配置信息 (脱敏)

    用于调试和监控，不返回敏感信息

    Returns:
        OpenClaw配置摘要
    """
    return {
        "success": True,
        "config": {
            "base_url": OPENCLAW_BASE_URL,
            "timeout": OPENCLAW_TIMEOUT,
            "auth_configured": bool(OPENCLAW_AUTH_TOKEN),
            "auth_token_prefix": OPENCLAW_AUTH_TOKEN[:10] + "..." if OPENCLAW_AUTH_TOKEN else None
        }
    }


# ============================================================================
# Callback Endpoints
# ============================================================================

class ChannelCallbackRequest(BaseModel):
    """OpenClaw Channel执行完成回调请求"""
    channel_id: str = Field(..., description="执行的Channel ID")
    execution_id: str = Field(..., description="执行ID")
    status: str = Field(..., description="执行状态: success, failed, partial")
    started_at: str = Field(..., description="开始时间")
    completed_at: str = Field(..., description="完成时间")
    duration_ms: int = Field(..., description="执行时长(毫秒)")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果数据")
    error: Optional[Dict[str, Any]] = Field(None, description="错误信息")
    stats: Optional[Dict[str, Any]] = Field(None, description="统计信息")


class ChannelCallbackResponse(BaseModel):
    """回调响应"""
    success: bool
    message: str
    processed: bool = False  # 是否已触发后续处理


@router.post("/callback/channel", response_model=ChannelCallbackResponse)
async def handle_channel_callback(
    request: ChannelCallbackRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    OpenClaw Channel执行完成回调端点

    当OpenClaw Channel完成执行后，OpenClaw Gateway会调用此端点通知FastAPI。

    处理流程:
    1. 验证回调签名 (TODO: 添加签名验证)
    2. 记录执行结果到数据库
    3. 更新相关的DataCollectionTask状态
    4. 如果成功，触发智能编排服务的后续处理

    示例回调数据:
    ```json
    {
      "channel_id": "rss-crawler",
      "execution_id": "exec-1234567890",
      "status": "success",
      "started_at": "2026-03-14T10:00:00Z",
      "completed_at": "2026-03-14T10:05:00Z",
      "duration_ms": 300000,
      "result": {
        "total_fetched": 70,
        "total_pushed": 70,
        "sources": 5
      },
      "stats": {
        "sources": 5,
        "successful": 4,
        "failed": 1
      }
    }
    ```

    Args:
        request: Channel执行结果
        background_tasks: FastAPI后台任务
        db: 数据库session

    Returns:
        处理结果确认
    """
    try:
        logger.info(
            f"📬 收到OpenClaw Channel回调: {request.channel_id} "
            f"(执行ID: {request.execution_id}, 状态: {request.status})"
        )

        # 1. 记录回调日志到数据库
        from models.article import CrawlLog
        from uuid import uuid4

        log_entry = CrawlLog(
            id=uuid4(),
            source=f"openclaw-{request.channel_id}",
            status=request.status,
            articles_count=request.stats.get('total_fetched', 0) if request.stats else 0,
            error_message=str(request.error) if request.error else None,
            completed_at=datetime.fromisoformat(request.completed_at.replace('Z', '+00:00'))
        )

        db.add(log_entry)
        await db.commit()

        # 2. 查找并更新相关的DataCollectionTask
        task_updated = False
        try:
            from models.business_opportunity import DataCollectionTask
            from sqlalchemy import select

            # 查找包含此execution_id的任务
            result = await db.execute(
                select(DataCollectionTask).where(
                    DataCollectionTask.ai_request.contains(request.execution_id)
                )
            )
            tasks = result.scalars().all()

            if tasks:
                task = tasks[0]

                # 更新任务状态
                if request.status == "success":
                    task.result = request.result
                    task.completed_at = datetime.utcnow()
                    task.status = "completed"
                else:
                    task.error_message = str(request.error) if request.error else "Channel execution failed"
                    task.completed_at = datetime.utcnow()
                    task.status = "failed"

                await db.commit()
                task_updated = True

                logger.info(f"✅ 更新数据采集任务: {task.id}")

                # 3. 如果任务成功，触发智能编排服务处理结果
                if request.status == "success" and request.result:
                    background_tasks.add_task(
                        _process_channel_result,
                        str(task.id),
                        request.result,
                        db
                    )

        except Exception as e:
            logger.warning(f"Failed to update DataCollectionTask: {e}")

        # 4. 记录Channel执行历史
        await _record_channel_execution_history(request, db)

        return ChannelCallbackResponse(
            success=True,
            message="Callback processed successfully",
            processed=task_updated
        )

    except Exception as e:
        logger.error(f"Failed to process channel callback: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process callback: {str(e)}"
        )


async def _process_channel_result(
    task_id: str,
    result: Dict[str, Any],
    db: AsyncSessionLocal
):
    """
    后台任务: 处理Channel执行结果

    当OpenClaw Channel成功完成数据采集后，此函数会被调用来处理结果。

    Args:
        task_id: 数据采集任务ID
        result: Channel执行结果
        db: 数据库session (新的session用于后台任务)
    """
    try:
        logger.info(f"🔄 处理Channel结果: 任务 {task_id}")

        # 调用智能编排服务处理采集结果
        from services.smart_orchestrator import get_orchestrator

        orchestrator = get_orchestrator()

        # 构造回调数据格式
        callback_data = {
            "request_id": task_id,
            "status": "completed",
            "result": result
        }

        await orchestrator.on_collection_complete(callback_data, db)

        logger.info(f"✅ Channel结果处理完成: 任务 {task_id}")

    except Exception as e:
        logger.error(f"Failed to process channel result for task {task_id}: {e}")


async def _record_channel_execution_history(
    request: ChannelCallbackRequest,
    db: AsyncSessionLocal
):
    """
    记录Channel执行历史到数据库

    用于分析和监控Channel性能。
    """
    try:
        # 这里可以记录到一个专门的channel_execution_history表
        # 或者使用Redis缓存最近的历史记录
        pass

    except Exception as e:
        logger.warning(f"Failed to record channel execution history: {e}")


@router.get("/callback/history")
async def get_callback_history(
    channel_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取Channel回调历史记录

    Args:
        channel_id: 可选，过滤特定Channel的历史
        limit: 返回的记录数

    Returns:
        历史记录列表
    """
    try:
        from models.article import CrawlLog
        from sqlalchemy import select, desc

        query = select(CrawlLog)

        if channel_id:
            query = query.where(CrawlLog.source == f"openclaw-{channel_id}")

        query = query.order_by(desc(CrawlLog.started_at)).limit(limit)

        result = await db.execute(query)
        logs = result.scalars().all()

        return {
            "success": True,
            "count": len(logs),
            "history": [
                {
                    "source": log.source,
                    "status": log.status,
                    "articles_count": log.articles_count,
                    "error_message": log.error_message,
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None
                }
                for log in logs
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get callback history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {str(e)}"
        )
