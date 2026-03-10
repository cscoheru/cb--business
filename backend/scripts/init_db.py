"""
数据库初始化脚本
用于首次部署时创建所有数据库表
"""
import asyncio
from config.database import engine
from models.base import Base
from models.user import User
from models.subscription import Subscription, Payment, UserUsage
from models.article import Article, ArticleTag, CrawlLog
from sqlalchemy import select


async def init_database():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")

    # 创建默认管理员用户
    from config.database import async_session_maker
    from api.auth import get_password_hash

    async with async_session_maker() as session:
        # 检查是否已存在管理员
        result = await session.execute(
            select(User).where(User.email == "admin@3strategy.cc")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            import uuid
            admin = User(
                id=uuid.uuid4(),
                email="admin@3strategy.cc",
                password_hash=get_password_hash("admin123456"),
                name="系统管理员",
                plan_tier="enterprise",
                plan_status="active",
                is_admin=True
            )
            session.add(admin)
            await session.commit()
            print("✅ Default admin user created (admin@3strategy.cc / admin123456)")
        else:
            print("ℹ️ Admin user already exists")


if __name__ == "__main__":
    asyncio.run(init_database())
