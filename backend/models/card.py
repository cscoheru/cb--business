# models/card.py
"""信息卡片数据模型"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from config.database import Base


class Card(Base):
    """信息卡片模型"""
    __tablename__ = 'cards'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    content = Column(JSONB, nullable=False)
    analysis = Column(JSONB, nullable=False)
    amazon_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    is_published = Column(Boolean, default=False, index=True)

    # 索引
    __table_args__ = (
        Index('idx_cards_created_at', 'created_at'),
        Index('idx_cards_category', 'category'),
        Index('idx_cards_published', 'is_published', 'published_at'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': str(self.id),  # Convert UUID to string for JSON serialization
            'title': self.title,
            'category': self.category,
            'content': self.content,
            'analysis': self.analysis,
            'amazon_data': self.amazon_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'views': self.views,
            'likes': self.likes,
            'is_published': self.is_published,
        }

    def __repr__(self):
        return f"<Card(id={self.id}, title={self.title}, category={self.category})>"
