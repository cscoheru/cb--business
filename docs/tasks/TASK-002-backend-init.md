# TASK-002: 后端项目初始化

> **所属会话**: 会话2（后端开发线）
> **优先级**: P0（最高）
> **预计工期**: 1天
> **依赖任务**: TASK-003（基础设施配置）
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

创建FastAPI后端项目的基础结构，配置开发环境，搭建项目框架，实现基础的健康检查和配置管理，为后续API开发做好准备。

---

## 背景信息

**项目上下文**：
- 这是一个面向国内跨境电商创业者的SaaS平台
- 采用 Freemium 工具型商业模式
- 后端使用 FastAPI + PostgreSQL + Redis

**依赖说明**：
本任务依赖 TASK-003 完成的：
- PostgreSQL数据库表已创建
- Redis连接可用
- 环境配置文件已准备

**为什么需要这个任务**：
后端项目初始化是所有后端API开发的基础，需要建立项目结构、配置依赖、实现基础功能。

---

## 验收标准

- [ ] FastAPI项目创建完成，可运行
- [ ] 项目目录结构符合规范
- [ ] 数据库连接池配置完成
- [ ] Redis连接配置完成
- [ ] 健康检查API可访问（`/health`）
- [ ] API文档自动生成（`/docs`）
- [ ] 环境变量加载正常
- [ ] 基础中间件（CORS、日志）配置完成

---

## 技术要求

### 技术栈
```
- Python 3.11+
- FastAPI 0.104+
- SQLAlchemy 2.0+ (异步)
- asyncpg (PostgreSQL异步驱动)
- redis-py (Redis客户端)
- Pydantic v2 (数据验证)
- python-jose (JWT)
- passlib (密码加密)
- uvicorn (ASGI服务器)
- python-dotenv (环境变量)
```

### 项目结构
```
/Users/kjonekong/Documents/cb-Business/backend/
├── main.py                    # FastAPI应用入口
├── requirements.txt           # Python依赖
├── .env                       # 环境变量（不提交）
├── .env.example               # 环境变量模板（TASK-003已创建）
├── config/                    # 配置模块
│   ├── __init__.py
│   ├── database.py            # 数据库配置
│   ├── redis.py               # Redis配置
│   └── settings.py            # 应用配置
├── api/                       # API路由
│   ├── __init__.py
│   ├── dependencies.py        # 依赖注入
│   └── health.py              # 健康检查API
├── models/                    # 数据库模型
│   ├── __init__.py
│   ├── base.py                # 基础模型类
│   ├── user.py                # 用户模型
│   └── subscription.py        # 订阅模型
├── schemas/                   # Pydantic模式
│   ├── __init__.py
│   ├── user.py                # 用户Schema
│   └── common.py              # 通用Schema
├── services/                  # 业务服务
│   ├── __init__.py
│   └── database_service.py    # 数据库服务
└── utils/                     # 工具函数
    ├── __init__.py
    ├── auth.py                # 认证工具
    └── logger.py              # 日志工具
```

### 依赖的基础设施

| 组件 | 连接信息 | 状态 |
|------|----------|------|
| PostgreSQL | 139.224.42.111:5432/crawler_db | ✅ TASK-003完成 |
| Redis | 139.224.42.111:6379 | ✅ TASK-003完成 |
| MinIO | 139.224.42.111:9000 | ✅ 已存在 |

---

## 参考资料

**主计划文档**：
`/Users/kjonekong/.claude/plans/pure-crunching-lantern.md`

**环境配置**：
`/Users/kjonekong/Documents/cb-Business/backend/.env`

**数据库Schema**：
`/Users/kjonekong/Documents/cb-Business/docs/database/schema.sql`

**技术文档**：
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/en/20/
- Pydantic: https://docs.pydantic.dev/

---

## 开发指南

### 步骤1：创建项目目录和虚拟环境

```bash
# 进入项目目录
cd /Users/kjonekong/Documents/cb-Business

# 创建后端目录
mkdir -p backend/{config,api,models,schemas,services,utils}

# 创建Python虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate

# 确认Python版本
python --version  # 应该是 3.11+
```

