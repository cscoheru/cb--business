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

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

### 运行开发服务器

```bash
python main.py
```

或使用uvicorn：

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

```bash
pytest tests/
```

## 部署

```bash
# 使用Railway部署
railway up
```

## 项目结构

```
backend/
├── main.py                    # FastAPI应用入口
├── requirements.txt           # Python依赖
├── config/                    # 配置模块
│   ├── database.py            # 数据库配置
│   ├── redis.py               # Redis配置
│   └── settings.py            # 应用配置
├── api/                       # API路由
│   ├── dependencies.py        # 依赖注入
│   └── health.py              # 健康检查API
├── models/                    # 数据库模型
│   ├── base.py                # 基础模型类
│   ├── user.py                # 用户模型
│   └── subscription.py        # 订阅模型
├── schemas/                   # Pydantic模式
│   ├── user.py                # 用户Schema
│   └── common.py              # 通用Schema
└── utils/                     # 工具函数
    ├── auth.py                # 认证工具
    └── logger.py              # 日志工具
```
# Deployment check - 2026年 3月12日 星期四 14时02分14秒 CST
