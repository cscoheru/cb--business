# models/card.py
"""信息卡片数据模型

支持多平台数据聚合：
- Amazon (Oxylabs)
- Lazada (东南亚)
- Shopee (东南亚)
- 其他平台扩展
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from config.database import Base


class Card(Base):
    """信息卡片模型

    存储多平台聚合的市场分析数据。
    content 字段包含标准化的分析结果。
    multi_platform_data 字段存储跨平台对比数据。
    """
    __tablename__ = 'cards'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)

    # 核心内容 (标准化分析结果)
    content = Column(JSONB, nullable=False, default={})
    analysis = Column(JSONB, nullable=False, default={})

    # 平台数据
    amazon_data = Column(JSONB, nullable=True)  # 兼容旧数据
    multi_platform_data = Column(JSONB, nullable=True)  # 新：多平台聚合数据

    # 时间和统计
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
            'id': str(self.id),
            'title': self.title,
            'category': self.category,
            'content': self.content or {},
            'analysis': self.analysis or {},
            'amazon_data': self.amazon_data,
            'multi_platform_data': self.multi_platform_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'views': self.views,
            'likes': self.likes,
            'is_published': self.is_published,
        }

    def get_platform_summary(self) -> dict:
        """获取平台数据摘要"""
        if not self.multi_platform_data:
            return {
                'platforms': ['amazon'] if self.amazon_data else [],
                'total_products': len(self.amazon_data.get('products', [])) if self.amazon_data else 0,
            }

        mpd = self.multi_platform_data
        return {
            'platforms': [p['platform'] for p in mpd.get('platforms', [])],
            'total_products': mpd.get('total_products', 0),
            'price_range': {
                'min': mpd.get('price', {}).get('min', 0),
                'max': mpd.get('price', {}).get('max', 0),
            },
            'avg_rating': mpd.get('rating', {}).get('weighted_avg', 0),
        }

    def __repr__(self):
        return f"<Card(id={self.id}, title={self.title}, category={self.category})>"
