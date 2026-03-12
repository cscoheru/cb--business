#!/usr/bin/env python3
"""Debug Amazon 页面结构"""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_amazon_page():
    """Debug Amazon Best Sellers page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        page = await context.new_page()
        url = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/pc"

        logger.info(f"访问: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)

        await asyncio.sleep(3)

        # 滚动加载更多
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)

        # 检查各种选择器
        selectors = [
            '#gridItemRoot',
            '[data-component-type="s-search-result"]',
            '.s-result-item',
            '[data-asin]',
            '.p13n-sc-static-release',
            '.zg-item-immersion',
        ]

        for selector in selectors:
            elements = await page.query_selector_all(selector)
            logger.info(f"选择器 '{selector}': {len(elements)} 个元素")

        # Amazon Best Sellers 页面特殊结构
        # 获取所有包含商品信息的容器
        logger.info("\n查找包含 ASIN 的父元素...")

        # 尝试通过查找包含链接的元素来定位商品
        product_links = await page.query_selector_all('#gridItemRoot a.a-link-normal')
        logger.info(f"找到 {len(product_links)} 个商品链接")

        # 检查前几个链接的 href 和内容
        for i, link in enumerate(product_links[:5]):
            href = await link.get_attribute('href')
            logger.info(f"  链接 {i}: {href[:100] if href else 'None'}")

            # 获取链接文本
            try:
                text = await link.inner_text()
                if text and len(text) > 10:
                    logger.info(f"    文本: {text[:80]}")
            except:
                pass

            # 检查是否有 ASIN 在链接中
            if href and '/dp/' in href:
                import re
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                if asin_match:
                    logger.info(f"    ASIN: {asin_match.group(1)}")

        for selector in selectors:
            elements = await page.query_selector_all(selector)
            logger.info(f"选择器 '{selector}': {len(elements)} 个元素")

            if elements and selector == '[data-asin]':
                # 检查前几个元素的 ASIN
                for i, elem in enumerate(elements[:5]):
                    asin = await elem.get_attribute('data-asin')
                    logger.info(f"  元素 {i}: ASIN = {asin}")

                    # 获取标题 - 尝试更多选择器
                    title_selectors = [
                        'h2 a span',
                        '.a-size-mini a span',
                        '#gridItemRoot h2 span',
                        '[data-cy="title-recipe-title"]',
                        'h2 .a-link-normal span',
                        '.p13n-sc-truncate',
                        'div.a-section.a-spacing-small span',
                    ]
                    title_found = False
                    for title_sel in title_selectors:
                        try:
                            title_elem = await elem.query_selector(title_sel)
                            if title_elem:
                                title = await title_elem.inner_text()
                                if title and len(title) > 5:
                                    logger.info(f"    标题 ({title_sel}): {title[:50]}")
                                    title_found = True
                                    break
                        except Exception as e:
                            pass

                    if not title_found:
                        logger.info(f"    未找到标题")
                        # 获取元素的 innerHTML 看看结构
                        try:
                            html = await elem.inner_html()
                            logger.info(f"    HTML 预览: {html[:200]}")
                        except:
                            pass

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_amazon_page())
