# models/daily_card_views.py
"""Daily card view tracking model for rate limiting"""

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, DATE
from datetime import date
import uuid

from config.database import Base


class DailyCardView(Base):
    """Daily card view tracking for rate limiting"""
    __tablename__ = 'daily_card_views'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    view_date = Column(DATE, nullable=False, index=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    view_count = Column(Integer, nullable=False, default=1)
    first_viewed_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<DailyCardView(user_id={self.user_id}, card_id={self.card_id}, count={self.view_count})>"
