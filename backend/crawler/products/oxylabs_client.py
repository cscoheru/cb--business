# crawler/products/oxylabs_client.py
"""Oxylabs API 客户端 - 替代 Playwright 爬虫

Oxylabs 提供专业的网页抓取 API，无需维护浏览器
- Amazon Product API: 产品详情、价格、评论
- Google Search API: 搜索趋势、知识图谱
- Universal Scraper: 任意网页内容

文档: https://developers.oxylabs.io/
"""

import os
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class OxylabsConfig:
    """Oxylabs API 配置"""
    base_url: str = "https://realtime.oxylabs.io/v1/queries"
    username: str = os.getenv("OXYLABS_USERNAME", "fisher_VEpfJ")
    password: str = os.getenv("OXYLABS_PASSWORD", "z7UnsI2Hkug_")

    @property
    def auth(self) -> tuple:
        return (self.username, self.password)


class OxylabsClient:
    """Oxylabs API 客户端"""

    def __init__(self, config: Optional[OxylabsConfig] = None):
        self.config = config or OxylabsConfig()
        self.client = httpx.AsyncClient(
            auth=self.config.auth,
            timeout=60.0,
            headers={"Content-Type": "application/json"}
        )

    async def close(self):
        await self.client.aclose()

    async def _request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求到 Oxylabs API"""
        try:
            response = await self.client.post(
                self.config.base_url,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # 检查任务状态
            job = data.get("job", {})
            if job.get("status") == "done":
                return data
            else:
                logger.warning(f"Job status: {job.get('status')}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"Oxylabs API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Oxylabs request failed: {e}")
            raise

    async def get_amazon_product(
        self,
        asin: str,
        domain: str = "com",
        geo_location: str = "90210"
    ) -> Dict[str, Any]:
        """
        获取 Amazon 产品详情

        Args:
            asin: Amazon ASIN (例如: B07FZ8S74R)
            domain: 域名 (com, co.uk, de, jp 等)
            geo_location: 地理位置代码

        Returns:
            产品数据字典，包含:
            - asin, title, brand, price, rating
            - images, bullet_points, reviews
            - stock, sales_rank 等
        """
        payload = {
            "source": "amazon_product",
            "query": asin,
            "domain": domain,
            "geo_location": geo_location,
            "parse": True
        }

        data = await self._request(payload)

        if data.get("results"):
            return data["results"][0]["content"]
        return {}

    async def search_amazon(
        self,
        query: str,
        domain: str = "com",
        category: Optional[str] = "aps",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索 Amazon 产品

        Args:
            query: 搜索关键词
            domain: 域名
            category: 分类 ID (aps=全部, electronics=电子产品)
            limit: 返回数量

        Returns:
            产品列表
        """
        payload = {
            "source": "amazon_search",
            "query": query,
            "domain": domain,
            "category": category,
            "parse": True,
            "limit": limit
        }

        data = await self._request(payload)

        if data.get("results"):
            content = data["results"][0].get("content", {})
            # 返回 organic 搜索结果（自然排名，非广告）
            if isinstance(content, dict):
                return content.get("organic", [])
            elif isinstance(content, list):
                return content
        return []

    async def get_amazon_bestsellers(
        self,
        category: str = "electronics",
        domain: str = "com",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取 Amazon Best Sellers

        由于 Oxylabs Best Sellers API 目前不稳定，此方法使用搜索API
        配合分类关键词来获取热门产品。

        Args:
            category: 分类名称 (URL 路径)
            domain: 域名
            limit: 返回数量

        Returns:
            产品列表
        """
        # 分类关键词映射
        category_keywords = {
            "electronics": "best selling electronics",
            "beauty": "best selling beauty products",
            "home": "best selling home products",
            "fashion": "best selling fashion clothing",
            "home-garden": "best selling home garden",
            "grocery": "best selling food grocery",
            "baby-products": "best selling baby products",
            "sports-fitness": "best selling sports fitness",
            "pets": "best selling pet supplies",
        }

        # 获取对应分类的搜索关键词
        search_query = category_keywords.get(category, f"best selling {category}")

        # 使用搜索API获取热门产品
        payload = {
            "source": "amazon_search",
            "query": search_query,
            "domain": domain,
            "parse": True,
            "limit": limit
        }

        try:
            data = await self._request(payload)

            if data.get("results"):
                content = data["results"][0].get("content", {})
                if isinstance(content, dict):
                    # 合并 organic 和 amazons_choices 结果
                    organic = content.get("organic", [])
                    choices = content.get("amazons_choices", [])
                    # 优先返回 organic，如果不够则补充 choices
                    results = organic[:limit]
                    if len(results) < limit:
                        results.extend(choices[:limit - len(results)])
                    return results
                elif isinstance(content, list):
                    return content[:limit]
        except Exception as e:
            logger.warning(f"Best Sellers fallback to search failed: {e}")

        return []

    async def google_search(
        self,
        query: str,
        geo_location: str = "California,United States",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Google 搜索

        Args:
            query: 搜索关键词
            geo_location: 地理位置
            limit: 返回数量

        Returns:
            搜索结果，包含:
            - organic: 有机搜索结果
            - knowledge: 知识图谱数据
            - ads: 广告结果
        """
        payload = {
            "source": "google_search",
            "query": query,
            "geo_location": geo_location,
            "parse": True,
            "limit": limit
        }

        data = await self._request(payload)

        if data.get("results"):
            return data["results"][0]["content"]
        return {}

    async def scrape_url(
        self,
        url: str,
        render: bool = False
    ) -> str:
        """
        通用网页抓取

        Args:
            url: 目标 URL
            render: 是否渲染 JavaScript

        Returns:
            HTML 内容
        """
        payload = {
            "source": "universal",
            "url": url,
            "render": render
        }

        data = await self._request(payload)

        if data.get("results"):
            return data["results"][0]["content"]
        return ""


# 使用示例
async def main():
    """测试 Oxylabs API"""
    client = OxylabsClient()

    try:
        # 1. 获取 Amazon 产品
        product = await client.get_amazon_product("B07FZ8S74R")
        print(f"Product: {product.get('title')}")
        print(f"Rating: {product.get('rating')}/5")
        print(f"Price: ${product.get('price')}")

        # 2. Google 搜索
        search = await client.google_search("adidas")
        print(f"Search results: {len(search.get('results', []))}")

    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
