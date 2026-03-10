# tests/test_admin.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAdminAccess:
    """测试管理员访问控制"""

    async def test_admin_stats_as_admin(self, client: AsyncClient, admin_headers):
        """测试管理员访问统计"""
        response = await client.get(
            "/api/v1/admin/stats",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "users" in data["data"]
        assert "subscriptions" in data["data"]

    async def test_admin_stats_as_normal_user(self, client: AsyncClient, auth_headers):
        """测试普通用户访问统计"""
        response = await client.get(
            "/api/v1/admin/stats",
            headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False

    async def test_admin_stats_unauthorized(self, client: AsyncClient):
        """测试未授权访问统计"""
        response = await client.get("/api/v1/admin/stats")

        assert response.status_code == 401


@pytest.mark.asyncio
class TestUserManagement:
    """测试用户管理"""

    async def test_list_users_as_admin(self, client: AsyncClient, admin_headers):
        """测试管理员列出用户"""
        response = await client.get(
            "/api/v1/admin/users",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "users" in data["data"]

    async def test_list_users_as_normal_user(self, client: AsyncClient, auth_headers):
        """测试普通用户列出用户"""
        response = await client.get(
            "/api/v1/admin/users",
            headers=auth_headers
        )

        assert response.status_code == 403

    async def test_get_user_detail_as_admin(self, client: AsyncClient, admin_headers, test_user):
        """测试管理员获取用户详情"""
        response = await client.get(
            f"/api/v1/admin/users/{test_user.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_user.id)

    async def test_update_user_as_admin(self, client: AsyncClient, admin_headers, test_user):
        """测试管理员更新用户"""
        response = await client.put(
            f"/api/v1/admin/users/{test_user.id}",
            headers=admin_headers,
            json={"role": "pro"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == "pro"

    async def test_delete_user_as_admin(self, client: AsyncClient, admin_headers, db_session):
        """测试管理员删除用户"""
        from models.user import User
        from api.auth import get_password_hash

        # 创建临时用户
        user = User(
            email="temp@example.com",
            hashed_password=get_password_hash("password123"),
            name="临时用户",
            is_active=True,
            is_verified=True,
            role="free"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 删除用户
        response = await client.delete(
            f"/api/v1/admin/users/{user.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
class TestSubscriptionManagement:
    """测试订阅管理"""

    async def test_list_all_subscriptions_as_admin(self, client: AsyncClient, admin_headers):
        """测试管理员列出所有订阅"""
        response = await client.get(
            "/api/v1/admin/subscriptions",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "subscriptions" in data["data"]

    async def test_update_subscription_as_admin(self, client: AsyncClient, admin_headers, test_subscription):
        """测试管理员更新订阅"""
        response = await client.put(
            f"/api/v1/admin/subscriptions/{test_subscription.id}",
            headers=admin_headers,
            json={"status": "active"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
class TestSystemHealth:
    """测试系统健康"""

    async def test_health_check(self, client: AsyncClient):
        """测试健康检查"""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_database_health(self, client: AsyncClient):
        """测试数据库健康"""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "database" in data["details"]
