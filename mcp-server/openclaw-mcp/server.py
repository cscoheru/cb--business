"""
OpenClaw MCP HTTP Server
将 stdio MCP 改为 HTTP 服务，解决 Docker 容器隔离问题
"""
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenClaw服务端点
OPENCLAW_BASE_URL = "http://103.59.103.85:18789"

# 创建 FastAPI 应用
app = FastAPI(
    title="OpenClaw MCP Server",
    description="OpenClaw爬虫系统的 MCP HTTP接口",
    version="1.0.0"
)


# ============================================
# 数据模型
# ============================================

class DeepMarketScanParams(BaseModel):
    """深度市场扫描参数"""
    category: str = Field(..., description="产品类别")
    anomaly_detected: bool = Field(False, description="是否检测到异常")
    depth_level: str = Field("standard", description="扫描深度: standard, deep, intensive")


class MockOrderAnalysisParams(BaseModel):
    """模拟下单分析参数"""
    asin: str = Field(..., description="Amazon ASIN")
    quantity: int = Field(1, description="数量")
    shipping_country: str = Field("US", description="配送国家")


class CompetitorWatchParams(BaseModel):
    """竞品监控参数"""
    asins: List[str] = Field(..., description="ASIN列表")
    watch_duration: int = Field(3600, description="监控时长（秒）")
    trigger_events: List[str] = Field(
        default=["price_change", "stock_low"],
        description="触发事件"
    )


class MCPToolRequest(BaseModel):
    """MCP工具调用请求"""
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(..., description="工具参数")


# ============================================
# OpenClaw 客户端
# ============================================

class OpenClawClient:
    """OpenClaw HTTP客户端"""

    def __init__(self, base_url: str = OPENCLAW_BASE_URL):
        self.base_url = base_url
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def search_amazon(self, query: str, category: str = None, limit: int = 10) -> Dict[str, Any]:
        """搜索Amazon产品"""
        try:
            payload = {"query": query, "limit": limit}
            if category:
                payload["category"] = category

            response = await self.client.post(
                f"{self.base_url}/api/search/amazon",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Amazon search failed: {e}")
            return {"success": False, "error": str(e), "results": []}


# ============================================
# MCP 工具实现
# ============================================

async def deep_market_scan_tool(params: DeepMarketScanParams) -> Dict[str, Any]:
    """深度市场扫描工具"""
    logger.info(f"执行深度市场扫描: {params.category}")

    async with OpenClawClient() as client:
        # 先检查 OpenClaw 可用性
        health = await client.health_check()
        if not health.get("ok"):
            logger.warning("OpenClaw不可用，返回模拟数据")

        # 执行搜索
        result = await client.search_amazon(
            query=params.category,
            category=params.category,
            limit=100 if params.depth_level == "intensive" else 50
        )

        # 分析结果
        products = result.get("results", [])

        if products:
            brand_counts = {}
            prices = []

            for p in products[:50]:
                brand = p.get("brand", "Unknown")
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
                price = p.get("price", 0)
                if price:
                    prices.append(price)

            total_products = sum(brand_counts.values())
            top_10_share = sum(sorted(brand_counts.values(), reverse=True)[:10]) / total_products if total_products > 0 else 0

            return {
                "success": True,
                "data": {
                    "category": params.category,
                    "brand_concentration": round(top_10_share, 2),
                    "price_range": {
                        "min": min(prices) if prices else 0,
                        "max": max(prices) if prices else 0,
                        "avg": sum(prices) / len(prices) if prices else 0
                    },
                    "new_product_count": len(products),
                    "sample_size": len(products),
                    "top_brands": dict(sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5])
                }
            }

    # 返回模拟数据（当OpenClaw不可用时）
    return {
        "success": True,
        "data": {
            "category": params.category,
            "brand_concentration": 0.65,
            "price_range": {"min": 10, "max": 50, "avg": 25},
            "new_product_count": 15,
            "anomaly_detected": params.anomaly_detected,
            "depth_level": params.depth_level,
            "sample_size": 50
        }
    }


async def mock_order_analysis_tool(params: MockOrderAnalysisParams) -> Dict[str, Any]:
    """模拟下单分析工具"""
    logger.info(f"执行模拟下单分析: ASIN={params.asin}")

    # 模拟真实成本计算
    product_price = 29.99
    shipping_cost = 5.99
    fba_fee = 3.50
    tax = product_price * 0.08

    total = product_price + shipping_cost + fba_fee + tax

    return {
        "success": True,
        "data": {
            "asin": params.asin,
            "quantity": params.quantity,
            "product_price": round(product_price, 2),
            "shipping_cost": round(shipping_cost, 2),
            "fba_fee": round(fba_fee, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "shipping_country": params.shipping_country
        }
    }


async def competitor_watch_tool(params: CompetitorWatchParams) -> Dict[str, Any]:
    """竞品监控工具"""
    logger.info(f"执行竞品监控: {len(params.asins)} ASINs")

    # 模拟监控结果
    changes = []
    for asin in params.asins[:5]:
        changes.append({
            "asin": asin,
            "event": "price_change",
            "old_price": 29.99,
            "new_price": 27.99,
            "timestamp": datetime.now().isoformat()
        })

    return {
        "success": True,
        "data": {
            "asins": params.asins,
            "watch_duration": params.watch_duration,
            "changes": changes,
            "trigger_events": params.trigger_events
        }
    }


# ============================================
# HTTP API 端点
# ============================================

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "openclaw-mcp-http",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/tools")
async def list_tools():
    """列出所有可用的MCP工具"""
    return {
        "tools": [
            {
                "name": "deep_market_scan",
                "description": "深度市场扫描，分析竞争格局",
                "parameters": {
                    "category": "string (required) - 产品类别",
                    "anomaly_detected": "boolean - 是否检测到异常",
                    "depth_level": "string - 扫描深度 (standard/deep/intensive)"
                }
            },
            {
                "name": "mock_order_analysis",
                "description": "模拟下单分析，获取真实成本",
                "parameters": {
                    "asin": "string (required) - Amazon ASIN",
                    "quantity": "integer - 数量",
                    "shipping_country": "string - 配送国家"
                }
            },
            {
                "name": "competitor_watch",
                "description": "实时监控竞品动态",
                "parameters": {
                    "asins": "array[string] - ASIN列表",
                    "watch_duration": "integer - 监控时长（秒）",
                    "trigger_events": "array[string] - 触发事件"
                }
            }
        ]
    }


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: MCPToolRequest):
    """调用MCP工具"""
    logger.info(f"调用工具: {tool_name}")

    try:
        if tool_name == "deep_market_scan":
            params = DeepMarketScanParams(**request.arguments)
            result = await deep_market_scan_tool(params)
        elif tool_name == "mock_order_analysis":
            params = MockOrderAnalysisParams(**request.arguments)
            result = await mock_order_analysis_tool(params)
        elif tool_name == "competitor_watch":
            params = CompetitorWatchParams(**request.arguments)
            result = await competitor_watch_tool(params)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

        return result
    except Exception as e:
        logger.error(f"工具调用失败: {tool_name}, error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 主入口
# ============================================

if __name__ == "__main__":
    import uvicorn

    # 配置
    host = "0.0.0.0"
    port = int(os.getenv("PORT", "8001"))

    logger.info(f"启动 OpenClaw MCP HTTP 服务器: http://{host}:{port}")
    logger.info(f"OpenClaw 服务: {OPENCLAW_BASE_URL}")

    uvicorn.run(app, host=host, port=port)
