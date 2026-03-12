# CB-Business (ZenConsult) 项目状态报告

**日期**: 2025-03-12
**项目**: 跨境电商AI智能助手
**域名**: www.zenconsult.top | api.zenconsult.top

---

## 📊 项目概览

### 目标
打造一个AI驱动的跨境电商市场洞察平台，智能聚合东南亚、欧美、拉美市场资讯，提供政策解读、机会发现、风险预警和实操指南。

### 技术架构
```
┌─────────────────────────────────────────────────────────┐
│                    用户访问                              │
│           www.zenconsult.top (Vercel)                  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────┐
│              HK Nginx 反向代理                           │
│           api.zenconsult.top                            │
│         nginx-gateway (172.22.0.5)                      │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI 后端                                │
│         cb-business-api-fixed (172.22.0.4)              │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼             ▼
    PostgreSQL    Redis       爬虫系统(Railway)
   (172.22.0.2)  (172.22.0.3)  crawler-system
```

---

## ✅ 已完成功能

### 1. 数据爬取系统
- ✅ 286篇文章已爬取并处理
- ✅ 支持多平台：Zhihu、Toutiao、WeChat、Mercopress等
- ✅ AI分类和内容分析
- ✅ Dify知识库集成

### 2. 后端API
- ✅ FastAPI框架搭建
- ✅ PostgreSQL数据库迁移
- ✅ Redis缓存集成
- ✅ 用户认证系统
- ✅ 订阅管理
- ✅ 使用量统计
- ✅ CORS配置

### 3. 前端功能
- ✅ Next.js 14 + TypeScript
- ✅ Hero搜索区域（异域浪漫渐变背景）
- ✅ 关键词云组件
- ✅ 区域资讯展示
- ✅ 国家门户页面 (/th, /vn, /my, /us, /br, /mx)
- ✅ 主题门户标签
- ✅ 能力/资源/兴趣评估系统
- ✅ 12阶段成长路径
- ✅ 搜索功能
- ✅ 用户登录/注册

### 4. 基础设施
- ✅ HK服务器部署（Docker Compose）
- ✅ Nginx反向代理 + SSL证书
- ✅ Vercel前端部署
- ✅ 数据库备份策略

---

## 🔧 部署配置

### HK服务器信息
```
SSH登录: ssh hk-jump (通过阿里云跳转)
跳转路径: 本机 → 阿里云(139.224.42.111) → HK(103.59.103.85)
```

### Docker容器状态
```
网络: cb-network (172.22.0.0/16)

容器名称                    IP地址      状态
──────────────────────────────────────────
cb-business-postgres      172.22.0.2   ✅ 运行中
cb-business-redis         172.22.0.3   ✅ 运行中
cb-business-api-fixed     172.22.0.4   ✅ 运行中
nginx-gateway             172.22.0.5   ✅ 运行中
```

### 数据库配置
```
Host: cb-business-postgres:5432
Database: cbdb
User: cbuser
Password: cbuser123
Articles: 286条
```

### 关键配置文件
```
HK服务器:
  /opt/docker/nginx/conf.d/zenconsult.conf    # Nginx配置
  /opt/docker/nginx/ssl/                      # SSL证书目录

本地项目:
  /Users/kjonekong/Documents/cb-Business/
  ├── backend/          # FastAPI后端
  ├── frontend/         # Next.js前端
  └── pyStcratch/       # 爬虫系统
```

### Vercel部署信息
```
项目名称: cscoheru-cb-business-frontend
项目ID: prj_PfXgcXsIwt5bKfJJbxQ01ZCWJEcV
环境变量: NEXT_PUBLIC_API_URL=https://api.zenconsult.top
```

---

## ⚠️ 当前问题

### 主要问题：网站显示"加载中..."

**症状**: 首页 https://www.zenconsult.top 显示"加载中..."，无法显示286篇文章

**已尝试的修复**:
1. ✅ 修复nginx反向代理网络连接
2. ✅ 修复SSL证书配置
3. ✅ 修复前端API端点 (`/api/v1/crawler-sync/articles` → `/api/v1/crawler/articles`)
4. ✅ 部署最新代码到Vercel

**验证结果**:
- ✅ 后端API正常：`curl https://api.zenconsult.top/api/v1/crawler/articles?per_page=1` 返回286篇文章
- ✅ nginx反向代理正常
- ✅ CORS配置正确
- ⚠️ 前端仍显示"加载中..."

