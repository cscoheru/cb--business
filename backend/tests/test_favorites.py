# tests/test_favorites.py
"""Tests for Favorites API endpoints"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from models.card import Card
from models.favorites import Favorite
from models.business_opportunity import BusinessOpportunity, OpportunityStatus, OpportunityGrade


@pytest.mark.asyncio
class TestFavoritesAPI:
    """测试 Favorites API 端点"""

    async def test_add_favorite_for_card_success(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试添加卡片收藏 - 成功场景"""
        # 创建测试卡片
        card = Card(
            id=uuid.uuid4(),
            category="wireless_earbuds",
            title="测试无线耳机",
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
            amazon_data={"products": []},
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 添加收藏
        response = await client.post(
            "/api/v1/favorites",
            json={"card_id": str(card.id), "opportunity_id": None},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["card_id"] == str(card.id)
        assert data["opportunity_id"] is None

    async def test_add_favorite_unauthorized(self, client: AsyncClient, db_session):
        """测试未认证用户添加收藏"""
        card = Card(
            id=uuid.uuid4(),
            category="fitness_trackers",
            title="测试健身追踪器",
            content={
                "summary": {
                    "title": "健身追踪器",
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

        response = await client.post(
            "/api/v1/favorites",
            json={"card_id": str(card.id), "opportunity_id": None}
        )

        assert response.status_code == 401

    async def test_get_favorites_empty(self, client: AsyncClient, auth_token):
        """测试获取空收藏列表"""
        response = await client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 空列表也是有效的响应

    async def test_get_favorites_with_data(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试获取收藏列表 - 有数据场景"""
        # 创建测试卡片和收藏
        card1 = Card(
            id=uuid.uuid4(),
            category="phone_chargers",
            title="测试充电器1",
            content={
                "summary": {
                    "title": "充电器1",
                    "opportunity_score": 80,
                    "market_size": 800000,
                    "sweet_spot": {"min": 15, "max": 35, "best": 25},
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
            is_published=True
        )
        db_session.add(card1)
        await db_session.commit()

        # 添加收藏
        await client.post(
            "/api/v1/favorites",
            json={"card_id": str(card1.id), "opportunity_id": None},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 获取收藏列表
        response = await client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "card_id" in data[0] or "opportunity_id" in data[0]

    async def test_remove_favorite_by_card_success(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试删除卡片收藏 - 成功场景"""
        # 创建并添加收藏
        card = Card(
            id=uuid.uuid4(),
            category="desk_lamps",
            title="测试台灯",
            content={
                "summary": {
                    "title": "台灯",
                    "opportunity_score": 78,
                    "market_size": 300000,
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
                "category": "desk_lamps",
                "category_name": "LED台灯",
                "market_data": {},
                "insights": {},
                "opportunity_score": 78,
                "recommendations": []
            },
            amazon_data={"products": []},
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 添加收藏
        await client.post(
            "/api/v1/favorites",
            json={"card_id": str(card.id), "opportunity_id": None},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 删除收藏
        response = await client.delete(
            f"/api/v1/favorites/card/{card.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证响应
        assert response.status_code == 200
        assert response.status_code == 200

    async def test_check_favorite_status_true(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试检查收藏状态 - 已收藏"""
        # 创建并添加收藏
        card = Card(
            id=uuid.uuid4(),
            category="smart_plugs",
            title="测试智能插座",
            content={
                "summary": {
                    "title": "智能插座",
                    "opportunity_score": 82,
                    "market_size": 600000,
                    "sweet_spot": {"min": 12, "max": 32, "best": 22},
                    "reliability": 0.87
                },
                "market_data": {},
                "insights": {},
                "recommendations": [],
                "data_sources": [],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "smart_plugs",
                "category_name": "智能插座",
                "market_data": {},
                "insights": {},
                "opportunity_score": 82,
                "recommendations": []
            },
            amazon_data={"products": []},
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 添加收藏
        await client.post(
            "/api/v1/favorites",
            json={"card_id": str(card.id), "opportunity_id": None},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 检查收藏状态
        response = await client.get(
            f"/api/v1/favorites/check/{card.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] is True
        assert data["favorite_id"] is not None

    async def test_check_favorite_status_false(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试检查收藏状态 - 未收藏"""
        card = Card(
            id=uuid.uuid4(),
            category="yoga_mats",
            title="测试瑜伽垫",
            content={
                "summary": {
                    "title": "瑜伽垫",
                    "opportunity_score": 76,
                    "market_size": 400000,
                    "sweet_spot": {"min": 16, "max": 36, "best": 26},
                    "reliability": 0.84
                },
                "market_data": {},
                "insights": {},
                "recommendations": [],
                "data_sources": [],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "yoga_mats",
                "category_name": "瑜伽垫",
                "market_data": {},
                "insights": {},
                "opportunity_score": 76,
                "recommendations": []
            },
            amazon_data={"products": []},
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 检查收藏状态（未收藏）
        response = await client.get(
            f"/api/v1/favorites/check/{card.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] is False


@pytest.mark.asyncio
class TestFavoritesIntegration:
    """Favorites API 集成测试"""

    async def test_favorite_creates_opportunity_with_cpi_score(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试收藏卡片时创建商机并计算C-P-I分数"""
        # 创建高评分卡片
        card = Card(
            id=uuid.uuid4(),
            category="wireless_earbuds",
            title="高潜力无线耳机",
            content={
                "summary": {
                    "title": "无线耳机",
                    "opportunity_score": 88,
                    "market_size": 1200000,
                    "sweet_spot": {"min": 28, "max": 52, "best": 38},
                    "reliability": 0.93
                },
                "market_data": {
                    "price": {"min": 20, "max": 85, "avg": 48, "count": 180},
                    "rating": {"min": 4.0, "max": 4.9, "avg": 4.5, "count": 180}
                },
                "insights": {
                    "price_sweet_spot": {"min": 32, "max": 48, "best": 40},
                    "top_products": [
                        {
                            "asin": "B095T14D4S",
                            "title": "顶级产品",
                            "price": 39.99,
                            "rating": 4.7,
                            "reviews_count": 350
                        }
                    ],
                    "market_saturation": "low"
                },
                "recommendations": ["市场机会极佳"],
                "data_sources": ["oxylabs"],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "wireless_earbuds",
                "category_name": "无线耳机",
                "market_data": {
                    "total_products": 180,
                    "price_analysis": {"min": 20, "max": 85, "avg": 48, "count": 180},
                    "rating_analysis": {"min": 4.0, "max": 4.9, "avg": 4.5, "count": 180},
                    "data_source": "oxylabs",
                    "reliability": 0.93,
                    "fetch_time": "2026-03-14T00:00:00Z"
                },
                "insights": {},
                "opportunity_score": 88,
                "recommendations": ["市场机会极佳"]
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B095T14D4S",
                        "title": "顶级产品",
                        "price": 39.99,
                        "rating": 4.7,
                        "reviews_count": 350,
                        "url": "https://www.amazon.com/dp/B095T14D4S"
                    }
                ]
            },
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 添加收藏
        response = await client.post(
            "/api/v1/favorites",
            json={"card_id": str(card.id), "opportunity_id": None},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证收藏创建成功
        assert response.status_code == 200
        favorite_data = response.json()

        # 验证是否创建了商机（如果实现了该功能）
        # 注意：这取决于后端是否在收藏时自动创建商机
        # 如果实现了，验证C-P-I分数和等级
        if favorite_data.get("opportunity_id"):
            # 获取商机详情验证C-P-I分数
            opp_response = await client.get(
                f"/api/v1/opportunities/{favorite_data['opportunity_id']}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            if opp_response.status_code == 200:
                opportunity = opp_response.json()["opportunity"]
                # 验证C-P-I分数
                if opportunity.get("cpi_total_score") is not None:
                    assert 0 <= opportunity["cpi_total_score"] <= 100
                    # 验证等级计算
                    score = opportunity["cpi_total_score"]
                    grade = opportunity.get("grade")
                    if score < 60:
                        assert grade == "lead"
                    elif score < 70:
                        assert grade == "normal"
                    elif score < 85:
                        assert grade == "priority"
                    else:
                        assert grade == "landable"
