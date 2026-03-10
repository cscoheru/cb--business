# config/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings

# 创建异步引擎
# 将postgresql://转换为postgresql+asyncpg://
async_db_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# 根据数据库类型设置不同的引擎参数
if "sqlite" in async_db_url:
    # SQLite 不支持连接池设置
    engine = create_async_engine(
        async_db_url,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL 使用连接池
    engine = create_async_engine(
        async_db_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 声明基类
Base = declarative_base()


# 依赖注入
async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
