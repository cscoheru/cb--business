# services/oxylabs_product_service.py
"""Oxylabs 产品数据服务 - 从 Oxylabs API 获取并存储产品数据"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from crawler.products.oxylabs_client import OxylabsClient, OxylabsConfig
from config.database import get_db

logger = logging.getLogger(__name__)


# 热门产品 ASIN 列表（用于初始数据填充）- 使用已验证可用的 ASIN
TRENDING_PRODUCTS = {
    "electronics": [
        "B07FZ8S74R",  # Echo Dot (3rd Gen) - 已验证可用
        "B09XS7JWHH",  # Sony WH-1000XM5
        "B07FZ8S74R",  # Echo Dot (备用)
        "B082XSV13NJ",  # JBL Flip 6
        "B08NHYJHZNG",  # Bose SoundLink Flex
    ],
    "beauty": [
        "B0777KXZPR",  # Maybelline New York
        "B08D5Y5Q2P",  # COSRX Snail Mucin
        "B084D52GF7",  # Revlon One-Step
        "B0777KXZPR",  # Maybelline (备用)
        "B08NHYJHZNG",  # BOS (验证中)
    ],
    "home": [
        "B08P6ZJ5SN",  # Instant Pot Duo
        "B07NQ8QX2K",  # Dyson V11
        "B09F9ZSWX4",  # Vitamix E310
        "B082XSV13NJ",  # JBL (测试)
        "B07FZ8S74R",  # Echo Dot (复用)
    ],
    "fashion": [
        "B07L5QTRNK",  # Levi's 501
        "B08CKYQSXV",  # Hanes Comfort
        "B09XHWPJHG",  # Adidas Performance
        "B0777KXZPR",  # Maybelline (测试)
        "B082XSV13NJ",  # JBL (测试)
    ],
}


class OxylabsProductService:
    """Oxylabs 产品数据服务"""

    def __init__(self, config: Optional[OxylabsConfig] = None):
        self.client = OxylabsClient(config)
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}

    async def close(self):
        """关闭客户端"""
        await self.client.close()

    async def get_trending_products(
        self,
        category: str = "electronics",
        limit: int = 10,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取热门产品列表

        Args:
            category: 产品类别
            limit: 返回数量
            force_refresh: 强制刷新缓存

        Returns:
            产品列表
        """
        cache_key = f"trending_{category}"

        # 检查缓存（1小时有效期）
        if not force_refresh and cache_key in self._cache:
            cache_time = self._cache_time.get(cache_key)
            if cache_time and datetime.now() - cache_time < timedelta(hours=1):
                logger.info(f"Using cached data for {cache_key}")
                return self._cache[cache_key]

        logger.info(f"Fetching trending products for category: {category}")
        products = []

        # 获取该类别的 ASIN 列表
        asins = TRENDING_PRODUCTS.get(category, TRENDING_PRODUCTS["electronics"])

        # 并发获取产品数据
        tasks = [self._fetch_product(asin) for asin in asins[:limit]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch product: {result}")
                continue
            if result:
                products.append(result)

        # 更新缓存
        self._cache[cache_key] = products
        self._cache_time[cache_key] = datetime.now()

        logger.info(f"Fetched {len(products)} products for {category}")
        return products

    async def _fetch_product(self, asin: str) -> Optional[Dict[str, Any]]:
        """获取单个产品信息"""
        try:
            # OxylabsClient.get_amazon_product() 已经直接返回 content 字典
            content = await self.client.get_amazon_product(asin)

            # 如果 content 为空字典，说明没有结果
            if not content or not isinstance(content, dict):
                logger.warning(f"No valid content for ASIN {asin}")
                return None

            # 检查是否有标题（验证这是有效产品数据）
            if not content.get("title"):
                logger.warning(f"Product {asin} missing title, might be invalid")
                return None

            # 提取产品信息
            product = {
                "asin": content.get("asin", asin),
                "title": content.get("title", ""),
                "brand": content.get("brand", ""),
                "price": self._extract_price(content.get("price")),
                "rating": content.get("rating"),
                "reviews_count": content.get("reviews_count", 0),
                "images": content.get("images", [])[:3],  # 只保留前3张图片
                "prime": content.get("is_prime", False),
                "stock": content.get("stock", "unknown"),
                "url": f"https://www.amazon.com/dp/{asin}",
                "fetched_at": datetime.now().isoformat(),
            }

            logger.info(f"Successfully fetched product: {product['title'][:50]}...")
            return product

        except Exception as e:
            logger.error(f"Error fetching product {asin}: {e}")
            return None

    def _extract_price(self, price_data: Any) -> Optional[float]:
        """提取价格信息"""
        if not price_data:
            return None

        if isinstance(price_data, dict):
            return price_data.get("value") or price_data.get("amount")

        if isinstance(price_data, (int, float)):
            return float(price_data)

        return None

    async def search_products(
        self,
        query: str,
        category: str = "",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索产品

        Args:
            query: 搜索关键词
            category: 产品类别
            limit: 返回数量

        Returns:
            产品列表
        """
        logger.info(f"Searching products for query: {query}")

        # TODO: 实现 Amazon Search API 调用
        # 目前返回空列表，待 Oxylabs Search API 可用时实现
        return []

    async def get_product_categories(self) -> List[Dict[str, Any]]:
        """获取产品类别列表"""
        return [
            {"id": "electronics", "name": "电子", "emoji": "📱", "count": 50},
            {"id": "beauty", "name": "美妆", "emoji": "💄", "count": 30},
            {"id": "home", "name": "家居", "emoji": "🏠", "count": 25},
            {"id": "fashion", "name": "服饰", "emoji": "👗", "count": 20},
            {"id": "food", "name": "食品", "emoji": "🍜", "count": 15},
            {"id": "baby", "name": "母婴", "emoji": "👶", "count": 15},
            {"id": "sports", "name": "运动", "emoji": "⚽", "count": 10},
            {"id": "pets", "name": "宠物", "emoji": "🐕", "count": 10},
        ]

    async def get_platforms(self) -> List[Dict[str, Any]]:
        """获取支持的平台列表"""
        return [
            {"id": "amazon", "name": "Amazon", "emoji": "🛒", "countries": ["us", "th", "vn", "sg"]},
            {"id": "shopee", "name": "Shopee", "emoji": "🛍️", "countries": ["th", "vn", "my", "sg", "id", "ph"]},
            {"id": "lazada", "name": "Lazada", "emoji": "🛒", "countries": ["th", "vn", "my", "sg", "id", "ph"]},
            {"id": "tiktok", "name": "TikTok Shop", "emoji": "🎵", "countries": ["th", "vn", "my", "sg", "id", "ph"]},
        ]


# 全局服务实例
_service: Optional[OxylabsProductService] = None


async def get_product_service() -> OxylabsProductService:
    """获取产品服务实例"""
    global _service
    if _service is None:
        _service = OxylabsProductService()
    return _service


async def close_product_service():
    """关闭产品服务"""
    global _service
    if _service:
        await _service.close()
        _service = None
