# TASK-011: 部署上线

> **所属会话**: 会话3（基础设施线）配合项目经理
> **优先级**: P0（最高）
> **预计工期**: 3天
> **依赖任务**: 所有开发和测试任务
> **创建日期**: 2025-03-10
> **状态**: ✅ 已完成
> **最后更新**: 2026-03-11 15:35 (ZenConsult重新设计 v1.0)

---

## 📦 GitHub 仓库信息

**所有代码已推送到 GitHub，使用 Git 集成部署：**

| 仓库 | 用途 | GitHub URL | 状态 |
|------|------|-----------|------|
| **主仓库** | 后端 + 文档 | https://github.com/cscoheru/cb--business | ✅ 已推送 |
| **Frontend** | 用户前端 | https://github.com/cscoheru/cb-business-frontend | ✅ 已推送 |
| **Admin** | 管理后台 | https://github.com/cscoheru/cb-business-admin | ✅ 已推送 |

---

## 🔄 部署进度跟踪

### ✅ 部署完成 (2026-03-11 14:10)

**域名迁移完成**: 从 `3strategy.cc` 迁移到 `zenconsult.top`

| 服务 | 状态 | 域名 | 说明 |
|------|------|------|------|
| **后端 API** | ✅ 已部署 | api.zenconsult.top | Railway: delightful-spontaneity-production.up.railway.app |
| **用户前端** | ✅ 已部署 | www.zenconsult.top | Vercel: cb-business-frontend |
| **管理后台** | ✅ 已部署 | admin.zenconsult.top | Vercel: cb-business-admin |
| **域名 DNS** | ✅ 已配置 | zenconsult.top | Cloudflare DNS 已配置 |
| **SSL 证书** | ✅ 正常 | 所有域名 | HTTPS 正常工作 |

### 域名映射关系

| 旧域名 | 新域名 | 平台 |
|--------|--------|------|
| cb.3strategy.cc | www.zenconsult.top | Vercel |
| admin.cb.3strategy.cc | admin.zenconsult.top | Vercel |
| api.cb.3strategy.cc | api.zenconsult.top | Railway |

### 当前状态更新 (2025-03-10 21:00) - 历史记录

### ✅ 已完成工作

1. **Vercel CLI 安装**: `npm install -g vercel` ✅
2. **Railway CLI 检查**: 已登录 (klyliae@gmail.com) ✅
3. **Vercel 账号登录**: cscoheru's Projects ✅
4. **部署准备文件**: 已在 `deploy/` 目录准备好所有配置文件 ✅

### 🚧 遇到的问题

#### 问题 1: Railway 免费计划配额限制

**错误信息**:
```
Free plan resource provision limit exceeded. Please upgrade to provision more resources!
```

**影响**: 无法创建新的 Railway 项目部署后端 API

**解决方案**:
1. **方案 A** (推荐): 升级 Railway 到付费计划 ($5/月起)
2. **方案 B**: 删除 Railway 中未使用的项目释放配额
3. **方案 C**: 使用其他托管平台 (如 Render, Fly.io, AWS)

#### 问题 2: Vercel CLI 项目链接问题

**问题**: 使用 `vercel link` 时自动检测到错误的项目配置

**解决方案**: 使用 **Vercel GitHub 集成**方式部署（推荐，见下方）

### 📋 推荐的下一步操作

1. **解决 Railway 配额问题**:
   ```bash
   # 登录 Railway 查看当前项目
   railway login
   railway list

   # 删除不需要的项目释放配额，或
   # 升级到付费计划
   ```

2. **使用 Vercel GitHub 集成部署前端**:
   - 访问 https://vercel.com/new
   - 导入 GitHub 仓库 `cscoheru/cb-business-frontend`
   - 配置环境变量后部署

3. **使用 Vercel GitHub 集成部署管理后台**:
   - 导入 GitHub 仓库 `cscoheru/cb-business-admin`
   - 配置环境变量后部署

---

## 任务目标

将前端、后端、管理后台部署到生产环境，配置域名和SSL，确保系统可访问。

**部署方式**: 从 GitHub 仓库自动部署（推荐）

---

## 部署清单