### 步骤2：安装依赖

```bash
# 创建requirements.txt
cat > requirements.txt << 'EOF'
# FastAPI核心
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# 数据库
sqlalchemy==2.0.23
asyncpg==0.29.0
redis==5.0.1

# 认证
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# 工具
python-dotenv==1.0.0
httpx==0.25.2
aiofiles==23.2.1

# 支付（后续集成）
# cryptography==41.0.7
# qrcode==7.4.2
EOF

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import fastapi; import sqlalchemy; import redis; print('All dependencies OK')"
```

### 步骤3：创建配置模块

```python
# backend/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""
    # 应用信息
    APP_NAME: str = "Cross-Border Business API"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: str = "*"

    # 微信支付（后续使用）
    WECHAT_APP_ID: str = ""
    WECHAT_MCH_ID: str = ""
    WECHAT_API_KEY: str = ""
    WECHAT_NOTIFY_URL: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()

settings = get_settings()
```

```python
# backend/config/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import settings

# 创建异步引擎
# 将postgresql://转换为postgresql+asyncpg://
async_db_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

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
```

```python
# backend/config/redis.py
import redis.asyncio as aioredis
from .settings import settings

class RedisClient:
    """Redis客户端"""
    def __init__(self):
        self.client = None

    async def connect(self):
        """连接Redis"""
        self.client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> str | None:
        """获取值"""
        if self.client:
            return await self.client.get(key)
        return None

    async def set(self, key: str, value: str, ex: int = None):
        """设置值"""
        if self.client:
            await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        """删除值"""
        if self.client:
            await self.client.delete(key)

# 全局Redis客户端实例
redis_client = RedisClient()

async def get_redis() -> RedisClient:
    """获取Redis客户端依赖"""
    if not redis_client.client:
        await redis_client.connect()
    return redis_client
```

```python
# backend/config/__init__.py
from .settings import settings, get_settings
from .database import Base, engine, AsyncSessionLocal, get_db
from .redis import redis_client, get_redis

__all__ = [
    "settings",
    "get_settings",
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "redis_client",
    "get_redis",
]
```

### 步骤4：创建数据库模型

```python
# backend/models/base.py
from sqlalchemy import Column, String, DateTime, func
from config.database import Base

class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CRUDMixin:
    """CRUD混入类"""
    @classmethod
    async def get_by_id(cls, db, id: int):
        return await db.get(cls, id)
```

```python
# backend/models/user.py
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from config.database import Base
from models.base import TimestampMixin
import enum

class PlanTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # UUID存储为String
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    name = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String)
    plan_tier = Column(SQLEnum(PlanTier), default=PlanTier.FREE, nullable=False)
    plan_status = Column(SQLEnum(PlanStatus), default=PlanStatus.ACTIVE, nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    region_preference = Column(String(50))
    currency_preference = Column(String(10), default="CNY")
```

```python
# backend/models/__init__.py
from config.database import Base
from models.user import User

__all__ = ["Base", "User"]
```

### 步骤5：创建API路由

```python
# backend/api/health.py
from fastapi import APIRouter
from pydantic import BaseModel
from config.database import engine
from config.redis import redis_client
from datetime import datetime

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    redis: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    # 检查数据库
    try:
        async with engine.begin() as conn:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 检查Redis
    try:
        if redis_client.client:
            await redis_client.client.ping()
            redis_status = "connected"
        else:
            redis_status = "not initialized"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        database=db_status,
        redis=redis_status
    )
```

```python
# backend/api/__init__.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from config.database import engine
from config.redis import redis_client
from api.health import router as health_router
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="跨境电商智能信息SaaS平台API",
    version="1.0.0",
    debug=settings.DEBUG
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router, tags=["health"])

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"{settings.APP_NAME} starting up...")
    await redis_client.connect()
    logger.info("Redis connected")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Shutting down...")
    await redis_client.disconnect()
    await engine.dispose()
    logger.info("Connections closed")
```

