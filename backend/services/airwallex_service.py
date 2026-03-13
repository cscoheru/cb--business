# services/airwallex_service.py
"""Airwallex Payment Service"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import httpx

logger = logging.getLogger(__name__)


class AirwallexConfig:
    """Airwallex Configuration"""

    # API Keys (set in environment variables)
    API_KEY = os.getenv("AIRWALLEX_API_KEY", "")
    SCOPED_API_KEY = os.getenv("AIRWALLEX_SCOPED_API_KEY", "5d407acf3dfa6535f89cb5dc0b8f1a4c97037fa64c54d67544fd6371b8b0e4618e09c6d8a34ff6cfb3069d4aade80e57")
    API_BASE_URL = os.getenv("AIRWALLEX_API_URL", "https://api-airwallex.com")

    # Account & Organization IDs
    ACCOUNT_ID = os.getenv("AIRWALLEX_ACCOUNT_ID", "acct_iViBmbvbOzuOUVZexPSWuA")
    ORGANIZATION_ID = os.getenv("AIRWALLEX_ORGANIZATION_ID", "org_3-rgzD0qRdqtriN1dz2WJQ")
    DEFAULT_CUSTOMER_ID = os.getenv("AIRWALLEX_CUSTOMER_ID", "IX_3QtmsQn2k8lKOEZGDWw")

    # Entity Information
    ENTITY_NAME = "广州兰卡企业管理顾问有限公司"
    BUSINESS_TYPE = "国际"  # 国内/国际

    # Payment Configuration
    CURRENCY = "CNY"
    COUNTRY = "CN"

    # Webhook Configuration
    WEBHOOK_SECRET = os.getenv("AIRWALLEX_WEBHOOK_SECRET", "whsec_53Xksbabmivyqn6sGAL5ItVUU0s--o67")
    WEBHOOK_URL = os.getenv("AIRWALLEX_WEBHOOK_URL", "https://api.zenconsult.top/api/v1/payments/webhooks/airwallex")


class AirwallexError(Exception):
    """Airwallex payment error"""
    def __init__(self, message: str, code: str = "AIRWALLEX_ERROR", details: Dict = None):
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self):
        return f"[{self.code}] {self.message}"

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class AirwallexService:
    """Airwallex Payment Service"""

    def __init__(self):
        # Use scoped API key if available, otherwise fall back to regular API key
        self.api_key = AirwallexConfig.SCOPED_API_KEY or AirwallexConfig.API_KEY
        self.base_url = AirwallexConfig.API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Log which key type is being used (for debugging)
        if AirwallexConfig.SCOPED_API_KEY:
            logger.info("Using Airwallex Scoped API Key")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make API request to Airwallex"""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers, timeout=30.0)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=self.headers, timeout=30.0)
                else:
                    raise AirwallexError(f"Unsupported method: {method}")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"Airwallex API error: {e.response.status_code} - {e.response.text}")
                raise AirwallexError(
                    message=f"API request failed: {e.response.status_code}",
                    code="API_ERROR",
                    details={"status": e.response.status_code, "body": e.response.text}
                )
            except httpx.RequestError as e:
                logger.error(f"Airwallex network error: {e}")
                raise AirwallexError(
                    message="Network error connecting to payment gateway",
                    code="NETWORK_ERROR"
                )

    async def create_payment_intent(
        self,
        amount_cny: int,
        user_id: str,
        plan_tier: str,
        billing_cycle: str,
        description: str,
        return_url: Optional[str] = None,
        customer_email: Optional[str] = None,
        airwallex_customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent with Airwallex

        Args:
            amount_cny: Amount in CNY fen (1 CNY = 100 fen)
            user_id: User ID for metadata
            plan_tier: Plan tier for metadata
            billing_cycle: Billing cycle for metadata
            description: Payment description
            return_url: URL to redirect after payment
            customer_email: Customer email (optional)
            airwallex_customer_id: Existing Airwallex customer ID (e.g., IX_3QtmsQn2k8lKOEZGDWw)

        Returns:
            Payment intent response with client_token
        """
        # Convert CNY to minor units (fen)
        amount_minor = amount_cny * 100

        # Create unique request ID
        request_id = str(uuid.uuid4())

        # Prepare payment intent request
        payload = {
            "amount": str(amount_minor),
            "currency": AirwallexConfig.CURRENCY,
            "merchant_order_id": request_id,
            "description": description,
            "return_url": return_url or "https://www.zenconsult.top/billing?success=true",
            "customer": {
                "merchant_customer_id": user_id,
                "email": customer_email
            },
            "metadata": {
                "user_id": user_id,
                "plan_tier": plan_tier,
                "billing_cycle": billing_cycle
            },
            "transaction_mode": "oneoff"
        }

        # Add Airwallex customer ID if provided (for existing customers)
        if airwallex_customer_id:
            payload["customer"]["id"] = airwallex_customer_id
            logger.info(f"Using existing Airwallex customer: {airwallex_customer_id}")

        try:
            result = await self._make_request(
                "POST",
                "/v1/pa/payment_intents",
                data=payload
            )

            logger.info(f"Created Airwallex payment intent: {result.get('id')}")

            return {
                "payment_intent_id": result.get("id"),
                "customer_id": result.get("customer_id"),
                "client_token": result.get("next_action", {}).get("token", result.get("client_token")),
                "amount": amount_cny,
                "currency": AirwallexConfig.CURRENCY,
                "request_id": request_id,
                "status": result.get("status", "requires_payment_method")
            }

        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise

    async def get_payment_status(
        self,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Get payment intent status

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Payment intent details
        """
        try:
            result = await self._make_request(
                "GET",
                f"/v1/pa/payment_intents/{payment_intent_id}"
            )

            return {
                "id": result.get("id"),
                "status": result.get("status"),
                "amount": int(result.get("amount", 0)) / 100,  # Convert back to CNY
                "currency": result.get("currency"),
                "created_at": result.get("created_at"),
                "metadata": result.get("metadata", {})
            }

        except Exception as e:
            logger.error(f"Failed to get payment status: {e}")
            raise

    async def get_customer(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Get customer details from Airwallex

        Args:
            customer_id: Airwallex customer ID (e.g., IX_3QtmsQn2k8lKOEZGDWw)

        Returns:
            Customer details
        """
        try:
            result = await self._make_request(
                "GET",
                f"/v1/pa/customers/{customer_id}"
            )

            return {
                "id": result.get("id"),
                "merchant_customer_id": result.get("merchant_customer_id"),
                "email": result.get("email"),
                "name": result.get("name"),
                "phone_number": result.get("phone_number"),
                "created_at": result.get("created_at"),
                "deleted_at": result.get("deleted_at")
            }

        except Exception as e:
            logger.error(f"Failed to get customer {customer_id}: {e}")
            raise

    async def create_customer(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or retrieve customer in Airwallex

        Args:
            user_id: User ID from database
            email: Customer email
            name: Customer name (optional)

        Returns:
            Customer details with merchant_customer_id
        """
        payload = {
            "merchant_customer_id": user_id,
            "email": email,
            "name": name or email,
            "phone_number": "",
            "date_of_birth": None,
            "address": {
                "country_code": "CN",
                "state": "",
                "suburb": "",
                "line_1": "",
                "line_2": "",
                "postcode": ""
            },
            "metadata": {
                "user_id": user_id
            }
        }

        try:
            result = await self._make_request(
                "POST",
                "/v1/pa/customers",
                data=payload
            )

            logger.info(f"Created/retrieved Airwallex customer: {result.get('id')}")

            return {
                "id": result.get("id"),
                "merchant_customer_id": result.get("merchant_customer_id", user_id),
                "email": result.get("email"),
                "name": result.get("name")
            }

        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            raise

    async def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        timestamp: str
    ) -> bool:
        """
        Verify Airwallex webhook signature

        Args:
            payload: Raw webhook payload
            signature: Signature from header
            timestamp: Timestamp from header

        Returns:
            True if signature is valid, False otherwise
        """
        import hmac
        import hashlib

        if not AirwallexConfig.WEBHOOK_SECRET:
            logger.warning("WEBHOOK_SECRET not configured, skipping signature verification")
            return True

        # Create expected signature
        expected_payload = f"{timestamp}.{payload}"
        expected_signature = hmac.new(
            AirwallexConfig.WEBHOOK_SECRET.encode(),
            expected_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature.encode(), signature.encode())

    def format_amount_for_display(self, amount_cny: int) -> str:
        """Format amount for display (e.g., 9900 -> ¥99.00)"""
        return f"¥{amount_cny:.2f}"

    def format_amount_for_api(self, amount_cny: int) -> int:
        """Convert CNY yuan to fen for API"""
        return amount_cny * 100


# Singleton instance
_airwallex_service: Optional[AirwallexService] = None


def get_airwallex_service() -> AirwallexService:
    """Get or create Airwallex service singleton"""
    global _airwallex_service
    if _airwallex_service is None:
        _airwallex_service = AirwallexService()
    return _airwallex_service
