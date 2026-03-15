# tests/test_cards.py
"""Tests for Cards API endpoints"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from models.card import Card


@pytest.mark.asyncio
class TestCardsAPI:
    """测试 Cards API 端点"""

    async def test_get_daily_cards_success(self, client: AsyncClient, db_session):
        """测试获取每日卡片 - 成功场景"""
        # 创建测试卡片数据
        card = Card(
            id=uuid.uuid4(),
            category="wireless_earbuds",
            title="测试无线耳机商机",
            content={
                "summary": {
                    "title": "无线耳机市场机会",
                    "opportunity_score": 85,
                    "market_size": 1000000,
                    "sweet_spot": {"min": 20, "max": 50, "best": 35},
                    "reliability": 0.9
                },
                "market_data": {
                    "price": {"min": 10, "max": 100, "avg": 50, "count": 100},
                    "rating": {"min": 3.5, "max": 5.0, "avg": 4.3, "count": 100}
                },
                "insights": {
                    "price_sweet_spot": {"min": 25, "max": 45, "best": 35},
                    "top_products": [],
                    "market_saturation": "medium"
                },
                "recommendations": ["建议1", "建议2"],
                "data_sources": ["oxylabs"],
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
                        "title": "测试产品",
                        "price": 29.99,
                        "rating": 4.3,
                        "reviews_count": 100
                    }
                ]
            },
            is_published=True,
            views=10,
            likes=5
        )
        db_session.add(card)
        await db_session.commit()

        # 调用 API
        response = await client.get("/api/v1/cards/daily")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "cards" in data
        assert isinstance(data["cards"], list)

    async def test_get_daily_cards_no_auth_required(self, client: AsyncClient):
        """测试获取每日卡片 - 无需认证"""
        response = await client.get("/api/v1/cards/daily")
        # 应该返回 200，即使没有数据
        assert response.status_code in [200, 404]

    async def test_get_card_by_id_success(self, client: AsyncClient, db_session):
        """测试通过 ID 获取卡片"""
        # 创建测试卡片
        card_id = uuid.uuid4()
        card = Card(
            id=card_id,
            category="fitness_trackers",
            title="测试健身追踪器",
            content={
                "summary": {
                    "title": "健身追踪器市场",
                    "opportunity_score": 75,
                    "market_size": 500000,
                    "sweet_spot": {"min": 15, "max": 40, "best": 25},
                    "reliability": 0.85
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
                "opportunity_score": 75,
                "recommendations": []
            },
            amazon_data={"products": []},
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 调用 API
        response = await client.get(f"/api/v1/cards/{card_id}")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["card"]["id"] == str(card_id)

    async def test_get_card_by_id_not_found(self, client: AsyncClient):
        """测试获取不存在的卡片"""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/cards/{fake_id}")
        assert response.status_code == 404

    async def test_like_card_success(self, client: AsyncClient, db_session):
        """测试点赞卡片"""
        # 创建测试卡片
        card = Card(
            id=uuid.uuid4(),
            category="phone_chargers",
            title="测试手机充电器",
            content={
                "summary": {
                    "title": "手机充电器",
                    "opportunity_score": 80,
                    "market_size": 800000,
                    "sweet_spot": {"min": 10, "max": 30, "best": 20},
                    "reliability": 0.88
                },
                "market_data": {},
                "insights": {},
                "recommendations": [],
                "data_sources": [],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "phone_chargers",
                "category_name": "手机充电器",
                "market_data": {},
                "insights": {},
                "opportunity_score": 80,
                "recommendations": []
            },
            amazon_data={"products": []},
            is_published=True,
            likes=0
        )
        db_session.add(card)
        await db_session.commit()

        initial_likes = card.likes

        # 调用点赞 API
        response = await client.post(f"/api/v1/cards/{card.id}/like")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["likes"] >= initial_likes

    async def test_get_latest_cards(self, client: AsyncClient, db_session):
        """测试获取最新卡片"""
        # 创建多个测试卡片
        for i in range(3):
            card = Card(
                id=uuid.uuid4(),
                category="desk_lamps",
                title=f"测试台灯 {i}",
                content={
                    "summary": {
                        "title": f"台灯 {i}",
                        "opportunity_score": 70 + i,
                        "market_size": 300000,
                        "sweet_spot": {"min": 15, "max": 35, "best": 25},
                        "reliability": 0.8
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
                    "opportunity_score": 70 + i,
                    "recommendations": []
                },
                amazon_data={"products": []},
                is_published=True
            )
            db_session.add(card)
        await db_session.commit()

        # 调用 API
        response = await client.get("/api/v1/cards/latest?limit=3")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["cards"]) <= 3

    async def test_get_card_stats(self, client: AsyncClient, db_session):
        """测试获取卡片统计"""
        # 创建不同类别的测试卡片
        categories = ["wireless_earbuds", "fitness_trackers", "smart_plugs"]
        for category in categories:
            card = Card(
                id=uuid.uuid4(),
                category=category,
                title=f"{category} 卡片",
                content={
                    "summary": {
                        "title": f"{category} 商机",
                        "opportunity_score": 75,
                        "market_size": 500000,
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
                    "category": category,
                    "category_name": category,
                    "market_data": {},
                    "insights": {},
                    "opportunity_score": 75,
                    "recommendations": []
                },
                amazon_data={"products": []},
                is_published=True
            )
            db_session.add(card)
        await db_session.commit()

        # 调用统计 API
        response = await client.get("/api/v1/cards/stats/overview")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "overview" in data
        assert "total_cards" in data["overview"]

    async def test_get_card_history_with_pagination(self, client: AsyncClient, db_session):
        """测试获取卡片历史 - 分页功能"""
        # 创建多个测试卡片
        for i in range(5):
            card = Card(
                id=uuid.uuid4(),
                category="bluetooth_speakers",
                title=f"蓝牙音箱 {i}",
                content={
                    "summary": {
                        "title": f"蓝牙音箱 {i}",
                        "opportunity_score": 70 + i,
                        "market_size": 400000,
                        "sweet_spot": {"min": 20, "max": 45, "best": 30},
                        "reliability": 0.82
                    },
                    "market_data": {},
                    "insights": {},
                    "recommendations": [],
                    "data_sources": [],
                    "generated_at": "2026-03-14T00:00:00Z"
                },
                analysis={
                    "category": "bluetooth_speakers",
                    "category_name": "蓝牙音箱",
                    "market_data": {},
                    "insights": {},
                    "opportunity_score": 70 + i,
                    "recommendations": []
                },
                amazon_data={"products": []},
                is_published=True
            )
            db_session.add(card)
        await db_session.commit()

        # 测试分页
        response = await client.get("/api/v1/cards/history?limit=3&skip=0")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["cards"]) <= 3
        assert data["total"] >= 5


@pytest.mark.asyncio
class TestCardsAPIIntegration:
    """Cards API 集成测试 - 测试完整的数据流"""

    async def test_cards_data_structure_completeness(self, client: AsyncClient, db_session):
        """测试卡片数据结构完整性"""
        # 创建包含完整数据的测试卡片
        card = Card(
            id=uuid.uuid4(),
            category="wireless_earbuds",
            title="完整数据测试卡片",
            content={
                "summary": {
                    "title": "无线耳机市场",
                    "opportunity_score": 85,
                    "market_size": 1000000,
                    "sweet_spot": {"min": 25, "max": 50, "best": 35},
                    "reliability": 0.92
                },
                "market_data": {
                    "price": {"min": 15, "max": 80, "avg": 45, "count": 150},
                    "rating": {"min": 3.8, "max": 4.8, "avg": 4.3, "count": 150}
                },
                "insights": {
                    "price_sweet_spot": {"min": 30, "max": 45, "best": 38},
                    "top_products": [
                        {
                            "asin": "B095T14D4S",
                            "title": "产品1",
                            "price": 35.99,
                            "rating": 4.5,
                            "reviews_count": 250
                        }
                    ],
                    "market_saturation": "low"
                },
                "recommendments": ["建议进入市场", "关注定价策略"],
                "data_sources": ["oxylabs", "google_trends"],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "wireless_earbuds",
                "category_name": "无线耳机",
                "market_data": {
                    "total_products": 150,
                    "price_analysis": {"min": 15, "max": 80, "avg": 45, "count": 150},
                    "rating_analysis": {"min": 3.8, "max": 4.8, "avg": 4.3, "count": 150},
                    "data_source": "oxylabs",
                    "reliability": 0.92,
                    "fetch_time": "2026-03-14T00:00:00Z"
                },
                "insights": {},
                "opportunity_score": 85,
                "recommendations": ["建议进入市场", "关注定价策略"]
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B095T14D4S",
                        "title": "无线耳机产品",
                        "price": 35.99,
                        "rating": 4.5,
                        "reviews_count": 250,
                        "url": "https://www.amazon.com/dp/B095T14D4S"
                    },
                    {
                        "asin": "B09DT48V16",
                        "title": "另一款无线耳机",
                        "price": 28.99,
                        "rating": 4.3,
                        "reviews_count": 180,
                        "url": "https://www.amazon.com/dp/B09DT48V16"
                    }
                ]
            },
            is_published=True,
            views=100,
            likes=25
        )
        db_session.add(card)
        await db_session.commit()

        # 获取卡片详情
        response = await client.get(f"/api/v1/cards/{card.id}")

        # 验证数据结构完整性
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        card_data = data["card"]
        assert "title" in card_data
        assert "category" in card_data
        assert "content" in card_data
        assert "analysis" in card_data
        assert "amazon_data" in card_data

        # 验证嵌套数据结构
        assert "summary" in card_data["content"]
        assert "opportunity_score" in card_data["content"]["summary"]
        assert "products" in card_data["amazon_data"]
        assert len(card_data["amazon_data"]["products"]) == 2
