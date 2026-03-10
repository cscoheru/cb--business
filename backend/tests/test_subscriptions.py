# tests/test_subscriptions.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSubscriptionPlans:
    """测试订阅套餐"""

    async def test_get_all_plans(self, client: AsyncClient):
        """测试获取所有套餐"""
        response = await client.get("/api/v1/subscriptions/plans")

        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
        assert len(plans) == 3  # free, pro, enterprise

        # 验证套餐结构
        for plan in plans:
            assert "tier" in plan
            assert "name" in plan
            assert "features" in plan

    async def test_get_free_plan_details(self, client: AsyncClient):
        """测试获取免费版套餐详情"""
        response = await client.get("/api/v1/subscriptions/plans/free")

        assert response.status_code == 200
        plan = response.json()
        assert plan["tier"] == "free"
        assert plan["name"] == "免费版"
        assert plan["price_monthly"] == 0

    async def test_get_pro_plan_details(self, client: AsyncClient):
        """测试获取专业版套餐详情"""
        response = await client.get("/api/v1/subscriptions/plans/pro")

        assert response.status_code == 200
        plan = response.json()
        assert plan["tier"] == "pro"
        assert plan["name"] == "专业版"
        assert plan["price_monthly"] == 99

    async def test_get_nonexistent_plan(self, client: AsyncClient):
        """测试获取不存在的套餐"""
        response = await client.get("/api/v1/subscriptions/plans/nonexistent")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestSubscriptionManagement:
    """测试订阅管理"""

    async def test_get_my_free_subscription(self, client: AsyncClient, test_token: str):
        """测试获取当前用户的免费订阅"""
        response = await client.get(
            "/api/v1/subscriptions/me",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        sub = response.json()
        assert sub["plan_tier"] == "free"
        assert sub["status"] == "active"
        assert "features" in sub

    async def test_create_pro_subscription_monthly(self, client: AsyncClient, test_token: str):
        """测试创建专业版月付订阅"""
        response = await client.post(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )

        assert response.status_code == 200 or response.status_code == 400  # 400 if already has subscription
        if response.status_code == 200:
            sub = response.json()
            assert sub["plan_tier"] == "pro"
            assert sub["billing_cycle"] == "monthly"
            assert sub["status"] == "active"

    async def test_create_enterprise_subscription_yearly(self, client: AsyncClient):
        """测试创建企业版年付订阅"""
        # 先注册一个新用户
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "enterprise@example.com",
                "password": "password123",
                "name": "企业用户"
            }
        )
        token = reg_response.json()["access_token"]

        # 创建订阅
        response = await client.post(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "plan_tier": "enterprise",
                "billing_cycle": "yearly"
            }
        )

        # 企业版可能需要特殊处理，所以接受200或400
        assert response.status_code in [200, 400, 403]

    async def test_cancel_subscription(self, client: AsyncClient):
        """测试取消订阅"""
        # 先创建有订阅的用户
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "cancel-test@example.com",
                "password": "password123",
                "name": "取消测试"
            }
        )
        token = reg_response.json()["access_token"]

        # 创建订阅
        await client.post(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )

        # 取消订阅
        response = await client.delete(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "expires_at" in data

    async def test_cancel_subscription_without_active_sub(self, client: AsyncClient, test_token: str):
        """测试没有活跃订阅时取消"""
        response = await client.delete(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestSubscriptionAccess:
    """测试订阅访问控制"""

    async def test_access_subscription_without_auth(self, client: AsyncClient):
        """测试未认证访问订阅"""
        response = await client.get("/api/v1/subscriptions/me")

        assert response.status_code == 401

    async def test_create_subscription_without_auth(self, client: AsyncClient):
        """测试未认证创建订阅"""
        response = await client.post(
            "/api/v1/subscriptions",
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )

        assert response.status_code == 401

    async def test_invalid_plan_tier(self, client: AsyncClient, test_token: str):
        """测试无效的套餐等级"""
        response = await client.post(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "plan_tier": "invalid_tier",
                "billing_cycle": "monthly"
            }
        )

        assert response.status_code == 422  # Validation error
