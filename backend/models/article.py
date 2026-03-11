# models/article.py
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, Integer, ForeignKey, UUID, func
from config.database import Base
import uuid


class Article(Base):
    """文章模型"""
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, )
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    full_content = Column(Text)
    link = Column(String(1000), unique=True, nullable=False)
    source = Column(String(100), nullable=False)  # 数据源名称
    language = Column(String(10), default="zh")  # zh/en

    # AI分析结果
    content_theme = Column(String(50))  # 机会/风险/政策/指南等
    region = Column(String(50))  # 地区
    country = Column(String(10))  # 国家代码 (th, vn, my, us, br, mx)
    platform = Column(String(50))  # 平台
    tags = Column(Text)  # JSON数组字符串 ["tag1", "tag2"]
    risk_level = Column(String(20))  # low/medium/high/critical
    opportunity_score = Column(Float)  # 0.0-1.0 商机评分

    # 元数据
    author = Column(String(200))
    published_at = Column(DateTime(timezone=True))
    crawled_at = Column(DateTime(timezone=True), server_default=func.now())

    # 状态
    is_processed = Column(Boolean, default=False)  # 是否已通过AI处理
    is_published = Column(Boolean, default=False)  # 是否已发布到用户

    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title[:30]}, source={self.source})>"


class ArticleTag(Base):
    """文章标签"""
    __tablename__ = "article_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, )
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CrawlLog(Base):
    """爬取日志"""
    __tablename__ = "crawl_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, )
    source = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # success/failed/partial
    articles_count = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<CrawlLog(source={self.source}, status={self.status}, count={self.articles_count})>"