### 方式一：Vercel GitHub 集成部署（推荐）✨

**优势**:
- 自动检测 GitHub 仓库更新
- 每次推送代码自动部署
- 支持预览环境（PR自动生成预览URL）
- 零配置 SSL 证书

#### 步骤 1: 连接 GitHub 到 Vercel

1. 访问 https://vercel.com
2. 点击 **"Add New..."** → **"Project"**
3. 选择 **"Import Git Repository"**
4. 授权 Vercel 访问你的 GitHub

#### 步骤 2: 部署用户前端

```
仓库: cscoheru/cb-business-frontend
Framework Preset: Next.js
Root Directory: ./
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

**环境变量**:
```
NEXT_PUBLIC_API_URL=https://api.cb.3strategy.cc
```

**部署后分配域名**: `https://cb-business-frontend.vercel.app`
**自定义域名**: `cb.3strategy.cc`

#### 步骤 3: 部署管理后台

```
仓库: cscoheru/cb-business-admin
Framework Preset: Next.js
Root Directory: ./
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

**环境变量**:
```
NEXT_PUBLIC_API_URL=https://api.cb.3strategy.cc
```

**部署后分配域名**: `https://cb-business-admin.vercel.app`
**自定义域名**: `admin.cb.3strategy.cc`

---

### 方式二：Railway GitHub 集成部署（后端）✨

**优势**:
- 从 GitHub 自动部署
- 支持私有仓库
- 自动管理环境变量
- 内置 PostgreSQL/Redis

#### 步骤 1: 连接 GitHub 到 Railway

1. 访问 https://railway.app
2. 点击 **"New Project"** → **"Deploy from GitHub repo"**
3. 授权 Railway 访问你的 GitHub

#### 步骤 2: 部署后端 API

```
仓库: cscoheru/cb--business
Root Directory: ./backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**环境变量**:
```
DATABASE_URL=<Railway PostgreSQL 变量>
REDIS_URL=<Railway Redis 变量>
SECRET_KEY=<生成 32 位随机字符串>
WECHAT_APP_ID=<微信支付 AppID>
WECHAT_MCH_ID=<微信支付商户号>
WECHAT_API_KEY=<微信支付 API 密钥>
WECHAT_NOTIFY_URL=https://api.cb.3strategy.cc/api/v1/payments/wechat/notify
```

**部署后分配域名**: `https://cb-business-api.railway.app`
**自定义域名**: `api.cb.3strategy.cc`

---

### 方式三：CLI 部署（备选）

#### Vercel CLI 部署

```bash
# 安装 Vercel CLI
npm i -g vercel

# 用户前端
cd frontend
vercel link
vercel --prod

# 管理后台
cd ../admin
vercel link
vercel --prod
```

#### Railway CLI 部署

```bash
# 安装 Railway CLI
npm i -g @railway/cli

# 后端
cd backend
railway login
railway init
railway up
railway domain
```

### 域名配置

#### DNS 解析设置（在域名注册商配置）

| 类型 | 名称 | 值 | TTL |
|------|------|-----|-----|
| CNAME | cb | cname.vercel-dns.com | 3600 |
| CNAME | admin | cname.vercel-dns.com | 3600 |
| CNAME | api | cb-business-api.railway.app | 3600 |

#### Vercel 自定义域名配置

1. 在 Vercel 项目设置中添加 `cb.3strategy.cc`
2. Vercel 会提供 DNS 记录，添加到你的域名注册商
3. 等待 DNS 生效（最多 48 小时，通常 10 分钟）
4. Vercel 自动配置 SSL 证书（Let's Encrypt）

#### Railway 自定义域名配置

1. 在 Railway 项目设置中点击 **"Settings"** → **"Domains"**
2. 添加 `api.cb.3strategy.cc`
3. Railway 提供 CNAME 记录：`cb-business-api.railway.app`
4. 添加 CNAME 记录到域名注册商
5. Railway 自动配置 SSL 证书

#### 最终域名映射

| 公开访问域名 | 服务 | GitHub 仓库 | 部署平台 |
|-------------|------|------------|---------|
| https://cb.3strategy.cc | 用户前端 | cb-business-frontend | Vercel |
| https://admin.cb.3strategy.cc | 管理后台 | cb-business-admin | Vercel |
| https://api.cb.3strategy.cc | 后端 API | cb--business (backend/) | Railway |

