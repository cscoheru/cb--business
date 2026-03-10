# models/subscription.py
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Numeric, Integer, Date, ForeignKey, Boolean, UUID, func
from config.database import Base
import enum


class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default='gen_random_uuid()')
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_tier = Column(String(20), nullable=False)
    status = Column(String(20), default="active")
    billing_cycle = Column(String(10))  # monthly, yearly
    amount = Column(Numeric(10, 2))
    currency = Column(String(10), default="CNY")
    started_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    canceled_at = Column(DateTime(timezone=True))
    auto_renew = Column(Boolean, default=True)
    payment_method = Column(String(50))
    external_subscription_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default='gen_random_uuid()')
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="CNY")
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(20), default="pending")  # pending, completed, failed, refunded
    transaction_id = Column(String(255), unique=True)
    external_order_id = Column(String(255))
    extra_data = Column(String)  # JSONB stored as String for now
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserUsage(Base):
    __tablename__ = "user_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default='gen_random_uuid()')
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    usage_type = Column(String(50), nullable=False)
    quantity = Column(Integer, default=1)
    period_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
