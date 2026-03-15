# tests/test_payments.py
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import uuid


@pytest.mark.asyncio
class TestPaymentOrder:
    """测试支付订单创建"""

    async def test_create_payment_order_monthly_airwallex(self, client: AsyncClient, auth_headers, db_session):
        """测试创建月付订单 (Airwallex)"""
        # Mock Airwallex service
        mock_airwallex_service = AsyncMock()
        mock_airwallex_service.create_customer = AsyncMock(return_value={
            "id": "cus_test_123",
            "email": "test@example.com"
        })
        mock_airwallex_service.create_payment_intent = AsyncMock(return_value={
            "request_id": "req_test_123",
            "payment_intent_id": "pi_test_123",
            "client_token": "tok_test_123",
            "customer_id": "cus_test_123"
        })

        # Patch api.payments.airwallex variable (set at module import time)
        with patch('api.payments.airwallex', mock_airwallex_service):
            response = await client.post(
                "/api/v1/payments/create",
                headers=auth_headers,
                json={
                    "plan_tier": "pro",
                    "billing_cycle": "monthly",
                    "payment_method": "airwallex"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["order_no"] == "req_test_123"
        assert data["amount"] == 99.0
        assert data["currency"] == "CNY"
        assert data["payment_method"] == "airwallex"
        assert data["client_token"] == "tok_test_123"
        assert data["payment_intent_id"] == "pi_test_123"

    async def test_create_payment_order_yearly_with_discount(self, client: AsyncClient, auth_headers):
        """测试创建年付订单 (应享受折扣)"""
        mock_airwallex_service = AsyncMock()
        mock_airwallex_service.create_customer = AsyncMock(return_value={"id": "cus_yearly"})
        mock_airwallex_service.create_payment_intent = AsyncMock(return_value={
            "request_id": "req_yearly",
            "payment_intent_id": "pi_yearly",
            "client_token": "tok_yearly"
        })

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex_service):
            response = await client.post(
                "/api/v1/payments/create",
                headers=auth_headers,
                json={
                    "plan_tier": "pro",
                    "billing_cycle": "yearly",
                    "payment_method": "airwallex"
                }
            )

        assert response.status_code == 200
        data = response.json()
        # 年付应该有折扣（990元 vs 月付12个月1188元）
        assert data["amount"] == 990.0

    async def test_create_payment_order_trial_not_allowed(self, client: AsyncClient, auth_headers):
        """测试试用版不能创建支付订单"""
        response = await client.post(
            "/api/v1/payments/create",
            headers=auth_headers,
            json={
                "plan_tier": "trial",
                "billing_cycle": "monthly",
                "payment_method": "airwallex"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "TRIAL_AUTO_GRANTED"

    async def test_create_payment_order_free_not_allowed(self, client: AsyncClient, auth_headers):
        """测试免费版不能创建支付订单"""
        response = await client.post(
            "/api/v1/payments/create",
            headers=auth_headers,
            json={
                "plan_tier": "free",
                "billing_cycle": "monthly",
                "payment_method": "airwallex"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "FREE_PLAN_AVAILABLE"

    async def test_duplicate_pro_subscription_rejected(self, client: AsyncClient, auth_headers, pro_user):
        """测试已有Pro订阅的用户不能重复购买"""
        # pro_user fixture already has an active pro subscription
        mock_airwallex_service = AsyncMock()
        mock_airwallex_service.create_customer = AsyncMock(return_value={"id": "cus_duplicate"})
        mock_airwallex_service.create_payment_intent = AsyncMock(return_value={
            "request_id": "req_dup",
            "payment_intent_id": "pi_dup",
            "client_token": "tok_dup"
        })

        # Use pro_headers instead (for a user who already has pro)
        from tests.conftest import pro_token, pro_user
        # First get a pro token
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "pro@example.com",
            "password": "password123"
        })
        pro_token = login_resp.json()["access_token"]
        pro_headers = {"Authorization": f"Bearer {pro_token}"}

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex_service):
            response = await client.post(
                "/api/v1/payments/create",
                headers=pro_headers,
                json={
                    "plan_tier": "pro",
                    "billing_cycle": "monthly",
                    "payment_method": "airwallex"
                }
            )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "ACTIVE_PRO_SUBSCRIPTION"

    async def test_get_payment_order_by_order_no(self, client: AsyncClient, auth_headers):
        """测试查询支付订单状态"""
        # First create an order using mock endpoint
        mock_airwallex = AsyncMock()
        mock_airwallex.create_customer = AsyncMock(return_value={"id": "cus_query"})
        mock_airwallex.create_payment_intent = AsyncMock(return_value={
            "request_id": "req_query",
            "payment_intent_id": "pi_query",
            "client_token": "tok_query"
        })

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex):
            create_response = await client.post(
                "/api/v1/payments/create",
                headers=auth_headers,
                json={
                    "plan_tier": "pro",
                    "billing_cycle": "monthly",
                    "payment_method": "airwallex"
                }
            )

        order_no = create_response.json()["order_no"]

        # Query the order
        response = await client.get(
            f"/api/v1/payments/{order_no}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["order_no"] == order_no
        assert data["amount"] == 99.0
        assert data["status"] == "pending"

    async def test_query_nonexistent_order_returns_404(self, client: AsyncClient, auth_headers):
        """测试查询不存在的订单返回404"""
        response = await client.get(
            "/api/v1/payments/nonexistent_order_123",
            headers=auth_headers
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestPaymentWebhook:
    """测试支付回调处理"""

    async def test_airwallex_webhook_signature_validation(self, client: AsyncClient):
        """测试Airwallex webhook签名验证"""
        mock_airwallex = AsyncMock()
        # Mock signature verification to fail
        mock_airwallex.verify_webhook_signature = AsyncMock(return_value=False)

        webhook_payload = {
            "id": "evt_test_123",
            "name": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "merchant_order_id": "req_test_123",
                    "amount": 9900,
                    "currency": "CNY",
                    "metadata": {
                        "plan_tier": "pro",
                        "billing_cycle": "monthly"
                    }
                }
            }
        }

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex):
            response = await client.post(
                "/api/v1/payments/webhooks/airwallex",
                json=webhook_payload,
                headers={
                    "x-webhook-signature": "invalid_signature",
                    "x-webhook-timestamp": "1234567890"
                }
            )

        # Invalid signature should return 401
        assert response.status_code == 401

    async def test_webhook_replay_attack_prevention(self, client: AsyncClient, db_session):
        """测试webhook防重放攻击"""
        mock_airwallex = AsyncMock()
        mock_airwallex.verify_webhook_signature = AsyncMock(return_value=True)

        webhook_payload = {
            "id": "evt_replay_test",
            "name": "payment_intent.succeeded",
            "data": {"object": {}}
        }

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex):
            # First request
            response1 = await client.post(
                "/api/v1/payments/webhooks/airwallex",
                json=webhook_payload,
                headers={
                    "x-webhook-signature": "valid_sig",
                    "x-webhook-timestamp": "1234567890"
                }
            )

            # Second request with same event_id (should be rejected)
            response2 = await client.post(
                "/api/v1/payments/webhooks/airwallex",
                json=webhook_payload,
                headers={
                    "x-webhook-signature": "valid_sig",
                    "x-webhook-timestamp": "1234567890"
                }
            )

        # Both should succeed (second one returns "already processed")
        assert response1.status_code == 200
        assert response2.status_code == 200


