# models/api_key.py
"""API Key 模型 - 第三方开发者认证

提供 API Key 管理和用量统计功能
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from config.database import Base
from models.base import TimestampMixin


class APITier(str):
    """API 订阅层级"""
    DEVELOPER = "developer"      # ¥299/月, 1000次/天
    BUSINESS = "business"        # ¥999/月, 10000次/天
    ENTERPRISE = "enterprise"    # ¥2999/月, 100000次/天


# 层级配置
TIER_LIMITS = {
    APITier.DEVELOPER: {
        "rate_limit_per_minute": 60,
        "rate_limit_per_day": 1000,
        "monthly_price": 299,
    },
    APITier.BUSINESS: {
        "rate_limit_per_minute": 300,
        "rate_limit_per_day": 10000,
        "monthly_price": 999,
    },
    APITier.ENTERPRISE: {
        "rate_limit_per_minute": 1000,
        "rate_limit_per_day": 100000,
        "monthly_price": 2999,
    },
}


class APIKey(Base, TimestampMixin):
    """API 密钥"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # 密钥信息
    key_hash = Column(String(64), unique=True, nullable=False)  # SHA256 hash
    key_prefix = Column(String(12), nullable=False)  # 显示用前缀 "cb_live_abc..."
    name = Column(String(100), nullable=False)  # "Production Key"

    # 订阅层级
    tier = Column(String(20), nullable=False, default=APITier.DEVELOPER)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))  # 订阅到期时间

    # 限流配置 (从 TIER_LIMITS 复制)
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    rate_limit_per_day = Column(Integer, default=1000, nullable=False)

    # 关联
    user = relationship("User", back_populates="api_keys")
    usage_records = relationship("APIUsage", back_populates="api_key", lazy="dynamic")

    def __repr__(self):
        return f"<APIKey {self.key_prefix}... ({self.tier})>"

    def to_dict(self):
        """转换为字典 (不包含敏感信息)"""
        return {
            "id": str(self.id),
            "key_prefix": self.key_prefix,
            "name": self.name,
            "tier": self.tier,
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_day": self.rate_limit_per_day,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class APIUsage(Base):
    """API 调用统计"""
    __tablename__ = "api_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False, index=True)

    # 调用信息
    endpoint = Column(String(100), nullable=False)  # /orchestrator/analyze
    method = Column(String(10), nullable=False)  # POST
    status_code = Column(Integer, nullable=False)  # 200, 429, 500

    # 性能
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer, default=0)  # AI token 消耗
    error_message = Column(String(500))  # 错误信息

    # 请求元数据
    ip_address = Column(String(45))  # IPv6 最长 45 字符
    user_agent = Column(String(255))

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # 关联
    api_key = relationship("APIKey", back_populates="usage_records")

    __table_args__ = (
        Index('idx_api_usage_key_date', 'api_key_id', 'created_at'),
    )

    def __repr__(self):
        return f"<APIUsage {self.endpoint} {self.status_code}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "api_key_id": str(self.api_key_id),
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
