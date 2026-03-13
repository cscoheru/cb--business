# models/favorite.py
"""用户收藏数据模型"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from config.database import Base


class Favorite(Base):
    """用户收藏模型"""
    __tablename__ = 'favorites'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey('cards.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # 唯一约束：一个用户对同一张卡片只能收藏一次
    __table_args__ = (
        UniqueConstraint('user_id', 'card_id', name='uq_user_card'),
        Index('idx_favorites_user_id', 'user_id'),
        Index('idx_favorites_card_id', 'card_id'),
        Index('idx_favorites_created_at', 'created_at'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'card_id': str(self.card_id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, card_id={self.card_id})>"
