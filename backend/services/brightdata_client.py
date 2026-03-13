# services/brightdata_client.py
"""Bright Data API客户端 - 完整版

Bright Data提供高质量的Amazon产品数据采集服务。

支持的功能:
1. 产品详情抓取 (Product Details)
2. 产品评论抓取 (Product Reviews)
3. 关键词搜索 (Discover by Keyword) - 异步
4. 类别搜索 (Discover by Category) - 异步
5. 热销产品 (Best Sellers) - 异步
6. 卖家信息 (Seller Info)

API文档: https://docs.brightdata.com/api-reference
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import httpx
import asyncio

logger = logging.getLogger(__name__)

# Bright Data配置
BRIGHTDATA_API_BASE = "https://api.brightdata.com"
BRIGHTDATA_SCRAPE_URL = f"{BRIGHTDATA_API_BASE}/datasets/v3/scrape"

# 数据集ID
DATASET_PRODUCT_DETAILS = "gd_l7q7dkf244hwjntr0"      # 产品详情
DATASET_PRODUCT_REVIEWS = "gd_le8e811kzy4ggddlq"      # 产品评论
DATASET_SELLER_INFO = "gd_l3l3f9kzy4ggddlq"            # 卖家信息

# 认证
BRIGHTDATA_API_KEY = "1c7806b0-3f98-48da-93ce-8a745c40b062"
BRIGHTDATA_TIMEOUT = 180.0  # 3分钟


class DiscoverType(str, Enum):
    """发现类型"""
    KEYWORD = "keyword"
    CATEGORY_URL = "category_url"
    BEST_SELLERS_URL = "best_sellers_url"


class BrightDataClient:
    """Bright Data API客户端 - 完整版"""

    def __init__(
        self,
        api_key: str = BRIGHTDATA_API_KEY,
        timeout: float = BRIGHTDATA_TIMEOUT
    ):
        """
        初始化Bright Data客户端

        Args:
            api_key: Bright Data API密钥
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    # ========================================================================
    # 1. 产品详情抓取
    # ========================================================================

    async def scrape_products(
        self,
        urls: List[str],
        zipcode: str = "94107",
        language: str = ""
    ) -> List[Dict[str, Any]]:
        """
        批量抓取Amazon产品详情

        Args:
            urls: Amazon产品URL列表
            zipcode: 邮编（用于价格定位）
            language: 语言代码

        Returns:
            产品数据列表
        """
        input_data = [
            {"url": url, "zipcode": zipcode, "language": language}
            for url in urls
        ]

        params = {
            "dataset_id": DATASET_PRODUCT_DETAILS,
            "notify": "false",
            "include_errors": "true"
        }

        logger.info(f"[BrightData] Scraping {len(urls)} products...")

        results = await self._scrape_sync(input_data, params)
        logger.info(f"[BrightData] Got {len(results)}/{len(urls)} products")

        return results

    async def scrape_product(
        self,
        url: str,
        zipcode: str = "94107"
    ) -> Optional[Dict[str, Any]]:
        """抓取单个产品详情"""
        results = await self.scrape_products([url], zipcode)
        return results[0] if results else None

    async def scrape_by_asins(
        self,
        asins: List[str],
        zipcode: str = "94107"
    ) -> List[Dict[str, Any]]:
        """通过ASIN列表批量抓取"""
        urls = [f"https://www.amazon.com/dp/{asin}" for asin in asins]
        return await self.scrape_products(urls, zipcode)

    # ========================================================================
    # 2. 产品评论抓取
    # ========================================================================

    async def scrape_reviews(
        self,
        urls: List[str],
        exclude_reviews: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        抓取产品评论

        Args:
            urls: 产品URL列表
            exclude_reviews: 要排除的评论ID列表

        Returns:
            评论数据列表
        """
        input_data = [
            {
                "url": url,
                "reviews_to_not_exclude": exclude_reviews or []
            }
            for url in urls
        ]

        params = {
            "dataset_id": DATASET_PRODUCT_REVIEWS,
            "notify": "false",
            "include_errors": "true"
        }

        logger.info(f"[BrightData] Scraping reviews for {len(urls)} products...")

        results = await self._scrape_sync(input_data, params)
        logger.info(f"[BrightData] Got {len(results)} review batches")

        return results

    # ========================================================================
    # 3. 关键词/类别/热销产品发现 (异步)
    # ========================================================================

    async def discover_by_keyword(
        self,
        keywords: List[str],
        zipcode: str = "94107"
    ) -> str:
        """
        通过关键词发现产品 (异步)

        返回snapshot_id，需要用monitor_snapshot()监控进度

        Args:
            keywords: 关键词列表
            zipcode: 邮编

        Returns:
            snapshot_id
        """
        input_data = [
            {"keyword": kw, "zipcode": zipcode}
            for kw in keywords
        ]

        return await self._discover_async(
            input_data,
            DiscoverType.KEYWORD
        )

    async def discover_by_category(
        self,
        category_urls: List[Dict[str, str]]
    ) -> str:
        """
        通过类别URL发现产品 (异步)

        Args:
            category_urls: 类别配置列表
                [{"url": "...", "sort_by": "Best Sellers", "zipcode": "10001"}]

        Returns:
            snapshot_id
        """
        return await self._discover_async(
            category_urls,
            DiscoverType.CATEGORY_URL
        )

    async def discover_bestsellers(
        self,
        category_urls: List[str]
    ) -> str:
        """
        发现热销产品 (异步)

        Args:
            category_urls: 热销产品类别URL列表

        Returns:
            snapshot_id
        """
        input_data = [{"category_url": url} for url in category_urls]
        return await self._discover_async(
            input_data,
            DiscoverType.BEST_SELLERS_URL
        )

    # ========================================================================
    # 4. Snapshot监控和下载
    # ========================================================================

    async def monitor_snapshot(
        self,
        snapshot_id: str,
        max_wait: int = 300,
        interval: int = 5
    ) -> bool:
        """
        监控snapshot进度直到完成

        Args:
            snapshot_id: Snapshot ID
            max_wait: 最大等待时间（秒）
            interval: 检查间隔（秒）

        Returns:
            是否成功完成
        """
        started = datetime.now()

        while True:
            elapsed = (datetime.now() - started).total_seconds()

            if elapsed > max_wait:
                logger.warning(f"[BrightData] Snapshot {snapshot_id} timeout after {max_wait}s")
                return False

            status = await self._get_snapshot_status(snapshot_id)

            if status.get("status") == "ready":
                logger.info(f"[BrightData] Snapshot {snapshot_id} is ready")
                return True
            elif status.get("status") == "failed":
                logger.error(f"[BrightData] Snapshot {snapshot_id} failed")
                return False

            logger.debug(f"[BrightData] Snapshot {snapshot_id} status: {status.get('status')}")
            await asyncio.sleep(interval)

    async def download_snapshot(
        self,
        snapshot_id: str
    ) -> List[Dict[str, Any]]:
        """
        下载已完成snapshot的数据

        Args:
            snapshot_id: Snapshot ID

        Returns:
            产品数据列表
        """
        url = f"{BRIGHTDATA_API_BASE}/datasets/v3/snapshots/{snapshot_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                headers=self._headers
            )
            response.raise_for_status()

            # 解析JSONL响应
            results = []
            for line in response.text.strip().split('\n'):
                if line.strip():
                    import json
                    try:
                        data = json.loads(line)
                        results.append(data)
                    except json.JSONDecodeError:
                        pass

            return results

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _scrape_sync(
        self,
        input_data: List[Dict],
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """执行同步抓取"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                BRIGHTDATA_SCRAPE_URL,
                headers=self._headers,
                params=params,
                json={"input": input_data}
            )
            response.raise_for_status()

            # 解析JSONL响应
            results = []
            for line in response.text.strip().split('\n'):
                if line.strip():
                    import json
                    try:
                        data = json.loads(line)
                        if "error" not in data:
                            results.append(self._normalize_product(data))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSONL line: {e}")

            return results

    async def _discover_async(
        self,
        input_data: List[Dict],
        discover_type: DiscoverType
    ) -> str:
        """发起异步发现请求"""
        params = {
            "dataset_id": DATASET_PRODUCT_DETAILS,
            "notify": "false",
            "include_errors": "true",
            "type": "discover_new",
            "discover_by": discover_type.value
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                BRIGHTDATA_SCRAPE_URL,
                headers=self._headers,
                params=params,
                json={"input": input_data}
            )
            response.raise_for_status()

            # 返回snapshot_id
            import json
            data = json.loads(response.text.strip())
            snapshot_id = data.get("snapshot_id")

            if not snapshot_id:
                raise ValueError(f"No snapshot_id in response: {data}")

            logger.info(f"[BrightData] Started {discover_type} discovery: {snapshot_id}")
            return snapshot_id

    async def _get_snapshot_status(self, snapshot_id: str) -> Dict[str, Any]:
        """获取snapshot状态"""
        url = f"{BRIGHTDATA_API_BASE}/datasets/v3/snapshots/{snapshot_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()

    def _normalize_product(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """标准化产品数据格式"""
        return {
            "asin": raw.get("asin"),
            "title": raw.get("title"),
            "brand": raw.get("brand") or raw.get("manufacturer"),
            "price": raw.get("final_price"),
            "original_price": raw.get("initial_price"),
            "currency": raw.get("currency", "USD"),
            "discount": raw.get("discount"),
            "rating": raw.get("rating"),
            "reviews_count": raw.get("reviews_count"),
            "image_url": raw.get("image_url") or raw.get("image"),
            "availability": raw.get("availability"),
            "categories": raw.get("categories", []),
            "features": raw.get("features", []),
            "description": raw.get("description"),
            "url": raw.get("url"),
            "scraped_at": datetime.now().isoformat(),
            "data_source": "brightdata"
        }


# ============================================================================
# Convenience Functions
# ============================================================================

_global_client: Optional[BrightDataClient] = None


def get_brightdata_client() -> BrightDataClient:
    """获取全局客户端单例"""
    global _global_client
    if _global_client is None:
        _global_client = BrightDataClient()
    return _global_client


# 产品详情
async def scrape_products(urls: List[str]) -> List[Dict[str, Any]]:
    """批量抓取产品详情"""
    client = get_brightdata_client()
    return await client.scrape_products(urls)


async def scrape_product(url: str) -> Optional[Dict[str, Any]]:
    """抓取单个产品"""
    client = get_brightdata_client()
    return await client.scrape_product(url)


async def scrape_by_asins(asins: List[str]) -> List[Dict[str, Any]]:
    """通过ASIN抓取产品"""
    client = get_brightdata_client()
    return await client.scrape_by_asins(asins)


# 评论
async def scrape_reviews(urls: List[str]) -> List[Dict[str, Any]]:
    """抓取产品评论"""
    client = get_brightdata_client()
    return await client.scrape_reviews(urls)


# 发现功能 (异步)
async def discover_by_keywords(keywords: List[str]) -> str:
    """通过关键词发现产品"""
    client = get_brightdata_client()
    return await client.discover_by_keyword(keywords)


async def discover_by_category(category_configs: List[Dict]) -> str:
    """通过类别发现产品"""
    client = get_brightdata_client()
    return await client.discover_by_category(category_configs)
