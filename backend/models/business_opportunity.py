# models/business_opportunity.py
"""智能商机跟踪系统 - 数据模型"""

from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
import enum

from config.database import Base


class OpportunityStatus(str, enum.Enum):
    """商机状态"""
    POTENTIAL = "potential"      # 发现期：初始发现的商机
    VERIFYING = "verifying"      # 验证期：正在采集数据验证
    ASSESSING = "assessing"      # 评估期：生成可行性报告
    EXECUTING = "executing"      # 执行期：用户开始执行
    ARCHIVED = "archived"        # 归档期：已完成或放弃
    IGNORED = "ignored"          # 忽略：AI判断不相关
    FAILED = "failed"            # 失败：验证失败


class OpportunityType(str, enum.Enum):
    """商机类型"""
    PRODUCT = "product"          # 产品机会
    POLICY = "policy"            # 政策机会
    PLATFORM = "platform"        # 平台机会
    BRAND = "brand"              # 品牌机会
    INDUSTRY = "industry"        # 行业机会
    REGION = "region"            # 地区机会


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"          # 待执行
    RUNNING = "running"          # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class TaskPriority(str, enum.Enum):
    """任务优先级"""
    HIGH = "high"                # 高优先级
    MEDIUM = "medium"            # 中优先级
    LOW = "low"                  # 低优先级


