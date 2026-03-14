# services/product_data_service.py
"""产品数据服务 - 从 Cards 表获取完整产品数据"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, desc
from config.database import AsyncSessionLocal
from models.card import Card

logger = logging.getLogger(__name__)


class ProductDataService:
    """
    产品数据服务

    从 Cards 表读取产品数据，支持获取完整字段（brand, image等）
    """

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 1800  # 30分钟缓存

    async def get_products_with_details(
        self,
        category_id: str,
        category_mapping: Dict[str, List[str]],
        limit: int,
        db: AsyncSessionLocal
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取包含完整详情的产品列表

        Args:
            category_id: 前端分类ID (electronics, home, sports等)
            category_mapping: 分类映射字典
            limit: 返回数量限制
            db: 数据库会话

        Returns:
            产品列表，如果未找到则返回None
        """
        mapped_categories = category_mapping.get(category_id, [])

        if not mapped_categories:
            logger.debug(f"No mapped categories for {category_id}")
            return None

        all_products = []

        # 从所有映射的类别中获取产品
        for card_category in mapped_categories:
            try:
                # 获取最新的卡片
                card_result = await db.execute(
                    select(Card)
                    .where(Card.category == card_category)
                    .where(Card.amazon_data.isnot(None))
                    .where(Card.is_published == True)
                    .order_by(desc(Card.created_at))
                    .limit(1)
                )
                card = card_result.scalar_one_or_none()

                if card and card.amazon_data:
                    products = card.amazon_data.get("products", [])
                    if products:
                        # 增强产品数据
                        enhanced_products = await self._enhance_products(products, card_category)
                        all_products.extend(enhanced_products)
                        logger.debug(f"Found {len(enhanced_products)} products in {card_category}")
            except Exception as e:
                logger.warning(f"Error reading cards for {card_category}: {e}")
                continue

        if not all_products:
            logger.debug(f"No products found in cards for {category_id}")
            return None

        # 按评分排序，取前N个
        all_products.sort(key=lambda p: p.get("rating", 0), reverse=True)
        return all_products[:limit]

    async def _enhance_products(
        self,
        products: List[Dict[str, Any]],
        category: str
    ) -> List[Dict[str, Any]]:
        """
        增强产品数据，确保所有必需字段都存在

        Args:
            products: 原始产品列表
            category: 产品类别

        Returns:
            增强后的产品列表
        """
        enhanced = []

        for product in products:
            if not product or not isinstance(product, dict):
                continue

            # 处理品牌字段 - 优先级：brand > manufacturer > "Unknown"
            brand = (
                product.get("brand") or
                product.get("manufacturer") or
                product.get("brand_name") or
                "Unknown Brand"
            )

            # 处理图片
            image = self._extract_image(product)

            # 处理价格
            price = self._extract_price(product)

            # 处理评分
            rating = self._extract_rating(product)

            # 处理评论数
            reviews_count = self._extract_reviews_count(product)

            # 构建URL
            url = self._build_url(product)

            enhanced_product = {
                "asin": product.get("asin", ""),
                "title": product.get("title", "N/A"),
                "brand": brand,
                "price": price,
                "rating": rating,
                "reviews_count": reviews_count,
                "image": image,
                "url": url,
                "category": category,
                "source": "cards_enhanced"
            }

            enhanced.append(enhanced_product)

        return enhanced

    def _extract_image(self, product: Dict[str, Any]) -> Optional[str]:
        """提取产品图片"""
        # 优先级：image > images[0].url > main_image > None
        if product.get("image"):
            return product["image"]

        images = product.get("images", [])
        if images and isinstance(images, list):
            if isinstance(images[0], dict):
                return images[0].get("url")
            elif isinstance(images[0], str):
                return images[0]

        return product.get("main_image")

    def _extract_price(self, product: Dict[str, Any]) -> Optional[float]:
        """提取价格"""
        price = product.get("price")

        # 如果是数字，直接返回
        if isinstance(price, (int, float)):
            return float(price)

        # 如果是字符串，尝试解析
        if isinstance(price, str):
            try:
                # 移除货币符号和空格
                clean_price = price.replace("$", "").replace(" ", "").strip()
                return float(clean_price)
            except (ValueError, AttributeError):
                pass

        return None

    def _extract_rating(self, product: Dict[str, Any]) -> Optional[float]:
        """提取评分"""
        rating = product.get("rating")

        if isinstance(rating, (int, float)):
            return float(rating)

        if isinstance(rating, str):
            try:
                return float(rating)
            except ValueError:
                pass

        return None

    def _extract_reviews_count(self, product: Dict[str, Any]) -> int:
        """提取评论数"""
        reviews = product.get("reviews_count", 0)

        if isinstance(reviews, int):
            return reviews

        if isinstance(reviews, str):
            try:
                return int(reviews.replace(",", "").strip())
            except (ValueError, AttributeError):
                pass

        return 0

    def _build_url(self, product: Dict[str, Any]) -> str:
        """构建产品URL"""
        asin = product.get("asin", "")

        # 如果已有完整URL
        url = product.get("url")
        if url:
            if url.startswith("http"):
                return url
            else:
                return f"https://www.amazon.com{url}"

        # 使用ASIN构建URL
        if asin:
            return f"https://www.amazon.com/dp/{asin}"

        return "https://www.amazon.com"


# 全局单例
_product_data_service: Optional[ProductDataService] = None


def get_product_data_service() -> ProductDataService:
    """获取产品数据服务单例"""
    global _product_data_service

    if _product_data_service is None:
        _product_data_service = ProductDataService()

    return _product_data_service
