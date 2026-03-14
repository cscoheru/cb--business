# models/favorite.py
"""用户收藏数据模型"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from config.database import Base


class Favorite(Base):
    """用户收藏模型 - 支持卡片和机会的收藏"""
    __tablename__ = 'favorites'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # 支持两种类型的收藏：卡片 或 商机
    card_id = Column(UUID(as_uuid=True), ForeignKey('cards.id', ondelete='CASCADE'), nullable=True, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey('business_opportunities.id', ondelete='CASCADE'), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # 唯一约束：一个用户对同一张卡片或同一个商机只能收藏一次
    # 使用部分索引确保 (card_id, opportunity_id) 中只有一个不为空
    __table_args__ = (
        UniqueConstraint('user_id', 'card_id', name='uq_user_card'),
        UniqueConstraint('user_id', 'opportunity_id', name='uq_user_opportunity'),
        Index('idx_favorites_user_id', 'user_id'),
        Index('idx_favorites_card_id', 'card_id'),
        Index('idx_favorites_opportunity_id', 'opportunity_id'),
        Index('idx_favorites_created_at', 'created_at'),

        # 检查约束：确保 card_id 和 opportunity_id 中至少有一个不为空
        # CheckConstraint('card_id IS NOT NULL OR opportunity_id IS NOT NULL', name='ck_favorite_target')
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'card_id': str(self.card_id) if self.card_id else None,
            'opportunity_id': str(self.opportunity_id) if self.opportunity_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        target = self.card_id or self.opportunity_id
        target_type = 'card' if self.card_id else 'opportunity'
        return f"<Favorite(id={self.id}, user_id={self.user_id}, {target_type}_id={target})>"