class BusinessOpportunity(Base):
    """商机模型"""
    __tablename__ = 'business_opportunities'

    # 基本信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(OpportunityStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=OpportunityStatus.POTENTIAL, index=True)
    opportunity_type = Column(SQLEnum(OpportunityType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)

    # 关系（延迟加载）
    from sqlalchemy.orm import relationship
    card = relationship("Card", foreign_keys=[card_id], lazy='joined')
    article = relationship("Article", foreign_keys=[article_id], lazy='joined')
    user = relationship("User", foreign_keys=[user_id], lazy='joined')

    # 商机要素（多维度JSONB）
    # 结构: {product: {...}, region: {...}, platform: {...}, policy: {...}, brand: {...}, industry: {...}}
    elements = Column(JSONB, nullable=False, default=dict)

    # AI分析结果
    # 结构: {why_opportunity, key_assumptions, verification_needs, data_requirements, confidence_history}
    ai_insights = Column(JSONB, nullable=False, default=dict)
    confidence_score = Column(Float, nullable=False, default=0.5, index=True)
    last_verification_at = Column(DateTime(timezone=True))

    # 用户交互
    # 结构: {views: int, saved: bool, feedback: str, notes: str}
    user_interactions = Column(JSONB, default=dict)

    # 锁定状态（用于试用过期）
    is_locked = Column(Boolean, default=False, nullable=False, server_default='false', index=True)
    locked_at = Column(DateTime(timezone=True))

    # 关联到Card和Article (融合设计)
    card_id = Column(UUID(as_uuid=True), ForeignKey('cards.id', ondelete='SET NULL'), nullable=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id', ondelete='SET NULL'), nullable=True)

    # 关联的用户ID（如果商机由特定用户创建）
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # 元数据
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    archived_at = Column(DateTime(timezone=True))
    archive_reason = Column(String(500))

    # 索引
    __table_args__ = (
        Index('idx_bo_elements', elements, postgresql_using='gin'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'status': self.status.value if isinstance(self.status, OpportunityStatus) else self.status,
            'opportunity_type': self.opportunity_type.value if isinstance(self.opportunity_type, OpportunityType) else self.opportunity_type,
            'elements': self.elements or {},
            'ai_insights': self.ai_insights or {},
            'confidence_score': self.confidence_score,
            'last_verification_at': self.last_verification_at.isoformat() if self.last_verification_at else None,
            'user_interactions': self.user_interactions or {},
            'card_id': str(self.card_id) if self.card_id else None,
            'article_id': str(self.article_id) if self.article_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'archive_reason': self.archive_reason,
        }

    def to_dict_include_related(self) -> Dict[str, Any]:
        """转换为字典，包含关联的card和article数据"""
        data = self.to_dict()

        # 添加关联的Card数据
        if self.card:
            data['card'] = {
                'id': str(self.card.id),
                'title': self.card.title,
                'category': self.card.category,
                'content': {
                    'summary': {
                        'title': self.card.content.get('summary', {}).get('title', ''),
                        'opportunity_score': self.card.content.get('summary', {}).get('opportunity_score', 0),
                    }
                },
                'amazon_data': self.card.amazon_data,
                'views': self.card.views,
                'likes': self.card.likes,
            }

        # 添加关联的Article数据
        if self.article:
            data['article'] = {
                'id': str(self.article.id),
                'title': self.article.title,
                'summary': self.article.summary,
                'link': self.article.link,
                'source': self.article.source,
                'region': self.article.region,
                'country': self.article.country,
                'platform': self.article.platform,
                'content_theme': self.article.content_theme,
                'tags': self.article.tags,
                'published_at': self.article.published_at.isoformat() if self.article.published_at else None,
            }

        return data

    def can_transition_to(self, new_status: OpportunityStatus) -> bool:
        """检查是否可以转换到新状态"""
        valid_transitions = {
            OpportunityStatus.POTENTIAL: [OpportunityStatus.VERIFYING, OpportunityStatus.IGNORED],
            OpportunityStatus.VERIFYING: [OpportunityStatus.ASSESSING, OpportunityStatus.FAILED, OpportunityStatus.IGNORED],
            OpportunityStatus.ASSESSING: [OpportunityStatus.EXECUTING, OpportunityStatus.ARCHIVED, OpportunityStatus.IGNORED],
            OpportunityStatus.EXECUTING: [OpportunityStatus.ARCHIVED],
            OpportunityStatus.IGNORED: [OpportunityStatus.ARCHIVED],
            OpportunityStatus.FAILED: [OpportunityStatus.ARCHIVED],
            OpportunityStatus.ARCHIVED: [],
        }

        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status: OpportunityStatus, reason: Optional[str] = None) -> bool:
        """执行状态转换"""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")

        self.status = new_status

        if new_status == OpportunityStatus.ARCHIVED:
            self.archived_at = datetime.utcnow()
            self.archive_reason = reason

        return True

    def should_auto_evolve(self) -> Optional[OpportunityStatus]:
        """判断是否应该自动演进"""
        if self.status == OpportunityStatus.VERIFYING:
            # 验证期：如果置信度高且没有新的数据需求
            if self.confidence_score >= 0.8:
                data_requirements = self.ai_insights.get('data_requirements', [])
                if not data_requirements:
                    return OpportunityStatus.ASSESSING

        elif self.status == OpportunityStatus.ASSESSING:
            # 评估期：如果已有可行性报告
            if self.ai_insights.get('feasibility_report'):
                return OpportunityStatus.EXECUTING  # 等待用户决策

        return None

    def add_confidence_history(self, old_score: float, new_score: float, data_source: str, reasoning: str):
        """添加置信度变更历史"""
        if 'confidence_history' not in self.ai_insights:
            self.ai_insights['confidence_history'] = []

        self.ai_insights['confidence_history'].append({
            'from': old_score,
            'to': new_score,
            'data_source': data_source,
            'reasoning': reasoning,
            'timestamp': datetime.utcnow().isoformat()
        })

    def __repr__(self):
        return f"<BusinessOpportunity(id={self.id}, title={self.title[:30]}, type={self.opportunity_type}, status={self.status})>"


class DataCollectionTask(Base):
    """数据采集任务模型"""
    __tablename__ = 'data_collection_tasks'

    # 基本信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey('business_opportunities.id', ondelete='CASCADE'), nullable=False, index=True)

    # 任务定义
    task_type = Column(String(100), nullable=False)  # product_search, review_monitoring, price_tracking等
    priority = Column(SQLEnum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM, index=True)

    # AI的需求
    # 结构: {question, data_needed, constraints, outcome_format}
    ai_request = Column(JSONB, nullable=False)
    expected_outcome = Column(JSONB)

    # OpenClaw执行
    channel_name = Column(String(100))  # openclaw channel名称
    execution_params = Column(JSONB)    # 传递给channel的参数

    # 状态与结果
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True)
    result = Column(JSONB)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # 时间跟踪
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # AI反馈
    ai_feedback = Column(JSONB)
    usefulness_score = Column(Float)  # 0-1, 数据对AI判断的帮助程度

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': str(self.id),
            'opportunity_id': str(self.opportunity_id),
            'task_type': self.task_type,
            'priority': self.priority.value if isinstance(self.priority, TaskPriority) else self.priority,
            'ai_request': self.ai_request,
            'expected_outcome': self.expected_outcome,
            'channel_name': self.channel_name,
            'execution_params': self.execution_params,
            'status': self.status.value if isinstance(self.status, TaskStatus) else self.status,
            'result': self.result,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'ai_feedback': self.ai_feedback,
            'usefulness_score': self.usefulness_score,
        }

    def mark_started(self):
        """标记任务开始"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: Dict[str, Any]):
        """标记任务完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def mark_failed(self, error_message: str):
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.retry_count += 1

    def __repr__(self):
        return f"<DataCollectionTask(id={self.id}, type={self.task_type}, status={self.status})>"
