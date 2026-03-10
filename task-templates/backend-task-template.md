# 后端任务书模板

> **模板版本**: v1.0
> **适用于**: 会话2（后端开发线）
> **技术栈**: FastAPI, Python 3.11+, SQLAlchemy, Pydantic

---

# TASK-XXX: [任务名称]

> **所属会话**: 会话2（后端开发线）
> **优先级**: P0/P1/P2
> **预计工期**: X 天
> **依赖任务**: TASK-XXX（如有）
> **创建日期**: YYYY-MM-DD
> **状态**: ⏳ 待开始 / 🔄 进行中 / ✅ 已完成 / ❌ 已阻塞

---

## 任务目标

[清晰描述这个后端任务要达成的目标]

**示例**：
- 实现用户认证系统（JWT）
- 创建订阅管理API
- 集成微信支付

---

## 背景信息

**项目上下文**：
- 这是一个面向国内跨境电商创业者的SaaS平台
- 采用 Freemium 工具型商业模式
- 后端使用 FastAPI + PostgreSQL

**为什么需要这个任务**：
[说明这个任务在整体项目中的作用]

---

## 验收标准

- [ ] API按规范实现完成
- [ ] 单元测试覆盖率 >80%
- [ ] API文档自动生成
- [ ] 与前端联调通过
- [ ] 通过代码审查

---

## 技术要求

### 技术栈
```
- Python 3.11+
- FastAPI
- SQLAlchemy (ORM)
- Pydantic (数据验证)
- python-jose (JWT)
- asyncpg (PostgreSQL异步驱动)
- redis-py (Redis客户端)
```

### 关键文件/路径
```
项目根目录: /Users/kjonekong/Documents/cb-Business/backend/
API目录: backend/api/
模型目录: backend/models/
服务目录: backend/services/
配置目录: backend/config/
```

### 依赖数据库

| 表名 | 用途 | 字段 | 状态 |
|------|------|------|------|
| users | 用户信息 | id, email, password_hash, plan_tier | ⏳ 待创建 |
| subscriptions | 订阅信息 | id, user_id, plan_tier, status | ⏳ 待创建 |

---

## 参考资料

**设计文档**：
- 主计划：`/Users/kjonekong/.claude/plans/pure-crunching-lantern.md`
- 数据库Schema：`/Users/kjonekong/Documents/cb-Business/docs/database/schema.sql`

**技术文档**：
- FastAPI：https://fastapi.tiangolo.com/
- SQLAlchemy：https://docs.sqlalchemy.org/

---

## 开发指南

### 步骤1：环境准备
```bash
cd /Users/kjonekong/Documents/cb-Business/backend
source venv/bin/activate  # 激活虚拟环境
pip install -r requirements.txt
```

### 步骤2：创建API路由
```python
# backend/api/xxx.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/xxx", tags=["xxx"])

@router.post("/create")
async def create_xxx(
    request: RequestModel,
    current_user: User = Depends(get_current_user)
):
    # 实现逻辑
    pass
```

### 步骤3：数据模型
```python
# backend/models/xxx.py
from sqlalchemy import Column, String, Integer
from database import Base

class XXX(Base):
    __tablename__ = "xxx"
    id = Column(Integer, primary_key=True)
    # ... 其他字段
```

### 步骤4：业务服务
```python
# backend/services/xxx_service.py
class XXXService:
    async def create_xxx(self, data: dict) -> dict:
        # 业务逻辑
        pass
```

### 注意事项
1. 所有API必须使用 async/await
2. 使用 Pydantic 进行数据验证
3. 敏感信息（密码、密钥）不能记录日志
4. 错误处理使用 HTTPException
5. 数据库操作使用 SQLAlchemy 异步模式

---

## API规范

### 请求格式
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

### 响应格式（成功）
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 响应格式（失败）
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

---

## 测试要求

### 单元测试
```bash
# 使用 pytest
cd backend
pytest tests/test_api_xxx.py -v
```

### API测试
```bash
# 使用 curl
curl -X POST http://localhost:8000/api/v1/xxx \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"field1": "value1"}'
```

### 测试覆盖
- [ ] 正常流程测试
- [ ] 异常情况测试
- [ ] 边界条件测试
- [ ] 权限验证测试

---

## 提交规范

### Git提交格式
```bash
git add .
git commit -m "feat: 实现用户认证API

- 添加JWT登录/注册端点
- 实现密码加密存储
- 添加token刷新机制

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 代码审查清单
- [ ] 代码符合 PEP 8 规范
- [ ] 所有函数有类型注解
- [ ] 有适当的错误处理
- [ ] 敏感信息已移除
- [ ] 测试已通过

---

## 进度更新

**开始时间**: YYYY-MM-DD HH:MM

**进度记录**:
- YYYY-MM-DD: 完成API框架
- YYYY-MM-DD: 完成业务逻辑
- ...

**完成时间**: YYYY-MM-DD HH:MM

---

## 问题记录

| 问题描述 | 发现时间 | 解决方案 | 状态 |
|----------|----------|----------|------|
| ... | ... | ... | ✅ 已解决 |

---

*本任务书由主会话（项目经理）创建和维护*
