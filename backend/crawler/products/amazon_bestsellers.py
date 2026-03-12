# crawler/products/amazon_bestsellers.py
"""Amazon Best Sellers 爬虫 - 使用公共页面，不需要 API"""

import asyncio
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


@dataclass
class AmazonProduct:
    """Amazon 商品数据模型"""
    asin: str  # Amazon Standard Identification Number
    title: str
    price: float
    original_price: Optional[float] = None
    rating: Optional[float] = None
    reviews_count: int = 0
    rank: int = 0  # Best Seller 排名
    category: str = None
    subcategory: str = None
    image_url: str = None
    product_url: str = None
    country: str = None
    platform: str = "amazon"

    # Prime 配送信息
    is_prime: bool = False

    # 卖家信息
    is_amazon_choice: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "asin": self.asin,
            "title": self.title,
            "price": self.price,
            "original_price": self.original_price,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "rank": self.rank,
            "category": self.category,
            "subcategory": self.subcategory,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "country": self.country,
            "platform": self.platform,
            "is_prime": self.is_prime,
            "is_amazon_choice": self.is_amazon,
        }


class AmazonBestSellersCrawler:
    """Amazon Best Sellers 爬虫"""

    # 各国 Amazon Best Sellers 配置
    COUNTRY_CONFIGS = {
        "us": {
            "url": "https://www.amazon.com",
            "name": "United States",
            "currency": "$",
            "categories": {
                "electronics": "Best-Sellers-Electronics/zgbs/pc",
                "clothing": "Best-Sellers-Clothing-Shoes-Jewelry/zgbs/fashion",
                "home": "Best-Sellers-Home-Kitchen/zgbs/home-garden",
                "toys": "Best-Sellers-Toys-Games/zgbs/toys-and-games",
                "beauty": "Best-Sellers-Beauty/zgbs/beauty",
                "sports": "Best-Sellers-Sports-Outdoors/zgbs/sporting-goods",
            },
        },
        "th": {
            "url": "https://www.amazon.co.th",
            "name": "Thailand",
            "currency": "฿",
            "categories": {
                "electronics": "Best-Sellers-Electronics/zgbs/pc",
                "home": "Best-Sellers-Home-Kitchen/zgbs/home-garden",
            },
        },
        "sg": {
            "url": "https://www.amazon.sg",
            "name": "Singapore",
            "currency": "SG$",
            "categories": {
                "electronics": "Best-Sellers-Electronics/zgbs/pc",
                "home": "Best-Sellers-Home-Kitchen/zgbs/home-garden",
            },
        },
        "vn": {
            "url": "https://www.amazon.com.vn",  # 可能需要确认
            "name": "Vietnam",
            "currency": "$",
            "categories": {
                "electronics": "Best-Sellers-Electronics/zgbs/pc",
            },
        },
    }

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context = None
        self.playwright = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()

        # 使用 stealth 减少检测
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )

        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )

        # 添加额外的 headers
        await self.context.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch_bestsellers(
        self,
        country: str,
        category: str = None,
        max_products: int = 50
    ) -> List[AmazonProduct]:
        """
        获取 Amazon Best Sellers

        Args:
            country: 国家代码 (us, th, sg, vn)
            category: 分类名称 (如 electronics, home)
            max_products: 最大商品数量

        Returns:
            商品列表
        """
        if country not in self.COUNTRY_CONFIGS:
            logger.error(f"不支持的 country: {country}")
            return []

        config = self.COUNTRY_CONFIGS[country]
        base_url = config["url"]

        # 如果没有指定分类，使用第一个分类
        if not category:
            categories = list(config["categories"].keys())
            category = categories[0] if categories else None

        if not category or category not in config["categories"]:
            logger.error(f"不支持的分类: {category}")
            return []

        category_path = config["categories"][category]
        url = f"{base_url}/{category_path}"

        products = []

        try:
            page = await self.context.new_page()
            page.set_default_timeout(30000)

            logger.info(f"正在访问: {url}")

            # 访问页面，等待网络空闲
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # 等待页面加载
            await asyncio.sleep(3)

            # Amazon 使用动态加载，滚动触发更多内容
            for i in range(2):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)

            # 尝试多种可能的商品容器选择器
            selectors = [
                '#gridItemRoot',  # 新版 Amazon
                '[data-component-type="s-search-result"]',
                '.s-result-item',
                '.zg-item-immersion',
                '[data-asin]',
            ]

            product_elements = []
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"使用选择器 '{selector}' 找到 {len(elements)} 个商品元素")
                    product_elements = elements
                    break

            if not product_elements:
                logger.warning("未找到商品元素，尝试备用方案...")
                # 尝试通过 ASIN 属性查找
                all_asin_elements = await page.query_selector_all('[data-asin]')
                product_elements = [e for e in all_asin_elements if await e.get_attribute('data-asin')]
                logger.info(f"通过 [data-asin] 找到 {len(product_elements)} 个商品")

            logger.info(f"开始解析 {len(product_elements)} 个商品")

            for i, elem in enumerate(product_elements[:max_products]):
                try:
                    product = await self._parse_product_element(elem, country, category)
                    if product and product.asin:
                        products.append(product)
                        logger.info(f"解析商品 {i+1}/{len(product_elements)}: {product.title[:50]}")
                except Exception as e:
                    logger.error(f"解析商品 {i} 失败: {e}")
                    continue

            await page.close()

        except Exception as e:
            logger.error(f"获取 {country} Best Sellers 失败: {e}")

        logger.info(f"{country} Best Sellers 获取完成: {len(products)} 个")
        return products

    async def _parse_product_element(
        self,
        element,
        country: str,
        category: str
    ) -> Optional[AmazonProduct]:
        """解析商品元素"""
        try:
            # Amazon Best Sellers 页面结构:
            # #gridItemRoot 包含排名徽章和商品信息
            # ASIN 在链接中 (/dp/ASIN)

            # 从商品链接中提取 ASIN
            product_links = await element.query_selector_all('a.a-link-normal[href*="/dp/"]')
            asin = None
            product_url = ""

            if product_links:
                href = await product_links[0].get_attribute('href')
                if href:
                    # 从 URL 中提取 ASIN
                    import re
                    asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                    if asin_match:
                        asin = asin_match.group(1)

                    # 构建完整 URL
                    if href.startswith('/'):
                        base_url = self.COUNTRY_CONFIGS[country]["url"]
                        product_url = f"{base_url}{href}"

            if not asin:
                return None

            # 商品标题 - 查找包含商品标题的链接
            title = ""
            title_links = await element.query_selector_all('a.a-link-normal, div.a-section.a-spacing-small p')
            for link in title_links:
                try:
                    text = await link.inner_text()
                    if text and len(text) > 15 and len(text) < 200:  # 标题通常在这个长度范围内
                        # 过滤掉评分、价格等非标题内容
                        if not any(x in text.lower() for x in ['stars', 'rating', '$', 'offers', 'prime']):
                            title = text.strip()
                            break
                except:
                    pass

            if not title:
                title = f"Amazon Product {asin}"

            # 价格
            price = 0.0
            original_price = None
            price_selectors = [
                '.a-price .a-offscreen',
                '.a-price-whole',
                '[data-a-color="price"] .a-offscreen',
            ]
            for selector in price_selectors:
                price_elem = await element.query_selector(selector)
                if price_elem:
                    price_text = await price_elem.inner_text()
                    price = self._parse_price(price_text)
                    if price > 0:
                        break

            # 原价（折扣商品）
            original_price_elem = await element.query_selector('.a-price.a-text-price .a-offscreen')
            if original_price_elem:
                original_price_text = await original_price_elem.inner_text()
                original_price = self._parse_price(original_price_text)

            # 评分
            rating = None
            rating_elem = await element.query_selector('i.a-icon-alt, [aria-label*="stars"]')
            if rating_elem:
                rating_text = await rating_elem.inner_text() or await rating_elem.get_attribute('aria-label')
                rating = self._parse_rating(rating_text)

            # 评论数
            reviews_count = 0
            reviews_elem = await element.query_selector('a span[href*="#customerReviews"], .a-size-base')
            if reviews_elem:
                reviews_text = await reviews_elem.inner_text()
                reviews_count = self._parse_reviews_count(reviews_text)

            # 图片
            image_url = None
            image_elem = await element.query_selector('.s-image, img')
            if image_elem:
                image_url = await image_elem.get_attribute('src') or await image_elem.get_attribute('data-src')

            # 排名（从 class 或 aria 获取）
            rank = 0
            rank_elem = await element.query_selector('[data-rank], .zg-badge-text')
            if rank_elem:
                rank_text = await rank_elem.inner_text() or await rank_elem.get_attribute('data-rank')
                if rank_text:
                    rank_match = re.search(r'(\d+)', rank_text.replace(',', ''))
                    if rank_match:
                        rank = int(rank_match.group(1))

            # Prime 标识
            is_prime = False
            prime_elem = await element.query_selector('[data-cel-widget="prime-badge"], .prime-badge')
            if prime_elem:
                is_prime = True

            # Amazon's Choice 标识
            is_amazon_choice = False
            choice_elem = await element.query_selector('.ac-badge-wrapper, [data-a-badge-type="amzn-choice"]')
            if choice_elem:
                is_amazon_choice = True

            return AmazonProduct(
                asin=asin,
                title=title.strip(),
                price=price,
                original_price=original_price,
                rating=rating,
                reviews_count=reviews_count,
                rank=rank,
                category=category,
                subcategory=None,
                image_url=image_url,
                product_url=product_url,
                country=country,
                platform="amazon",
                is_prime=is_prime,
                is_amazon_choice=is_amazon_choice,
            )

        except Exception as e:
            logger.error(f"解析商品元素失败: {e}")
            return None

    def _parse_price(self, price_text: str) -> float:
        """解析价格"""
        if not price_text:
            return 0.0

        # 移除货币符号、空格、逗号
        price_text = price_text.strip()
        price_text = re.sub(r'[^\d.]', '', price_text)

        try:
            return float(price_text)
        except ValueError:
            return 0.0

    def _parse_rating(self, rating_text: str) -> Optional[float]:
        """解析评分"""
        if not rating_text:
            return None

        # 格式: "4.5 out of 5 stars", "4,5 sterren", "4.5"
        match = re.search(r'([\d.,]+)', rating_text.replace(',', '.'))
        if match:
            try:
                rating = float(match.group(1))
                if 0 <= rating <= 5:
                    return rating
            except ValueError:
                pass

        return None

    def _parse_reviews_count(self, count_text: str) -> int:
        """解析评论数"""
        if not count_text:
            return 0

        # 格式: "(1,234)", "1.2K", "1,234 ratings"
        count_text = count_text.strip().replace('(', '').replace(')', '').replace(',', '')

        # 处理 K 单位
        if 'k' in count_text.lower():
            match = re.search(r'([\d.]+)k', count_text.lower())
            if match:
                return int(float(match.group(1)) * 1000)

        # 直接提取数字
        match = re.search(r'(\d+)', count_text)
        if match:
            return int(match.group(1))

        return 0

    async def fetch_all_categories(
        self,
        country: str,
        max_products_per_category: int = 20
    ) -> Dict[str, List[AmazonProduct]]:
        """获取指定国家所有分类的 Best Sellers"""
        if country not in self.COUNTRY_CONFIGS:
            logger.error(f"不支持的 country: {country}")
            return {}

        config = self.COUNTRY_CONFIGS[country]
        results = {}

        for category_name, category_path in config["categories"].items():
            try:
                logger.info(f"获取 {country} - {category_name} 分类...")
                products = await self.fetch_bestsellers(
                    country=country,
                    category=category_name,
                    max_products=max_products_per_category
                )
                results[category_name] = products

                # 避免请求过快
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"获取 {country} - {category_name} 失败: {e}")
                results[category_name] = []

        return results

    async def get_product_details(self, country: str, asin: str) -> Optional[AmazonProduct]:
        """
        获取单个商品的详细信息

        Args:
            country: 国家代码
            asin: 商品 ASIN

        Returns:
            商品详情
        """
        config = self.COUNTRY_CONFIGS.get(country, self.COUNTRY_CONFIGS["us"])
        url = f"{config['url']}/dp/{asin}"

        try:
            page = await self.context.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)

            # 这里可以解析商品详情页获取更多信息
            # 暂时返回基础信息

            await page.close()

        except Exception as e:
            logger.error(f"获取商品详情失败 ({asin}): {e}")

        return None


# ==================== 测试代码 ====================

async def test_amazon_bestsellers():
    """测试 Amazon Best Sellers 爬虫"""
    async with AmazonBestSellersCrawler() as crawler:
        # 测试获取美国电子产品 Best Sellers
        products = await crawler.fetch_bestsellers(
            country="us",
            category="electronics",
            max_products=10
        )

        print(f"\n获取到 {len(products)} 个商品:")
        for i, product in enumerate(products[:10], 1):
            print(f"{i}. [{product.rank}] {product.title}")
            print(f"   ASIN: {product.asin}")
            print(f"   价格: ${product.price}")
            print(f"   评分: {product.rating} ({product.reviews_count} 评论)")
            print()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(test_amazon_bestsellers())
