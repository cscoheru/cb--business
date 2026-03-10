# tests/test_auth.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthFlow:
    """测试认证流程"""

    async def test_register_new_user(self, client: AsyncClient):
        """测试用户注册"""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "password123",
            "name": "新用户"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "新用户"

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """测试重复邮箱注册"""
        response = await client.post("/api/v1/auth/register", json={
            "email": test_user.email,
            "password": "password123",
            "name": "重复用户"
        })

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data or "error" in data

    async def test_login_success(self, client: AsyncClient, test_user):
        """测试成功登录"""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """测试错误密码登录"""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "wrongpassword"
        })

        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """测试不存在用户登录"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })

        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """测试获取当前用户信息"""
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    async def test_get_current_user_without_auth(self, client: AsyncClient):
        """测试未认证获取用户信息"""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient, test_user):
        """测试刷新Token"""
        # 先登录获取refresh_token
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "password123"
        })
        refresh_token = login_response.json()["refresh_token"]

        # 使用refresh_token获取新的access_token
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """测试无效的refresh_token"""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_refresh_token"
        })

        assert response.status_code == 401


@pytest.mark.asyncio
class TestUserManagement:
    """测试用户管理"""

    async def test_update_user_profile(self, client: AsyncClient, auth_headers):
        """测试更新用户资料"""
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"name": "更新后的名字"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的名字"

    async def test_change_password(self, client: AsyncClient, auth_headers):
        """测试修改密码"""
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": "password123",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 200

        # 验证新密码可以登录
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "newpassword123"
        })
        assert login_response.status_code == 200

    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers):
        """测试使用错误的当前密码修改密码"""
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 400