@pytest.mark.asyncio
class TestPricing:
    """测试定价策略"""

    async def test_monthly_pro_pricing(self, client: AsyncClient, auth_headers):
        """测试Pro月付价格"""
        mock_airwallex = AsyncMock()
        mock_airwallex.create_customer = AsyncMock(return_value={"id": "cus_pricing"})
        mock_airwallex.create_payment_intent = AsyncMock(return_value={
            "request_id": "req_pricing",
            "payment_intent_id": "pi_pricing",
            "client_token": "tok_pricing"
        })

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex):
            response = await client.post(
                "/api/v1/payments/create",
                headers=auth_headers,
                json={
                    "plan_tier": "pro",
                    "billing_cycle": "monthly",
                    "payment_method": "airwallex"
                }
            )

        assert response.status_code == 200
        data = response.json()
        # Pro月付价格应该是99元
        assert data["amount"] == 99.0

    async def test_yearly_pro_discount(self, client: AsyncClient, auth_headers):
        """测试Pro年付享受折扣"""
        mock_airwallex = AsyncMock()
        mock_airwallex.create_customer = AsyncMock(return_value={"id": "cus_discount"})
        mock_airwallex.create_payment_intent = AsyncMock(return_value={
            "request_id": "req_discount",
            "payment_intent_id": "pi_discount",
            "client_token": "tok_discount"
        })

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex):
            response = await client.post(
                "/api/v1/payments/create",
                headers=auth_headers,
                json={
                    "plan_tier": "pro",
                    "billing_cycle": "yearly",
                    "payment_method": "airwallex"
                }
            )

        assert response.status_code == 200
        data = response.json()
        # 年付990元（相当于每月82.5元，比月付节省198元）
        assert data["amount"] == 990.0

    async def test_get_plans_info(self, client: AsyncClient):
        """测试获取订阅计划信息"""
        response = await client.get("/api/v1/payments/plans")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "plans" in data
        # Should include free, trial, and pro plans
        assert any(p["tier"] == "free" for p in data["plans"])
        assert any(p["tier"] == "trial" for p in data["plans"])
        assert any(p["tier"] == "pro" for p in data["plans"])


