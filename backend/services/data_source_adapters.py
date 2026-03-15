# services/data_source_adapters.py
"""数据源适配器 - 将各平台客户端适配到统一的 DataSourceProtocol

架构设计：
1. 每个适配器实现 DataSourceProtocol 接口
2. 统一返回 StandardizedProduct 格式
3. 支持并行调用和错误隔离
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# 导入数据源协议和注册中心
from services.data_source_registry import (
    DataSourceProtocol,
    DataSourceMetadata,
    DataSourceStatus,
)

# 导入标准化产品模型
from models.standardized_product import (
    StandardizedProduct,
    AggregatedProducts,
    Platform,
    Region,
)

logger = logging.getLogger(__name__)


# ==================== Oxylabs 数据源适配器 ====================

class OxylabsDataSource(DataSourceProtocol):
    """Oxylabs 数据源适配器

    支持：
    - Amazon 产品搜索和详情
    - Google Trends 数据
    """

    def __init__(self):
        from crawler.products.oxylabs_client import OxylabsClient, OxylabsConfig
        self.client = OxylabsClient(OxylabsConfig())
        self._enabled = True
        self._status = DataSourceStatus.ACTIVE
        self._last_error: Optional[str] = None
        self._last_success: Optional[datetime] = None

    async def fetch_market_data(
        self,
        category: str,
        query: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取市场数据

        Args:
            category: 品类标识（如 'wireless_earbuds'）
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            标准化的数据格式
        """
        try:
            # 品类到搜索关键词的映射
            category_keywords = {
                "wireless_earbuds": "wireless earbuds",
                "smart_plugs": "smart plug",
                "fitness_trackers": "fitness tracker",
                "phone_chargers": "phone charger",
                "desk_lamps": "LED desk lamp",
                "phone_cases": "phone case",
                "yoga_mats": "yoga mat",
                "coffee_makers": "coffee maker",
                "bluetooth_speakers": "bluetooth speaker",
                "webcams": "webcam",
                "keyboards": "mechanical keyboard",
                "mouse": "wireless mouse",
            }

            search_query = category_keywords.get(category, query or category)

            # 搜索 Amazon
            amazon_products = await self.client.search_amazon(
                query=search_query,
                domain="com",
                limit=limit
            )

            # 标准化产品数据
            standardized_products = []
            for p in amazon_products[:limit]:
                try:
                    product = StandardizedProduct.from_amazon(p, Region.US)
                    standardized_products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to standardize product: {e}")
                    continue

            # 更新状态
            self._last_success = datetime.utcnow()
            self._status = DataSourceStatus.ACTIVE
            self._last_error = None

            return {
                "source": "oxylabs_amazon",
                "products": [p.to_dict() for p in standardized_products],
                "trends": [],  # 可以添加 Google Trends 数据
                "sentiments": [],
                "metadata": {
                    "fetch_time": datetime.utcnow().isoformat(),
                    "reliability": 0.95,
                    "data_points": len(standardized_products),
                    "platform": "amazon",
                    "region": "US",
                }
            }

        except Exception as e:
            logger.error(f"Oxylabs data fetch failed: {e}")
            self._status = DataSourceStatus.ERROR
            self._last_error = str(e)
            raise

    def get_metadata(self) -> DataSourceMetadata:
        """获取数据源元数据"""
        return DataSourceMetadata(
            name="Oxylabs Amazon",
            description="Amazon 市场数据 (通过 Oxylabs API)",
            version="1.0.0",
            reliability=0.95,
            latency_ms=2000,
            cost_per_request=0.01,
            status=self._status,
            last_success=self._last_success,
            last_error=self._last_error,
        )

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单的健康检查 - 搜索一个通用关键词
            await self.client.search_amazon("test", limit=1)
            return True
        except Exception as e:
            logger.warning(f"Oxylabs health check failed: {e}")
            return False

    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True
        logger.info("Oxylabs data source enabled")

    def disable(self):
        self._enabled = False
        logger.info("Oxylabs data source disabled")

    async def close(self):
        """关闭客户端"""
        await self.client.close()


# ==================== Lazada 数据源适配器 ====================