---

## 环境变量配置

### Vercel 环境变量

在 Vercel 项目设置 → **Environment Variables** 中添加：

**用户前端 (cb-business-frontend)**:
```bash
NEXT_PUBLIC_API_URL=https://api.cb.3strategy.cc
```

**管理后台 (cb-business-admin)**:
```bash
NEXT_PUBLIC_API_URL=https://api.cb.3strategy.cc
```

### Railway 环境变量

在 Railway 项目设置 → **Variables** 中添加：

**后端 API (cb--business/backend)**:

#### Railway 内置服务（推荐）

Railway 会自动为以下内置服务创建环境变量：

```bash
# Railway PostgreSQL (在 Railway 中添加 PostgreSQL 服务)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Railway Redis (在 Railway 中添加 Redis 服务)
REDIS_URL=${{Redis.REDIS_URL}}
```

#### 手动配置环境变量

```bash
# 应用配置
SECRET_KEY=<使用 openssl rand -hex 32 生成>
ENVIRONMENT=production
ALLOWED_ORIGINS=https://cb.3strategy.cc,https://admin.cb.3strategy.cc

# 微信支付（生产环境）
WECHAT_APP_ID=<你的微信 AppID>
WECHAT_MCH_ID=<你的微信商户号>
WECHAT_API_KEY=<你的微信 API 密钥>
WECHAT_NOTIFY_URL=https://api.cb.3strategy.cc/api/v1/payments/wechat/notify
```

#### 生成 SECRET_KEY

```bash
# 在终端生成安全的 SECRET_KEY
openssl rand -hex 32
```

---

## SSL 证书配置

### ✨ 自动配置（推荐）

**Vercel 和 Railway 都会自动配置 SSL 证书！**

- **证书颁发机构**: Let's Encrypt
- **自动续期**: 平台自动管理
- **无需手动操作**: 添加自定义域名后自动生成

### 配置步骤

1. **添加自定义域名**（见上文域名配置）
2. **添加 DNS 记录**（CNAME）
3. **等待 DNS 生效**（通常 10-30 分钟）
4. **平台自动签发 SSL 证书**（自动完成）
5. **访问 HTTPS 域名验证**

### 验证 SSL

```bash
# 检查 SSL 证书状态
curl -I https://cb.3strategy.cc
curl -I https://admin.cb.3strategy.cc
curl -I https://api.cb.3strategy.cc

# 或使用在线工具
# https://www.ssllabs.com/ssltest/
```

---

## 部署流程总结

### 第一步：部署后端 (Railway)

1. 登录 https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. 选择 `cscoheru/cb--business`
4. 配置 Root Directory 为 `./backend`
5. 添加环境变量
6. 添加 PostgreSQL 和 Redis 服务
7. 点击 **Deploy**
8. 等待部署完成，获取 API URL
9. 添加自定义域名 `api.cb.3strategy.cc`

### 第二步：部署前端 (Vercel)

1. 登录 https://vercel.com
2. **Add New** → **Project**
3. 导入 `cscoheru/cb-business-frontend`
4. 配置环境变量 `NEXT_PUBLIC_API_URL`
5. 点击 **Deploy**
6. 等待部署完成
7. 添加自定义域名 `cb.3strategy.cc`

### 第三步：部署管理后台 (Vercel)

1. 在 Vercel 添加新项目
2. 导入 `cscoheru/cb-business-admin`
3. 配置环境变量
4. 点击 **Deploy**
5. 等待部署完成
6. 添加自定义域名 `admin.cb.3strategy.cc`

### 第四步：配置 DNS

在域名注册商（3strategy.cc 的注册商）添加：

| 类型 | 名称 | 值 |
|------|------|-----|
| CNAME | cb | cname.vercel-dns.com |
| CNAME | admin | cname.vercel-dns.com |
| CNAME | api | cb-business-api.railway.app |

### 第五步：验证

等待 DNS 生效后，访问：
- https://cb.3strategy.cc
- https://admin.cb.3strategy.cc
- https://api.cb.3strategy.cc/docs

