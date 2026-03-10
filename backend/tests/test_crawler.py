# tests/test_crawler.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCrawlerSources:
    """测试爬虫数据源"""

    async def test_list_sources(self, client: AsyncClient, auth_headers):
        """测试列出数据源"""
        response = await client.get(
            "/api/v1/crawler/sources",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_list_sources_unauthorized(self, client: AsyncClient):
        """测试未授权访问数据源"""
        response = await client.get("/api/v1/crawler/sources")

        assert response.status_code == 401


@pytest.mark.asyncio
class TestCrawlerTrigger:
    """测试爬虫触发"""

    async def test_trigger_crawl_as_free_user(self, client: AsyncClient, auth_headers):
        """测试免费用户触发爬虫"""
        response = await client.post(
            "/api/v1/crawler/trigger/retail_dive",
            headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False

    async def test_trigger_crawl_as_pro_user(self, client: AsyncClient, pro_headers):
        """测试Pro用户触发爬虫"""
        response = await client.post(
            "/api/v1/crawler/trigger/retail_dive",
            headers=pro_headers
        )

        # 数据源不存在时返回404，权限正常时返回200
        assert response.status_code in [200, 404]

    async def test_trigger_nonexistent_source(self, client: AsyncClient, pro_headers):
        """测试触发不存在的数据源"""
        response = await client.post(
            "/api/v1/crawler/trigger/nonexistent_source",
            headers=pro_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


@pytest.mark.asyncio
class TestCrawlStatus:
    """测试爬取状态"""

    async def test_get_crawl_status(self, client: AsyncClient, auth_headers):
        """测试获取爬取状态"""
        response = await client.get(
            "/api/v1/crawler/status/retail_dive",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        assert data["source"] == "retail_dive"

    async def test_get_crawl_status_never_crawled(self, client: AsyncClient, auth_headers):
        """测试获取从未爬取的数据源状态"""
        response = await client.get(
            "/api/v1/crawler/status/shopify_blog",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "never"


@pytest.mark.asyncio
class TestArticles:
    """测试文章"""

    async def test_list_articles_empty(self, client: AsyncClient, auth_headers):
        """测试列出空文章列表"""
        response = await client.get(
            "/api/v1/crawler/articles",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 0
        assert len(data["articles"]) == 0

    async def test_list_articles_with_filters(self, client: AsyncClient, auth_headers):
        """测试带过滤器的文章列表"""
        response = await client.get(
            "/api/v1/crawler/articles?theme=opportunity&region=southeast_asia",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_list_articles_pagination(self, client: AsyncClient, auth_headers):
        """测试文章分页"""
        response = await client.get(
            "/api/v1/crawler/articles?page=1&per_page=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    async def test_list_articles_unauthorized(self, client: AsyncClient):
        """测试未授权访问文章列表"""
        response = await client.get("/api/v1/crawler/articles")

        assert response.status_code == 401

    async def test_get_article_not_found(self, client: AsyncClient, auth_headers):
        """测试获取不存在的文章"""
        import uuid
        article_id = uuid.uuid4()

        response = await client.get(
            f"/api/v1/crawler/articles/{article_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    async def test_get_article_invalid_id(self, client: AsyncClient, auth_headers):
        """测试使用无效ID获取文章"""
        response = await client.get(
            "/api/v1/crawler/articles/invalid-uuid",
            headers=auth_headers
        )

        assert response.status_code == 400