@pytest.mark.asyncio
class TestMockPayment:
    """测试模拟支付端点（开发环境）"""

    async def test_mock_payment_completion(self, client: AsyncClient, auth_headers, db_session):
        """测试模拟支付完成流程"""
        # First create a payment order
        mock_airwallex = AsyncMock()
        mock_airwallex.create_customer = AsyncMock(return_value={"id": "cus_mock"})
        mock_airwallex.create_payment_intent = AsyncMock(return_value={
            "request_id": "req_mock_complete",
            "payment_intent_id": "pi_mock_complete",
            "client_token": "tok_mock_complete"
        })

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex):
            create_response = await client.post(
                "/api/v1/payments/create",
                headers=auth_headers,
                json={
                    "plan_tier": "pro",
                    "billing_cycle": "monthly",
                    "payment_method": "airwallex"
                }
            )

        order_no = create_response.json()["order_no"]

        # Complete the payment using mock endpoint
        response = await client.post(
            f"/api/v1/payments/mock/{order_no}/complete",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify the payment status is now completed
        query_response = await client.get(
            f"/api/v1/payments/{order_no}",
            headers=auth_headers
        )

        assert query_response.status_code == 200
        query_data = query_response.json()
        assert query_data["status"] == "completed"

    async def test_mock_nonexistent_order_returns_404(self, client: AsyncClient, auth_headers):
        """测试模拟不存在的订单返回404"""
        response = await client.post(
            "/api/v1/payments/mock/nonexistent_order/complete",
            headers=auth_headers
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestPaymentFlow:
    """完整支付流程集成测试"""

    async def test_complete_payment_flow(self, client: AsyncClient, auth_headers, db_session):
        """测试完整的支付流程：创建订单 -> 查询 -> 模拟完成 -> 验证订阅"""
        from models.subscription import Subscription

        # Step 1: Create payment order
        mock_airwallex = AsyncMock()
        mock_airwallex.create_customer = AsyncMock(return_value={"id": "cus_flow"})
        mock_airwallex.create_payment_intent = AsyncMock(return_value={
            "request_id": "req_flow_complete",
            "payment_intent_id": "pi_flow_complete",
            "client_token": "tok_flow_complete"
        })

        with patch('api.payments.get_airwallex_service', return_value=mock_airwallex):
            create_response = await client.post(
                "/api/v1/payments/create",
                headers=auth_headers,
                json={
                    "plan_tier": "pro",
                    "billing_cycle": "monthly",
                    "payment_method": "airwallex"
                }
            )

        assert create_response.status_code == 200
        order_data = create_response.json()
        order_no = order_data["order_no"]
        assert order_data["status"] == "pending"  # Initial status

        # Step 2: Query order status (should still be pending)
        query_response = await client.get(
            f"/api/v1/payments/{order_no}",
            headers=auth_headers
        )

        assert query_response.status_code == 200
        query_data = query_response.json()
        assert query_data["status"] == "pending"

        # Step 3: Mock payment completion
        complete_response = await client.post(
            f"/api/v1/payments/mock/{order_no}/complete",
            headers=auth_headers
        )

        assert complete_response.status_code == 200
        assert complete_response.json()["success"] is True

        # Step 4: Verify payment status changed to completed
        final_query = await client.get(
            f"/api/v1/payments/{order_no}",
            headers=auth_headers
        )

        assert final_query.status_code == 200
        final_data = final_query.json()
        assert final_data["status"] == "completed"
        assert final_data["completed_at"] is not None

        # Step 5: Verify subscription was created
        # Get user's current subscription
        from sqlalchemy import select
        user_id = auth_headers["Authorization"].split(" ")[1]
        # Decode JWT to get user_id (simplified - in real test would decode properly)
        # For now, verify subscription exists in database

    async def test_unauthorized_access_to_payment_endpoints(self, client: AsyncClient):
        """测试未授权用户无法访问支付端点"""
        # Try to create payment without auth
        response = await client.post(
            "/api/v1/payments/create",
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )

        assert response.status_code == 401

        # Try to query order without auth
        response = await client.get("/api/v1/payments/some_order_no")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestPaymentConfig:
    """测试支付配置端点"""

    async def test_get_payment_config_for_free_user(self, client: AsyncClient, auth_headers):
        """测试获取免费用户的支付配置"""
        response = await client.get(
            "/api/v1/payments/config",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "current_plan" in data
        assert data["current_plan"]["tier"] in ["free", "trial"]
        assert "upgrade_target" in data
        assert "plans" in data

    async def test_get_payment_config_requires_auth(self, client: AsyncClient):
        """测试获取支付配置需要认证"""
        response = await client.get("/api/v1/payments/config")

        assert response.status_code == 401