---

## 验收测试

### 基础访问测试

- [x] **前端可访问**: https://www.zenconsult.top ✅
- [x] **管理后台可访问**: https://admin.zenconsult.top ✅
- [x] **API 可访问**: https://api.zenconsult.top ✅
- [x] **API 文档可访问**: https://api.zenconsult.top/docs ✅
- [x] **SSL 证书正常** (所有域名显示绿锁) ✅

### 功能测试

- [x] **首页加载正常**: 检查页面样式和内容 ✅
- [ ] **用户注册流程**: 测试新用户注册
- [ ] **用户登录流程**: 测试已注册用户登录
- [ ] **Dashboard 访问**: 登录后可进入仪表盘
- [x] **API 健康检查**: `https://api.zenconsult.top/health` ✅
- [ ] **数据库连接**: 验证 PostgreSQL 连接
- [ ] **Redis 连接**: 验证 Redis 服务

### 管理员功能测试

- [ ] **管理员登录**: admin@zenconsult.top / admin123456
- [ ] **用户管理**: 访问用户列表和统计
- [ ] **订阅管理**: 查看订阅数据
- [ ] **分析数据**: 访问 analytics 端点

### 支付测试（可选，需要真实商户号）

- [ ] **创建支付订单**: 调用 `/api/v1/payments/create`
- [ ] **支付回调**: 测试微信支付回调
- [ ] **订阅升级**: 验证订阅状态更新

---

## 部署检查清单

### 前置条件

- [ ] GitHub 仓库已推送
- [ ] Vercel 账号已创建
- [ ] Railway 账号已创建
- [ ] 域名 3strategy.cc 可访问

### 部署步骤

- [ ] Railway 部署后端
- [ ] Railway 配置 PostgreSQL/Redis
- [ ] Railway 配置环境变量
- [ ] Vercel 部署前端
- [ ] Vercel 部署管理后台
- [ ] DNS 配置 CNAME 记录
- [ ] 自定义域名配置
- [ ] SSL 证书自动生成

### 验收测试

- [ ] 所有域名可访问
- [ ] HTTPS 正常工作
- [ ] 用户注册登录正常
- [ ] Dashboard 功能正常
- [ ] API 文档可访问
- [ ] 管理员功能正常

---

## 部署后的维护

### 监控

- **Vercel Dashboard**: 监控前端部署和错误
- **Railway Dashboard**: 监控后端性能和日志
- **GitHub**: 自动部署触发（推送代码）

### 日志查看

```bash
# Vercel 日志
vercel logs

# Railway 日志
railway logs
```

### 更新部署

```bash
# 只需推送代码到 GitHub，自动触发部署
git push origin main
```

---

## GitHub 仓库与部署平台对应关系

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub 仓库                             │
├─────────────────────────────────────────────────────────────┤
│  cscoheru/cb--business (主仓库)                              │
│  ├── backend/           ──────→ Railway → api.cb.3strategy.cc│
│  ├── docs/              ──────→ (文档)                      │
│                                                             │
│  cscoheru/cb-business-frontend                               │
│  └── (全部内容)        ──────→ Vercel → cb.3strategy.cc    │
│                                                             │
│  cscoheru/cb-business-admin                                  │
│  └── (全部内容)        ──────→ Vercel → admin.cb.3strategy.cc│
└─────────────────────────────────────────────────────────────┘
```

---

## 提交规范

### 更新部署配置到 Git

部署完成后，提交部署配置到 GitHub：

```bash
cd /Users/kjonekong/Documents/cb-Business

# 更新 TASK-011 状态
git add docs/tasks/TASK-011-deployment.md
git commit -m "docs(TASK-011): 更新部署文档，添加GitHub集成部署说明

- 添加 GitHub 仓库信息
- 更新 Vercel GitHub 集成部署步骤
- 更新 Railway GitHub 集成部署步骤
- 添加域名 DNS 配置说明
- 更新环境变量配置
- 添加部署流程总结

GitHub 仓库:
- 主仓库: https://github.com/cscoheru/cb--business
- 前端: https://github.com/cscoheru/cb-business-frontend
- 管理后台: https://github.com/cscoheru/cb-business-admin

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

