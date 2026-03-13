# models/airwallex.py
"""Airwallex payment gateway models"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import JSONB
from config.database import Base
from datetime import datetime
import uuid


class AirwallexPaymentIntent(Base):
    """Airwallex payment intent tracking"""
    __tablename__ = "airwallex_payment_intents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    airwallex_intent_id = Column(String(255), unique=True, nullable=False, index=True)
    merchant_order_id = Column(String(255), unique=True, nullable=False, index=True)
    amount_minor = Column(Integer, nullable=False)  # Amount in fen (1 CNY = 100 fen)
    currency = Column(String(10), default="CNY")
    status = Column(String(50), default="requires_payment_method", index=True)
    client_token = Column(Text)
    description = Column(Text)
    return_url = Column(Text)
    metadata = Column(JSONB)  # {plan_tier, billing_cycle, etc}
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AirwallexWebhookEvent(Base):
    """Airwallex webhook event log for idempotency and debugging"""
    __tablename__ = "airwallex_webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="pending", index=True)  # pending, processed, failed
    payload = Column(JSONB, nullable=False)  # Full webhook payload
    signature = Column(Text)
    timestamp = Column(DateTime(timezone=True))
    processed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
