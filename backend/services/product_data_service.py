# services/product_data_service.py
"""产品数据服务 - 两步获取完整产品数据

第一步: 从 cards 表获取 ASIN 列表 (使用缓存)
第二步: 批量获取产品详情 (获取完整字段: brand, image等)

这样可以平衡性能和数据完整性:
- 快速: 从 cards 表获取 ASIN 列表 (已有数据)
- 完整: 对前 N 个产品获取详细信息 (brand, images)
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from sqlalchemy import select, desc
from config.database import AsyncSessionLocal
from models.card import Card
from crawler.products.oxylabs_client import OxylabsClient

logger = logging.getLogger(__name__)


@dataclass
class ProductDetailConfig:
    """产品详情获取配置"""
    # 最多获取详情的产品数量
    max_detail_products: int = 10
    # 其余产品使用缓存数据 (cards 表中的数据)
    use_cache_for_remaining: bool = True


class ProductDataService:
    """产品数据服务 - 统一的产品数据获取接口"""

    def __init__(self, config: Optional[ProductDetailConfig] = None):
        self.config = config or ProductDetailConfig()

    async def get_products_with_details(
        self,
        category_id: str,
        category_mapping: Dict[str, List[str]],
        limit: int = 24,
        db: Optional[AsyncSessionLocal] = None
    ) -> List[Dict[str, Any]]:
        """
        获取产品列表 (包含完整字段)

        两步获取策略:
        1. 从 cards 表读取产品 ASIN 列表 (快速)
        2. 对前 max_detail_products 个产品调用 Oxylabs 获取详情

        Args:
            category_id: 前端分类ID (electronics, home, sports等)
            category_mapping: 分类映射字典
            limit: 返回数量限制
            db: 数据库会话 (可选，如果不提供则创建新会话)

        Returns:
            产品列表，前N个包含完整字段 (brand, images)，其余使用缓存数据
        """
        # Step 1: 从 cards 表获取 ASIN 列表
        asin_products = await self._get_asin_list_from_cards(
            category_id, category_mapping, limit, db
        )

        if not asin_products:
            logger.warning(f"No products found in cards for {category_id}")
            return []

        # Step 2: 对前 N 个产品获取完整详情
        detailed_products = []
        cache_products = []

        for i, product in enumerate(asin_products):
            asin = product.get("asin")
            if not asin:
                continue

            if i < self.config.max_detail_products:
                # 获取完整产品详情
                detail = await self._fetch_product_detail(asin)
                if detail:
                    detailed_products.append(detail)
                else:
                    # 详情获取失败，使用缓存数据
                    cache_products.append(self._format_cache_product(product))
            else:
                # 使用缓存数据
                cache_products.append(self._format_cache_product(product))

        logger.info(
            f"Retrieved {len(detailed_products)} detailed products "
            f"and {len(cache_products)} cache products for {category_id}"
        )

        return detailed_products + cache_products[:limit - len(detailed_products)]

    async def _get_asin_list_from_cards(
        self,
        category_id: str,
        category_mapping: Dict[str, List[str]],
        limit: int,
        db: AsyncSessionLocal
    ) -> List[Dict[str, Any]]:
        """从 cards 表获取 ASIN 列表"""
        mapped_categories = category_mapping.get(category_id, [])

        if not mapped_categories:
            logger.debug(f"No mapped categories for {category_id}")
            return []

        # 从所有映射的类别中获取最新的卡片
        all_products = []

        for card_category in mapped_categories:
            try:
                result = await db.execute(
                    select(Card)
                    .where(Card.category == card_category)
                    .where(Card.amazon_data.isnot(None))
                    .where(Card.is_published == True)
                    .order_by(desc(Card.created_at))
                    .limit(1)
                )
                card = result.scalar_one_or_none()

                if card and card.amazon_data:
                    products = card.amazon_data.get("products", [])
                    if products:
                        all_products.extend(products)
                        logger.debug(f"Found {len(products)} products in {card_category}")
            except Exception as e:
                logger.warning(f"Error reading cards for {card_category}: {e}")
                continue

        return all_products[:limit]

    async def _fetch_product_detail(self, asin: str) -> Optional[Dict[str, Any]]:
        """获取单个产品的完整详情"""
        try:
            client = OxylabsClient()

            # 使用搜索 API 查找该 ASIN
            products = await client.search_amazon(
                query=asin,
                domain="com",
                limit=1,
                use_cache=True,
                cache_ttl=3600
            )

            await client.close()

            if not products or len(products) == 0:
                logger.warning(f"No search results for ASIN {asin}")
                return None

            # 获取第一个产品
            detail = products[0]

            # 提取图片
            image_url = self._extract_image(detail)

            # 格式化返回
            return {
                "asin": asin,
                "title": detail.get("title", "N/A"),
                "brand": detail.get("brand") or detail.get("manufacturer") or "N/A",
                "price": detail.get("price"),
                "rating": detail.get("rating"),
                "reviews_count": detail.get("reviews_count", 0),
                "image": image_url,
                "url": detail.get("url", f"https://www.amazon.com/dp/{asin}"),
                "source": "oxylabs_search_detail"
            }

        except Exception as e:
            logger.warning(f"Failed to fetch detail for {asin}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    def _format_cache_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """格式化缓存数据的产品"""
        asin = product.get("asin", "")
        return {
            "asin": asin,
            "title": product.get("title", "N/A"),
            "brand": product.get("brand") or "N/A",
            "price": product.get("price"),
            "rating": product.get("rating"),
            "reviews_count": product.get("reviews_count", 0),
            "image": product.get("image"),  # 可能为 None
            "url": product.get("url") or f"https://www.amazon.com/dp/{asin}",
            "source": "cards_cache"
        }

    def _extract_image(self, product_data: Dict[str, Any]) -> Optional[str]:
        """从产品数据中提取主图"""
        # 尝试多种可能的图片字段
        image_fields = ["main_image", "image", "image_url", "product_image"]

        for field in image_fields:
            img = product_data.get(field)
            if img:
                return img

        # 检查 images 数组
        images = product_data.get("images", [])
        if images and isinstance(images, list):
            if isinstance(images[0], dict):
                return images[0].get("url") or images[0].get("link")
            elif isinstance(images[0], str):
                return images[0]

        return None


# 全局单例
_product_data_service: Optional[ProductDataService] = None


def get_product_data_service() -> ProductDataService:
    """获取全局产品数据服务单例"""
    global _product_data_service
    if _product_data_service is None:
        _product_data_service = ProductDataService()
    return _product_data_service
