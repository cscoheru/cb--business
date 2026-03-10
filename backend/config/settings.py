# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    # 应用信息
    APP_NAME: str = "Cross-Border Business API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production

    # 数据库
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: str = ""  # 默认为空，要求显式配置

    # 微信支付
    WECHAT_APP_ID: str = ""
    WECHAT_MCH_ID: str = ""
    WECHAT_API_KEY: str = ""
    WECHAT_API_V3_KEY: str = ""  # API v3 密钥
    WECHAT_CERT_PATH: str = ""  # 证书路径
    WECHAT_NOTIFY_URL: str = ""

    # MinIO 对象存储
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET_NAME: str = ""
    MINIO_USE_SSL: bool = False

    # 邮件配置
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""
    RESEND_FROM_NAME: str = ""

    # 功能开关
    FEATURE_REGISTRATION_ENABLED: bool = True
    FEATURE_PAYMENT_WECHAT_ENABLED: bool = False
    FEATURE_AI_CONTENT_GENERATION_ENABLED: bool = True

    # 日志级别
    LOG_LEVEL: str = "INFO"

    # 智谱AI
    ZHIPU_AI_KEY: str = ""

    # 支付回调URL
    PAYMENT_BASE_URL: str = "https://api.cb.3strategy.cc"  # 生产环境URL

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-in-production-use-openssl-rand-hex-32":
            raise ValueError("SECRET_KEY must be changed in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://', 'sqlite:///', 'sqlite+aiosqlite://')):
            raise ValueError("DATABASE_URL must start with postgresql://, postgresql+asyncpg://, sqlite:///, or sqlite+aiosqlite://")
        return v

    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_cors_origins(cls, v, info):
        # Allow wildcard in development only
        environment = info.data.get('ENVIRONMENT', 'development')
        if v == "*" and environment == "production":
            raise ValueError("Wildcard CORS origins are not allowed in production")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
