"""
MCP客户端配置 - FastAPI连接OpenClaw MCP Server

配置说明:
1. OpenClaw MCP Server部署在HK服务器 (HTTP模式)
2. FastAPI通过HTTP协议连接MCP
3. AI可以通过MCP直接调用OpenClaw技能
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP SDK未安装，OpenClaw MCP功能将不可用")

logger = logging.getLogger(__name__)

# MCP Server配置
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://openclaw-mcp-server:8001")


class OpenClawMCPClient:
    """
    OpenClaw MCP客户端

    连接到OpenClaw MCP Server，让FastAPI能够调用OpenClaw的技能
    """

    def __init__(
        self,
        server_command: str = "python3",
        server_args: List[str] = None,
        env: Dict[str, str] = None
    ):
        """
        初始化MCP客户端

        Args:
            server_command: 启动MCP服务器的命令
            server_args: 命令参数
            env: 环境变量
        """
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK未安装，请运行: pip install mcp")

        self.server_command = server_command
        self.server_args = server_args or ["-m", "openclaw_mcp.main"]
        self.env = env or {
            "OPENCLAW_BASE_URL": "http://103.59.103.85:18789",
            "LOG_LEVEL": "INFO",
            "PYTHONPATH": "/root/openclaw-mcp"
        }

        self.session: Optional[ClientSession] = None
        self.stdio_context = None
        self._connected = False

    async def connect(self) -> bool:
        """
        连接到MCP服务器

        Returns:
            连接是否成功
        """
        try:
            if self._connected:
                return True

            logger.info(f"连接到OpenClaw MCP Server: {self.server_command}")

            # 创建服务器参数
            server_params = StdioServerParameters(
                command=self.server_command,
                args=self.server_args,
                env=self.env
            )

            # 创建stdio客户端上下文
            self.stdio_context = stdio_client(server_params)

            # 进入上下文，创建会话
            streams = await self.stdio_context.__aenter__()

            # 创建ClientSession
            self.session = ClientSession(streams[0], streams[1])

            # 初始化会话
            await self.session.initialize()

            self._connected = True
            logger.info("✅ OpenClaw MCP连接成功")

            # 记录可用工具
            tools = await self.session.list_tools()
            logger.info(f"可用工具: {[tool.name for tool in tools.tools]}")

            return True

        except Exception as e:
            logger.error(f"❌ 连接OpenClaw MCP失败: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """断开MCP连接"""
        if self.stdio_context:
            await self.stdio_context.__aexit__(None, None, None)
            self._connected = False
            logger.info("OpenClaw MCP已断开")

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> List[Any]:
        """
        调用MCP工具 (OpenClaw技能)

        Args:
            name: 工具/技能名称
            arguments: 技能参数

        Returns:
            工具执行结果列表
        """
        if not self._connected:
            if not await self.connect():
                raise ConnectionError("MCP未连接")

        try:
            logger.info(f"调用MCP工具: {name}, 参数: {json.dumps(arguments, ensure_ascii=False)}")

            result = await self.session.call_tool(name, arguments)

            logger.info(f"MCP工具返回: {len(result)}个结果")
            return result

        except Exception as e:
            logger.error(f"调用MCP工具失败: {e}")
            raise

    async def list_tools(self) -> List[str]:
        """列出所有可用的工具"""
        if not self._connected:
            if not await self.connect():
                return []

        try:
            tools_response = await self.session.list_tools()
            return [tool.name for tool in tools_response.tools]
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            return []

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()


class HTTPMCPClient:
    """
    HTTP MCP客户端

    通过HTTP协议连接到OpenClaw MCP Server
    解决Docker容器隔离问题
    """

    def __init__(self, base_url: str = None):
        """
        初始化HTTP MCP客户端

        Args:
            base_url: MCP服务器URL
        """
        self.base_url = base_url or MCP_SERVER_URL
        self.client: Optional[httpx.AsyncClient] = None
        self._connected = False

    async def connect(self) -> bool:
        """连接到MCP服务器 (HTTP健康检查)"""
        try:
            if self._connected:
                return True

            self.client = httpx.AsyncClient(timeout=60.0)

            # 健康检查
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()

            self._connected = True
            logger.info(f"✅ HTTP MCP连接成功: {self.base_url}")

            # 记录可用工具
            tools_response = await self.client.get(f"{self.base_url}/tools")
            if tools_response.status_code == 200:
                tools_data = tools_response.json()
                tool_names = [t["name"] for t in tools_data.get("tools", [])]
                logger.info(f"可用工具: {tool_names}")

            return True

        except Exception as e:
            logger.error(f"❌ HTTP MCP连接失败: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """断开HTTP连接"""
        if self.client:
            await self.client.aclose()
            self._connected = False
            logger.info("HTTP MCP已断开")

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用MCP工具 (OpenClaw技能)

        Args:
            name: 工具/技能名称
            arguments: 技能参数

        Returns:
            工具执行结果
        """
        if not self._connected:
            if not await self.connect():
                raise ConnectionError("HTTP MCP未连接")

        try:
            logger.info(f"调用HTTP MCP工具: {name}, 参数: {json.dumps(arguments, ensure_ascii=False)}")

            response = await self.client.post(
                f"{self.base_url}/tools/{name}",
                json={"name": name, "arguments": arguments},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"HTTP MCP工具返回: {result.get('success')}")
            return result

        except Exception as e:
            logger.error(f"调用HTTP MCP工具失败: {e}")
            raise

    async def list_tools(self) -> List[str]:
        """列出所有可用的工具"""
        if not self._connected:
            if not await self.connect():
                return []

        try:
            response = await self.client.get(f"{self.base_url}/tools")
            if response.status_code == 200:
                tools_data = response.json()
                return [t["name"] for t in tools_data.get("tools", [])]
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")

        return []

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()


