# tests/test_opportunities.py
"""Tests for Opportunities API endpoints"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from models.card import Card
from models.business_opportunity import (
    BusinessOpportunity,
    OpportunityStatus,
    OpportunityType,
    OpportunityGrade
)


@pytest.mark.asyncio
class TestOpportunitiesAPI:
    """测试 Opportunities API 端点"""

    async def test_get_opportunity_funnel_success(self, client: AsyncClient):
        """测试获取商机漏斗 - 成功场景"""
        response = await client.get("/api/v1/opportunities/funnel")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "funnel" in data
        assert "total" in data
        assert "description" in data

        # 验证漏斗数据结构
        funnel = data["funnel"]
        expected_statuses = ["potential", "verifying", "assessing", "executing"]
        for status in expected_statuses:
            assert status in funnel
            assert "count" in funnel[status]
            assert "avg_confidence" in funnel[status]
            assert "label" in funnel[status]

    async def test_get_opportunity_funnel_no_auth_required(self, client: AsyncClient):
        """测试获取商机漏斗 - 无需认证"""
        response = await client.get("/api/v1/opportunities/funnel")
        # 应该返回 200，即使没有数据
        assert response.status_code == 200

    async def test_generate_opportunities_from_cards(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试从卡片生成商机"""
        # 创建多个测试卡片
        cards = []
        for i in range(3):
            card = Card(
                id=uuid.uuid4(),
                category="wireless_earbuds",
                title=f"测试无线耳机 {i}",
                content={
                    "summary": {
                        "title": f"无线耳机 {i}",
                        "opportunity_score": 75 + i * 5,
                        "market_size": 1000000,
                        "sweet_spot": {"min": 25, "max": 50, "best": 35},
                        "reliability": 0.9 - i * 0.02
                    },
                    "market_data": {
                        "price": {"min": 20, "max": 80, "avg": 50, "count": 100 + i * 20},
                        "rating": {"min": 3.5, "max": 5.0, "avg": 4.3, "count": 100 + i * 20}
                    },
                    "insights": {
                        "price_sweet_spot": {"min": 30, "max": 45, "best": 38},
                        "top_products": [
                            {
                                "asin": f"B095T14D{i}",
                                "title": f"产品{i}",
                                "price": 35.99 + i * 5,
                                "rating": 4.3 + i * 0.1,
                                "reviews_count": 100 + i * 50
                            }
                        ],
                        "market_saturation": "medium" if i == 1 else "low"
                    },
                    "recommendations": [f"建议{i}"],
                    "data_sources": ["oxylabs"],
                    "generated_at": "2026-03-14T00:00:00Z"
                },
                analysis={
                    "category": "wireless_earbuds",
                    "category_name": "无线耳机",
                    "market_data": {
                        "total_products": 100 + i * 20,
                        "price_analysis": {"min": 20, "max": 80, "avg": 50, "count": 100 + i * 20},
                        "rating_analysis": {"min": 3.5, "max": 5.0, "avg": 4.3, "count": 100 + i * 20},
                        "data_source": "oxylabs",
                        "reliability": 0.9 - i * 0.02,
                        "fetch_time": "2026-03-14T00:00:00Z"
                    },
                    "insights": {},
                    "opportunity_score": 75 + i * 5,
                    "recommendations": [f"建议{i}"]
                },
                amazon_data={
                    "products": [
                        {
                            "asin": f"B095T14D{i}",
                            "title": f"产品{i}",
                            "price": 35.99 + i * 5,
                            "rating": 4.3 + i * 0.1,
                            "reviews_count": 100 + i * 50,
                            "url": f"https://www.amazon.com/dp/B095T14D{i}"
                        }
                    ]
                },
                is_published=True
            )
            cards.append(card)
            db_session.add(card)
        await db_session.commit()

        # 生成商机
        response = await client.post(
            "/api/v1/opportunities/generate-from-cards",
            params={"limit": 3},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "generated" in data
        assert "opportunities" in data
        assert isinstance(data["opportunities"], list)
        assert data["generated"] >= 0

    async def test_get_opportunity_by_id(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试通过ID获取商机"""
        # 创建测试商机
        opportunity = BusinessOpportunity(
            id=uuid.uuid4(),
            title="测试商机",
            description="这是一个测试商机",
            status=OpportunityStatus.POTENTIAL,
            opportunity_type=OpportunityType.PRODUCT,
            grade=OpportunityGrade.PRIORITY,
            cpi_total_score=75.5,
            cpi_competition_score=70.0,
            cpi_potential_score=80.0,
            cpi_intelligence_gap_score=75.0,
            confidence_score=0.85,
            elements={"product": {"category": "wireless_earbuds"}},
            ai_insights={"why_opportunity": "测试原因"},
            user_interactions={"views": 0, "saved": False}
        )
        db_session.add(opportunity)
        await db_session.commit()

        # 获取商机详情
        response = await client.get(
            f"/api/v1/opportunities/{opportunity.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["opportunity"]["id"] == str(opportunity.id)
        assert data["opportunity"]["title"] == "测试商机"
        assert data["opportunity"]["grade"] == "priority"
        assert data["opportunity"]["cpi_total_score"] == 75.5

    async def test_get_opportunity_by_id_not_found(
        self, client: AsyncClient, auth_token
    ):
        """测试获取不存在的商机"""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/opportunities/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    async def test_list_opportunities_with_filters(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试列出商机 - 带筛选条件"""
        # 创建不同状态和等级的测试商机
        opportunities = [
            BusinessOpportunity(
                id=uuid.uuid4(),
                title=f"商机 {i}",
                description=f"测试商机描述 {i}",
                status=OpportunityStatus.POTENTIAL if i < 2 else OpportunityStatus.VERIFYING,
                opportunity_type=OpportunityType.PRODUCT,
                grade=OpportunityGrade.NORMAL if i == 0 else OpportunityGrade.PRIORITY,
                cpi_total_score=65.0 + i * 10,
                confidence_score=0.75 + i * 0.05,
                elements={},
                ai_insights={},
                user_interactions={}
            )
            for i in range(4)
        ]
        for opp in opportunities:
            db_session.add(opp)
        await db_session.commit()

        # 测试按等级筛选
        response = await client.get(
            "/api/v1/opportunities?grade=priority&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "opportunities" in data
        assert "total" in data

        # 验证筛选结果
        for opp in data["opportunities"]:
            assert opp["grade"] == "priority"


@pytest.mark.asyncio
class TestOpportunityCPIAlgorithm:
    """测试商机C-P-I算法"""

    async def test_cpi_score_calculation_for_high_potential_card(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试高潜力卡片的C-P-I分数计算"""
        # 创建高潜力卡片
        card = Card(
            id=uuid.uuid4(),
            category="wireless_earbuds",
            title="高潜力无线耳机市场",
            content={
                "summary": {
                    "title": "无线耳机市场",
                    "opportunity_score": 92,
                    "market_size": 1500000,
                    "sweet_spot": {"min": 30, "max": 55, "best": 42},
                    "reliability": 0.95
                },
                "market_data": {
                    "price": {"min": 25, "max": 90, "avg": 55, "count": 200},
                    "rating": {"min": 4.0, "max": 4.9, "avg": 4.5, "count": 200}
                },
                "insights": {
                    "price_sweet_spot": {"min": 35, "max": 50, "best": 42},
                    "top_products": [
                        {
                            "asin": "B095T14D4S",
                            "title": "顶级产品",
                            "price": 42.99,
                            "rating": 4.8,
                            "reviews_count": 500
                        }
                    ],
                    "market_saturation": "low"
                },
                "recommendations": ["强烈建议进入"],
                "data_sources": ["oxylabs", "google_trends"],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "wireless_earbuds",
                "category_name": "无线耳机",
                "market_data": {
                    "total_products": 200,
                    "price_analysis": {"min": 25, "max": 90, "avg": 55, "count": 200},
                    "rating_analysis": {"min": 4.0, "max": 4.9, "avg": 4.5, "count": 200},
                    "data_source": "oxylabs",
                    "reliability": 0.95,
                    "fetch_time": "2026-03-14T00:00:00Z"
                },
                "insights": {},
                "opportunity_score": 92,
                "recommendations": ["强烈建议进入"]
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B095T14D4S",
                        "title": "顶级产品",
                        "price": 42.99,
                        "rating": 4.8,
                        "reviews_count": 500,
                        "url": "https://www.amazon.com/dp/B095T14D4S"
                    }
                ]
            },
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 生成商机
        response = await client.post(
            "/api/v1/opportunities/generate-from-cards",
            params={"card_ids": [str(card.id)], "limit": 1},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # 验证C-P-I分数
        if response.status_code == 200:
            data = response.json()
            if data["opportunities"]:
                opportunity = data["opportunities"][0]
                # 验证有C-P-I分数
                assert opportunity["cpi_total_score"] is not None
                # 高潜力卡片应该得到高分
                assert opportunity["cpi_total_score"] >= 70
                # 验证等级
                assert opportunity["grade"] in ["priority", "landable"]

    async def test_cpi_score_ranges_and_grades(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试C-P-I分数范围与等级对应关系"""
        # 创建不同opportunity_score的卡片
        test_cases = [
            (55, "lead"),      # < 60: LEAD
            (65, "normal"),    # 60-69: NORMAL
            (75, "priority"),  # 70-84: PRIORITY
            (90, "landable"),  # >= 85: LANDABLE
        ]

        for score, expected_grade in test_cases:
            card = Card(
                id=uuid.uuid4(),
                category="fitness_trackers",
                title=f"测试卡片 {score}分",
                content={
                    "summary": {
                        "title": f"测试 {score}",
                        "opportunity_score": score,
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
                    "opportunity_score": score,
                    "recommendations": []
                },
                amazon_data={"products": []},
                is_published=True
            )
            db_session.add(card)
        await db_session.commit()

        # 生成所有商机
        response = await client.post(
            "/api/v1/opportunities/generate-from-cards",
            params={"limit": 10},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        if response.status_code == 200:
            data = response.json()
            # 验证等级对应关系
            for opp in data["opportunities"]:
                score = opp.get("cpi_total_score", 0)
                grade = opp.get("grade")

                if score < 60:
                    assert grade == "lead", f"Score {score} should be lead, got {grade}"
                elif score < 70:
                    assert grade == "normal", f"Score {score} should be normal, got {grade}"
                elif score < 85:
                    assert grade == "priority", f"Score {score} should be priority, got {grade}"
                else:
                    assert grade == "landable", f"Score {score} should be landable, got {grade}"


@pytest.mark.asyncio
class TestOpportunitiesIntegration:
    """Opportunities API 集成测试"""

    async def test_opportunity_lifecycle_from_card_to_graded(
        self, client: AsyncClient, db_session, auth_token
    ):
        """测试商机完整生命周期：卡片→商机→评级→状态变化"""
        # 1. 创建高质量卡片
        card = Card(
            id=uuid.uuid4(),
            category="phone_chargers",
            title="高潜力手机充电器",
            content={
                "summary": {
                    "title": "手机充电器",
                    "opportunity_score": 88,
                    "market_size": 900000,
                    "sweet_spot": {"min": 22, "max": 48, "best": 35},
                    "reliability": 0.91
                },
                "market_data": {
                    "price": {"min": 18, "max": 75, "avg": 45, "count": 160},
                    "rating": {"min": 3.9, "max": 4.8, "avg": 4.4, "count": 160}
                },
                "insights": {
                    "price_sweet_spot": {"min": 28, "max": 42, "best": 35},
                    "top_products": [
                        {
                            "asin": "B095T14D4S",
                            "title": "热门充电器",
                            "price": 34.99,
                            "rating": 4.6,
                            "reviews_count": 280
                        }
                    ],
                    "market_saturation": "low"
                },
                "recommendations": ["市场潜力大"],
                "data_sources": ["oxylabs"],
                "generated_at": "2026-03-14T00:00:00Z"
            },
            analysis={
                "category": "phone_chargers",
                "category_name": "手机充电器",
                "market_data": {
                    "total_products": 160,
                    "price_analysis": {"min": 18, "max": 75, "avg": 45, "count": 160},
                    "rating_analysis": {"min": 3.9, "max": 4.8, "avg": 4.4, "count": 160},
                    "data_source": "oxylabs",
                    "reliability": 0.91,
                    "fetch_time": "2026-03-14T00:00:00Z"
                },
                "insights": {},
                "opportunity_score": 88,
                "recommendations": ["市场潜力大"]
            },
            amazon_data={
                "products": [
                    {
                        "asin": "B095T14D4S",
                        "title": "热门充电器",
                        "price": 34.99,
                        "rating": 4.6,
                        "reviews_count": 280,
                        "url": "https://www.amazon.com/dp/B095T14D4S"
                    }
                ]
            },
            is_published=True
        )
        db_session.add(card)
        await db_session.commit()

        # 2. 生成商机
        gen_response = await client.post(
            "/api/v1/opportunities/generate-from-cards",
            params={"card_ids": [str(card.id)], "limit": 1},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert gen_response.status_code == 200
        gen_data = gen_response.json()

        if gen_data["opportunities"]:
            opportunity_id = gen_data["opportunities"][0]["id"]

            # 3. 获取商机详情
            opp_response = await client.get(
                f"/api/v1/opportunities/{opportunity_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

            assert opp_response.status_code == 200
            opportunity = opp_response.json()["opportunity"]

            # 4. 验证C-P-I完整数据
            assert "cpi_total_score" in opportunity
            assert "cpi_competition_score" in opportunity
            assert "cpi_potential_score" in opportunity
            assert "cpi_intelligence_gap_score" in opportunity
            assert "grade" in opportunity

            # 5. 验证分数在合理范围内
            assert 0 <= opportunity["cpi_total_score"] <= 100
            assert 0 <= opportunity["cpi_competition_score"] <= 100
            assert 0 <= opportunity["cpi_potential_score"] <= 100
            assert 0 <= opportunity["cpi_intelligence_gap_score"] <= 100

            # 6. 验证等级与分数一致
            score = opportunity["cpi_total_score"]
            grade = opportunity["grade"]
            if score >= 85:
                assert grade == "landable"
            elif score >= 70:
                assert grade == "priority"
            elif score >= 60:
                assert grade == "normal"
            else:
                assert grade == "lead"
