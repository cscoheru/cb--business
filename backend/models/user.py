# models/user.py
from sqlalchemy import Column, String, DateTime, UUID, Boolean
from config.database import Base
from models.base import TimestampMixin
import enum


class PlanTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    name = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String)
    plan_tier = Column(String(20), default=PlanTier.FREE.value, nullable=False)
    plan_status = Column(String(20), default=PlanStatus.ACTIVE.value, nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    region_preference = Column(String(50))
    currency_preference = Column(String(10), default="CNY")
    is_admin = Column(Boolean, default=False, nullable=False)
    airwallex_customer_id = Column(String(255), index=True)  # Airwallex customer ID for payments
