# tests/conftest.py
"""
Pytest configuration for backend API tests.
Uses SQLite in-memory database for fast testing.
"""
import pytest
import os
import sys
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Set test environment BEFORE any imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:?cache=shared"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["ALLOWED_ORIGINS"] = "*"

# Mock Redis client before importing
class MockRedisClient:
    def __init__(self):
        self.client = None
    
    async def connect(self):
        self.client = MagicMock()
    
    async def disconnect(self):
        pass
    
    async def get(self, key: str):
        return None
    
    async def set(self, key: str, value: str, ex: int = None):
        pass
    
    async def delete(self, key: str):
        pass
    
    async def ping(self) -> bool:
        return True

mock_redis_client = MockRedisClient()

async def mock_get_redis() -> MockRedisClient:
    if not mock_redis_client.client:
        await mock_redis_client.connect()
    return mock_redis_client

class MockRedisModule:
    redis_client = mock_redis_client
    get_redis = mock_get_redis

sys.modules["config.redis"] = MockRedisModule()

# Now import
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import TypeDecorator, VARCHAR, JSON
from sqlalchemy.dialects.postgresql import JSONB
from api import app
from api.dependencies import get_db
# Import from models/__init__ to ensure all models are registered with Base
from models import Base, User, Subscription, Article, Payment, Favorite


# SQLite 兼容层：将 JSONB 映射为 JSON (SQLite 支持)
class SQLiteJSONB(TypeDecorator):
    """SQLite 兼容的 JSONB 类型"""
    impl = JSON

    cache_ok = True

    def process_result_value(self, value, dialect):
        return value

    def bind_processor(self, dialect):
        if dialect.name == 'sqlite':
            return super().bind_processor(dialect)
        return super().bind_processor(dialect)


# Create a single test engine that will be shared
test_engine = None
test_session_factory = None


@pytest.fixture(scope="function")
async def db_setup():
    """Set up test database and session factory."""
    global test_engine, test_session_factory

    # Use shared cache in-memory database so all connections see the same data
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:?cache=shared",
        connect_args={"check_same_thread": False},
    )

    # CRITICAL: Replace config.database.engine with our test_engine
    # This ensures the FastAPI app uses the same database
    from config import database as db_module
    db_module.engine = test_engine
    # Also recreate the session factory with our test engine
    db_module.AsyncSessionLocal = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # 为 SQLite 替换所有 JSONB 类型为 JSON
    from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
    for table in Base.metadata.tables.values():
        for column in table.columns:
            # 检查是否是 JSONB 或包含 JSONB
            if hasattr(column.type, 'aspect_types'):
                # Array/JSON 等复杂类型
                for aspect in column.type.aspect_types:
                    if isinstance(aspect, type(JSONB)):
                        column.type = SQLiteJSON()
            elif str(column.type) == 'JSONB':
                column.type = SQLiteJSON()

    # Create all tables
    async with test_engine.begin() as conn:
        def log_tables(connection):
            print(f"Creating {len(Base.metadata.tables)} tables...")
            for table_name in Base.metadata.tables.keys():
                print(f"  - {table_name}")
        await conn.run_sync(log_tables)
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    # Create session factory
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield test_engine

    # Cleanup
    await test_engine.dispose()
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture(scope="function")
async def db_session(db_setup):
    """Create a test database session."""
    # Use the global test_session_factory created by db_setup
    async with test_session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session):
    """Create a test client with database override."""
    # Override api.dependencies.get_db
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
    """Create a test user."""
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
    """Create a Pro test user."""
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
    """Create an admin test user."""
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
    """Get authentication token for test user."""
    response = await client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def pro_token(client: AsyncClient, pro_user: User) -> str:
    """Get authentication token for Pro user."""
    response = await client.post("/api/v1/auth/login", json={
        "email": pro_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """Get authentication token for admin user."""
    response = await client.post("/api/v1/auth/login", json={
        "email": admin_user.email,
        "password": "admin123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def auth_headers(auth_token: str) -> dict:
    """Get authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
async def pro_headers(pro_token: str) -> dict:
    """Get Pro user authentication headers."""
    return {"Authorization": f"Bearer {pro_token}"}


@pytest.fixture(scope="function")
async def admin_headers(admin_token: str) -> dict:
    """Get admin authentication headers."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
async def test_subscription(db_session: AsyncSession, test_user: User) -> Subscription:
    """Create a test subscription."""
    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=test_user.id,
        plan_tier="pro",
        billing_cycle="monthly",
        status="active"
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription
