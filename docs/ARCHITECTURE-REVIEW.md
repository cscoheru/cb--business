# CB-Business 架构技术评审

> **评审日期**: 2026-03-13
> **评审人**: AI技术专家
> **目的**: 以终为始，识别架构问题、风险和低效之处

---

## 🏗️ 实际架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户访问流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户浏览器                                                          │
│    ↓                                                                 │
│  Vercel CDN (https://www.zenconsult.top)                           │
│    ↓                                                                 │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  HK服务器 (103.59.103.85)                            │           │
│  │                                                        │           │
│  │  nginx-gateway (172.22.0.5:80/443)                   │           │
│  │    ↓                                                   │           │
│  │  cb-business-api (172.22.0.4:8000)                   │           │
│  │    ↓                                                   │           │
│  │  ┌────────────────────────────────────────┐           │           │
│  │  │  跨境网络调用 ( latency: ~50-100ms)     │           │           │
│  │  └────────────────────────────────────────┘           │           │
│  │    ↓                                                   │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                      │
│  ↓                                                                   │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  阿里云服务器 (139.224.42.111)                       │           │
│  │                                                        │           │
│  │  PostgreSQL :5432                              │           │
│  │  Redis        :6379                              │           │
│  │  MinIO        :9000                             │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚨 严重问题 (Critical Issues)

### 1. 跨云架构导致的性能问题

**问题描述**:
```
HK FastAPI → 阿里云 PostgreSQL
  每次查询: +50-100ms 延迟
  每个请求: 可能10-20次数据库查询
  总延迟: 500-2000ms (仅数据库I/O)
```

**影响**:
- API响应时间 > 2秒 (用户体验差)
- 数据库连接池效率低
- 高峰期可能出现连接耗尽

**严重程度**: 🔴 **HIGH**

---

### 2. 单点故障风险

**问题描述**:
- 阿里云PostgreSQL是**单实例** (没有看到主从/高可用配置)
- 如果阿里云服务器宕机 → **整个服务不可用**

**影响**:
- 数据丢失风险
- 服务中断风险
- 无法自动故障转移

**严重程度**: 🔴 **CRITICAL**

---

### 3. 数据库连接安全性

**发现问题**:
```bash
DATABASE_URL=postgresql://postgres:changeme-postgres-password-123@139.224.42.111:5432/crawler_db
```

**问题**:
- 密码明文存储在代码库
- 暴露在环境变量中
- 数据库传输可能未加密

**严重程度**: 🟡 **MEDIUM**

---

### 4. HK服务器本地有PostgreSQL但未使用

**发现**:
```
cb-business-postgres: 172.22.0.2 (HK服务器上)
但实际连接到: 139.224.42.111 (阿里云)
```

**问题**:
- 本地有PostgreSQL但不用
- 跨云调用增加延迟
- 资源浪费

**严重程度**: 🟡 **MEDIUM**

---

## ⚠️ 高风险问题 (High Risk Issues)

### 5. Scheduler使用SQLite而非PostgreSQL

**发现问题**:
```python
jobstores = {
    'default': MemoryJobStore()  # 使用内存存储
}
```

**问题**:
- 定时任务状态存储在内存中
- 容器重启 → **所有任务丢失**
- 无法追踪任务历史

**影响**:
- 每日卡片生成任务可能丢失
- 无法恢复任务状态

**严重程度**: 🟠 **HIGH**

---

### 6. 无监控和告警系统

**发现问题**:
- 没有应用性能监控 (APM)
- 没有错误追踪 (如Sentry)
- 没有数据库慢查询监控
- 没有API响应时间监控

**影响**:
- 问题发生后才知道
- 无法预防性发现问题
- 故障排查困难

**严重程度**: 🟠 **HIGH**

---

### 7. 前后端分离导致的CORS复杂性

**发现问题**:
```
Frontend: Vercel (动态域名)
Backend: HK服务器 (nginx代理)
```

**问题**:
- CORS配置复杂
- 开发/生产环境切换麻烦
- 可能的认证/授权问题

**严重程度**: 🟡 **MEDIUM**

---

## 📉 低效问题 (Inefficiency Issues)

### 8. Oxylabs API调用无缓存

**问题描述**:
```python
# 每次都实时调用Oxylabs API
product = await client.get_amazon_product(asin)
```

**问题**:
- Amazon产品数据短期内不会变化
- 重复调用浪费API额度
- 响应慢

**建议**:
- Redis缓存产品数据 (TTL: 1小时)
- 减少API调用90%

---

### 9. 静态资源未使用CDN

**问题描述**:
- 产品图片存储在MinIO
- 没有配置CDN加速
- 每次都从阿里云加载

**建议**:
- 使用阿里云OSS + CDN
- 或配置MinIO CDN

---

### 10. 数据库查询未优化

**潜在问题**:
- 可能存在N+1查询
- 可能缺少索引
- 可能未使用连接池

**建议**:
- 添加慢查询日志
- 使用查询分析工具

---

## 🏗️ 架构改进建议

### 短期改进 (1-2周)

#### 1. 优化数据库连接 (紧急)

**方案A**: 数据库迁移到HK
```
阿里云 PostgreSQL → HK服务器 PostgreSQL
好处:
  ✓ 消除跨境延迟 (50-100ms → 1-5ms)
  ✓ 降低网络故障风险
  ✓ 提高API响应速度
```

**方案B**: 使用连接池优化
```python
# 增加连接池配置
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### 2. Scheduler持久化 (重要)

**改进**:
```python
# 使用PostgreSQL存储任务状态
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}
```

#### 3. 添加监控 (重要)

**推荐**:
- 应用性能: Sentry + New Relic
- 数据库: pg_stat_statements
- 服务器: uptime-kuma (已有!)

---

### 中期改进 (1-2月)

#### 4. 数据库高可用

**方案**:
```
主从复制 + 自动故障转移
  PostgreSQL主库 (阿里云)
    ↓ 流复制
  PostgreSQL从库 (HK)
