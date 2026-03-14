# OpenClaw 备忘录 - cb-Business 项目

> 创建日期: 2026-03-12
> 最后更新: 2026-03-12
> 项目: cb-Business (跨境电商智能信息SaaS平台)

---

## 目录

1. [OpenClaw 是什么](#1-openclaw-是什么)
2. [当前架构状态](#2-当前架构状态)
3. [OpenClaw 在项目中的角色](#3-openclaw-在项目中的角色)
4. [与 OpenClaw 交互的方式](#4-与-openclaw-交互的方式)
5. [Claude Code 协作配置](#5-claude-code-协作配置)
6. [核心应用场景](#6-核心应用场景)
7. [配置文件结构](#7-配置文件结构)
8. [常用命令](#8-常用命令)
9. [实施清单](#9-实施清单)

---

## 1. OpenClaw 是什么

### 定义

**OpenClaw** 是一个 AI 智能体的 WhatsApp/Telegram/Discord/iMessage 网关系统，提供中心化的 Gateway 服务来协调 AI 智能体、渠道和工具。

### 核心特点

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  OpenClaw = AI 智能体协调中台                                               │
│                                                                              │
│  核心组件:                                                                   │
│  ├─ Gateway (端口 18789) - WebSocket 服务器，任务调度中心                   │
│  ├─ Agents - AI 智能体执行任务                                              │
│  ├─ Channels - 通信渠道 (WhatsApp/Telegram/Discord)                          │
│  ├─ Tools - 可执行工具 (浏览器/命令行/文件操作)                              │
│  └─ Workspace - 持久化记忆和配置                                             │
│                                                                              │
│  技术特点:                                                                   │
│  ├─ WebSocket 双向通信 (长连接)                                              │
│  ├─ Token 认证机制                                                           │
│  ├─ Cron/Heartbeat 调度系统                                                 │
│  ├─ Docker 容器化支持                                                        │
│  └─ Node.js 基础架构                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 关键概念对比

| 概念 | 说明 | 配置 |
|------|------|------|
| **Gateway** | 中心服务，Port 18789 | `gateway.mode` (local/remote) |
| **Heartbeat** | 周期性检查 (~30分钟) | `heartbeat.every` (如 "30m") |
| **Cron** | 精确定时任务 | `cron/jobs.json` |
| **Workspace** | 智能体记忆目录 | `~/.openclaw/workspace/` |
| **Channels** | 消息渠道 | `channels.*` 配置 |

---

## 2. 当前架构状态

### 已完成部署

```
HK 服务器 (Docker 环境)
├── OpenClaw Gateway (已部署)
│   └── Port: 18789
│   └── 模式: Remote
│   └── Token 认证: 已启用
│
├── FastAPI 后端 (已迁移)
│   └── Port: 8000
│   └── PostgreSQL 连接: 已配置
│   └── Redis 缓存: 已配置
│
├── PostgreSQL (已迁移)
│   └── Host: 139.224.42.111:5432
│   └── Database: crawler_db
│
└── Redis (已迁移)
    └── Host: 139.224.42.111:6379
```

### Vercel 前端连接

```
Vercel Frontend
    ↓ HTTPS + API Key
HK Server Nginx (Port 443)
    ↓ Reverse Proxy
FastAPI Backend (Port 8000)
    ↓
PostgreSQL / Redis
```

### 架构优势

| 方面 | Railway 方案 | HK + OpenClaw 方案 |
|------|-------------|-------------------|
| 部署稳定性 | ❌ 经常失败 | ✅ 完全控制 |
| 调度可靠性 | ❌ 重启丢失 | ✅ 持久化 |
| 监控能力 | ❌ 基础日志 | ✅ 主动监控+通知 |
| 成本 | $$ | $ |
| 扩展性 | 受限 | 灵活 |

---

## 3. OpenClaw 在项目中的角色

### 3.1 在本次迁移中的角色

```
迁移阶段:
├── 迁移编排协调
│   ├── 监控服务健康状态
│   ├── 验证数据迁移完整性
│   ├── 协调服务切换
│   └── 发送迁移进度通知
│
├── 数据一致性验证
│   ├── 对比迁移前后数据量
│   ├── 验证文章内容完整性
│   └── 生成迁移报告
│
└── 服务监控与告警
    ├── API 服务可用性检查
    ├── 数据库连接监控
    └── 异常时发送通知
```

### 3.2 在网站运行中的角色

```
日常运营:
├── 智能爬虫调度
│   ├── 基于数据质量的动态调整
│   ├── 高优先级内容立即爬取
│   └── 失败重试与告警
│
├── 内容质量监控
│   ├── 检查更新频率
│   ├── 识别低质量源
│   └── 机会分趋势分析
│
├── 用户行为分析
│   ├── 热点内容追踪
│   ├── 用户分群
│   └── 转化漏斗分析
│
├── 付费用户服务
│   ├── 个性化内容推送
│   ├── 每日早报/周报
│   └── 智能客服
│
├── 运营自动化
│   ├── 自动生成报告
│   ├── 用户生命周期管理
│   └── 营销活动推送
│
└── 系统运维
    ├── 健康检查 (每30分钟)
    ├── 性能监控
    ├── 错误追踪
    └── 备份提醒
```

---

## 4. 与 OpenClaw 交互的方式

### 交互方式全景图

```
                    ┌─────────────────────────────┐
                    │       OpenClaw Gateway       │
                    │         (Port 18789)          │
                    └──────────────┬───────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│   命令行 CLI   │        │  Web Dashboard│        │  聊天应用 Bot  │
│               │        │               │        │               │
│ openclaw cmd  │        │ Browser UI    │        │ WhatsApp      │
│               │        │               │        │ Telegram      │
└───────────────┘        └───────────────┘        └───────────────┘
        │                          │                          │
        │                          │                          │
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│   API 调用     │        │  Agent 协议   │        │  脚本自动化   │
│               │        │               │        │               │
│ WebSocket/HTTP│        │ 子智能体协作  │        │ Cron Jobs     │
└───────────────┘        └───────────────┘        └───────────────┘
```

### 4.1 命令行 (CLI)

```bash
# ===== 基础命令 =====
openclaw --help                    # 查看所有命令
openclaw status                    # 查看运行状态
openclaw version                   # 查看版本

# ===== Gateway 管理 =====
openclaw gateway start             # 启动 Gateway
openclaw gateway stop              # 停止 Gateway
openclaw gateway restart           # 重启 Gateway
openclaw gateway status            # 查看状态
openclaw gateway logs              # 查看日志

# ===== 配置管理 =====
openclaw config set <key> <value>  # 设置配置
openclaw config get <key>           # 获取配置
openclaw config list               # 列出所有配置
openclaw config reset              # 重置配置

# ===== 智能体交互 =====
openclaw agent run "指令"          # 运行单次任务
openclaw agent chat                # 进入对话模式
openclaw agent list                # 列出智能体

# ===== 渠道管理 =====
openclaw channels login            # 登录 WhatsApp (扫码)
openclaw channels add --channel telegram --token "xxx"
openclaw channels list             # 查看已连接渠道
openclaw channels remove <id>      # 移除渠道

# ===== 定时任务 =====
openclaw cron list                 # 列出定时任务
openclaw cron add "cron_expr" "task"
openclaw cron remove <id>
openclaw cron enable <id>
openclaw cron disable <id>

# ===== 工具与插件 =====
openclaw tools list                # 列出可用工具
openclaw plugins list              # 列出插件

# ===== 诊断与维护 =====
openclaw doctor                    # 诊断检查
openclaw doctor --generate-gateway-token  # 生成新 Token
openclaw dashboard                 # 打开 Web 控制面板
```

### 4.2 Web Dashboard

```bash
# 启动 Web 控制面板
openclaw dashboard

# 访问: http://127.0.0.1:18789/
```

**Dashboard 功能:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  OpenClaw Web Dashboard                                                     │
│                                                                              │
│  📊 概览                                                                    │
│  ├── Gateway 状态: 🟢 运行中 (运行时间: 2天3小时)                              │
│  ├── 已连接节点: 3                                                          │
│  ├── 活跃任务: 2                                                            │
│  └── 今日消息: 156                                                          │
│                                                                              │
│  🤖 智能体管理                                                               │
│  ├── 主智能体 (main) - [编辑] [重置]                                        │
│  ├── 创建新智能体...                                                         │
│  └── 智能体配置...                                                           │
│                                                                              │
│  📝 定时任务 (Cron)                                                          │
│  ├── daily-report (0 8 * * *) - [启用] [编辑]                                │
│  ├── crawler-monitor (*/30 * * * *) - [启用] [编辑]                           │
│  └── 添加新任务...                                                           │
│                                                                              │
│  📱 渠道管理                                                                 │
│  ├── WhatsApp - 🟢 已连接                                                   │
│  ├── Telegram - 🟢 已连接                                                    │
│  └── 添加渠道...                                                             │
│                                                                              │
│  📋 日志查看                                                                 │
│  └── 实时日志 / 历史日志                                                     │
│                                                                              │
│  ⚙️ 设置                                                                     │
│  ├── Gateway 配置                                                            │
│  ├── 智能体配置                                                              │
│  ├── 工具权限                                                                │
│  └── 安全设置                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 WhatsApp/Telegram Bot

**配置方式:**

```bash
# WhatsApp
openclaw channels login
# 扫码连接

# Telegram
openclaw channels add --channel telegram --token "YOUR_BOT_TOKEN"
```

**交互示例:**

```
用户: 今天有什么重要机会？
─────────────────────────────────────────
OpenClaw: 📊 今日重要机会 (3条)

🔥 亚马逊欧洲站新政策
   机会分: 0.92 | 影响: 高
   摘要: 亚马逊宣布从4月1日起...
   [查看详情]

用户: 帮我查 Shopee 泰国站最新政策
─────────────────────────────────────────
OpenClaw: 🔍 正在搜索...
找到5篇相关文章：
1. Shopee泰国佣金调整 (2026-03-10)
2. 泰国增值税新规...
[需要详细报告吗？]

用户: 生成周报
─────────────────────────────────────────
OpenClaw: 📊 正在生成本周数据报告...
[2分钟后]
报告已生成！查看: https://...
```

### 4.4 API 交互

```bash
# HTTP API
curl http://your-hk-server:18789/health

# WebSocket API
ws://your-hk-server:18789/ws?token=YOUR_TOKEN
```

```javascript
// Node.js 示例
const WebSocket = require('ws');

const ws = new WebSocket('ws://server:18789/ws?token=TOKEN');

ws.on('open', () => {
  ws.send(JSON.stringify({
    type: 'task',
    content: '检查爬虫状态'
  }));
});

ws.on('message', (data) => {
  console.log('响应:', data.toString());
});
```

---

## 5. Claude Code 协作配置

### 协作流程

```
您                    Claude Code              OpenClaw
│                         │                        │
│  "帮我设置监控"         │                        │
│  ────────────────────→ │                        │
│                         │                        │
│                         │  1. Read ~/.openclaw/openclaw.json
│                         │  2. Read ~/.openclaw/workspace/*.md
│                         │                        │
│                         │  3. 分析需求            │
│                         │  4. 生成配置            │
│                         │                        │
│                         │  5. Edit HEARTBEAT.md   │
│                         │  6. Bash: openclaw config set ...
│                         │  7. Bash: openclaw gateway restart
│                         │                        │
│  ←────────────────────  ✅ 配置完成！             │
│                         │                        │
```

### Claude Code 可执行的操作

```bash
# ===== 文件操作 =====
Read: ~/.openclaw/openclaw.json              # 读取配置
Read: ~/.openclaw/workspace/*.md             # 读取工作区
Edit: ~/.openclaw/workspace/HEARTBEAT.md     # 编辑心跳任务
Write: ~/.openclaw/workspace/SOUL.md         # 创建新文件
Edit: ~/.openclaw/cron/jobs.json             # 编辑定时任务

# ===== 命令执行 =====
Bash: openclaw config set <key> <value>      # 设置配置
Bash: openclaw gateway restart               # 重启服务
Bash: openclaw channels list                 # 查看渠道
Bash: openclaw cron list                     # 查看定时任务
Bash: openclaw status                        # 查看状态
Bash: docker compose restart openclaw-gateway # Docker 重启

# ===== 诊断操作 =====
Bash: openclaw doctor                        # 系统诊断
Bash: openclaw logs --follow                 # 查看日志
Bash: curl http://localhost:8000/health      # API 检查
```

### 配置示例请求

```bash
# 您可以对 Claude Code 说:

"检查我当前的 OpenClaw 配置"
"帮我设置爬虫监控"
"设置每天早上8点的数据报告"
"配置 WhatsApp 通知"
"创建一个智能客服"
"设置 heartbeat 每30分钟检查"
"测试 OpenClaw 能否访问数据库"
"查看最近的日志"
```

---

## 6. 核心应用场景

### 6.1 智能爬虫调度

```markdown
场景: 动态调整爬虫频率和优先级

实现方式:
1. Heartbeat 每30分钟检查
2. 查询最新文章时间
3. 如果某源超过6小时未更新 → 主动爬取
4. 发现高机会分文章(>0.8) → 立即推送

配置文件: ~/.openclaw/workspace/HEARTBEAT.md
```

### 6.2 内容质量监控

```markdown
场景: 监控数据源质量

监控指标:
- 更新频率
- 文章数量
- 机会分分布
- 内容重复率

异常处理:
- 质量下降 → 重新爬取
- 连续失败 → 发送告警
- 新源发现 → 自动添加
```

### 6.3 用户行为分析

```markdown
场景: 分析用户行为，优化内容

分析内容:
- 热点文章追踪
- 用户兴趣分群
- 转化漏斗分析
- 内容缺口识别

输出:
- 每日热点报告
- 用户画像更新
- 内容策略建议
```

### 6.4 付费用户服务

```markdown
场景: 为付费用户提供个性化服务

服务内容:
1. 每日早报 (早上8点)
   - 高机会分文章
   - 个性化推荐
   - 行动建议

2. 实时推送
   - 政策变化通知
   - 高风险预警
   - 机会提醒

3. 智能客服
   - 回答业务问题
   - 查询相关文章
   - 提供操作指南

4. 专属报告
   - 周报/月报
   - 数据分析
   - 趋势预测
```

### 6.5 数据洞察与报告

```markdown
自动生成报告类型:

1. 每日数据早报 (8:00)
   - 新增文章数
   - 高机会文章
   - 风险预警
   - 热门主题

2. 每周深度分析
   - 机会趋势图
   - 竞争格局变化
   - 用户增长分析
   - 内容质量评估

3. 每月战略报告
   - 市场机会预测
   - 竞品动态跟踪
   - 产品迭代建议
   - 商业策略调整
```

### 6.6 运营自动化

```markdown
自动化任务:

内容运营:
✅ 自动识别高价值内容 → 推送至首页
✅ 检测重复内容 → 自动去重
✅ 热点话题聚合 → 生成专题页

用户运营:
✅ 新用户欢迎消息
✅ 试用期到期提醒
✅ 付费续费提醒
✅ 长时间未登录唤醒

系统运维:
✅ 数据库连接池监控
✅ Redis 缓存命中率检查
✅ API 响应时间追踪
✅ 错误日志聚合分析
```

### 6.7 网站外的其他功能

```markdown
个人生产力:
├── 日程管理 (自动创建日历事件)
├── 任务管理 (待办事项跟踪)
├── 笔记管理 (自动分类归档)
└── 报告生成 (工作总结)

消息管理:
├── 多渠道统一 (WhatsApp/Telegram/Email)
├── 智能路由 (工作/私人分类)
├── 自动回复 (忙碌模式)
└── 消息聚合 (每日汇总)

研究助手:
├── 市场研究 (自动搜索整理)
├── 竞品分析 (对比分析报告)
├── 文献综述 (资料整理)
└── 数据收集 (自动爬取)

自动化工作流:
├── 财务自动化 (汇率/手续费追踪)
├── 社交媒体 (内容发布/统计)
├── 供应商管理 (信息收集/对比)
└── 数据监控 (价格/排名/异常)
```

---

## 7. 配置文件结构

### 目录结构

```
~/.openclaw/
├── openclaw.json              # 主配置文件
├── openclaw.json.bak          # 配置备份
│
├── workspace/                 # 智能体工作区
│   ├── AGENTS.md              # 智能体角色定义
│   ├── SOUL.md                # 个性与价值观
│   ├── TOOLS.md               # 可用工具说明
│   ├── IDENTITY.md            # 身份标识
│   ├── USER.md                # 用户偏好
│   ├── HEARTBEAT.md           # 定期任务清单 ⭐
│   ├── MEMORY.md              # 长期记忆（精选）
│   │
│   └── memory/                # 日常记忆
│       ├── 2026-03-01.md
│       ├── 2026-03-02.md
│       └── ...
│
├── cron/                      # 定时任务
│   └── jobs.json              # Cron 任务配置
│
├── agents/                    # 智能体数据
│   └── <agent-id>/
│       └── sessions/
│
├── channels/                  # 渠道配置
│
├── logs/                      # 日志文件
│
└── devices.json               # 设备管理
```

### 关键配置文件

#### openclaw.json

```json
{
  "gateway": {
    "mode": "remote",              // local | remote
    "port": 18789,
    "host": "0.0.0.0",             // remote 模式
    "token": "ogt_xxx..."          // 访问令牌
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "heartbeat": {
        "every": "30m"             // 心跳间隔
      },
      "maxConcurrent": 4
    }
  },
  "channels": {
    "whatsapp": {
      "allowFrom": ["+86xxx"]      // 允许的号码
    },
    "telegram": {
      "token": "bot_token"
    }
  }
}
```

#### HEARTBEAT.md (心跳任务)

```markdown
# 定期检查任务

每30分钟执行:

1. 检查爬虫服务健康
   - curl http://localhost:8000/health
   - 检查响应时间

2. 检查数据库
   - 最新文章时间
   - 今日新增数量
   - 高机会分文章数

3. 检查异常
   - API 连接失败
   - 超过2小时无新数据
   - 数据库连接问题

4. 发送通知
   - 如有异常，通过 WhatsApp/Telegram 通知

如果一切正常: HEARTBEAT_OK
```

#### SOUL.md (智能体身份)

```markdown
# CB-Business 智能客服

你是 CB-Business 的跨境电商专家助手。

你的职责:
- 回答关于跨境电商的问题
- 查询数据库中的文章
- 提供开店指南、政策解读、风险预警
- 推荐相关文章

回答风格:
- 专业、友好、简洁
- 使用 emoji 让回答更生动
- 总是提供行动建议

不做的:
- 不编造信息
- 不透露敏感数据
- 不执行危险操作
```

#### cron/jobs.json (定时任务)

```json
{
  "jobs": [
    {
      "id": "daily-report",
      "name": "每日数据报告",
      "schedule": "0 8 * * *",
      "enabled": true,
      "action": "generate_report",
      "channel": "telegram"
    },
    {
      "id": "weekly-report",
      "name": "每周数据分析",
      "schedule": "0 9 * * 1",
      "enabled": true,
      "action": "generate_weekly_report"
    }
  ]
}
```

---

## 8. 常用命令

### 日常运维

```bash
# ===== 检查状态 =====
openclaw status                    # 整体状态
openclaw gateway status            # Gateway 状态
openclaw channels list             # 渠道状态
openclaw cron list                 # 定时任务

# ===== 查看日志 =====
openclaw gateway logs              # Gateway 日志
openclaw logs --follow             # 实时日志
tail -f ~/.openclaw/logs/gateway.log  # 日志文件

# ===== 重启服务 =====
openclaw gateway restart           # 重启 Gateway
docker compose restart openclaw-gateway  # Docker 重启

# ===== 配置管理 =====
openclaw config set gateway.mode remote
openclaw config get gateway.token
openclaw config list

# ===== Token 管理 =====
openclaw doctor --generate-gateway-token  # 生成新 Token
openclaw doctor --generate-gateway-token --force  # 强制更新

# ===== 诊断检查 =====
openclaw doctor                    # 完整诊断
openclaw gateway health            # 健康检查
curl http://localhost:8000/health  # API 检查
```

### 测试命令

```bash
# ===== 测试智能体 =====
openclaw agent run "检查爬虫状态"
openclaw agent run "查询今日新增文章"
openclaw agent chat                # 对话模式

# ===== 测试 API =====
curl http://localhost:18789/health
curl -H "X-API-KEY: xxx" http://localhost:8000/api/v1/articles

# ===== 测试数据库 =====
docker exec -it postgres psql -U user -d crawler_db
SELECT COUNT(*) FROM articles;
SELECT MAX(created_at) FROM articles;
```

---

## 9. 实施清单

### 第一阶段: 基础配置 ✅ (已完成)

- [x] OpenClaw Gateway 部署
- [x] FastAPI 后端迁移
- [x] PostgreSQL 数据库迁移
- [x] Redis 缓存迁移

### 第二阶段: 监控设置 (待实施)

```bash
# 可以让 Claude Code 帮忙执行:

# 1. 配置 Heartbeat 监控
"帮我编辑 ~/.openclaw/workspace/HEARTBEAT.md，添加爬虫监控任务"

# 2. 设置心跳间隔
"执行: openclaw config set agents.defaults.heartbeat.every 30m"

# 3. 配置通知渠道
"帮我配置 WhatsApp 通知"
"或者配置 Telegram Bot"

# 4. 测试监控
"测试 heartbeat 是否正常工作"
```

### 第三阶段: 报告自动化 (待实施)

```bash
# 让 Claude Code 帮忙:

# 1. 创建每日报告任务
"创建 cron 任务：每天早上8点生成数据报告"

# 2. 创建报告模板
"创建报告模板 ~/.openclaw/workspace/templates/daily-report.md"

# 3. 测试报告生成
"测试生成一份报告"

# 4. 配置发送渠道
"配置报告发送到 Telegram"
```

### 第四阶段: 智能客服 (待实施)

```bash
# 让 Claude Code 帮忙:

# 1. 配置智能体身份
"编辑 ~/.openclaw/workspace/SOUL.md，设置跨境电商专家身份"

# 2. 配置响应规则
"创建响应规则文件"

# 3. 配置工具权限
"允许智能体访问数据库"

# 4. 测试问答
"测试客服问答功能"
```

### 第五阶段: 高级功能 (待实施)

```bash
# 让 Claude Code 帮忙:

# 1. 用户行为分析
"创建用户行为分析任务"

# 2. 内容质量监控
"设置内容质量检查"

# 3. 自动化工作流
"创建自动化任务脚本"

# 4. 数据备份提醒
"设置每周备份提醒"
```

---

## 快速参考

### 常见问题

**Q: 如何查看 OpenClaw 是否在运行？**
```bash
openclaw status
# 或
openclaw gateway status
```

**Q: 如何重启 OpenClaw？**
```bash
openclaw gateway restart
# Docker 环境
docker compose restart openclaw-gateway
```

**Q: 如何添加 WhatsApp 渠道？**
```bash
openclaw channels login
# 用 WhatsApp 扫描二维码
```

**Q: 如何查看日志？**
```bash
openclaw logs --follow
# 或
tail -f ~/.openclaw/logs/gateway.log
```

**Q: 如何让 Claude Code 帮忙配置？**
直接说: "帮我设置 XXX" 或 "检查我的 OpenClaw 配置"

### 配置文件快速定位

```
配置文件: ~/.openclaw/openclaw.json
心跳任务: ~/.openclaw/workspace/HEARTBEAT.md
智能体身份: ~/.openclaw/workspace/SOUL.md
定时任务: ~/.openclaw/cron/jobs.json
日志文件: ~/.openclaw/logs/
```

---

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-03-12 | 初始版本，包含架构、配置、使用说明 |

---

## 备注

- OpenClaw Gateway 默认端口: 18789
- FastAPI 后端端口: 8000
- PostgreSQL: 139.224.42.111:5432
- Redis: 139.224.42.111:6379
- Token 务必保管好，定期更换 (建议每90天)

---

*本文档由 Claude Code 辅助创建*
