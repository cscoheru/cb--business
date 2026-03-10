# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from api import app
from config.database import get_db
from models.base import Base
from models.user import User
from models.subscription import Subscription, Payment
from models.article import Article, CrawlLog


# 测试数据库URL（使用SQLite内存数据库）
TEST_DATABASE_URL = "sqlite+aiosqlite://://"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    from api.auth import get_password_hash

    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        name="测试用户",
        is_active=True,
        is_verified=True,
        role="free"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def pro_user(db_session: AsyncSession) -> User:
    """创建Pro测试用户"""
    from api.auth import get_password_hash

    user = User(
        email="pro@example.com",
        hashed_password=get_password_hash("password123"),
        name="Pro用户",
        is_active=True,
        is_verified=True,
        role="pro"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 创建Pro订阅
    subscription = Subscription(
        user_id=user.id,
        plan_tier="pro",
        billing_cycle="monthly",
        status="active"
    )
    db_session.add(subscription)
    await db_session.commit()

    return user


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """创建管理员用户"""
    from api.auth import get_password_hash

    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        name="管理员",
        is_active=True,
        is_verified=True,
        role="admin"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def auth_token(client: AsyncClient, test_user: User) -> str:
    """获取认证Token"""
    response = await client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    return data["data"]["access_token"]


@pytest.fixture(scope="function")
async def pro_token(client: AsyncClient, pro_user: User) -> str:
    """获取Pro用户Token"""
    response = await client.post("/api/v1/auth/login", json={
        "email": pro_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    return data["data"]["access_token"]


@pytest.fixture(scope="function")
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """获取管理员Token"""
    response = await client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    return data["data"]["access_token"]


@pytest.fixture(scope="function")
async def test_subscription(db_session: AsyncSession, test_user: User) -> Subscription:
    """创建测试订阅"""
    subscription = Subscription(
        user_id=test_user.id,
        plan_tier="pro",
        billing_cycle="monthly",
        status="active"
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


@pytest.fixture(scope="function")
async def auth_headers(auth_token: str) -> dict:
    """获取认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
async def pro_headers(pro_token: str) -> dict:
    """获取Pro用户请求头"""
    return {"Authorization": f"Bearer {pro_token}"}


@pytest.fixture(scope="function")
async def admin_headers(admin_token: str) -> dict:
    """获取管理员请求头"""
    return {"Authorization": f"Bearer {admin_token}"}
