# 任务书索引

> **最后更新**: 2025-03-10
> **状态**: 所有任务书已创建完成

---

## 快速导航

### 按会话分类

#### 会话1：前端开发线

| 任务ID | 任务名称 | 工期 | 状态 | 任务书 |
|--------|----------|------|------|--------|
| TASK-001 | 前端项目初始化 | 1天 | ⏳ 待开始 | [TASK-001-frontend-init.md](TASK-001-frontend-init.md) |
| TASK-007 | 用户前端核心页面 | 5天 | ⏳ 待开始 | [TASK-007-user-frontend-pages.md](TASK-007-user-frontend-pages.md) |
| TASK-008 | 管理后台核心页面 | 4天 | ⏳ 待开始 | [TASK-008-admin-frontend-pages.md](TASK-008-admin-frontend-pages.md) |

#### 会话2：后端开发线

| 任务ID | 任务名称 | 工期 | 状态 | 任务书 |
|--------|----------|------|------|--------|
| TASK-002 | 后端项目初始化 | 1天 | ⏳ 待开始 | [TASK-002-backend-init.md](TASK-002-backend-init.md) |
| TASK-004 | 认证系统实现 | 2天 | ⏳ 待开始 | [TASK-004-auth-system.md](TASK-004-auth-system.md) |
| TASK-005 | 订阅管理系统 | 3天 | ⏳ 待开始 | [TASK-005-subscription-system.md](TASK-005-subscription-system.md) |
| TASK-006 | 支付集成实现 | 3天 | ⏳ 待开始 | [TASK-006-payment-integration.md](TASK-006-payment-integration.md) |
| TASK-009 | 爬虫服务实现 | 4天 | ⏳ 待开始 | [TASK-009-crawler-service.md](TASK-009-crawler-service.md) |
| TASK-010 | 集成测试 | 2天 | ⏳ 待开始 | [TASK-010-integration-testing.md](TASK-010-integration-testing.md) |

#### 会话3：基础设施线

| 任务ID | 任务名称 | 工期 | 状态 | 任务书 |
|--------|----------|------|------|--------|
| TASK-003 | 基础设施配置 | 2天 | ⏳ 待开始 | [TASK-003-infrastructure-setup.md](TASK-003-infrastructure-setup.md) |
| TASK-011 | 部署上线 | 3天 | ⏳ 待开始 | [TASK-011-deployment.md](TASK-011-deployment.md) |

---

## 按依赖关系

```
TASK-003（基础设施配置）
    ↓
TASK-002（后端初始化） ← TASK-001（前端初始化）
    ↓                      ↓
TASK-004（认证系统）──────→ TASK-007（前端页面）
    ↓                      ↓
TASK-005（订阅管理）──────→ TASK-008（管理后台）
    ↓
TASK-006（支付集成）
    ↓
TASK-009（爬虫服务）
    ↓
TASK-010（集成测试）
    ↓
TASK-011（部署上线）
```

---

## 任务书模板

| 类型 | 模板文件 |
|------|----------|
| 前端任务 | [frontend-task-template.md](../task-templates/frontend-task-template.md) |
| 后端任务 | [backend-task-template.md](../task-templates/backend-task-template.md) |
| 基础设施任务 | [infrastructure-task-template.md](../task-templates/infrastructure-task-template.md) |

---

## 如何使用任务书

### 在新会话中导入任务

1. 打开新的会话
2. 直接输入：

```
请读取并执行任务：
/Users/kjonekong/Documents/cb-Business/docs/tasks/TASK-XXX-任务名称.md
```

3. 子代理会自动读取任务书并开始执行

### 汇报完成情况

任务完成后，在主会话中汇报：

- ✅ 完成的内容
- ⚠️ 遇到的问题
- 📋 需要协调的事项

---

## 进度追踪

| 里程碑 | 目标日期 | 状态 |
|--------|----------|------|
| M1: 基础设施就绪 | Day 5 | ⏳ 待开始 |
| M2: 后端API可用 | Day 10 | ⏳ 待开始 |
| M3: 前端MVP完成 | Day 15 | ⏳ 待开始 |
| M4: 支付集成完成 | Day 20 | ⏳ 待开始 |
| M5: 部署上线 | Day 25 | ⏳ 待开始 |

---

*本文档由主会话（项目经理）维护*
