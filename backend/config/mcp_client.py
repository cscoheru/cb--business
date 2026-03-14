"""
MCP客户端配置 - FastAPI连接OpenClaw MCP Server

配置说明:
1. OpenClaw MCP Server部署在HK服务器
2. FastAPI通过stdio协议连接MCP
3. AI可以通过MCP直接调用OpenClaw技能
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP SDK未安装，OpenClaw MCP功能将不可用")

logger = logging.getLogger(__name__)


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


# 全局单例
openclaw_mcp: Optional[OpenClawMCPClient] = None


def get_mcp_client() -> OpenClawMCPClient:
    """
    获取全局MCP客户端单例

    Returns:
        OpenClawMCPClient实例
    """
    global openclaw_mcp

    if openclaw_mcp is None:
        if not MCP_AVAILABLE:
            logger.warning("MCP SDK未安装，返回Mock客户端")
            openclaw_mcp = MockMCPClient()
        else:
            openclaw_mcp = OpenClawMCPClient()

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

    async def call_tool(self, name: str, arguments: Dict[str, Any]):
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

        response = mock_responses.get(name, {"success": True, "data": {}})

        # 返回格式与真实MCP一致
        from mcp.types import TextContent
        return [TextContent(
            type="text",
            text=json.dumps(response, ensure_ascii=False)
        )]

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

    # 解析结果
    import json
    if result and len(result) > 0:
        text_content = result[0]
        if hasattr(text_content, 'text'):
            return json.loads(text_content.text)

    return {"success": False, "error": "无返回结果"}
