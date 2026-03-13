# services/data_sources/google_trends_source.py
"""Google Trends数据源适配器"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from crawler.trends.google_trends import GoogleTrendsClient
from services.data_source_registry import (
    DataSourceProtocol,
    DataSourceMetadata,
    DataSourceStatus
)

logger = logging.getLogger(__name__)


class GoogleTrendsDataSource:
    """Google Trends数据源适配器"""

    def __init__(self, enabled: bool = True):
        self._client: Optional[GoogleTrendsClient] = None
        self._enabled = enabled
        self._metadata = DataSourceMetadata(
            name="Google Trends",
            description="Google搜索趋势数据、相关查询",
            version="1.0.0",
            reliability=0.85,  # 非官方API，可靠性稍低
            latency_ms=2000,
            cost_per_request=0.0,  # 免费但有限流
            status=DataSourceStatus.ACTIVE if enabled else DataSourceStatus.DISABLED
        )

    async def _get_client(self) -> GoogleTrendsClient:
        """获取或创建客户端"""
        if self._client is None:
            self._client = GoogleTrendsClient()
        return self._client

    async def fetch_market_data(
        self,
        category: str,
        query: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取Google Trends数据

        Returns:
            标准化的数据格式，包含趋势和相关查询
        """
        client = await self._get_client()

        try:
            # 获取趋势数据
            trends_data = await client.get_trends(
                keywords=[query],
                country="US",
                category=0  # 所有分类
            )

            # 标准化返回格式
            result = {
                "source": "google_trends",
                "products": [],  # Trends不提供产品数据
                "trends": self._normalize_trends(trends_data),
                "sentiments": [],
                "metadata": {
                    "fetch_time": datetime.now(timezone.utc).isoformat(),
                    "reliability": self._metadata.reliability,
                    "data_points": len(trends_data) if trends_data else 0,
                    "source_type": "search_trends",
                    "region": "US"
                }
            }

            # 更新成功状态
            self._metadata.last_success = datetime.now(timezone.utc)
            self._metadata.status = DataSourceStatus.ACTIVE

            logger.info(f"✅ Google Trends获取到 {len(trends_data) if trends_data else 0} 条趋势")
            return result

        except Exception as e:
            self._metadata.last_error = str(e)
            self._metadata.status = DataSourceStatus.ERROR
            logger.error(f"❌ Google Trends获取失败: {e}")
            raise

    def _normalize_trends(self, trends_data: List) -> List[Dict[str, Any]]:
        """标准化趋势数据格式"""
        normalized = []

        for trend in trends_data:
            normalized_trend = {
                "keyword": trend.get("title", ""),
                "volume": trend.get("volume", 0),
                "traffic": trend.get("traffic", 0),
                "related_queries": trend.get("related_queries", []),
                "source": "google_trends",
                "timestamp": trend.get("timestamp", datetime.now(timezone.utc).isoformat())
            }
            normalized.append(normalized_trend)

        return normalized

    def get_metadata(self) -> DataSourceMetadata:
        """获取数据源元数据"""
        return self._metadata

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            client = await self._get_client()
            # 尝试获取一个简单的趋势
            result = await client.get_trends(keywords=["test"], country="US")
            return result is not None
        except Exception as e:
            logger.warning(f"Google Trends健康检查失败: {e}")
            return False

    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True
        self._metadata.status = DataSourceStatus.ACTIVE
        logger.info("✅ Google Trends数据源已启用")

    def disable(self):
        self._enabled = False
        self._metadata.status = DataSourceStatus.DISABLED
        logger.info("❌ Google Trends数据源已禁用")
