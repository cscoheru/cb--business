# CB-Business 项目上下文文档

**日期**: 2026-03-15
**项目类型**: 跨境电商智能信息SaaS平台
**技术栈**: Next.js + FastAPI + PostgreSQL + Redis
**部署状态**: Production (Live)

---

## 项目概述

### 业务模型
CB-Business是一个面向跨境电商的智能信息SaaS平台，通过AI分析全球市场数据，为卖家提供商业机会洞察。

**核心价值**:
- 🌍 全球市场数据监控 (12个品类)
- 🤖 AI驱动的机会发现 (C-P-I算法)
- 📊 实时趋势分析 (OpenClaw RSS采集)
- 💡 智能卡片生成 (327+市场洞察)

**目标用户**:
- Amazon跨境卖家
- Shopify独立站卖家
- 品牌出海企业
- 贸易公司

---

## 技术架构

### 前端架构
```
Next.js 13+ (App Router)
├── app/                    # App Router页面
│   ├── page.tsx           # 首页
│   ├── cards/             # 卡片页
│   ├── favorites/         # 收藏页
│   ├── dashboard/         # 用户中心
│   │   ├── page.tsx       # 仪表盘首页
│   │   ├── market/        # 市场概览
│   │   ├── policies/      # 政策中心
│   │   ├── risks/         # 风险预警
│   │   ├── opportunities/ # 机会发现
│   │   └── settings/      # 设置
│   ├── login/             # 登录
│   ├── register/          # 注册
│   ├── checkout/          # 支付
│   └── pricing/           # 定价
├── components/            # React组件
│   ├── cards/            # 卡片组件
│   ├── ui/               # shadcn/ui组件
│   ├── admin/            # 管理后台组件
│   └── layout/           # 布局组件
├── lib/                  # 工具库
│   ├── api.ts            # API客户端
│   ├── auth-context.tsx  # 认证上下文
│   └── contexts/         # 其他Context
└── e2e/                  # E2E测试
    ├── fixtures.ts       # 测试辅助
    ├── auth.spec.ts      # 认证测试
    └── ...
```

### 后端架构
```
FastAPI (Python 3.10+)
├── api/                   # API路由
│   ├── __init__.py       # CORS配置
│   ├── auth.py           # 认证API
│   ├── users.py          # 用户API
│   ├── cards.py          # 卡片API
│   ├── favorites.py      # 收藏API
│   ├── payments.py       # 支付API
│   ├── subscriptions.py  # 订阅API
│   └── ...
├── services/             # 业务逻辑
│   ├── card_generator.py # 卡片生成
│   ├── cache.py          # 缓存服务
│   ├── airwallex_service.py # 支付服务
│   └── smart_orchestrator.py # AI编排
├── models/               # 数据模型
│   ├── user.py
│   ├── card.py
│   ├── favorite.py
│   └── ...
├── scheduler/            # 定时任务
│   └── opportunity_tasks.py
├── crawler/              # 数据采集
│   └── products/
│       └── oxylabs_client.py
└── config/               # 配置
    ├── settings.py
    └── database.py
```

### 基础设施
```
HK Server (103.59.103.85)
├── Docker Network: cb-network (172.22.0.0/16)
│   ├── 172.22.0.2: cb-business-postgres
│   ├── 172.22.0.3: cb-business-redis
│   ├── 172.22.0.4: cb-business-api-fixed (FastAPI)
│   └── 172.22.0.5: nginx-gateway
├── Nginx配置: /opt/docker/nginx/conf.d/zenconsult.conf
└── SSL证书: /etc/nginx/ssl/api.zenconsult.top.*
```

### 部署架构
```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  浏览器访问   │  │  移动端访问   │  │  API调用     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      CDN层 (Vercel)                          │
│                    www.zenconsult.top                         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    反向代理层 (Nginx)                        │
│                  api.zenconsult.top                          │
│  - SSL终止                                                    │
│  - CORS处理 (FastAPI CORSMiddleware)                         │
│  - 负载均衡                                                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (FastAPI)                          │
│                    172.22.0.4:8000                           │
│  - RESTful API                                               │
│  - JWT认证                                                   │
│  - 业务逻辑                                                   │
└─────────────┬──────────────────────────┬────────────────────┘
              │                          │
              ▼                          ▼
┌───────────────────────────┐  ┌───────────────────────────┐
│   PostgreSQL (数据层)     │  │    Redis (缓存层)         │
│   172.22.0.2:5432         │  │    172.22.0.3:6379        │
│  - 17张表                  │  │  - 卡片缓存 (30min)       │
│  - 用户数据                │  │  - 会话缓存                │
│  - 业务数据                │  │  - API响应缓存             │
└───────────────────────────┘  └───────────────────────────┘
```

---

## 数据模型

### 核心表结构

#### users (用户表)
```sql
- id: UUID (PK)
- email: String (unique)
- hashed_password: String
- name: String
- plan_tier: Enum['trial', 'free', 'pro']
- plan_status: Enum['active', 'expired', 'locked']
- created_at: DateTime
- last_login_at: DateTime
- is_admin: Boolean
```

#### cards (卡片表)
```sql
- id: UUID (PK)
- category: String (12品类)
- title: String
- description: Text
- opportunity_score: Float (0-100)
- amazon_data: JSONB (产品数据)
- created_at: DateTime
```

#### favorites (收藏表)
```sql
- id: UUID (PK)
- user_id: UUID (FK)
- card_id: UUID (FK, nullable)
- opportunity_id: UUID (FK, nullable)
- created_at: DateTime
```

