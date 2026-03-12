# models/product.py
"""产品数据模型"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from config.database import Base


class Product(Base):
    """产品数据表"""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 基本信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # 产品分类
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # 标签数组

    # 价格信息
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    price_range = Column(String(50), nullable=True)  # 价格区间标记

    # 平台信息
    platform = Column(String(50), nullable=False)  # amazon, shopee, lazada, tiktok
    country = Column(String(10), nullable=True)   # us, th, vn, my, sg, id, ph, br
    platform_product_id = Column(String(200), nullable=True)  # 平台产品ID/ASIN/item_id
    shop_id = Column(String(100), nullable=True)  # 店铺ID (Shopee/Lazada)

    # 销售指标
    rank = Column(Integer, nullable=True)          # 排名
    sold_count = Column(Integer, default=0)       # 销量
    rating = Column(Float, nullable=True)         # 评分
    reviews_count = Column(Integer, default=0)    # 评论数

    # 趋势数据
    trend_rank = Column(Integer, nullable=True)           # 趋势排名
    trend_direction = Column(String(10), nullable=True)   # up/down/stable
    trend_days_on_list = Column(Integer, default=0)        # 在榜天数

    # 图片/链接
    image_url = Column(Text, nullable=True)
    product_url = Column(Text, nullable=True)

    # 元数据
    source = Column(String(100), nullable=True)   # 数据来源
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # AI分析结果
    opportunity_score = Column(Float, nullable=True)      # 机会评分 (0-100)
    difficulty_score = Column(Float, nullable=True)      # 难度评分 (0-100)
    profit_margin = Column(Float, nullable=True)         # 预估利润率
    ai_insights = Column(JSON, nullable=True)             # AI分析结果

    # 索引
    __table_args__ = (
        # 复合索引：平台+国家
        # Index('idx_products_platform_country', 'platform', 'country'),
        # 分类索引
        # Index('idx_products_category', 'category'),
        # 趋势排名索引
        # Index('idx_products_trend_rank', 'trend_rank'),
    )


class ProductReview(Base):
    """产品评论表"""
    __tablename__ = "product_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 产品关联
    product_id = Column(UUID(as_uuid=True), nullable=True)

    # 评论基本信息
    platform = Column(String(50), nullable=False)  # amazon, shopee, lazada, tiktok
    country = Column(String(10), nullable=True)   # us, th, vn, my...
    platform_review_id = Column(String(200), nullable=True)  # 平台评论ID

    # 评论内容
    rating = Column(Integer, nullable=True)        # 1-5星
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    translated_content = Column(Text, nullable=True)  # 翻译后的内容

    # 评论元数据
    author_name = Column(String(200), nullable=True)
    author_verified = Column(Boolean, default=False)  # 是否验证购买
    review_date = Column(DateTime, nullable=True)
    helpful_count = Column(Integer, default=0)
    media_urls = Column(JSON, nullable=True)      # 图片/视频URL

    # AI分析结果
    sentiment = Column(Float, nullable=True)       # 情感分数 (-1到1)
    sentiment_label = Column(String(20), nullable=True)  # positive/neutral/negative
    keywords = Column(JSON, nullable=True)         # 关键词数组
    topics = Column(JSON, nullable=True)           # 主题分类
    pain_points = Column(JSON, nullable=True)      # 痛点标签
    mentioned_features = Column(JSON, nullable=True)  # 提到的产品特性

    # 客服/物流标签
    tags = Column(JSON, nullable=True)             # ['质量问题', '物流慢', '客服好'...]

    # 元数据
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductReviewSummary(Base):
    """评论汇总表（用于快速查询）"""
    __tablename__ = "product_review_summaries"

    product_id = Column(UUID(as_uuid=True), primary_key=True)

    # 基础统计
    total_reviews = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    rating_distribution = Column(JSON, nullable=True)  # {5: 120, 4: 30, ...}

    # 情感分析
    sentiment_score = Column(Float, nullable=True)
    positive_ratio = Column(Float, nullable=True)     # 好评率
    negative_ratio = Column(Float, nullable=True)     # 差评率

    # 关键词/主题
    top_keywords = Column(JSON, nullable=True)
    top_topics = Column(JSON, nullable=True)
    top_pain_points = Column(JSON, nullable=True)

    # 竞品对比
    vs_competitors = Column(JSON, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