**可能原因**:
1. Vercel CDN缓存未更新
2. 浏览器缓存问题
3. 客户端JavaScript错误（需浏览器控制台检查）
4. API调用超时

**下一步调试**:
```bash
# 1. 打开浏览器 https://www.zenconsult.top
# 2. 按F12打开开发者工具
# 3. 检查Console是否有JavaScript错误
# 4. 检查Network面板，找到 /api/v1/crawler/articles 请求
# 5. 查看请求状态码和响应内容
# 6. 尝试硬刷新 Ctrl+Shift+R
```

---

## 📁 关键文件清单

### 前端核心文件
```
frontend/
├── lib/api.ts                           # API客户端定义
├── components/
│   └── home/
│       └── home-content.tsx             # 首页内容组件（已修复API端点）
├── app/
│   ├── page.tsx                         # 首页
│   └── [country]/
│       └── page.tsx                     # 国家门户页面
└── .env.production                      # 生产环境变量
```

### 后端核心文件
```
backend/
├── api/
│   ├── crawler.py                       # 爬虫API端点
│   └── crawler_sync.py                  # 同步API（未部署）
├── docker-compose.yml                   # Docker编排
└── Dockerfile                           # 镜像构建
```

### HK服务器配置
```
/opt/docker/nginx/conf.d/zenconsult.conf  # Nginx配置
```

---

## 🚀 快速命令参考

### HK服务器操作
```bash
# SSH登录
ssh hk-jump

# 检查容器状态
docker ps --filter name=cb-business

# 检查容器网络
docker network inspect cb-network

# 查看API日志
docker logs cb-business-api-fixed

# 重启API容器
docker restart cb-business-api-fixed

# 测试nginx配置
docker exec nginx-gateway nginx -t

# 重载nginx
docker exec nginx-gateway nginx -s reload

# 进入数据库
docker exec -it cb-business-postgres psql -U cbuser -d cbdb
```

### 本地开发
```bash
# 前端开发
cd /Users/kjonekong/Documents/cb-Business/frontend
npm run dev

# 部署到Vercel
npx vercel --prod

# 测试API
curl 'https://api.zenconsult.top/api/v1/crawler/articles?per_page=1'
```

---

## 📝 待办事项

### 高优先级
1. ⚠️ **调试网站"加载中"问题** - 检查浏览器控制台
2. 验证286篇文章在前端正常显示
3. 检查国家门户页面文章显示

### 中优先级
4. 实现产品数据展示（Amazon等）
5. 优化关键词云组件
6. 完善搜索功能

### 低优先级
7. 添加更多爬虫来源
8. 优化SEO
9. 性能优化

---

## 🔍 API端点文档

### 公开端点
```
GET /api/v1/crawler/articles
  参数: page, per_page, region, country, theme, platform
  返回: {articles: [...], total: N, page: N, per_page: N}

GET /api/v1/crawler/articles/{id}
  返回: 单篇文章详情

GET /health
  返回: 系统健康状态
```

### 认证端点
```
POST /api/v1/auth/register
POST /api/v1/auth/login
GET /api/v1/users/me
```

---

## 📊 数据统计

### 文章数据
- 总数: 286篇
- 状态: 已处理
- 来源: Zhihu, Toutiao, WeChat, Mercopress等

### 用户数据
- 注册用户: （待统计）
- 付费用户: （待统计）

---

## 🎯 下次会话开始指南

### 快速恢复上下文
```
"继续CB-Business工作，当前问题是网站显示'加载中'，
后端API正常返回286篇文章，需要检查浏览器控制台。"
```

### 或直接读取状态
```
"读取 /Users/kjonekong/Documents/cb-Business/03122025—project_status.md"
```

---

## 📞 关键联系人信息

无

---

## 📅 更新日志

### 2025-03-12
- ✅ 修复nginx反向代理网络连接
- ✅ 修复SSL证书配置
- ✅ 修复前端API端点
- ✅ 部署到Vercel
- ⚠️ 网站仍显示"加载中"待调试

### 2025-03-11及之前
- ✅ 完成基础架构搭建
- ✅ 完成前后端核心功能
- ✅ 完成HK服务器部署
- ✅ 爬虫系统迁移到Railway