# 全局单例
openclaw_mcp: Optional[OpenClawMCPClient] = None


def get_mcp_client() -> OpenClawMCPClient:
    """
    获取全局MCP客户端单例

    Returns:
        OpenClawMCPClient实例 (HTTP模式优先)
    """
    global openclaw_mcp

    if openclaw_mcp is None:
        # 优先使用HTTP MCP客户端
        openclaw_mcp = HTTPMCPClient()
        logger.info("使用HTTP MCP客户端")

    return openclaw_mcp


class MockMCPClient:
    """
    Mock MCP客户端 (当MCP不可用时使用)

    返回模拟数据，确保系统不会因MCP不可用而崩溃
    """

    def __init__(self):
        self._connected = False

    async def connect(self) -> bool:
        logger.warning("使用Mock MCP客户端")
        self._connected = True
        return True

    async def disconnect(self):
        self._connected = False

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """返回模拟数据"""
        logger.info(f"Mock MCP调用: {name}")

        mock_responses = {
            "deep_market_scan": {
                "success": True,
                "data": {
                    "category": arguments.get("category", "unknown"),
                    "brand_concentration": 0.65,
                    "price_range": {"min": 10, "max": 50, "avg": 25},
                    "new_product_count": 15,
                    "competition_level": "medium"
                }
            },
            "mock_order_analysis": {
                "success": True,
                "data": {
                    "asin": arguments.get("asin", ""),
                    "product_price": 29.99,
                    "shipping_cost": 5.99,
                    "fba_fee": 3.50,
                    "tax": 2.40,
                    "total": 41.88
                }
            },
            "competitor_watch": {
                "success": True,
                "data": {
                    "asins": arguments.get("asins", []),
                    "changes": [],
                    "watch_duration": arguments.get("watch_duration", 3600)
                }
            }
        }

        return mock_responses.get(name, {"success": True, "data": {}})

    async def list_tools(self) -> List[str]:
        return ["deep_market_scan", "mock_order_analysis", "competitor_watch"]

    def is_connected(self) -> bool:
        return self._connected


# 便捷函数
async def call_openclaw_skill(
    skill_name: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    便捷函数：调用OpenClaw技能

    Args:
        skill_name: 技能名称
        params: 技能参数

    Returns:
        技能执行结果
    """
    client = get_mcp_client()

    if not client.is_connected():
        await client.connect()

    result = await client.call_tool(skill_name, params)

    # HTTP MCP客户端返回dict，stdio返回list
    if isinstance(result, dict):
        return result
    elif isinstance(result, list) and len(result) > 0:
        # 兼容stdio格式
        text_content = result[0]
        if hasattr(text_content, 'text'):
            return json.loads(text_content.text)

    return {"success": False, "error": "无返回结果"}
