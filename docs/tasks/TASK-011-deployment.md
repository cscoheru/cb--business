# TASK-011: 部署上线

> **所属会话**: 会话3（基础设施线）配合项目经理
> **优先级**: P0（最高）
> **预计工期**: 3天
> **依赖任务**: 所有开发和测试任务
> **创建日期**: 2025-03-10
> **状态**: ⏳ 进行中（部分完成，遇到Railway配额限制）
> **最后更新**: 2025-03-10 21:00

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

### 当前状态更新 (2025-03-10 21:00)

| 服务 | 状态 | 说明 | 下一步操作 |
|------|------|------|-----------|
| **后端 API** | 🔴 阻塞 | Railway 免费计划资源配额已满 | 需要升级 Railway 计划或使用替代方案 |
| **用户前端** | 🟡 待部署 | Vercel CLI 已安装，项目未链接 | 使用 Vercel GitHub 集成部署 |
| **管理后台** | 🟡 待部署 | Vercel CLI 已安装，项目未链接 | 使用 Vercel GitHub 集成部署 |
| **域名 DNS** | ⏸️ 待配置 | 等待服务部署完成 | 配置 CNAME 记录 |
| **SSL 证书** | ⏸️ 待配置 | 等待 DNS 配置完成 | 平台自动生成 |

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

- [ ] **前端可访问**: https://cb.3strategy.cc
- [ ] **管理后台可访问**: https://admin.cb.3strategy.cc
- [ ] **API 可访问**: https://api.cb.3strategy.cc
- [ ] **API 文档可访问**: https://api.cb.3strategy.cc/docs
- [ ] **SSL 证书正常** (所有域名显示绿锁)

### 功能测试

- [ ] **首页加载正常**: 检查页面样式和内容
- [ ] **用户注册流程**: 测试新用户注册
- [ ] **用户登录流程**: 测试已注册用户登录
- [ ] **Dashboard 访问**: 登录后可进入仪表盘
- [ ] **API 健康检查**: `https://api.cb.3strategy.cc/health`
- [ ] **数据库连接**: 验证 PostgreSQL 连接
- [ ] **Redis 连接**: 验证 Redis 服务

### 管理员功能测试

- [ ] **管理员登录**: admin@3strategy.cc / admin123456
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
*最后更新: 2025-03-10 - 添加 GitHub 集成部署说明*
