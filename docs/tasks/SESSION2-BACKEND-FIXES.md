# 会话2：后端修复任务清单

> **优先级**: P0（部署前必须完成）
> **预计工期**: 1-2小时
> **创建日期**: 2026-03-10

---

## 🔴 Critical 问题（必须修复）

### 1. 修复UUID类型比较错误

**文件**: `backend/api/admin.py`, `backend/api/subscriptions.py`

**问题**: UUID对象与字符串比较导致查询失败

**修复**:

```python
# backend/api/admin.py:102
# 错误代码
UserUsage.user_id == str(user.id)

# 修复后
UserUsage.user_id == user.id
```

```python
# backend/api/subscriptions.py:39
# 错误代码
Subscription.user_id == str(current_user.id)

# 修复后
Subscription.user_id == current_user.id
```

**验证**: 运行相关测试确认查询正常

---

### 2. 更新requirements.txt

**文件**: `backend/requirements.txt`

**添加缺失的依赖**:

```txt
# 密码哈希
bcrypt>=4.0.1

# 支付二维码生成
qrcode>=7.4.2

# SQLite异步支持（测试环境）
aiosqlite>=0.19.0

# UUID类型支持
sqlalchemy-utils>=0.41.1
```

**验证**: `pip install -r requirements.txt` 无错误

---

### 3. 创建数据库初始化脚本

**新建文件**: `backend/scripts/init_db.py`

```python
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

async def init_database():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")

    # 创建默认管理员用户
    from sqlalchemy.ext.asyncio import AsyncSession
    from config.database import async_session_maker
    from models.user import User, PlanTier
    import bcrypt

    async with async_session_maker() as session:
        # 检查是否已存在管理员
        result = await session.execute(
            select(User).where(User.email == "admin@3strategy.cc")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            hashed_password = bcrypt.hashpw("admin123456".encode(), bcrypt.gensalt()).decode()
            admin = User(
                email="admin@3strategy.cc",
                password_hash=hashed_password,
                name="系统管理员",
                plan_tier=PlanTier.ENTERPRISE,
                is_admin=True
            )
            session.add(admin)
            await session.commit()
            print("✅ Default admin user created (admin@3strategy.cc / admin123456)")
        else:
            print("ℹ️ Admin user already exists")

if __name__ == "__main__":
    asyncio.run(init_database())
```

**验证**: `python scripts/init_db.py` 成功创建表

---

### 4. 添加管理员权限字段

**修改文件**: `backend/models/user.py`

```python
# 在 User 类中添加
is_admin = Column(Boolean, default=False, nullable=False, comment="是否为管理员")
```

**修改文件**: `backend/api/admin.py`

```python
# 修改 get_admin_user 函数
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """验证当前用户是否为管理员"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_ADMIN", "message": "需要管理员权限"}
        )
    return current_user
```

**创建迁移脚本**: `backend/migrations/add_is_admin.sql`

```sql
-- 添加 is_admin 字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL;

-- 设置默认管理员
UPDATE users SET is_admin = TRUE WHERE email = 'admin@3strategy.cc';
```

**验证**: 登录非管理员企业版用户，确认无法访问管理API

---

### 5. 修复微信支付API URL

**文件**: `backend/services/wechat_pay.py`

**问题**: 使用已废弃的沙箱环境

**修复**:

```python
def _get_api_url(self) -> str:
    """获取微信支付API URL"""
    # 微信支付已废弃沙箱环境，直接使用生产环境
    return "https://api.mch.weixin.qq.com/pay/unifiedorder"
```

**同时删除**: `backend/config/settings.py` 中的 `WECHAT_SANDBOX` 配置

**验证**: 支付接口调用正常

---

## 🟠 High Priority 问题（强烈建议修复）

### 6. 加强支付回调验证

**文件**: `backend/api/payments.py`

**添加验证逻辑**:

```python
@router.post("/wechat/notify")
async def wechat_notify(request: Request, db: AsyncSession = Depends(get_db)):
    # ... 现有代码 ...

    # 添加金额验证
    if data.get("total_fee") != int(payment.amount * 100):
        logger.warning(f"Payment amount mismatch: {data.get('total_fee')} != {payment.amount * 100}")
        return wechat_pay.build_notify_response(False, "金额不匹配")

    # 添加重放攻击防护（使用Redis）
    from config.redis import redis_client
    cache_key = f"payment_notify:{order_no}"
    existing = await redis_client.get(cache_key)
    if existing:
        logger.info(f"Payment already processed: {order_no}")
        return wechat_pay.build_notify_response(True, "OK")  # 已处理

    await redis_client.set(cache_key, "1", ex=3600)  # 1小时过期

    # ... 继续处理 ...
```

---

### 7. 添加全局异常处理器

**修改/创建文件**: `backend/api/__init__.py`

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.headers.get("X-Error-Code", "HTTP_ERROR")
        }
    )
```

**同时修复**: `backend/api/payments.py` 添加 `import uuid`

---

### 8. 添加环境变量验证

**文件**: `backend/config/settings.py`

**添加验证器**:

```python
from pydantic import validator

class Settings(BaseSettings):
    # ... 现有字段 ...

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-in-production-use-openssl-rand-hex-32":
            raise ValueError("SECRET_KEY must be changed in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'sqlite:///')):
            raise ValueError("DATABASE_URL must start with postgresql:// or sqlite:///")
        return v

    @validator('ALLOWED_ORIGINS')
    def validate_cors_origins(cls, v):
        if v == "*" and ENVIRONMENT == "production":
            raise ValueError("Wildcard CORS origins are not allowed in production")
        return v
```

---

### 9. 修复CORS配置

**文件**: `backend/config/settings.py`

**修改默认值**:

```python
class Settings(BaseSettings):
    # ...
    ALLOWED_ORIGINS: str = ""  # 默认为空，要求显式配置
    ENVIRONMENT: str = "development"
```

**更新**: `backend/main.py` 中的CORS配置

```python
origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📋 验证清单

完成所有修复后，请验证：

- [ ] 后端服务正常启动
- [ ] `pytest` 测试通过
- [ ] 数据库表正确创建
- [ ] 管理员权限验证正常
- [ ] 支付回调验证正常
- [ ] 环境变量验证生效
- [ ] CORS配置正确

---

## 📁 修改文件清单

| 文件 | 操作 | 类型 |
|------|------|------|
| `api/admin.py` | 修改 | 代码 |
| `api/subscriptions.py` | 修改 | 代码 |
| `requirements.txt` | 修改 | 配置 |
| `scripts/init_db.py` | 新建 | 代码 |
| `models/user.py` | 修改 | 代码 |
| `api/__init__.py` | 新建/修改 | 代码 |
| `services/wechat_pay.py` | 修改 | 代码 |
| `api/payments.py` | 修改 | 代码 |
| `config/settings.py` | 修改 | 配置 |
| `migrations/add_is_admin.sql` | 新建 | SQL |
| `main.py` | 修改 | 配置 |

---

*本修复清单由代码审查报告生成*