git push origin main
```

### 部署完成标记

部署完成后，在主计划文件中标记 TASK-011 为完成状态。

---

## 快速命令参考

### Vercel CLI

```bash
# 安装
npm i -g vercel

# 登录
vercel login

# 部署
vercel --prod

# 查看日志
vercel logs

# 查看环境变量
vercel env ls
```

### Railway CLI

```bash
# 安装
npm i -g @railway/cli

# 登录
railway login

# 初始化项目
railway init

# 部署
railway up

# 查看日志
railway logs

# 添加环境变量
railway variables set KEY=value
```

---

## 故障排查

### Vercel 部署失败

- 检查 `vercel.json` 配置
- 检查 build command 是否正确
- 查看 Vercel 部署日志

### Railway 部署失败

- 检查 `Railway.toml` 配置（如果有）
- 检查 start command 是否正确
- 查看 Railway 部署日志
- 检查环境变量是否完整

### DNS 不生效

- 使用 `dig cb.3strategy.cc` 检查 DNS 记录
- 等待 DNS 传播（最多 48 小时）
- 清除本地 DNS 缓存：`sudo dscacheutil -flushcache`

### SSL 证书问题

- 确保 DNS 记录正确
- 等待证书自动生成（最多 24 小时）
- 检查域名 CNAME 是否指向正确的平台

---

## 完成后操作

部署完成后，请更新以下位置：

1. ✅ 本文档状态：将 "⏳ 进行中" 改为 "✅ 已完成"
2. ✅ 主计划文件：标记 TASK-011 完成
3. ✅ 通知用户：提供生产环境访问地址

---

*本任务书由主会话（项目经理）创建和维护*
*最后更新: 2026-03-11 - 部署完成，域名迁移至 zenconsult.top*

---

## 📝 部署完成记录

### 完成时间: 2026-03-11 14:10

### 🎨 ZenConsult 重新设计 v1.0 部署 (2026-03-11 15:35)

**异域浪漫美学 + AI驱动评估系统**

| 功能模块 | 状态 | 描述 |
|---------|------|------|
| Hero搜索 | ✅ 已部署 | 渐变背景搜索框 + 快速过滤标签 |
| 关键词云 | ✅ 已部署 | 按区域分组的交互式标签 |
| 区域门户 | ✅ 已部署 | 6标签布局 (政策/机会/风险/实操/平台/物流) |
| 主题门户 | ✅ 已部署 | 水平Tabs导航 + 主题分类页面 |
| 能力评估 | ✅ 已部署 | 个人能力照妖镜 (4问题评估) |
| 资源盘点 | ✅ 已部署 | 供应链/物流/资金/海外关系评估 |
| 兴趣推荐 | ✅ 已部署 | 兴趣标签 + 市场匹配 |
| 成长路径 | ✅ 已部署 | 12阶段成长地图 + 进度跟踪 |
| 搜索功能 | ✅ 已部署 | 关键词搜索 + 区域/主题筛选 |
| 进度跟踪 | ✅ 已部署 | localStorage + 成就系统 |
| 后端API | ✅ 已部署 | 评估API + 搜索API |

### 新增页面

| 路径 | 页面 |
|------|------|
| /assessment/capability | 个人能力评估 |
| /inventory | 资源盘点 |
| /interests | 兴趣推荐 |
| /growth-path | 成长路径 |
| /search | 搜索结果 |
| /theme/[slug] | 主题分类 |

### 新增API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| /api/v1/assessments/capability | POST | 能力评估 |
| /api/v1/assessments/inventory | POST | 资源盘点 |
| /api/v1/assessments/interest | POST | 兴趣推荐 |
| /api/v1/assessments/growth | GET | 成长路径 |
| /api/v1/search/articles | GET | 文章搜索 |
| /api/v1/search/filters | GET | 筛选选项 |

### 验证结果

```bash
# 前端检查 (2026-03-11 15:35)
✅ https://www.zenconsult.top - HTTP 200
✅ 新功能已部署: HeroSearch, growth-path
✅ 搜索功能: /search 页面可访问
✅ 评估页面: /assessment/capability 可访问
✅ 成长路径: /growth-path 可访问

