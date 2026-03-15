# models/user_interaction.py
"""用户交互追踪模型 - 记录和分析用户行为"""

from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, ForeignKey, Index, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import enum

from config.database import Base


class InteractionEventType(str, enum.Enum):
    """交互事件类型"""
    # 浏览行为
    VIEW_CARD = "view_card"                    # 查看卡片
    VIEW_OPPORTUNITY = "view_opportunity"      # 查看商机详情
    VIEW_ARTICLE = "view_article"              # 查看文章

    # 互动行为
    FAVORITE_CARD = "favorite_card"            # 收藏卡片
    UNFAVORITE_CARD = "unfavorite_card"        # 取消收藏
    FAVORITE_OPPORTUNITY = "favorite_opportunity"  # 收藏商机
    SHARE_OPPORTUNITY = "share_opportunity"    # 分享商机

    # 分析行为
    GENERATE_REPORT = "generate_report"        # 生成AI报告
    DOWNLOAD_REPORT = "download_report"        # 下载报告
    EXPORT_DATA = "export_data"                # 导出数据
    COMPARE_COMPETITORS = "compare_competitors"  # 竞品对比

    # 搜索行为
    SEARCH_KEYWORDS = "search_keywords"        # 搜索关键词
    FILTER_CATEGORY = "filter_category"        # 筛选分类
    FILTER_PRICE_RANGE = "filter_price_range"  # 筛选价格区间

    # 导航行为
    VISIT_DASHBOARD = "visit_dashboard"        # 访问仪表板
    VISIT_PRICING = "visit_pricing"            # 访问定价页
    VISIT_CHECKOUT = "visit_checkout"          # 访问结账页

    # 转化行为
    START_TRIAL = "start_trial"                # 开始试用
    SUBSCRIBE = "subscribe"                    # 订阅
    UPGRADE_PLAN = "upgrade_plan"              # 升级方案
    CANCEL_SUBSCRIPTION = "cancel_subscription"  # 取消订阅

    # 社交行为
    INVITE_TEAM = "invite_team"                # 邀请团队成员
    SHARE_REPORT = "share_report"              # 分享报告


class UserInteraction(Base):
    """用户交互事件记录"""
    __tablename__ = 'user_interactions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 用户信息
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # 事件信息
    event_type = Column(SQLEnum(InteractionEventType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    event_name = Column(String(100), nullable=False)  # 事件名称（用于自定义事件）
    category = Column(String(50), nullable=False, index=True)  # 事件分类: browsing, engagement, conversion, etc.

    # 目标对象
    target_type = Column(String(50))  # 目标类型: card, opportunity, article, report, etc.
    target_id = Column(UUID(as_uuid=True))  # 目标ID

    # 事件数据
    event_metadata = Column(JSONB, default=dict)  # 事件元数据: {referrer, device, location, ...}
    properties = Column(JSONB, default=dict)  # 事件属性: {price_range, keywords, ...}

    # 转化追踪
    session_id = Column(String(100), index=True)  # 会话ID
    funnel_stage = Column(String(50), index=True)  # 转化漏斗阶段: awareness, consideration, conversion, retention
    attribution = Column(JSONB, default=dict)  # 归因数据: {source, medium, campaign}

    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('ix_user_interactions_user_event', 'user_id', 'event_type'),
        Index('ix_user_interactions_target', 'target_type', 'target_id'),
        Index('ix_user_interactions_created_at', 'created_at'),
    )


class UserSession(Base):
    """用户会话记录"""
    __tablename__ = 'user_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # 会话信息
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # 设备信息
    device_type = Column(String(50))  # desktop, mobile, tablet
    browser = Column(String(50))
    os = Column(String(50))
    ip_address = Column(String(50))

    # 来源追踪
    source = Column(String(50))  # direct, organic, referral, social, email, paid
    medium = Column(String(50))  # none, organic, cpc, banner, email
    campaign = Column(String(100))
    referral_url = Column(Text)

    # 会话统计
    page_views = Column(Integer, default=0)
    events_count = Column(Integer, default=0)
    conversions = Column(Integer, default=0)  # 转化次数

    # 转化漏斗
    funnel_stage = Column(String(50))  # 到达的漏斗阶段
    funnel_stages_visited = Column(JSONB, default=list)  # 访问过的漏斗阶段

    # 元数据
    meta_data = Column(JSONB, default=dict)


class UserEngagement(Base):
    """用户参与度统计（每日汇总）"""
    __tablename__ = 'user_engagement'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # 统计日期
    date = Column(DateTime(timezone=True), nullable=False, index=True)

    # 活跃度指标
    is_active = Column(Boolean, default=False, index=True)  # 当日是否活跃
    session_count = Column(Integer, default=0)  # 会话数
    page_views = Column(Integer, default=0)  # 页面浏览数
    events_count = Column(Integer, default=0)  # 事件数

    # 功能使用
    cards_viewed = Column(Integer, default=0)  # 查看的卡片数
    opportunities_viewed = Column(Integer, default=0)  # 查看的商机数
    favorites_count = Column(Integer, default=0)  # 收藏数
    reports_generated = Column(Integer, default=0)  # 生成的报告数
    searches_performed = Column(Integer, default=0)  # 搜索次数

    # 参与度评分 (0-100)
    engagement_score = Column(Float, default=0.0)  # 综合参与度分数
    activity_score = Column(Float, default=0.0)  # 活跃度分数
    depth_score = Column(Float, default=0.0)  # 深度分数
    growth_score = Column(Float, default=0.0)  # 增长分数

    # 资产积累（用于判断沉没成本）
    total_favorites = Column(Integer, default=0)  # 累计收藏数
    total_reports = Column(Integer, default=0)  # 累计报告数
    total_days_active = Column(Integer, default=0)  # 累计活跃天数
    streak_days = Column(Integer, default=0)  # 连续活跃天数

    # 转化指标
    trial_started = Column(Boolean, default=False)  # 是否开始试用
    trial_converted = Column(Boolean, default=False)  # 是否转化为付费
    conversion_day = Column(Integer)  # 转化天数（从注册到付费的天数）

    # 元数据
    meta_data = Column(JSONB, default=dict)

    # 唯一约束
    __table_args__ = (
        Index('ix_user_engagement_user_date', 'user_id', 'date', unique=True),
    )


class ConversionEvent(Base):
    """转化事件（关键转化点记录）"""
    __tablename__ = 'conversion_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # 转化信息
    conversion_type = Column(String(50), nullable=False, index=True)  # trial_start, subscription, upgrade, renewal
    conversion_stage = Column(String(50), nullable=False)  # funnel_stage
    conversion_value = Column(Float)  # 转化价值（美元）

    # 事件详情
    event_data = Column(JSONB, default=dict)  # 转化事件详细数据
    attribution = Column(JSONB, default=dict)  # 归因数据

    # 时间戳
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # 试用相关
    trial_days_used = Column(Integer)  # 试用天数
    trial_assets = Column(JSONB)  # 试用期间积累的资产 {favorites: 10, reports: 5}
