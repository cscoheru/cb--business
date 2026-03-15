# services/product_data_service.py
"""产品数据服务 - 从 Cards 表获取完整产品数据"""
import logging
import asyncio
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
        db: AsyncSessionLocal,
        fetch_details: bool = False,
        details_limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取包含完整详情的产品列表

        Args:
            category_id: 前端分类ID (electronics, home, sports等)
            category_mapping: 分类映射字典
            limit: 返回数量限制
            db: 数据库会话
            fetch_details: 是否获取完整详情（调用Oxylabs Product API）
            details_limit: 获取详情的产品数量限制

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
                        # 增强产品数据（可选获取完整详情）
                        enhanced_products = await self._enhance_products(
                            products,
                            card_category,
                            fetch_details=fetch_details,
                            details_limit=details_limit
                        )
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
        category: str,
        fetch_details: bool = False,
        details_limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        增强产品数据，确保所有必需字段都存在

        Args:
            products: 原始产品列表
            category: 产品类别
            fetch_details: 是否获取完整详情（调用Oxylabs Product API）
            details_limit: 获取详情的产品数量限制

        Returns:
            增强后的产品列表
        """
        enhanced = []

        # 如果启用详情获取，先对前N个产品获取完整数据
        detailed_products = {}
        if fetch_details and products:
            asins_to_fetch = [p.get("asin") for p in products[:details_limit] if p.get("asin")]
            if asins_to_fetch:
                detailed_products = await self._fetch_product_details_batch(asins_to_fetch)

        for idx, product in enumerate(products):
            if not product or not isinstance(product, dict):
                continue

            asin = product.get("asin", "")

            # 如果有从Product API获取的详情，使用详情数据
            if asin in detailed_products:
                enhanced.append(detailed_products[asin])
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
                "asin": asin,
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

    async def _fetch_product_details_batch(
        self,
        asins: List[str],
        concurrent_limit: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量获取产品完整详情（调用Oxylabs Product API）

        Args:
            asins: ASIN列表
            concurrent_limit: 并发请求限制

        Returns:
            字典：{asin: enhanced_product_data}
        """
        if not asins:
            return {}

        # 动态导入OxylabsClient（避免循环依赖）
        try:
            from crawler.products.oxylabs_client import OxylabsClient
        except ImportError as e:
            logger.error(f"Failed to import OxylabsClient: {e}")
            return {}

        client = OxylabsClient()
        results = {}
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def fetch_with_limit(asin: str) -> tuple[str, Optional[Dict[str, Any]]]:
            """带并发限制的获取函数"""
            async with semaphore:
                try:
                    # 调用Oxylabs Product API（内置1小时缓存）
                    product_data = await client.get_amazon_product(asin)

                    if product_data:
                        # 转换为标准格式
                        return asin, self._convert_oxylabs_product(product_data)
                    else:
                        return asin, None
                except Exception as e:
                    logger.warning(f"Failed to fetch details for {asin}: {e}")
                    return asin, None

        # 并发获取所有产品详情
        tasks = [fetch_with_limit(asin) for asin in asins]
        fetched_results = await asyncio.gather(*tasks, return_exceptions=False)

        # 构建结果字典
        for asin, product_data in fetched_results:
            if product_data:
                results[asin] = product_data

        logger.info(f"Fetched details for {len(results)}/{len(asins)} products")
        return results

    def _convert_oxylabs_product(self, oxylabs_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将Oxylabs Product API返回的数据转换为标准格式

        Args:
            oxylabs_data: Oxylabs Product API返回的原始数据

        Returns:
            标准格式的产品数据
        """
        # 提取品牌 - 优先级：brand > manufacturer > "Unknown Brand"
        brand = (
            oxylabs_data.get("brand") or
            oxylabs_data.get("manufacturer") or
            "Unknown Brand"
        )

        # 提取主图
        image = self._extract_oxylabs_image(oxylabs_data)

        # 提取价格
        price = self._extract_oxylabs_price(oxylabs_data)

        # 提取评分
        rating = oxylabs_data.get("rating") or oxylabs_data.get("rating_value")

        # 标准化评分格式
        if isinstance(rating, (int, float)):
            rating = float(rating)
        elif isinstance(rating, str):
            try:
                rating = float(rating)
            except ValueError:
                rating = None
        else:
            rating = None

        # 提取评论数
        reviews_count = oxylabs_data.get("reviews_count") or 0

        # 构建URL
        asin = oxylabs_data.get("asin", "")
        url = f"https://www.amazon.com/dp/{asin}" if asin else "https://www.amazon.com"

        return {
            "asin": asin,
            "title": oxylabs_data.get("title", "N/A"),
            "brand": brand,
            "price": price,
            "rating": rating,
            "reviews_count": reviews_count,
            "image": image,
            "url": url,
            "source": "oxylabs_product_api"
        }

    def _extract_oxylabs_image(self, product_data: Dict[str, Any]) -> Optional[str]:
        """从Oxylabs数据中提取图片"""
        # Oxylabs Product API返回的图片字段结构
        images = product_data.get("images")

        if images and isinstance(images, list):
            # 如果是字典列表，取第一张
            if images and isinstance(images[0], dict):
                return images[0].get("url") or images[0].get("link")
            # 如果是字符串列表，直接取第一个
            elif images and isinstance(images[0], str):
                return images[0]

        # 尝试其他可能的图片字段
        return product_data.get("main_image") or product_data.get("image")

    def _extract_oxylabs_price(self, product_data: Dict[str, Any]) -> Optional[float]:
        """从Oxylabs数据中提取价格"""
        # Oxylabs可能返回的价格字段
        price = (
            product_data.get("price") or
            product_data.get("price_amount") or
            product_data.get("buybox_winner", {}).get("price")
        )

        if isinstance(price, (int, float)):
            return float(price)

        if isinstance(price, str):
            try:
                # 移除货币符号
                clean_price = price.replace("$", "").replace("£", "").replace("€", "")
                clean_price = clean_price.replace(",", "").strip()
                return float(clean_price)
            except (ValueError, AttributeError):
                pass

        return None


# 全局单例
_product_data_service: Optional[ProductDataService] = None


def get_product_data_service() -> ProductDataService:
    """获取产品数据服务单例"""
    global _product_data_service

    if _product_data_service is None:
        _product_data_service = ProductDataService()

    return _product_data_service
