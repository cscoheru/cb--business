# tests/test_utils.py
"""Test utilities and fixtures"""
import pytest
import asyncio
import uuid
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Must set environment before any config imports
import os
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/test_db"
os.environ["REDIS_URL"] = "redis://localhost"
os.environ["SECRET_KEY"] = "test_secret_key"

# Mock Redis before imports
mock_redis_instance = MagicMock()
mock_redis_instance.connect = AsyncMock()
mock_redis_instance.disconnect = AsyncMock()

import sys
sys.modules["config.redis"] = MagicMock()
sys.modules["config.redis"].redis_client = mock_redis_instance

# Now import - this will create the engine with the test DATABASE_URL
from api import app
from config.database import get_db
from models.base import Base
from models.user import User
from models.subscription import Subscription

# Clear startup events to prevent connection attempts
app.state.startup_calls = []
app.state.shutdown_calls = []


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
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
async def db_session(db_engine):
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Test client with dependency overrides"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create a mock lifespan that doesn't connect to external services
    async def mock_lifespan(app):
        yield
    
    # Temporarily replace lifespan
    original_router = app.router
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    from api.auth import get_password_hash
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("password123"),
        name="测试用户",
        plan_tier="free",
        plan_status="active"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def pro_user(db_session: AsyncSession) -> User:
    from api.auth import get_password_hash
    user = User(
        id=uuid.uuid4(),
        email="pro@example.com",
        password_hash=get_password_hash("password123"),
        name="Pro用户",
        plan_tier="pro",
        plan_status="active"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    subscription = Subscription(
        id=uuid.uuid4(),
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
    from api.auth import get_password_hash
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        password_hash=get_password_hash("admin123"),
        name="管理员",
        plan_tier="enterprise",  # Admin endpoints require enterprise tier
        plan_status="active"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def auth_token(client: AsyncClient, test_user: User) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def pro_token(client: AsyncClient, pro_user: User) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": pro_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    response = await client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "password": "admin123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
async def pro_headers(pro_token: str) -> dict:
    return {"Authorization": f"Bearer {pro_token}"}


@pytest.fixture(scope="function")
async def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}
