# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from config.database import get_db
from config.settings import settings
from api import app
from models.user import Base, User
from models.subscription import Subscription, UserUsage


# 测试数据库URL (使用SQLite内存数据库)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # 使用ASGI transport创建httpx客户端
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_token(client: AsyncClient) -> str:
    """创建测试用户并返回token"""
    # 注册测试用户
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "test123456",
            "name": "测试用户"
        }
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def test_user(client: AsyncClient, test_token: str) -> dict:
    """获取测试用户信息"""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
async def pro_user_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """创建专业版测试用户"""
    # 创建用户
    from utils.auth import get_password_hash
    user = User(
        email="pro@example.com",
        name="专业版用户",
        password_hash=get_password_hash("test123456"),
        plan_tier="pro",
        plan_status="active"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 返回JWT token
    from utils.auth import create_access_token
    from datetime import timedelta

    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=30)
    )
    return token


@pytest.fixture
def mock_user_data():
    """测试用户数据"""
    return {
        "email": "newuser@example.com",
        "password": "password123",
        "name": "新用户"
    }


@pytest.fixture
def mock_subscription_data():
    """测试订阅数据"""
    return {
        "plan_tier": "pro",
        "billing_cycle": "monthly"
    }