### 步骤6：创建应用入口

```python
# backend/main.py
import uvicorn
from api import app

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

### 步骤7：创建.gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 环境变量
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# 日志
*.log

# 数据库
*.db
*.sqlite3
EOF
```

### 步骤8：创建README

```bash
cat > README.md << 'EOF'
# Cross-Border Business Backend

跨境电商智能信息SaaS平台后端服务

## 技术栈

- FastAPI 0.104+
- Python 3.11+
- SQLAlchemy 2.0+ (异步)
- PostgreSQL (asyncpg)
- Redis

## 开发

### 安装依赖

\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

\`\`\`bash
cp .env.example .env
\`\`\`

### 运行开发服务器

\`\`\`bash
python main.py
\`\`\`

或使用uvicorn：

\`\`\`bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

\`\`\`bash
pytest tests/
\`\`\`

## 部署

\`\`\`bash
# 使用Railway部署
railway up
\`\`\`
EOF
```

---

## 测试要求

### 启动测试
```bash
# 激活虚拟环境
cd /Users/kjonekong/Documents/cb-Business/backend
source venv/bin/activate

# 启动服务器
python main.py
```

### API测试
```bash
# 测试健康检查
curl http://localhost:8000/health

# 预期返回：
# {
#   "status": "healthy",
#   "timestamp": "2025-03-10T...",
#   "database": "connected",
#   "redis": "connected"
# }
```

### 访问API文档
在浏览器中打开：
- http://localhost:8000/docs（Swagger UI）
- http://localhost:8000/redoc（ReDoc）

### 验证清单
- [ ] 服务器正常启动
- [ ] 健康检查返回正确
- [ ] 数据库连接成功
- [ ] Redis连接成功
- [ ] API文档可访问
- [ ] CORS配置生效
- [ ] 日志正常输出

---

## 提交规范

```bash
cd /Users/kjonekong/Documents/cb-Business/backend

# 添加所有文件
git add .

# 提交
git commit -m "feat(TASK-002): 完成后端项目初始化

- 创建FastAPI项目结构
- 配置数据库连接池（SQLAlchemy异步）
- 配置Redis客户端
- 实现健康检查API
- 配置CORS中间件
- 创建基础模型类和User模型
- 配置环境变量加载
- 添加开发文档

项目结构:
- config/ 配置模块
- api/ API路由
- models/ 数据库模型
- schemas/ Pydantic模式
- services/ 业务服务
- utils/ 工具函数

技术栈:
- FastAPI 0.104.1
- SQLAlchemy 2.0.23 (异步)
- asyncpg 0.29.0
- redis-py 5.0.1

验收:
- ✅ 服务器可正常启动
- ✅ /health 端点返回正确
- ✅ 数据库连接成功
- ✅ Redis连接成功
- ✅ API文档自动生成

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 进度更新

**开始时间**: [填写开始时间]

**进度记录**:
- [ ] 创建项目目录和虚拟环境
- [ ] 安装Python依赖
- [ ] 创建配置模块
- [ ] 创建数据库模型
- [ ] 实现健康检查API
- [ ] 配置CORS和中间件
- [ ] 创建应用入口
- [ ] 编写README文档

**完成时间**: [填写完成时间]

---

## 问题记录

| 问题描述 | 发现时间 | 解决方案 | 状态 |
|----------|----------|----------|------|
| （如有问题记录在这里） | | | |

---

## 注意事项

1. **环境变量**：
   - 确保 `.env` 文件已正确配置
   - 不要提交 `.env` 到git

2. **数据库连接**：
   - 确保 TASK-003 已完成
   - 数据库表已创建

3. **Python版本**：
   - 确保使用 Python 3.11+
   - 虚拟环境已激活

---

## 下一步

完成本任务后，可以继续：
- **TASK-004**: 认证系统（用户注册、登录、JWT）
- **TASK-005**: 订阅管理系统

*本任务书由主会话（项目经理）创建和维护*
