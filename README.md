# 跨境电商智能信息SaaS平台

> **项目名称**: Cross-Border Business (CB)
> **版本**: v1.0
> **创建日期**: 2025-03-10
> **状态**: 开发中

---

## 项目简介

面向国内跨境电商创业者的SaaS平台，帮助他们在东南亚、欧美、拉美市场发现机会、避免踩坑。采用 **Freemium 增长加速器**模式，提供陪伴式成长服务。

### 核心价值

- 🔍 **机会发现**：AI分析市场趋势，推荐高潜力机会
- ⚠️ **风险预警**：实时监控政策变化，提前预警风险
- 📋 **实操指南**：详细操作手册，从0到1上手指南
- 💰 **成本计算**：精确计算产品成本、物流费用、利润

### 商业模式

```
免费探索 → 找到方向 → 深入调研 → 触发付费 → 获得加速 → 实现目标
```

**免费版**：探索所有信息、基础工具
**专业版**（¥99/月）：精确数据分析、供应商数据库、AI分析、专属社群

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    项目经理（主会话）                          │
│  - 整体规划与协调                                            │
│  - 任务分配与进度跟踪                                        │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   会话1       │  │   会话2       │  │   会话3       │
│  前端开发线    │  │  后端开发线    │  │  基础设施线    │
│              │  │              │  │              │
│ - Next.js 15 │  │ - FastAPI    │  │ - PostgreSQL │
│ - shadcn/ui  │  │ - SQLAlchemy │  │ - Redis      │
│ - TypeScript │  │ - JWT Auth   │  │ - Nginx      │
└───────────────┘  └───────────────┘  └───────────────┘
```

### 技术栈

**前端**：
- Next.js 15 (App Router)
- TypeScript 5
- Tailwind CSS 3
- shadcn/ui (Radix UI)
- Recharts

**后端**：
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (异步)
- PostgreSQL + asyncpg
- Redis

**基础设施**：
- Vercel (前端)
- Railway (后端)
- 阿里云杭州 (数据库)
- Nginx (反向代理)

---

## 项目结构

```
/Users/kjonekong/Documents/cb-Business/
├── docs/                       # 文档目录
│   ├── tasks/                  # 任务书（11个）
│   │   ├── TASK-001-frontend-init.md
│   │   ├── TASK-002-backend-init.md
│   │   ├── TASK-003-infrastructure-setup.md
│   │   ├── TASK-004-auth-system.md
│   │   ├── TASK-005-subscription-system.md
│   │   ├── TASK-006-payment-integration.md
│   │   ├── TASK-007-user-frontend-pages.md
│   │   ├── TASK-008-admin-frontend-pages.md
│   │   ├── TASK-009-crawler-service.md
│   │   ├── TASK-010-integration-testing.md
│   │   └── TASK-011-deployment.md
│   ├── api/                    # API文档
│   └── database/               # 数据库文档
│
├── task-templates/             # 任务书模板
│   ├── frontend-task-template.md
│   ├── backend-task-template.md
│   └── infrastructure-task-template.md
│
├── frontend/                   # 用户前端（待创建）
├── admin/                      # 管理后台（待创建）
├── backend/                    # 后端API（待创建）
├── crawler/                    # 爬虫服务（待创建）
│
└── README.md                   # 本文件
```

---

## 任务书使用指南

### 如何启动新开发会话

**步骤1**：在主会话中，项目经理决定启动哪个会话

**步骤2**：打开新的会话，导入任务书

```
请读取并执行任务：
/Users/kjonekong/Documents/cb-Business/docs/tasks/TASK-XXX-任务名称.md
```

**步骤3**：子代理读取任务书后，按照任务书内容自主完成开发

**步骤4**：完成后，向主会话汇报完成情况

### 会话分工

| 会话 | 负责任务 | 主要工作 |
|------|----------|----------|
| **会话1** | 前端开发线 | TASK-001, TASK-007, TASK-008 |
| **会话2** | 后端开发线 | TASK-002, TASK-004, TASK-005, TASK-006, TASK-009, TASK-010 |
| **会话3** | 基础设施线 | TASK-003, TASK-011 |

### 启动顺序

```
Day 1: 会话3（基础设施配置）
   ↓ 完成
Day 2-3: 会话2（后端开发）
   ↓ 完成基础API
Day 4-8: 会话1（前端开发）+ 会话2继续
   ↓ 完成核心功能
Day 9-10: 会话2 + 会话1（集成测试）
   ↓ 测试通过
Day 11-13: 会话3（部署上线）
```

---

## 开发指南

### 本地开发

```bash
# 一键启动所有服务
./dev.sh

# 或分别启动
# Terminal 1: 后端
cd backend && source venv/bin/activate && python main.py

# Terminal 2: 前端
cd frontend && npm run dev

# Terminal 3: 管理后台
cd admin && PORT=3001 npm run dev
```

### 访问地址

- 用户前端：http://localhost:3000
- 管理后台：http://localhost:3001
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
# 后端
cp backend/.env.example backend/.env

# 前端
cp frontend/.env.example frontend/.env.local

# 管理后台
cp admin/.env.example admin/.env.local
```

---

## 重要文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 主计划 | `~/.claude/plans/pure-crunching-lantern.md` | 完整的项目计划 |
| 基础设施 | `~/infrastructure/INFRASTRUCTURE.md` | 现有基础设施信息 |
| 任务书 | `docs/tasks/` | 各任务的详细说明 |

---

## 开发规范

### Git提交

```bash
feat: 新功能
fix: 修复bug
refactor: 重构
test: 测试
docs: 文档
chore: 配置/工具
```

### 分支策略

- `main`: 主分支，生产环境
- `develop`: 开发分支
- `feature/xxx`: 功能分支
- `fix/xxx`: 修复分支

---

## 当前状态

### 已完成

- ✅ 项目结构创建
- ✅ 任务书模板创建
- ✅ 11个任务书创建完成

### 进行中

- ⏳ 等待启动第一个开发会话

### 待开始

所有11个任务待执行。

---

## 快速开始

### 作为开发人员

1. 选择你要执行的任务书
2. 打开新会话，导入任务书
3. 按照任务书执行开发
4. 完成后向主会话汇报

### 作为项目经理

1. 审查主计划文档
2. 决定启动哪个会话
3. 协调各会话进度
4. 处理跨会话问题
5. 更新项目文档

---

## 联系方式

**项目负责人**: [你的名字]
**项目位置**: `/Users/kjonekong/Documents/cb-Business/`
**主计划**: `~/.claude/plans/pure-crunching-lantern.md`

---

## 许可证

Proprietary - All rights reserved

---

*本文档由 Claude Code 项目经理创建和维护*
*最后更新: 2025-03-10*
