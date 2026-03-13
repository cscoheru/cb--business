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

from fastapi import APIRouter, HTTPException, Depends, Query
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