class LazadaDataSource(DataSourceProtocol):
    """Lazada 数据源适配器

    支持：
    - 东南亚市场（TH, VN, MY, SG, ID, PH）
    - OAuth 认证
    - 商品搜索
    """

    # 品类到 Lazada 分类 ID 的映射
    CATEGORY_MAPPING = {
        "wireless_earbuds": "10102020",  # 示例分类ID
        "smart_plugs": "10103010",
        "fitness_trackers": "10100500",
        "phone_chargers": "10101010",
        "desk_lamps": "10100600",
        "phone_cases": "10101005",
        "yoga_mats": "10100700",
        "coffee_makers": "10100800",
        "bluetooth_speakers": "10102030",
        "webcams": "10100900",
        "keyboards": "10102050",
        "mouse": "10102060",
    }

    def __init__(self, country: str = "th"):
        """
        初始化 Lazada 数据源

        Args:
            country: 国家代码 (th, vn, my, sg, id, ph)
        """
        self.country = country
        self._enabled = True
        self._status = DataSourceStatus.ACTIVE
        self._last_error: Optional[str] = None
        self._last_success: Optional[datetime] = None

        # 延迟初始化客户端（需要 OAuth 凭证）
        self._client = None

    def _get_client(self):
        """获取 Lazada 客户端"""
        if self._client is None:
            from crawler.products.lazada_api import LazadaAPIClient, LazadaConfig

            config = LazadaConfig(
                app_key=os.getenv("LAZADA_APP_KEY", ""),
                app_secret=os.getenv("LAZADA_APP_SECRET", ""),
                country=self.country,
                access_token=os.getenv("LAZADA_ACCESS_TOKEN"),
            )
            self._client = LazadaAPIClient(config)
        return self._client

    def _get_region(self) -> Region:
        """获取区域枚举"""
        region_map = {
            "th": Region.TH,
            "vn": Region.VN,
            "my": Region.MY,
            "sg": Region.SG,
            "id": Region.ID,
            "ph": Region.PH,
        }
        return region_map.get(self.country, Region.TH)

    async def fetch_market_data(
        self,
        category: str,
        query: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取市场数据"""
        try:
            # 检查是否有凭证
            if not os.getenv("LAZADA_APP_KEY"):
                logger.warning("Lazada credentials not configured, returning mock data")
                return self._get_mock_data(category, limit)

            client = self._get_client()
            region = self._get_region()

            # 尝试获取商品数据
            # 注意：Lazada API 的搜索功能需要确认具体端点
            products = await client.get_products(limit=limit)

            # 标准化产品数据
            standardized_products = []
            for p in products[:limit]:
                try:
                    product = StandardizedProduct.from_lazada(
                        p.to_dict() if hasattr(p, 'to_dict') else p,
                        region
                    )
                    standardized_products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to standardize Lazada product: {e}")
                    continue

            self._last_success = datetime.utcnow()
            self._status = DataSourceStatus.ACTIVE
            self._last_error = None

            return {
                "source": f"lazada_{self.country}",
                "products": [p.to_dict() for p in standardized_products],
                "trends": [],
                "sentiments": [],
                "metadata": {
                    "fetch_time": datetime.utcnow().isoformat(),
                    "reliability": 0.85,
                    "data_points": len(standardized_products),
                    "platform": "lazada",
                    "region": self.country.upper(),
                }
            }

        except Exception as e:
            logger.error(f"Lazada data fetch failed: {e}")
            self._status = DataSourceStatus.ERROR
            self._last_error = str(e)

            # 返回 mock 数据作为降级
            return self._get_mock_data(category, limit)

    def _get_mock_data(self, category: str, limit: int) -> Dict[str, Any]:
        """获取 mock 数据（当 API 不可用时）"""
        return {
            "source": f"lazada_{self.country}_mock",
            "products": [],
            "trends": [],
            "sentiments": [],
            "metadata": {
                "fetch_time": datetime.utcnow().isoformat(),
                "reliability": 0.5,
                "data_points": 0,
                "platform": "lazada",
                "region": self.country.upper(),
                "mock": True,
            }
        }

    def get_metadata(self) -> DataSourceMetadata:
        """获取数据源元数据"""
        return DataSourceMetadata(
            name=f"Lazada {self.country.upper()}",
            description=f"Lazada {self.country.upper()} 市场数据",
            version="1.0.0",
            reliability=0.85,
            latency_ms=1500,
            cost_per_request=0.0,
            status=self._status,
            last_success=self._last_success,
            last_error=self._last_error,
        )

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not os.getenv("LAZADA_APP_KEY"):
                return False
            client = self._get_client()
            await client.get_category_tree()
            return True
        except Exception as e:
            logger.warning(f"Lazada health check failed: {e}")
            return False

    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True
        logger.info(f"Lazada {self.country} data source enabled")

    def disable(self):
        self._enabled = False
        logger.info(f"Lazada {self.country} data source disabled")


# ==================== 数据源注册函数 ====================

def register_all_data_sources(registry):
    """
    注册所有数据源到注册中心

    Args:
        registry: DataSourceRegistry 实例
    """
    # 注册 Oxylabs (Amazon)
    registry.register("oxylabs_amazon", OxylabsDataSource())

    # 注册 Lazada 各国数据源
    for country in ["th", "vn", "my", "sg", "id", "ph"]:
        registry.register(f"lazada_{country}", LazadaDataSource(country))

    logger.info(f"✅ Registered {len(registry.list_sources())} data sources")


# ==================== 工具函数 ====================

async def fetch_multi_platform_data(
    category: str,
    query: str,
    platforms: Optional[List[str]] = None,
    limit: int = 20
) -> AggregatedProducts:
    """
    跨平台获取数据

    Args:
        category: 品类标识
        query: 搜索关键词
        platforms: 要查询的平台列表 (None = 全部)
        limit: 每个平台的数量限制

    Returns:
        AggregatedProducts: 聚合的产品数据
    """
    from services.data_source_registry import data_source_registry

    # 确定要查询的平台
    if platforms is None:
        platforms = ["oxylabs_amazon", "lazada_th", "lazada_vn"]

    # 获取所有数据
    result = await data_source_registry.fetch_all(
        category=category,
        query=query,
        limit=limit
    )

    # 聚合数据
    aggregated = AggregatedProducts(
        category=category,
        query=query,
    )

    for source_name, source_data in result.get("data", {}).items():
        products = [
            StandardizedProduct(**p) if isinstance(p, dict) else p
            for p in source_data.get("products", [])
        ]
        if products:
            aggregated.add_products(source_name, products)

    return aggregated
