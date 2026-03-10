# tests/test_subscriptions.py
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSubscriptionFlow:
    """测试订阅流程"""

    async def test_create_subscription_monthly(self, client: AsyncClient, auth_headers):
        """测试创建月付订阅"""
        response = await client.post(
            "/api/v1/subscriptions",
            headers=auth_headers,
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["plan_tier"] == "pro"
        assert data["data"]["billing_cycle"] == "monthly"
        assert data["data"]["status"] in ["pending", "active"]

    async def test_create_subscription_yearly(self, client: AsyncClient, auth_headers):
        """测试创建年付订阅"""
        response = await client.post(
            "/api/v1/subscriptions",
            headers=auth_headers,
            json={
                "plan_tier": "pro",
                "billing_cycle": "yearly"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["billing_cycle"] == "yearly"

    async def test_get_current_subscription(self, client: AsyncClient, test_subscription, auth_headers):
        """测试获取当前订阅"""
        response = await client.get(
            "/api/v1/subscriptions/current",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["plan_tier"] == "pro"

    async def test_list_subscriptions(self, client: AsyncClient, test_subscription, auth_headers):
        """测试列出所有订阅"""
        response = await client.get(
            "/api/v1/subscriptions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    async def test_cancel_subscription(self, client: AsyncClient, test_subscription, auth_headers):
        """测试取消订阅"""
        response = await client.post(
            f"/api/v1/subscriptions/{test_subscription.id}/cancel",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "cancelled"

    async def test_reactivate_subscription(self, client: AsyncClient, db_session, test_subscription, auth_headers):
        """测试重新激活订阅"""
        # 先取消订阅
        await client.post(
            f"/api/v1/subscriptions/{test_subscription.id}/cancel",
            headers=auth_headers
        )

        # 重新激活
        response = await client.post(
            f"/api/v1/subscriptions/{test_subscription.id}/reactivate",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "active"

    async def test_create_enterprise_subscription(self, client: AsyncClient, auth_headers):
        """测试创建企业版订阅"""
        response = await client.post(
            "/api/v1/subscriptions",
            headers=auth_headers,
            json={
                "plan_tier": "enterprise",
                "billing_cycle": "yearly"
            }
        )

        # 企业版需要联系，应该返回特殊状态
        assert response.status_code in [200, 400]


@pytest.mark.asyncio
class TestSubscriptionAccess:
    """测试订阅访问控制"""

    async def test_free_user_cannot_access_pro_features(self, client: AsyncClient, auth_headers):
        """测试免费用户不能访问Pro功能"""
        # 尝试访问需要Pro权限的功能（爬虫触发）
        response = await client.post(
            "/api/v1/crawler/trigger/retail_dive",
            headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False

    async def test_pro_user_can_access_pro_features(self, client: AsyncClient, pro_headers):
        """测试Pro用户可以访问Pro功能"""
        # 尝试访问需要Pro权限的功能
        response = await client.post(
            "/api/v1/crawler/trigger/retail_dive",
            headers=pro_headers
        )

        # 应该允许访问（即使数据源不存在，也是404而非403）
        assert response.status_code != 403

    async def test_admin_can_access_all_features(self, client: AsyncClient, admin_headers):
        """测试管理员可以访问所有功能"""
        response = await client.get(
            "/api/v1/admin/stats",
            headers=admin_headers
        )

        assert response.status_code == 200


@pytest.mark.asyncio
class TestUsageTracking:
    """测试使用量跟踪"""

    async def test_get_usage_stats(self, client: AsyncClient, auth_headers):
        """测试获取使用统计"""
        response = await client.get(
            "/api/v1/usage/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api_calls" in data["data"]
        assert "period" in data["data"]

    async def test_check_feature_access_free_user(self, client: AsyncClient, auth_headers):
        """测试检查免费用户功能访问"""
        response = await client.get(
            "/api/v1/usage/check-feature/crawler_trigger",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["allowed"] is False

    async def test_check_feature_access_pro_user(self, client: AsyncClient, pro_headers):
        """测试检查Pro用户功能访问"""
        response = await client.get(
            "/api/v1/usage/check-feature/crawler_trigger",
            headers=pro_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["allowed"] is True
