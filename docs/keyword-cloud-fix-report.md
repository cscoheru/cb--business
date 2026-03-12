# 关键词云问题诊断与解决方案

> 更新时间: 2026-03-12 11:10

---

## 🔍 问题诊断

### 根本原因

**爬虫 API 数据库连接失败**
- API 端点: `/api/v1/crawler/articles`
- 错误: `asyncpg.exceptions.InvalidPasswordError: password authentication failed`
- 影响: 前端无法获取文章数据，导致首页显示 "0 篇资讯"

### 数据库状态
- 数据库中有 **286 篇文章**
- PostgreSQL 服务正常
- 问题: asyncpg 驱动认证问题

---

## ✅ 已完成的修复

### 1. 前端降级方案
**文件**: `frontend/components/home/home-content.tsx`

```typescript
// 新的降级逻辑
1. 首先尝试 /api/v1/crawler-sync/articles (新同步端点)
2. 失败后降级到 /api/v1/products/trending (产品 API)
3. 将产品数据转换为文章格式展示
```

### 2. 创建同步 API 端点
**文件**: `backend/api/crawler_sync.py`

- 使用 `psycopg2-binary` (同步驱动)
- 绕过 asyncpg 认证问题
- 直接查询数据库返回文章

### 3. 前端已部署
- Vercel 部署完成
- URL: https://www.zenconsult.top
- CDN 缓存: 需要约 5-10 分钟刷新

---

## ⏳ 等待中

### CDN 缓存刷新
Vercel 的 CDN 缓存需要时间刷新，预计 5-10 分钟后：

- 新的前端代码会生效
- 降级到产品 API 会显示内容
- 用户将看到 "Amazon 产品" 而非 "整理中..."

---

## 🔧 待完成的后端部署

### 方案 A: 修复 asyncpg 连接 (优先)

```bash
# 1. 检查数据库密码配置
# 2. 重新创建数据库用户和密码
# 3. 重启 API 容器

# 在 HK 服务器执行:
docker exec -i cb-business-postgres psql -U cbuser -d cbdb << SQL
ALTER USER cbuser WITH PASSWORD 'new_password';
GRANT ALL PRIVILEGES ON DATABASE cbdb TO cbuser;
SQL

# 更新 .env.prod
# 重建容器
docker-compose -f docker-compose.prod.yml up -d --build api
```

### 方案 B: 部署同步 API 端点 (备用)

```bash
# 1. 添加 psycopg2-binary 到 requirements.txt
echo "psycopg2-binary==2.9.9" >> requirements.txt

# 2. 上传 crawler_sync.py 到服务器
scp api/crawler_sync.py hk:/root/cb-business/api/

# 3. 更新 api/__init__.py 添加路由

# 4. 重建并部署
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate api
```

---

## 📊 当前状态

| 组件 | 状态 | 说明 |
|------|------|------|
| **前端代码** | ✅ 已更新 | 使用降级方案 |
| **前端部署** | ✅ 已部署 | Vercel CDN 刷新中 |
| **产品 API** | ✅ 正常 | `/api/v1/products/*` |
| **数据库** | ✅ 正常 | 286 篇文章 |
| **爬虫 API** | ❌ 异步端点 | asyncpg 认证失败 |
| **同步 API** | ⏳ 待部署 | 已创建，未部署 |

---

## 🎯 快速验证

### 检查前端是否工作

```bash
# 5-10分钟后检查
curl -s "https://www.zenconsult.top/" | grep "篇资讯"

# 期望结果：不再是 "0 篇资讯"
# 应该看到从产品 API 获取的内容
```

### 检查产品 API

```bash
# 产品 API 正常工作
curl -s "https://api.zenconsult.top/api/v1/products/trending?category=electronics&limit=3" | jq

# 返回 Echo Dot, Sony 等产品数据
```

---

## 📝 下一步行动

### 立即可做
1. ⏳ **等待 10 分钟** - Vercel CDN 缓存刷新
2. 🌐 **访问网站** - 检查是否显示内容
3. ✅ **验证** - 确认降级方案生效

### 如果仍然为空
1. 部署同步 API 端点
2. 重建 Docker 容器
3. 清除 Vercel 缓存

---

## 💡 技术总结

### 问题架构

```
Frontend (Vercel)
    ↓ fetch()
Backend API (HK)
    ↓ asyncpg
PostgreSQL Database
    ↓ ❌ 密码认证失败
Empty Response
```

### 降级方案架构

```
Frontend (Vercel)
    ↓ fetch()
Backend API (HK)
    ↓
/products/trending (Oxylabs API)
    ↓ ✅ 正常工作
Product Data → Display as Articles
```

---

## 🚀 长期解决方案

1. **完全修复 asyncpg 连接**
   - 统一数据库密码管理
   - 使用 secrets 管理工具

2. **添加数据库连接池监控**
   - 自动重连机制
   - 连接失败告警

3. **前端优化**
   - 添加更详细的错误提示
   - 显示降级内容来源

---

*报告生成: 2026-03-12 11:10*
*状态: 前端已部署，等待 CDN 刷新*
