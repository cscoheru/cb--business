# crawler/products/shopee_trending.py
"""Shopee热销商品爬虫 - 使用公共页面，不需要API"""

import asyncio
import re
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


@dataclass
class ShopeeProduct:
    """Shopee商品数据模型"""
    title: str
    price: float
    original_price: float = None
    sold_count: int = 0
    rating: float = None
    reviews_count: int = 0
    shop_id: str = None
    item_id: str = None
    image: str = None
    link: str = None
    category: str = None
    country: str = None
    platform: str = "shopee"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "price": self.price,
            "original_price": self.original_price,
            "sold_count": self.sold_count,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "shop_id": self.shop_id,
            "item_id": self.item_id,
            "image": self.image,
            "link": self.link,
            "category": self.category,
            "country": self.country,
            "platform": self.platform,
        }


class ShopeeTrendingCrawler:
    """Shopee热销商品爬虫"""

    # 各国Shopee域名配置
    COUNTRY_CONFIGS = {
        "th": {
            "url": "https://shopee.co.th",
            "name": "Thailand",
            "categories": [
                "/th/cat/110437",  # 电子产品
                "/th/shop-category/110394",  # 时尚服饰
                "/th/cat/110495",  # 美妆保健
                "/th/cat/110438",  # 家居生活
            ],
        },
        "vn": {
            "url": "https://shopee.vn",
            "name": "Vietnam",
            "categories": [
                "/vn/category/110394",  # 时尚服饰
                "/vn/category/110437",  # 电子产品
            ],
        },
        "my": {
            "url": "https://shopee.com.my",
            "name": "Malaysia",
            "categories": [
                "/my-category/110437",  # 电子产品
                "/my-category/110394",  # 时尚服饰
            ],
        },
        "sg": {
            "url": "https://shopee.sg",
            "name": "Singapore",
            "categories": [
                "/sg/category/110437",  # 电子产品
            ],
        },
        "id": {
            "url": "https://shopee.co.id",
            "name": "Indonesia",
            "categories": [
                "/id/category/110437",  # 电子产品
            ],
        },
        "ph": {
            "url": "https://shopee.ph",
            "name": "Philippines",
            "categories": [
                "/ph/category/110437",  # 电子产品
            ],
        },
    }

    def __init__(self):
        self.browser = None
        self.context = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def start(self):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def fetch_trending_products(
        self,
        country: str,
        category: str = None,
        max_products: int = 100
    ) -> List[ShopeeProduct]:
        """
        获取Shopee热销商品

        Args:
            country: 国家代码 (th, vn, my, sg, id, ph)
            category: 分类URL (可选)
            max_products: 最大商品数量

        Returns:
            商品列表
        """
        if country not in self.COUNTRY_CONFIGS:
            logger.error(f"不支持的 country: {country}")
            return []

        config = self.COUNTRY_CONFIGS[country]
        base_url = config["url"]

        # 如果没有指定分类，使用默认分类
        if not category:
            categories = config["categories"]
            category = categories[0] if categories else ""

        url = f"{base_url}{category}"
        products = []

        try:
            page = await self.context.new_page()

            # 设置超时和重试
            page.set_default_timeout(30000)

            logger.info(f"正在访问: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # 等待页面加载
            await asyncio.sleep(3)

            # 滚动加载更多商品
            for _ in range(3):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)

            # 提取商品数据
            product_elements = await page.query_selector_all('.shopee-search-item-result__item')

            logger.info(f"找到 {len(product_elements)} 个商品元素")

            for i, elem in enumerate(product_elements[:max_products]):
                try:
                    product = await self._parse_product_element(elem, country)
                    if product:
                        products.append(product)
                        logger.info(f"解析商品 {i+1}/{len(product_elements)}: {product.title[:50]}")
                except Exception as e:
                    logger.error(f"解析商品 {i} 失败: {e}")
                    continue

            await page.close()

        except Exception as e:
            logger.error(f"获取 {country} 热销商品失败: {e}")

        logger.info(f"{country} 热销商品获取完成: {len(products)} 个")
        return products

    async def _parse_product_element(self, element, country: str) -> ShopeeProduct:
        """解析商品元素"""
        try:
            # 商品标题
            title_elem = await element.query_selector('.shopee-item-card__subject-link')
            title = await title_elem.inner_text() if title_elem else ""

            # 商品链接
            link = await title_elem.get_attribute('href') if title_elem else ""

            # 提取 shop_id 和 item_id
            shop_id, item_id = self._extract_ids_from_link(link)

            # 价格
            price_elem = await element.query_selector('.shopee-shopping-cart-fee-price')
            price_text = await price_elem.inner_text() if price_elem else "0"
            price = self._parse_price(price_text)

            # 原价（如果有折扣）
            original_price_elem = await element.query_selector('.shopee-item-card__original-price')
            original_price = None
            if original_price_elem:
                original_price_text = await original_price_elem.inner_text()
                original_price = self._parse_price(original_price_text)

            # 销量
            sold_elem = await element.query_selector('.shopee-item-card__sold-count')
            sold_count = 0
            if sold_elem:
                sold_text = await sold_elem.inner_text()
                sold_count = self._parse_sold_count(sold_text)

            # 评分
            rating_elem = await element.query_selector('.shopee-item-card__rating')
            rating = None
            reviews_count = 0
            if rating_elem:
                rating_text = await rating_elem.get_attribute('title') or ""
                rating = self._parse_rating(rating_text)

                # 评论数
                rating_count_elem = await rating_elem.query_selector('.shopee-item-card__rating-count')
                if rating_count_elem:
                    count_text = await rating_count_elem.inner_text()
                    reviews_count = self._parse_reviews_count(count_text)

            # 图片
            image_elem = await element.query_selector('.shopee-item-card__cover img')
            image = None
            if image_elem:
                image = await image_elem.get_attribute('src') or await image_elem.get_attribute('data-src')

            # 分类（从链接推断）
            category = self._extract_category_from_link(link)

            return ShopeeProduct(
                title=title.strip(),
                price=price,
                original_price=original_price,
                sold_count=sold_count,
                rating=rating,
                reviews_count=reviews_count,
                shop_id=shop_id,
                item_id=item_id,
                image=image,
                link=link,
                category=category,
                country=country,
                platform="shopee",
            )

        except Exception as e:
            logger.error(f"解析商品元素失败: {e}")
            return None

    def _extract_ids_from_link(self, link: str) -> tuple:
        """从链接中提取 shop_id 和 item_id"""
        if not link:
            return None, None

        # Shopee链接格式: /product-name-i.{item_id}-s.{shop_id}
        match = re.search(r'-i\.(\d+)-s\.(\d+)', link)
        if match:
            item_id = match.group(1)
            shop_id = match.group(2)
            return shop_id, item_id

        # 另一种格式
        match = re.search(r'/i\.(\d+)/(\d+)', link)
        if match:
            item_id = match.group(2)
            shop_id = match.group(1)
            return shop_id, item_id

        return None, None

    def _parse_price(self, price_text: str) -> float:
        """解析价格"""
        if not price_text:
            return 0.0

        # 移除货币符号和空格
        price_text = price_text.strip().replace(',', '').replace('฿', '').replace('₫', '').replace('RM', '').replace('SG$', '').replace('Rp', '').replace('₱', '')

        try:
            return float(price_text)
        except ValueError:
            return 0.0

    def _parse_sold_count(self, sold_text: str) -> int:
        """解析销量"""
        if not sold_text:
            return 0

        # 格式: "已售1.2万", "1K+ sold", "234 sold"
        sold_text = sold_text.strip().lower()

        # 提取数字
        match = re.search(r'([\d.]+)([k万]?)', sold_text)
        if match:
            num = float(match.group(1))
            unit = match.group(2)

            if unit in ['k', 'k+']:
                return int(num * 1000)
            elif unit in ['万']:
                return int(num * 10000)
            else:
                return int(num)

        # 直接提取数字
        numbers = re.findall(r'\d+', sold_text)
        if numbers:
            return int(numbers[0])

        return 0

    def _parse_rating(self, rating_text: str) -> float:
        """解析评分"""
        if not rating_text:
            return None

        # 格式: "4.5", "4.5/5"
        match = re.search(r'(\d+\.?\d*)', rating_text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        return None

    def _parse_reviews_count(self, count_text: str) -> int:
        """解析评论数"""
        if not count_text:
            return 0

        # 格式: "(1.2K)", "(234)", "1.2K"
        count_text = count_text.strip().replace('(', '').replace(')', '').replace(',', '')

        # 处理K单位
        if 'k' in count_text.lower():
            match = re.search(r'([\d.]+)k', count_text.lower())
            if match:
                return int(float(match.group(1)) * 1000)

        # 直接提取数字
        match = re.search(r'\d+', count_text)
        if match:
            return int(match.group(1))

        return 0

    def _extract_category_from_link(self, link: str) -> str:
        """从链接中提取分类"""
        if not link:
            return None

        # 从URL路径提取分类
        parts = link.strip('/').split('/')
        if len(parts) > 1:
            # 通常分类在第二或第三部分
            return parts[1] if len(parts) > 1 else None

        return None

    async def fetch_all_countries(
        self,
        max_products_per_country: int = 50
    ) -> Dict[str, List[ShopeeProduct]]:
        """获取所有国家的热销商品"""
        results = {}

        for country in self.COUNTRY_CONFIGS.keys():
            try:
                products = await self.fetch_trending_products(
                    country=country,
                    max_products=max_products_per_country
                )
                results[country] = products

                # 避免请求过快
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"获取 {country} 数据失败: {e}")
                results[country] = []

        return results


# 测试代码
async def test_shopee_crawler():
    """测试Shopee爬虫"""
    async with ShopeeTrendingCrawler() as crawler:
        # 测试获取泰国热销商品
        products = await crawler.fetch_trending_products(
            country="th",
            max_products=20
        )

        print(f"\n获取到 {len(products)} 个商品:")
        for i, product in enumerate(products[:10], 1):
            print(f"{i}. {product.title}")
            print(f"   价格: ฿{product.price}")
            print(f"   销量: {product.sold_count}")
            print(f"   评分: {product.rating}")
            print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_shopee_crawler())
