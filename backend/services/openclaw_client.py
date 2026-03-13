# services/openclaw_client.py
"""OpenClaw Gateway客户端封装

提供Python风格的接口与OpenClaw Gateway通信，
简化FastAPI服务与OpenClaw的集成。

主要功能:
- 触发Channel执行
- 查询Channel状态
- 批量写入数据到PostgreSQL
- 健康检查

部署信息:
- OpenClaw Gateway: http://103.59.103.85:18789
- 认证Token: VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger(__name__)

# OpenClaw配置
OPENCLAW_BASE_URL = "http://103.59.103.85:18789"
OPENCLAW_AUTH_TOKEN = "VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30"
DEFAULT_TIMEOUT = 300.0  # 5分钟


class ChannelStatus(str, Enum):
    """Channel状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    DISABLED = "disabled"


class OpenClawClient:
    """OpenClaw Gateway客户端

    提供与OpenClaw Gateway通信的统一接口
    """

    def __init__(
        self,
        base_url: str = OPENCLAW_BASE_URL,
        auth_token: str = OPENCLAW_AUTH_TOKEN,
        timeout: float = DEFAULT_TIMEOUT
    ):
        """
        初始化OpenClaw客户端

        Args:
            base_url: OpenClaw Gateway URL
            auth_token: 认证Token
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    async def trigger_channel(
        self,
        channel_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        触发OpenClaw Channel执行

        Args:
            channel_id: Channel ID (如 'rss-crawler', 'oxylabs-monitor')
            params: 传递给Channel的参数

        Returns:
            执行结果，包含execution_id

        Raises:
            httpx.HTTPError: 如果请求失败
        """
        url = f"{self.base_url}/api/channels/trigger"

        payload = {
            "channel": channel_id,
            "params": params or {}
        }

        logger.info(f"Triggering OpenClaw channel: {channel_id}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self._headers,
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Channel {channel_id} triggered, execution_id: {result.get('execution_id')}")

            return result

    async def get_channels_status(self) -> Dict[str, Any]:
        """
        获取所有Channels的状态

        Returns:
            Channels状态列表

        Raises:
            httpx.HTTPError: 如果请求失败
        """
        url = f"{self.base_url}/api/channels"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                headers=self._headers
            )
            response.raise_for_status()

            return response.json()

    async def get_channel_logs(
        self,
        channel_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取指定Channel的执行日志

        Args:
            channel_id: Channel ID
            limit: 返回的日志条数

        Returns:
            Channel日志数据

        Raises:
            httpx.HTTPError: 如果请求失败
        """
        url = f"{self.base_url}/api/channels/{channel_id}/logs"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                headers=self._headers,
                params={"limit": limit}
            )
            response.raise_for_status()

            return response.json()

    async def check_health(self) -> Dict[str, Any]:
        """
        检查OpenClaw Gateway健康状态

        Returns:
            健康检查结果

        Raises:
            httpx.HTTPError: 如果请求失败
        """
        url = f"{self.base_url}/health"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                }
        except httpx.HTTPError as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def trigger_all_channels(self) -> Dict[str, Any]:
        """
        触发所有启用的Channels

        Returns:
            触发结果汇总

        Raises:
            httpx.HTTPError: 如果请求失败
        """
        # 先获取所有Channels状态
        status_data = await self.get_channels_status()
        channels = status_data.get("channels", [])

        # 过滤出启用的Channels
        enabled_channels = [
            ch for ch in channels
            if ch.get("enabled", True)
        ]

        logger.info(f"Triggering {len(enabled_channels)} enabled channels")

        # 触发所有启用的Channel
        results = []
        success_count = 0
        failed_count = 0

        for channel in enabled_channels:
            try:
                result = await self.trigger_channel(
                    channel_id=channel.get("id"),
                    params={}
                )
                success_count += 1
                results.append({
                    "channel": channel.get("id"),
                    "success": True,
                    "execution_id": result.get("execution_id")
                })
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to trigger channel {channel.get('id')}: {e}")
                results.append({
                    "channel": channel.get("id"),
                    "success": False,
                    "error": str(e)
                })

        return {
            "total_channels": len(enabled_channels),
            "successful_triggers": success_count,
            "failed_triggers": failed_count,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Convenience Functions (使用全局单例客户端)
# ============================================================================

_global_client: Optional[OpenClawClient] = None


def get_openclaw_client() -> OpenClawClient:
    """
    获取全局OpenClaw客户端单例

    Returns:
        OpenClawClient实例
    """
    global _global_client
    if _global_client is None:
        _global_client = OpenClawClient()
    return _global_client


async def trigger_channel(
    channel_id: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    便捷函数: 触发Channel

    Args:
        channel_id: Channel ID
        params: Channel参数

    Returns:
        执行结果
    """
    client = get_openclaw_client()
    return await client.trigger_channel(channel_id, params)


async def get_channels_status() -> Dict[str, Any]:
    """
    便捷函数: 获取Channels状态

    Returns:
        Channels状态列表
    """
    client = get_openclaw_client()
    return await client.get_channels_status()


async def check_openclaw_health() -> Dict[str, Any]:
    """
    便捷函数: 检查OpenClaw健康状态

    Returns:
        健康检查结果
    """
    client = get_openclaw_client()
    return await client.check_health()


async def trigger_immediate_sync() -> Dict[str, Any]:
    """
    便捷函数: 触发立即同步所有Channels

    Returns:
        同步结果汇总
    """
    client = get_openclaw_client()
    return await client.trigger_all_channels()