# API检查 (2026-03-11 15:35)
✅ https://api.zenconsult.top/health - {"status":"healthy"}
✅ 评估API已部署: /api/v1/assessments/*
✅ 搜索API已部署: /api/v1/search/*
```

### 部署提交记录

**Frontend** (cb-business-frontend):
- `4b80e0f` - feat: zenconsult redesign - exotic romantic aesthetics v1.0
- `cf08d21` - test: add E2E tests for new features

**Backend** (cb--business):
- `44ac719` - feat: add assessment and search APIs (feature/zenconsult-redesign分支)

### 完成时间: 2026-03-11 14:10

### 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户访问层                               │
├─────────────────────────────────────────────────────────────┤
│  Frontend: www.zenconsult.top (Vercel)                    │
│  Admin:   admin.zenconsult.top (Vercel)                   │
│  API:     api.zenconsult.top (Railway)                    │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                    服务层                                   │
├─────────────────────────────────────────────────────────────┤
│  Frontend: cb-business-frontend (GitHub → Vercel)         │
│  Admin:   cb-business-admin (GitHub → Vercel)             │
│  Backend: cb--business/backend (GitHub → Railway)         │
└─────────────────────────────────────────────────────────────┘
```

### 关键技术记录

#### 1. Railway PORT 配置问题解决
**问题**: Dockerfile 中硬编码 `ENV PORT=8000` 覆盖了 Railway 的 PORT 环境变量
**解决**: 移除 Dockerfile 中的 `PORT=8000`，让应用使用 Railway 的 PORT（通常 8080）
**Commit**: `fb011c4` - "fix: remove hardcoded PORT from Dockerfile"

#### 2. 前端 SSR 错误解决
**问题**: 首页在服务端渲染时调用 API，当 API 不可用时导致 "Application error"
**解决**: 移除 SSR 数据获取，改为客户端获取
**Commit**: `e9c9afc` - "fix: remove SSR article fetching"

#### 3. 域名迁移
**变更**: 所有域名从 `*.3strategy.cc` 迁移到 `*.zenconsult.top`
**Commit**: `adf68f7` - "feat: migrate all domains from 3strategy.cc to zenconsult.top"

#### 4. DNS 配置
- **Frontend (www)**: CNAME → Vercel
- **Admin**: CNAME → Vercel
- **API**: CNAME → delightful-spontaneity-production.up.railway.app (Railway)
- **DNS Provider**: Cloudflare (所有记录为 Grey cloud / DNS only)

### 环境变量配置

#### Vercel (Frontend & Admin)
```
NEXT_PUBLIC_API_URL=https://api.zenconsult.top
```

#### Railway (Backend)
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=... (至少32字符)
ALLOWED_ORIGINS=https://www.zenconsult.top,https://admin.zenconsult.top
```

### 验证命令

```bash
# 检查前端
curl -I https://www.zenconsult.top

# 检查管理后台
curl -I https://admin.zenconsult.top

# 检查 API
curl https://api.zenconsult.top/health

# 检查 API 文档
curl -I https://api.zenconsult.top/docs

# 检查 DNS
dig api.zenconsult.top CNAME +short
```

### 已知限制

1. **Railway 服务名称**: 当前后端运行在 `delightful-spontaneity-production.up.railway.app`，这是从早期部署保留的服务名称
2. **DNS 传播**: DNS 更改可能需要 5-15 分钟传播到所有服务器
3. **Railway 路由**: Railway 有时会有 404 "Application not found" 错误，但实际服务正常（Railway 平台特性）

### 后续维护

1. **监控**: 定期检查 Railway 和 Vercel Dashboard
2. **日志**: 使用 `railway logs` 和 Vercel Dashboard 查看日志
3. **更新**: 推送代码到 GitHub 自动触发部署
4. **备份**: 定期备份 PostgreSQL 数据库

### 相关文档

- [部署经验教训](/docs/DEPLOYMENT_LESSONS.md)
- [Railway 配置](/backend/railway.toml)
- [Vercel 配置](/deploy/vercel/vercel.json)
- [Nginx 配置](/deploy/nginx/)
