#!/usr/bin/env python3
"""Debug Shopee page structure - take screenshot and inspect elements"""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_shopee_page():
    """Debug Shopee page structure"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()
        url = "https://shopee.co.th/th/cat/110437"

        logger.info(f"访问: {url}")
        await page.goto(url, wait_until='networkidle', timeout=30000)

        # Wait for page to load
        await asyncio.sleep(5)

        # Scroll to load more
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)

        # Take screenshot
        await page.screenshot(path='shopee_debug.png', full_page=True)
        logger.info("截图已保存: shopee_debug.png")

        # Get page HTML
        html = await page.content()
        with open('shopee_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info("HTML已保存: shopee_debug.html")

        # Try different selectors
        selectors_to_try = [
            '.shopee-search-item-result__item',
            '[data-sqe="item"]',
            '.col-xs-2-4',
            '.shopee-item-card',
            '[class*="item-card"]',
            '[class*="product"]',
        ]

        logger.info("\n测试选择器:")
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                logger.info(f"  {selector}: 找到 {len(elements)} 个元素")
            except Exception as e:
                logger.info(f"  {selector}: 错误 - {e}")

        # Get all class names containing "item" or "product"
        logger.info("\n查找可能的商品容器...")
        all_elements = await page.query_selector_all('*')
        class_names = set()
        for elem in all_elements[:100]:  # Check first 100 elements
            try:
                class_attr = await elem.get_attribute('class')
                if class_attr and any(keyword in class_attr.lower() for keyword in ['item', 'product', 'card']):
                    class_names.add(class_attr)
            except:
                pass

        logger.info(f"找到的class名 (前20个): {list(class_names)[:20]}")

        await browser.close()
        logger.info("调试完成")


if __name__ == "__main__":
    asyncio.run(debug_shopee_page())
