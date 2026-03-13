# services/data_source_registry.py
"""数据源注册和管理 - 统一的多信息源聚合架构

架构设计：
1. 每个数据源实现 DataSourceProtocol 接口
2. DataSourceRegistry 负责注册、管理、调用所有数据源
3. CardGenerator 聚合所有数据源的结果
4. AI分析基于所有数据源的综合数据

优势：
- 可插拔：每个数据源独立，可随时替换/新增/禁用
- 可测试：可以mock单个数据源进行测试
- 可监控：每个数据源的成功率、响应时间独立统计
- 可降级：某个数据源失败不影响整体
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DataSourceStatus(Enum):
    """数据源状态"""
    ACTIVE = "active"       # 启用中
    DISABLED = "disabled"   # 已禁用
    DEGRADED = "degraded"   # 性能下降
    ERROR = "error"         # 错误状态


@dataclass
class DataSourceMetadata:
    """数据源元数据"""
    name: str                      # 数据源名称
    description: str               # 描述
    version: str                   # 版本
    reliability: float             # 可靠性 (0-1)
    latency_ms: int                # 平均延迟（毫秒）
    cost_per_request: float        # 每次请求成本
    status: DataSourceStatus       # 当前状态
    last_success: Optional[datetime] = None  # 最后成功时间
    last_error: Optional[str] = None         # 最后错误信息


class DataSourceProtocol(Protocol):
    """数据源接口协议

    所有数据源必须实现此协议，确保统一的数据格式和行为。
    """

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
            标准化的数据格式：
            {
                "source": "数据源名称",
                "products": [...],        # 产品/商品数据
                "trends": [...],          # 趋势数据
                "sentiments": [...],      # 情感分析数据
                "metadata": {             # 元数据
                    "fetch_time": "ISO时间",
                    "reliability": 0.95,
                    "data_points": 100
                }
            }
        """
        ...

    def get_metadata(self) -> DataSourceMetadata:
        """获取数据源元数据"""
        ...

    async def health_check(self) -> bool:
        """健康检查"""
        ...

    def is_enabled(self) -> bool:
        """是否启用"""
        ...

    def enable(self):
        """启用数据源"""
        ...

    def disable(self):
        """禁用数据源"""
        ...


class DataSourceRegistry:
    """数据源注册中心

    负责管理所有数据源的生命周期：
    - 注册数据源
    - 并行调用多个数据源
    - 聚合结果
    - 错误处理和降级
    """

    def __init__(self):
        self._sources: Dict[str, DataSourceProtocol] = {}
        self._stats: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, source: DataSourceProtocol) -> None:
        """注册数据源"""
        self._sources[name] = source
        self._stats[name] = {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "avg_latency_ms": 0,
            "last_call_time": None
        }
        logger.info(f"✅ 注册数据源: {name}")

    def unregister(self, name: str) -> None:
        """注销数据源"""
        if name in self._sources:
            del self._sources[name]
            del self._stats[name]
            logger.info(f"🗑️ 注销数据源: {name}")

    def get_source(self, name: str) -> Optional[DataSourceProtocol]:
        """获取数据源"""
        return self._sources.get(name)

    def list_sources(self) -> List[DataSourceMetadata]:
        """列出所有数据源的元数据"""
        return [source.get_metadata() for source in self._sources.values()]

    def list_enabled_sources(self) -> List[str]:
        """列出启用的数据源名称"""
        return [
            name for name, source in self._sources.items()
            if source.is_enabled()
        ]

    async def fetch_all(
        self,
        category: str,
        query: str,
        limit: int = 20,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        并行获取所有启用的数据源

        Args:
            category: 品类标识
            query: 搜索关键词
            limit: 每个数据源的返回限制
            timeout: 超时时间（秒）

        Returns:
            聚合后的数据：
            {
                "success": True,
                "total_sources": 3,
                "successful_sources": 2,
                "failed_sources": 1,
                "data": {
                    "oxylabs": {...},
                    "google_trends": {...}
                },
                "aggregated": {
                    "products": [...],
                    "trends": [...],
                    "sentiments": [...]
                },
                "errors": {
                    "reddit_trends": "timeout"
                },
                "metadata": {
                    "fetch_time": "...",
                    "total_latency_ms": 3500
                }
            }
        """
        import asyncio
        from datetime import datetime

        enabled_sources = self.list_enabled_sources()
        if not enabled_sources:
            logger.warning("⚠️ 没有启用的数据源")
            return {
                "success": False,
                "error": "没有启用的数据源",
                "data": {},
                "aggregated": {
                    "products": [],
                    "trends": [],
                    "sentiments": []
                }
            }

        logger.info(f"🔍 并行获取 {len(enabled_sources)} 个数据源: {enabled_sources}")

        # 并行调用所有数据源
        tasks = []
        for source_name in enabled_sources:
            source = self._sources[source_name]
            tasks.append(self._fetch_with_timeout(source, category, query, limit, timeout))

        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_latency = int((datetime.now() - start_time).total_seconds() * 1000)

        # 聚合结果
        aggregated = {
            "products": [],
            "trends": [],
            "sentiments": []
        }

        successful_results = {}
        failed_sources = {}

        for i, (source_name, result) in enumerate(zip(enabled_sources, results)):
            # 更新统计
            self._stats[source_name]["total_calls"] += 1
            self._stats[source_name]["last_call_time"] = datetime.now().isoformat()

            if isinstance(result, Exception):
                logger.error(f"❌ {source_name} 失败: {result}")
                self._stats[source_name]["failed_calls"] += 1
                failed_sources[source_name] = str(result)
            elif result and isinstance(result, dict):
                logger.info(f"✅ {source_name} 成功")
                self._stats[source_name]["success_calls"] += 1
                successful_results[source_name] = result

                # 聚合数据
                if "products" in result:
                    aggregated["products"].extend(result["products"])
                if "trends" in result:
                    aggregated["trends"].extend(result["trends"])
                if "sentiments" in result:
                    aggregated["sentiments"].extend(result["sentiments"])

        return {
            "success": len(successful_results) > 0,
            "total_sources": len(enabled_sources),
            "successful_sources": len(successful_results),
            "failed_sources": len(failed_sources),
            "data": successful_results,
            "aggregated": aggregated,
            "errors": failed_sources,
            "metadata": {
                "fetch_time": datetime.now().isoformat(),
                "total_latency_ms": total_latency,
                "sources_called": enabled_sources
            }
        }

    async def _fetch_with_timeout(
        self,
        source: DataSourceProtocol,
        category: str,
        query: str,
        limit: int,
        timeout: float
    ) -> Dict[str, Any]:
        """带超时的数据获取"""
        import asyncio
        try:
            return await asyncio.wait_for(
                source.fetch_market_data(category, query, limit),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ {source.get_metadata().name} 超时")
            raise
        except Exception as e:
            logger.error(f"❌ {source.get_metadata().name} 错误: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """获取所有数据源的统计信息"""
        return {
            "sources": self._stats,
            "total_sources": len(self._sources),
            "enabled_sources": len(self.list_enabled_sources())
        }


# 全局数据源注册表
data_source_registry = DataSourceRegistry()