```

#### 5. 缓存策略

**三层缓存**:
```
1. Vercel Edge Cache (静态内容)
2. Redis (热点数据)
3. Database (持久化)
```

#### 6. API性能优化

**措施**:
- 异步处理非关键路径
- 批量查询优化
- 使用GraphQL减少over-fetching

---

### 长期改进 (3-6月)

#### 7. 微服务拆分

**场景**: 如果功能复杂度增加

**拆分方案**:
```
monolith → services:
  - api-gateway (nginx)
  - card-service (FastAPI)
  - crawler-service (FastAPI)
  - analytics-service (FastAPI)
```

#### 8. CDN + 边缘计算

**方案**:
- 静态资源 → 阿里云OSS + CDN
- API → Cloudflare Workers (边缘计算)

---

## 🎯 优先级排序

| 问题 | 严重程度 | 修复难度 | 优先级 |
|-----|---------|---------|--------|
| 数据库跨境延迟 | 🔴 HIGH | 🟢 EASY | **P0** |
| Scheduler内存存储 | 🟠 HIGH | 🟢 EASY | **P0** |
| 数据库单点故障 | 🔴 CRITICAL | 🔴 MEDIUM | **P1** |
| 无监控告警 | 🟠 HIGH | 🟢 EASY | **P1** |
| Oxylabs无缓存 | 🟡 MEDIUM | 🟢 EASY | **P2** |
| 密码明文存储 | 🟡 MEDIUM | 🟢 EASY | **P2** |
| 静态资源无CDN | 🟡 MEDIUM | 🟡 MEDIUM | **P3** |

---

## ✅ Phase 1开发建议 (考虑现有架构)

基于上述问题，Phase 1开发时应该：

### 1. 同时修复P0问题

**任务清单**:
- [ ] 数据库连接优化 (连接池配置)
- [ ] Scheduler改用PostgreSQL存储
- [ ] Oxylabs数据Redis缓存

### 2. 添加基础监控

**最小化监控**:
- [ ] 添加Sentry错误追踪
- [ ] 添加API响应时间日志
- [ ] 添加数据库慢查询日志

### 3. 数据设计考虑性能

**cards表设计**:
```sql
-- 添加索引
CREATE INDEX idx_cards_created_at ON cards(created_at DESC);
CREATE INDEX idx_cards_category ON cards(category);
CREATE INDEX idx_cards_published ON cards(is_published, published_at);

-- 使用JSONB减少JOIN
content JSONB NOT NULL,
analysis JSONB NOT NULL
```

---

## 🤔 你需要回答的问题

1. **数据库迁移**:
   - 是否愿意把PostgreSQL从阿里云迁移到HK？
   - 或者接受当前延迟，优化其他方面？

2. **高可用需求**:
   - Phase 1是否需要考虑高可用？
   - 还是等用户量增长后再处理？

3. **预算考虑**:
   - 是否有预算用于:
     - 阿里云RDS高可用版 (~$200/月)
     - Sentry监控 (~$26/月)
     - 阿里云OSS + CDN (~$50/月)

---

## 📝 总结

### 现有架构的优点 ✅

1. **前后端分离** - 易于独立部署和扩展
2. **Docker容器化** - 环境一致性好
3. **nginx网关** - 反向代理和负载均衡
4. **MinIO对象存储** - 自主可控

### 现有架构的风险 ⚠️

1. **跨境延迟** - 影响用户体验
2. **单点故障** - 数据无保障
3. **缺少监控** - 问题后知后觉
4. **内存Scheduler** - 任务无持久化

### 我的建议 💡

**Phase 1** (2周):
- ✅ 功能开发 + 修复P0问题
- ✅ 添加基础监控
- ✅ 性能优化 (缓存)

**Phase 2** (用户量增长后):
- ✅ 数据库高可用
- ✅ CDN加速
- ✅ 完整监控体系

---

**你觉得这个评审如何？哪些问题需要优先处理？**
