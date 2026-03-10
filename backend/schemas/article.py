# schemas/article.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ContentTheme(str, Enum):
    """内容主题"""
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    POLICY = "policy"
    GUIDE = "guide"
    MARKET = "market"
    PLATFORM = "platform"


class Region(str, Enum):
    """地区"""
    SOUTHEAST_ASIA = "southeast_asia"
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    LATIN_AMERICA = "latin_america"
    GLOBAL = "global"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ArticleResponse(BaseModel):
    """文章响应"""
    id: str
    title: str
    summary: Optional[str] = None
    full_content: Optional[str] = None
    link: str
    source: str
    language: str
    content_theme: Optional[str] = None
    region: Optional[str] = None
    platform: Optional[str] = None
    tags: Optional[List[str]] = None
    risk_level: Optional[str] = None
    opportunity_score: Optional[float] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    crawled_at: Optional[datetime] = None
    is_processed: bool = False
    is_published: bool = False

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """文章列表响应"""
    articles: List[ArticleResponse]
    total: int
    page: int = 1
    per_page: int = 20


class CrawlTriggerResponse(BaseModel):
    """爬取触发响应"""
    success: bool
    message: str
    source: str
    articles_count: int
    started_at: datetime


class CrawlStatusResponse(BaseModel):
    """爬取状态响应"""
    source: str
    status: str
    last_crawl_at: Optional[datetime]
    articles_count: int
    next_crawl_at: Optional[datetime]