#### subscriptions (订阅表)
```sql
- id: UUID (PK)
- user_id: UUID (FK)
- plan_tier: Enum
- status: Enum
- started_at: DateTime
- expires_at: DateTime
```

---

## API端点清单

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/users/me` - 获取当前用户

### 卡片相关
- `GET /api/v1/cards/daily` - Top 3精选卡片
- `GET /api/v1/cards/history` - 全部12张卡片
- `GET /api/v1/cards/latest` - 最新卡片
- `GET /api/v1/cards/{id}` - 单张卡片详情

### 收藏相关
- `GET /api/v1/favorites` - 用户收藏列表
- `POST /api/v1/favorites` - 添加收藏
- `DELETE /api/v1/favorites/card/{card_id}` - 取消收藏
- `GET /api/v1/favorites/check/{card_id}` - 检查收藏状态

### 支付相关
- `POST /api/v1/payments/create` - 创建支付订单
- `GET /api/v1/payments/{order_no}` - 查询支付状态
- `POST /api/v1/payments/webhooks/airwallex` - Airwallex回调

### 订阅相关
- `GET /api/v1/subscriptions/me` - 我的订阅
- `GET /api/v1/subscriptions/plans` - 订阅计划

### 爬虫相关
- `GET /api/v1/crawler-sync/articles` - 文章列表 (正确)
- `GET /api/v1/crawler-sync/article/{id}` - 文章详情

---

## 订阅模式

### Tier系统
```
┌──────────────────────────────────────────────────────────┐
│  Trial (试用)          Free (免费)        Pro (专业)      │
│  ─────────────        ──────────────    ──────────────  │
│  • 7天期限            • 永久免费         • 按月/年订阅   │
│  • 全功能访问          • 3张卡片/天       • 无限制访问    │
│  • 50 API调用/天       • 10 API调用/天   • 无限API调用  │
│  • 基础数据更新        • 每日更新         • 实时更新     │
│  • 社区支持            • 社区支持         • 优先支持     │
└──────────────────────────────────────────────────────────┘
```

### 定价策略
- Trial: 免费7天 → 自动转为Free
- Free: ¥0/月
- Pro Monthly: ¥99/月
- Pro Yearly: ¥990/年 (优惠¥198)

---

## AI能力

### C-P-I算法
```
机会评分 = 竞争度(40%) × 潜力(35%) × 信息差(25%)

竞争度(C):
  - 市场饱和度
  - 竞品数量
  - 价格竞争程度

潜力(P):
  - 市场规模
  - 增长趋势
  - 利润空间

信息差(I):
  - 数据稀缺性
  - 分析难度
  - 时间敏感度
```

### OpenClaw集成
- **RSS采集**: 45个数据源，每2小时更新
- **AI分析**: GLM-4 Plus内容分类
- **实时数据**: 481篇文章，327张卡片

---

## 常见问题模式

### 1. CORS错误
**症状**: "No 'Access-Control-Allow-Origin' header"
**原因**: FastAPI容器未运行最新代码
**解决**: `ssh hk-jump "docker restart cb-business-api-fixed"`

### 2. TypeScript类型错误
**症状**: "Property 'xxx' does not exist on type"
**原因**: Playwright fixtures类型问题
**解决**: 使用helper function而非base.extend

### 3. 收藏数显示矛盾
**症状**: "4个项目...没有内容"
**原因**: favoriteCount vs cards.length不一致
**解决**: 使用实际渲染数

**详见**: `/Users/kjonekong/.claude/projects/-Users-kjonekong/memory/recurring-issues.md`

---

## 开发工作流

### 前端开发
```bash
cd /Users/kjonekong/Documents/cb-Business/frontend
npm run dev          # 启动开发服务器 (localhost:3000)
npm run build        # 构建生产版本
npm run test:e2e     # 运行E2E测试
```

### 后端开发
```bash
ssh hk-jump                                    # SSH到HK服务器
docker exec -it cb-business-api-fixed bash    # 进入容器
# 或者本地开发:
cd backend && source venv/bin/activate && python main.py
```

### 部署流程
```bash
# 前端: 自动部署
git push origin main  # → Vercel自动部署

# 后端: 手动部署
ssh hk-jump "docker restart cb-business-api-fixed"
```

---

## 环境变量

### 前端 (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://api.zenconsult.top
```

### 后端 (.env)
```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://172.22.0.3:6379
SECRET_KEY=...
OXYLABS_CREDENTIALS=...
AIRWALLEX_API_KEY=...
AIRWALLEX_WEBHOOK_SECRET=...
```

---

## 监控与日志

### 健康检查
```bash
curl https://api.zenconsult.top/health
```

### 容器状态
```bash
ssh hk-jump "docker ps --filter 'network=cb-network'"
```

### 应用日志
```bash
ssh hk-jump "docker logs -f cb-business-api-fixed"
```

### 数据库连接
```bash
ssh hk-jump "docker exec -it cb-business-postgres psql -U cbuser -d cbdb"
```

---

## 相关文档

- **项目进展**: `PROJECT-PROGRESS-2026-03-15.md`
- **E2E测试报告**: `E2E-TEST-REPORT-2026-03-15.md`
- **架构文档**: `/backend/docs/DATA_SOURCE_ARCHITECTURE.md`
- **Memory**: `/Users/kjonekong/.claude/projects/-Users-kjonekong/memory/`

---

**文档结束**
**维护者**: Claude Code
**下次更新**: 架构或部署变更时
