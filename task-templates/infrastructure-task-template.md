# 基础设施任务书模板

> **模板版本**: v1.0
> **适用于**: 会话3（基础设施线）
> **技术栈**: PostgreSQL, Redis, Nginx, MinIO, Docker

---

# TASK-XXX: [任务名称]

> **所属会话**: 会话3（基础设施线）
> **优先级**: P0/P1/P2
> **预计工期**: X 天
> **依赖任务**: TASK-XXX（如有）
> **创建日期**: YYYY-MM-DD
> **状态**: ⏳ 待开始 / 🔄 进行中 / ✅ 已完成 / ❌ 已阻塞

---

## 任务目标

[清晰描述这个基础设施任务要达成的目标]

**示例**：
- 创建PostgreSQL数据库和表结构
- 配置Redis缓存
- 配置Nginx反向代理

---

## 背景信息

**项目上下文**：
- 这是一个面向国内跨境电商创业者的SaaS平台
- 复用现有基础设施（节点A阿里云杭州）
- 数据库和缓存已存在，需要创建新表

**为什么需要这个任务**：
[说明这个任务在整体项目中的作用]

---

## 验收标准

- [ ] 数据库表创建成功
- [ ] 索引配置正确
- [ ] Redis连接测试通过
- [ ] Nginx配置生效
- [ ] 服务可访问

---

## 技术要求

### 现有基础设施
```
节点A（阿里云杭州）：
- PostgreSQL: 139.224.42.111:5432
- Redis: 139.224.42.111:6379
- MinIO: 139.224.42.111:9000/9001

节点B（香港）：
- Chatwoot: 待配置
- Uptime Kuma: 待配置
```

### 关键路径
```
数据库Schema: /Users/kjonekong/Documents/cb-Business/docs/database/schema.sql
Nginx配置: /etc/nginx/sites-available/cb.3strategy.cc
环境配置: /Users/kjonekong/Documents/cb-Business/backend/.env
```

---

## 参考资料

**设计文档**：
- 主计划：`/Users/kjonekong/.claude/plans/pure-crunching-lantern.md`
- 基础设施文档：`/Users/kjonekong/infrastructure/INFRASTRUCTURE.md`

**数据库设计**：
- Schema文件：`/Users/kjonekong/Documents/cb-Business/docs/database/schema.sql`

---

## 开发指南

### 步骤1：连接数据库
```bash
# 连接到节点A的PostgreSQL
psql -h 139.224.42.111 -U postgres -d crawler_db
```

### 步骤2：执行Schema
```bash
# 在psql中执行
\i /Users/kjonekong/Documents/cb-Business/docs/database/schema.sql
```

### 步骤3：验证表创建
```sql
-- 查看所有表
\dt

-- 验证索引
\di

-- 测试查询
SELECT COUNT(*) FROM users;
```

### 步骤4：配置Redis
```bash
# 测试Redis连接
redis-cli -h 139.224.42.111 -p 6379
> PING
# 应返回 PONG
```

### 步骤5：配置Nginx
```nginx
# /etc/nginx/sites-available/cb.3strategy.cc
server {
    listen 80;
    server_name api.cb.3strategy.cc;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 注意事项
1. 所有敏感信息（密码、密钥）使用环境变量
2. 数据库操作先在测试环境验证
3. Nginx配置修改后需要reload
4. 修改前备份原配置文件

---

## 测试要求

### 数据库测试
- [ ] 表创建成功
- [ ] 索引生效
- [ ] 外键约束正常
- [ ] 查询性能正常

### Redis测试
- [ ] 连接正常
- [ ] 读写正常
- [ ] 过期策略生效

### Nginx测试
- [ ] 反向代理正常
- [ ] SSL证书正常
- [ ] 负载均衡正常（如有）

---

## 部署检查清单

- [ ] 数据库备份完成
- [ ] 配置文件已备份
- [ ] 回滚方案已准备
- [ ] 监控已配置
- [ ] 日志已配置

---

## 提交规范

### 配置文件提交
```bash
git add .
git commit -m "chore: 配置PostgreSQL数据库

- 创建用户和订阅表
- 添加索引优化查询
- 配置外键约束

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 环境变量模板
```bash
# .env.example - 提交到git
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
WECHAT_APP_ID=your_app_id
WECHAT_MCH_ID=your_mch_id

# .env - 不提交，包含真实值
```

---

## 进度更新

**开始时间**: YYYY-MM-DD HH:MM

**进度记录**:
- YYYY-MM-DD: 完成数据库配置
- YYYY-MM-DD: 完成Redis配置
- ...

**完成时间**: YYYY-MM-DD HH:MM

---

## 问题记录

| 问题描述 | 发现时间 | 解决方案 | 状态 |
|----------|----------|----------|------|
| ... | ... | ... | ✅ 已解决 |

---

## 应急回滚

如果部署出现问题，执行以下回滚步骤：

1. **数据库回滚**：
```bash
psql -h 139.224.42.111 -U postgres -d crawler_db < backup.sql
```

2. **Nginx回滚**：
```bash
sudo cp /etc/nginx/sites-available/cb.3strategy.cc.backup \
        /etc/nginx/sites-available/cb.3strategy.cc
sudo nginx -s reload
```

---

*本任务书由主会话（项目经理）创建和维护*
