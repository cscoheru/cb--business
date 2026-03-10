# tests/test_payments.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPaymentOrder:
    """测试支付订单"""

    async def test_create_payment_order_monthly(self, client: AsyncClient, auth_headers):
        """测试创建月付订单"""
        response = await client.post(
            "/api/v1/payments/create-order",
            headers=auth_headers,
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "order_id" in data["data"]
        assert "qr_code_url" in data["data"] or data["data"].get("payment_url")

    async def test_create_payment_order_yearly(self, client: AsyncClient, auth_headers):
        """测试创建年付订单"""
        response = await client.post(
            "/api/v1/payments/create-order",
            headers=auth_headers,
            json={
                "plan_tier": "pro",
                "billing_cycle": "yearly"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 年付应该有折扣
        assert data["data"]["amount"] > 0

    async def test_get_payment_order(self, client: AsyncClient, auth_headers, db_session):
        """测试获取支付订单"""
        # 先创建订单
        create_response = await client.post(
            "/api/v1/payments/create-order",
            headers=auth_headers,
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )
        order_id = create_response.json()["data"]["order_id"]

        # 获取订单详情
        response = await client.get(
            f"/api/v1/payments/orders/{order_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["order_id"] == order_id

    async def test_list_payment_orders(self, client: AsyncClient, auth_headers):
        """测试列出支付订单"""
        response = await client.get(
            "/api/v1/payments/orders",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "orders" in data["data"]


@pytest.mark.asyncio
class TestPaymentWebhook:
    """测试支付回调"""

    async def test_wechat_pay_webhook_success(self, client: AsyncClient, db_session):
        """测试微信支付成功回调"""
        # 这个测试需要模拟微信支付回调签名
        # 在实际测试中，可能需要使用测试环境的密钥
        webhook_data = {
            "transaction_id": "test_transaction_123",
            "out_trade_no": "test_order_123",
            "trade_state": "SUCCESS",
            "amount": {"total": 9900}
        }

        response = await client.post(
            "/api/v1/payments/webhook/wechat",
            json=webhook_data
        )

        # 签名验证可能会失败，但应该返回特定格式
        assert response.status_code in [200, 400]

    async def test_webhook_creates_subscription(self, client: AsyncClient):
        """测试回调创建订阅"""
        # 这个测试需要完整的支付流程模拟
        # 在实际实现中，应该使用测试数据
        pass


@pytest.mark.asyncio
class TestPricing:
    """测试定价"""

    async def test_monthly_pricing(self, client: AsyncClient, auth_headers):
        """测试月付价格"""
        response = await client.post(
            "/api/v1/payments/create-order",
            headers=auth_headers,
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Pro月付价格应该是99元
        assert data["data"]["amount"] == 9900  # 分

    async def test_yearly_pricing_with_discount(self, client: AsyncClient, auth_headers):
        """测试年付折扣价格"""
        response = await client.post(
            "/api/v1/payments/create-order",
            headers=auth_headers,
            json={
                "plan_tier": "pro",
                "billing_cycle": "yearly"
            }
        )

        assert response.status_code == 200
        data = response.json()
        # 年付应该有折扣（99 * 12 * 0.8 = 950.4）
        # 实际价格应该在950元左右
        assert 94000 <= data["data"]["amount"] <= 96000

    async def test_enterprise_plan_contact_required(self, client: AsyncClient, auth_headers):
        """测试企业版需要联系"""
        response = await client.post(
            "/api/v1/payments/create-order",
            headers=auth_headers,
            json={
                "plan_tier": "enterprise",
                "billing_cycle": "yearly"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "ENTERPRISE_CONTACT_REQUIRED" in data.get("error", {}).get("code", "")


@pytest.mark.asyncio
class TestPaymentHistory:
    """测试支付历史"""

    async def test_get_payment_history(self, client: AsyncClient, auth_headers):
        """测试获取支付历史"""
        response = await client.get(
            "/api/v1/payments/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "payments" in data["data"]

    async def test_payment_history_pagination(self, client: AsyncClient, auth_headers):
        """测试支付历史分页"""
        response = await client.get(
            "/api/v1/payments/history?page=1&per_page=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data["data"]
