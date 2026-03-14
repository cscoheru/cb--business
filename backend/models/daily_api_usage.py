# models/daily_api_usage.py
"""Daily API usage tracking model for rate limiting"""

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, DATE
from datetime import date
import uuid

from config.database import Base


class DailyApiUsage(Base):
    """Daily API usage tracking for rate limiting"""
    __tablename__ = 'daily_api_usage'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    usage_date = Column(DATE, nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    call_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<DailyApiUsage(user_id={self.user_id}, endpoint={self.endpoint}, count={self.call_count})>"
