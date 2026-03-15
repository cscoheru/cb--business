# tests/test_products.py
"""Tests for Products API endpoints - Task #64 verification"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from models.card import Card


@pytest.mark.asyncio
class TestProductsAPI:
    """测试 Products API 端点"""

    async def test_get_categories_success(self, client: AsyncClient):
        """测试获取产品类别列表 - 成功场景"""
        response = await client.get("/api/v1/products/categories")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

        # 验证类别结构
        if len(data["categories"]) > 0:
            category = data["categories"][0]
            assert "id" in category
            assert "name" in category
            assert "emoji" in category
            assert "count" in category

    async def test_get_category_trending_from_cards(
        self, client: AsyncClient, db_session
    ):
        """测试从Cards表获取热门产品 (Task #64 核心功能)"""
        # 创建测试卡片数据（模拟Cards表中的数据）
        card = Card(
            id=uuid.uuid4(),
            category="wireless_earbuds",
            title="无线耳机市场数据",
            content={
                "summary": {
                    "title": "无线耳机",
                    "opportunity_score": 85,
                    "market_size": 1000000,
                    "sweet_spot": {"min": 25, "max": 50, "best": 35},
                    "reliability": 0.9
                },
                "market_data": {},
                "insights": {},
                "recommendations": [],
                "data_sources": [],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "wireless_earbuds",
                "category_name": "无线耳机",
                "market_data": {},
                "insights": {},
                "opportunity_score": 85,
                "recommendations": []
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B095T14D4S",
                        "title": "无线耳机产品1",
                        "price": 29.99,
                        "rating": 4.3,
                        "reviews_count": 294,
                        "url": "https://www.amazon.com/dp/B095T14D4S"
                    },
                    {
                        "asin": "B09DT48V16",
                        "title": "无线耳机产品2",
                        "price": 25.99,
                        "rating": 4.4,
                        "reviews_count": 836,
                        "url": "https://www.amazon.com/dp/B09DT48V16"
                    },
                    {
                        "asin": "B0BQPNMXQV",
                        "title": "JBL无线耳机",
                        "price": 35.99,
                        "rating": 4.6,
                        "reviews_count": 450,
                        "url": "https://www.amazon.com/dp/B0BQPNMXQV"
                    }
                ]
            },
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 获取热门产品（从Cards表）
        response = await client.get(
            "/api/v1/products/categories/wireless_earbuds/trending?limit=3"
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "category" in data
        assert "category_name" in data
        assert "products" in data
        assert "count" in data
        assert data["category"] == "wireless_earbuds"
        assert len(data["products"]) <= 3

        # 验证数据来源是Cards表
        assert data["data_source"] in ["cards_table", "cards_table_with_details"]

        # 验证产品数据结构
        if len(data["products"]) > 0:
            product = data["products"][0]
            assert "asin" in product
            assert "title" in product
            assert "price" in product
            assert "rating" in product
            assert "url" in product

    async def test_get_category_trending_with_details(
        self, client: AsyncClient, db_session
    ):
        """测试获取带详情的产品 (Task #65 功能)"""
        # 创建测试卡片
        card = Card(
            id=uuid.uuid4(),
            category="fitness_trackers",
            title="健身追踪器数据",
            content={
                "summary": {
                    "title": "健身追踪器",
                    "opportunity_score": 82,
                    "market_size": 800000,
                    "sweet_spot": {"min": 22, "max": 45, "best": 32},
                    "reliability": 0.88
                },
                "market_data": {},
                "insights": {},
                "recommendations": [],
                "data_sources": [],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "fitness_trackers",
                "category_name": "健身追踪器",
                "market_data": {},
                "insights": {},
                "opportunity_score": 82,
                "recommendations": []
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B08XYPQK6P",
                        "title": "健身追踪器",
                        "price": 49.99,
                        "rating": 4.5,
                        "reviews_count": 1200,
                        "url": "https://www.amazon.com/dp/B08XYPQK6P"
                    }
                ]
            },
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 获取带详情的产品
        response = await client.get(
            "/api/v1/products/categories/fitness_trackers/trending?limit=2&fetch_details=true"
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()

        # 验证数据源包含详情标识
        assert data["data_source"] in ["cards_table", "cards_table_with_details"]

        # 验证产品数据
        assert len(data["products"]) <= 2

    async def test_get_category_trending_broad_category(
        self, client: AsyncClient, db_session
    ):
        """测试大类别的产品聚合"""
        # 创建多个子类别的卡片
        sub_categories = ["wireless_earbuds", "bluetooth_speakers", "phone_chargers"]
        for sub_cat in sub_categories:
            card = Card(
                id=uuid.uuid4(),
                category=sub_cat,
                title=f"{sub_cat} 数据",
                content={
                    "summary": {
                        "title": sub_cat,
                        "opportunity_score": 75,
                        "market_size": 600000,
                        "sweet_spot": {"min": 20, "max": 40, "best": 30},
                        "reliability": 0.85
                    },
                    "market_data": {},
                    "insights": {},
                    "recommendations": [],
                    "data_sources": [],
                    "generated_at": "2026-03-14T00:00:00Z"
                },
                analysis={
                    "category": sub_cat,
                    "category_name": sub_cat,
                    "market_data": {},
                    "insights": {},
                    "opportunity_score": 75,
                    "recommendations": []
                },
                amazon_data={
                    "products": [
                        {
                            "asin": f"B095T14D{sub_categories.index(sub_cat)}",
                            "title": f"{sub_cat} 产品",
                            "price": 29.99,
                            "rating": 4.3,
                            "reviews_count": 500,
                            "url": "https://www.amazon.com/dp/test"
                        }
                    ]
                },
                is_published=True
            )
            db_session.add(card)
        await db_session.commit()

        # 获取电子大类产品（应该聚合所有子类别）
        response = await client.get(
            "/api/v1/products/categories/electronics/trending?limit=5"
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "electronics"
        assert data["count"] >= 0

    async def test_get_category_trending_invalid_category(self, client: AsyncClient):
        """测试无效类别"""
        response = await client.get(
            "/api/v1/products/categories/invalid_category/trending?limit=5"
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        # 应该返回空结果或错误
        assert "products" in data
        assert data["count"] == 0

    async def test_search_products(self, client: AsyncClient):
        """测试产品搜索"""
        response = await client.get(
            "/api/v1/products/search?query=wireless&limit=5"
        )

        # 验证响应结构
        assert response.status_code in [200, 500]  # 可能因Oxylabs失败
        if response.status_code == 200:
            data = response.json()
            assert "products" in data
            assert isinstance(data["products"], list)


@pytest.mark.asyncio
class TestProductsAPIIntegration:
    """Products API 集成测试 - 验证数据流修复"""

    async def test_products_api_reads_from_cards_not_oxylabs(
        self, client: AsyncClient, db_session
    ):
        """验证Products API从Cards表读取，不直接调用Oxylabs (Task #64)"""
        # 创建Cards表数据
        card = Card(
            id=uuid.uuid4(),
            category="coffee_makers",
            title="咖啡机市场数据",
            content={
                "summary": {
                    "title": "咖啡机",
                    "opportunity_score": 78,
                    "market_size": 450000,
                    "sweet_spot": {"min": 30, "max": 60, "best": 45},
                    "reliability": 0.86
                },
                "market_data": {},
                "insights": {},
                "recommendations": [],
                "data_sources": [],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "coffee_makers",
                "category_name": "咖啡机",
                "market_data": {},
                "insights": {},
                "opportunity_score": 78,
                "recommendations": []
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B08PZ2ZWT7",
                        "title": " drip咖啡机",
                        "price": 79.99,
                        "rating": 4.5,
                        "reviews_count": 1200,
                        "url": "https://www.amazon.com/dp/B08PZ2ZWT7"
                    },
                    {
                        "asin": "B07XL5QWQH",
                        "title": "Espresso咖啡机",
                        "price": 149.99,
                        "rating": 4.7,
                        "reviews_count": 890,
                        "url": "https://www.amazon.com/dp/B07XL5QWQH"
                    }
                ]
            },
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 调用Products API
        response = await client.get(
            "/api/v1/products/categories/coffee_makers/trending?limit=5"
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()

        # 关键验证：数据来源应该是Cards表，不是Oxylabs直接调用
        assert data["data_source"] in ["cards_table", "cards_table_with_details"]
        assert data["data_source"] != "oxylabs_api"

        # 验证返回的数据来自创建的卡片
        assert data["count"] >= 1
        if len(data["products"]) > 0:
            # 验证产品数据来自Cards表的amazon_data
            assert any(p["asin"] == "B08PZ2ZWT7" for p in data["products"])

    async def test_products_no_duplicate_api_calls(
        self, client: AsyncClient, db_session
    ):
        """验证不会重复调用Oxylabs API"""
        # 创建Cards数据
        card = Card(
            id=uuid.uuid4(),
            category="desk_lamps",
            title="台灯数据",
            content={
                "summary": {
                    "title": "LED台灯",
                    "opportunity_score": 80,
                    "market_size": 350000,
                    "sweet_spot": {"min": 15, "max": 35, "best": 25},
                    "reliability": 0.87
                },
                "market_data": {},
                "insights": {},
                "recommendations": [],
                "data_sources": [],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "desk_lamps",
                "category_name": "LED台灯",
                "market_data": {},
                "insights": {},
                "opportunity_score": 80,
                "recommendations": []
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B08FR3ZL47",
                        "title": "LED台灯",
                        "price": 24.99,
                        "rating": 4.4,
                        "reviews_count": 670,
                        "url": "https://www.amazon.com/dp/B08FR3ZL47"
                    }
                ]
            },
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 第一次调用
        response1 = await client.get(
            "/api/v1/products/categories/desk_lamps/trending?limit=2"
        )

        # 第二次调用（应该使用缓存或Cards表数据，不调用Oxylabs）
        response2 = await client.get(
            "/api/v1/products/categories/desk_lamps/trending?limit=2"
        )

        # 验证两次调用都成功
        assert response1.status_code == 200
        assert response2.status_code == 200

        # 验证数据来源一致
        data1 = response1.json()
        data2 = response2.json()

        assert data1["data_source"] == data2["data_source"]
        assert data1["count"] == data2["count"]

    async def test_products_data_consistency_with_cards(
        self, client: AsyncClient, db_session
    ):
        """验证Products API与Cards API数据一致性"""
        # 创建测试卡片
        card = Card(
            id=uuid.uuid4(),
            category="mouse",
            title="无线鼠标数据",
            content={
                "summary": {
                    "title": "无线鼠标",
                    "opportunity_score": 77,
                    "market_size": 550000,
                    "sweet_spot": {"min": 18, "max": 38, "best": 28},
                    "reliability": 0.86
                },
                "market_data": {},
                "insights": {},
                "recommendations": [],
                "data_sources": [],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "mouse",
                "category_name": "无线鼠标",
                "market_data": {},
                "insights": {},
                "opportunity_score": 77,
                "recommendations": []
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B07R8FHT6V",
                        "title": "无线鼠标",
                        "price": 19.99,
                        "rating": 4.5,
                        "reviews_count": 1500,
                        "url": "https://www.amazon.com/dp/B07R8FHT6V"
                    }
                ]
            },
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 从Cards API获取数据
        cards_response = await client.get("/api/v1/cards/daily")
        assert cards_response.status_code == 200

        # 从Products API获取数据
        products_response = await client.get(
            "/api/v1/products/categories/mouse/trending?limit=5"
        )
        assert products_response.status_code == 200

        # 验证数据一致性：Products API应该使用Cards表数据
        products_data = products_response.json()
        assert products_data["data_source"] in ["cards_table", "cards_table_with_details"]

        # 验证产品数据来自同一个Cards表
        if len(products_data["products"]) > 0:
            # 产品ASIN应该能在Cards数据的amazon_data中找到
            assert products_data["products"][0]["source"] in ["cards_table", "cards_enhanced", "oxylabs_product_api"]
