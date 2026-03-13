# services/data_sources/oxylabs_source.py
"""Oxylabs数据源适配器 - 实现DataSourceProtocol接口

将OxylabsClient包装成符合DataSourceProtocol接口的适配器
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from datetime import timezone

from crawler.products.oxylabs_client import OxylabsClient
from services.data_source_registry import (
    DataSourceProtocol,
    DataSourceMetadata,
    DataSourceStatus
)

logger = logging.getLogger(__name__)


class OxylabsDataSource:
    """Oxylabs数据源适配器"""

    def __init__(self, enabled: bool = True):
        self._client: Optional[OxylabsClient] = None
        self._enabled = enabled
        self._metadata = DataSourceMetadata(
            name="Oxylabs Amazon API",
            description="Amazon产品数据、价格、评分",
            version="1.0.0",
            reliability=0.95,  # Oxylabs声明的高可靠性
            latency_ms=3000,   # 平均3秒响应时间
            cost_per_request=0.005,  # 约每次请求$0.005
            status=DataSourceStatus.ACTIVE if enabled else DataSourceStatus.DISABLED
        )

    async def _get_client(self) -> OxylabsClient:
        """获取或创建客户端"""
        if self._client is None:
            self._client = OxylabsClient()
        return self._client

    async def fetch_market_data(
        self,
        category: str,
        query: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取Amazon市场数据

        Returns:
            标准化的数据格式
        """
        client = await self._get_client()

        try:
            # 调用Oxylabs API
            products = await client.search_amazon(
                query=query,
                domain="com",
                limit=limit,
                use_cache=False  # 由上层控制缓存
            )

            # 标准化返回格式
            result = {
                "source": "oxylabs",
                "products": self._normalize_products(products),
                "trends": [],  # Oxylabs不提供趋势数据
                "sentiments": [],  # 可以后续添加评论情感分析
                "metadata": {
                    "fetch_time": datetime.now(timezone.utc).isoformat(),
                    "reliability": self._metadata.reliability,
                    "data_points": len(products),
                    "source_type": "ecommerce_platform",
                    "region": "US",
                    "currency": "USD"
                }
            }

            # 更新成功状态
            self._metadata.last_success = datetime.now(timezone.utc)
            self._metadata.status = DataSourceStatus.ACTIVE

            logger.info(f"✅ Oxylabs获取到 {len(products)} 个产品")
            return result

        except Exception as e:
            self._metadata.last_error = str(e)
            self._metadata.status = DataSourceStatus.ERROR
            logger.error(f"❌ Oxylabs获取失败: {e}")
            raise

    def _normalize_products(self, products: List[Dict]) -> List[Dict[str, Any]]:
        """标准化产品数据格式"""
        normalized = []

        for product in products:
            # 提取关键字段，处理可能的缺失值
            normalized_product = {
                "id": product.get("asin", ""),
                "title": product.get("title", "Unknown"),
                "price": product.get("price", 0),
                "rating": product.get("rating", 0),
                "reviews_count": product.get("reviews_count", 0),
                "url": product.get("url", ""),
                "image": product.get("image", ""),
                "brand": product.get("brand", ""),
                "source": "oxylabs_amazon"
            }
            normalized.append(normalized_product)

        return normalized

    def get_metadata(self) -> DataSourceMetadata:
        """获取数据源元数据"""
        return self._metadata

    async def health_check(self) -> bool:
        """健康检查 - 尝试获取一个产品"""
        try:
            client = await self._get_client()
            result = await client.search_amazon(query="wireless earbuds", limit=1)
            return len(result) > 0
        except Exception as e:
            logger.warning(f"Oxylabs健康检查失败: {e}")
            return False

    def is_enabled(self) -> bool:
        """是否启用"""
        return self._enabled

    def enable(self):
        """启用数据源"""
        self._enabled = True
        self._metadata.status = DataSourceStatus.ACTIVE
        logger.info("✅ Oxylabs数据源已启用")

    def disable(self):
        """禁用数据源"""
        self._enabled = False
        self._metadata.status = DataSourceStatus.DISABLED
        logger.info("❌ Oxylabs数据源已禁用")

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.close()
            self._client = None
