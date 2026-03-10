# TASK-003: 基础设施配置

> **所属会话**: 会话3（基础设施线）
> **优先级**: P0（最高）
> **预计工期**: 2天
> **依赖任务**: 无
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

在现有基础设施上创建项目所需的数据库表结构、配置Redis缓存、准备环境配置文件，为后端和前端开发提供基础支撑。

---

## 背景信息

**项目上下文**：
- 这是一个面向国内跨境电商创业者的SaaS平台
- 采用 Freemium 工具型商业模式
- 复用现有基础设施（节点A阿里云杭州）

**现有基础设施**：
- PostgreSQL: 139.224.42.111:5432（已有 `crawler_db` 和 `knowledge_db`）
- Redis: 139.224.42.111:6379
- MinIO: 139.224.42.111:9000/9001

**为什么需要这个任务**：
后端和前端开发依赖数据库结构和Redis配置，这是整个项目的基础，需要最先完成。

---

## 验收标准

- [ ] 在 `crawler_db` 数据库中创建所有新表（users, subscriptions, payments, articles, opportunities, risk_alerts, cost_references, user_usage）
- [ ] 所有索引创建成功
- [ ] Redis连接测试通过
- [ ] 环境配置模板文件创建完成
- [ ] 数据库Schema文档生成

---

## 技术要求

### 现有基础设施连接信息

```
节点A（阿里云杭州）：
PostgreSQL:
  Host: 139.224.42.111
  Port: 5432
  Database: crawler_db（使用现有数据库）
  用户名: postgres
  密码: [从基础设施文档获取]

Redis:
  Host: 139.224.42.111
  Port: 6379
  密码: [从基础设施文档获取]

MinIO:
  Host: 139.224.42.111
  Port: 9000（API）, 9001（Console）
  Access Key: [从基础设施文档获取]
  Secret Key: [从基础设施文档获取]
```

### 关键路径

```
项目根目录: /Users/kjonekong/Documents/cb-Business/
数据库Schema: docs/database/schema.sql
环境配置: backend/.env.example
基础设施文档: /Users/kjonekong/infrastructure/INFRASTRUCTURE.md
```

---

## 参考资料

**主计划文档**：
`/Users/kjonekong/.claude/plans/pure-crunching-lantern.md`

**基础设施文档**：
`/Users/kjonekong/infrastructure/INFRASTRUCTURE.md`（包含连接凭证）

**数据库设计**（在主计划的"数据库设计"章节）：
```
-- 用户表
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),
  name VARCHAR(100),
  phone VARCHAR(20),
  avatar_url TEXT,
  plan_tier VARCHAR(20) DEFAULT 'free',
  plan_status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login_at TIMESTAMP WITH TIME ZONE,
  region_preference VARCHAR(50),
  currency_preference VARCHAR(10) DEFAULT 'CNY'
);

-- 订阅表
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  plan_tier VARCHAR(20) NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  billing_cycle VARCHAR(10),
  amount DECIMAL(10,2),
  currency VARCHAR(10) DEFAULT 'CNY',
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE,
  canceled_at TIMESTAMP WITH TIME ZONE,
  auto_renew BOOLEAN DEFAULT TRUE,
  payment_method VARCHAR(50),
  external_subscription_id VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 支付记录表
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  subscription_id UUID REFERENCES subscriptions(id),
  amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(10) DEFAULT 'CNY',
  payment_method VARCHAR(50) NOT NULL,
  payment_status VARCHAR(20) DEFAULT 'pending',
  transaction_id VARCHAR(255) UNIQUE,
  external_order_id VARCHAR(255),
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

-- 用户使用记录表
CREATE TABLE user_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  usage_type VARCHAR(50) NOT NULL,
  quantity INTEGER DEFAULT 1,
  period_date DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 文章表（扩展原有结构）
CREATE TABLE articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  summary TEXT,
  content TEXT,
  source VARCHAR(50),
  url TEXT UNIQUE,
  published_at TIMESTAMP WITH TIME ZONE,
  crawled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  region VARCHAR(50),
  country VARCHAR(50),
  platform VARCHAR(50),
  content_theme VARCHAR(20),
  subcategory VARCHAR(50),
  tags TEXT[],
  risk_level VARCHAR(20),
  opportunity_score DECIMAL(3,2),
  slug TEXT UNIQUE,
  meta_description TEXT,
  is_published BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 机会表
CREATE TABLE opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region VARCHAR(50) NOT NULL,
  country VARCHAR(50),
  product_category VARCHAR(50),
  opportunity_type VARCHAR(50),
  title TEXT,
  description TEXT,
  opportunity_score DECIMAL(3,2),
  estimated_market_size BIGINT,
  competition_level VARCHAR(20),
  growth_potential VARCHAR(20),
  entry_difficulty INTEGER,
  data_sources JSONB,
  valid_until TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 风险预警表
CREATE TABLE risk_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_type VARCHAR(50),
  severity VARCHAR(20),
  title TEXT,
  description TEXT,
  affected_regions TEXT[],
  affected_platforms TEXT[],
  affected_categories TEXT[],
  mitigation_actions JSONB,
  source_url TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  resolved_at TIMESTAMP WITH TIME ZONE
);

-- 成本参考表
CREATE TABLE cost_references (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region VARCHAR(50) NOT NULL,
  country VARCHAR(50),
  platform VARCHAR(50),
  cost_type VARCHAR(50),
  cost_item TEXT,
  amount DECIMAL(10,2),
  currency VARCHAR(10),
  frequency VARCHAR(20),
  effective_date TIMESTAMP WITH TIME ZONE,
  valid_until TIMESTAMP WITH TIME ZONE
);

-- 索引
CREATE INDEX idx_articles_region ON articles(region);
CREATE INDEX idx_articles_theme ON articles(content_theme);
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_user_usage_user_date ON user_usage(user_id, period_date);
```

---

## 开发指南

### 步骤1：连接到PostgreSQL数据库

```bash
# 方式1：使用psql命令行
psql -h 139.224.42.111 -U postgres -d crawler_db

# 方式2：如果需要密码
psql -h 139.224.42.111 -U postgres -d crawler_db -W

# 方式3：使用连接字符串
psql "postgresql://postgres:password@139.224.42.111:5432/crawler_db"
```

### 步骤2：创建数据库表

**方法A：直接在psql中执行**
```sql
-- 连接成功后，复制粘贴上面的CREATE TABLE语句
-- 逐个执行
```

**方法B：创建schema.sql文件后导入**
```bash
# 1. 创建schema文件
cat > /Users/kjonekong/Documents/cb-Business/docs/database/schema.sql << 'EOF'
-- [上面的所有CREATE TABLE语句]
EOF

# 2. 在psql中导入
\i /Users/kjonekong/Documents/cb-Business/docs/database/schema.sql
```

### 步骤3：验证表创建

```sql
-- 查看所有表
\dt

-- 预期输出应包含：
-- Schema |        Name        | Type  | Owner
-- --------+--------------------+-------+----------
-- public  | articles           | table | postgres
-- public  | cost_references    | table | postgres
-- public  | opportunities      | table | postgres
-- public  | payments           | table | postgres
-- public  | risk_alerts        | table | postgres
-- public  | subscriptions      | table | postgres
-- public  | user_usage         | table | postgres
-- public  | users              | table | postgres

-- 查看表结构
\d users

-- 查看索引
\di

-- 测试查询
SELECT COUNT(*) FROM users;
```

### 步骤4：测试Redis连接

```bash
# 连接Redis
redis-cli -h 139.224.42.111 -p 6379

# 如果有密码
redis-cli -h 139.224.42.111 -p 6379 -a your_password

# 在Redis CLI中测试
> PING
# 应返回: PONG

> SET test "hello"
> GET test
# 应返回: "hello"

> DEL test
```

### 步骤5：创建环境配置模板

```bash
# 创建后端环境配置模板
cat > /Users/kjonekong/Documents/cb-Business/backend/.env.example << 'EOF'
# 数据库配置
DATABASE_URL=postgresql://postgres:password@139.224.42.111:5432/crawler_db

# Redis配置
REDIS_URL=redis://:password@139.224.42.111:6379

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 微信支付配置
WECHAT_APP_ID=your_wechat_app_id
WECHAT_MCH_ID=your_wechat_mch_id
WECHAT_API_KEY=your_wechat_api_key
WECHAT_NOTIFY_URL=https://api.cb.3strategy.cc/api/v1/payments/wechat/notify

# 支付宝配置（备用）
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_PRIVATE_KEY=your_alipay_private_key
ALIPAY_PUBLIC_KEY=your_alipay_public_key

# MinIO配置
MINIO_ENDPOINT=139.224.42.111:9000
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
MINIO_BUCKET_NAME=cb-business
MINIO_USE_SSL=false

# 应用配置
APP_NAME=Cross-Border Business
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,http://cb.3strategy.cc
EOF

# 创建实际环境配置文件（不提交到git）
cp /Users/kjonekong/Documents/cb-Business/backend/.env.example \
   /Users/kjonekong/Documents/cb-Business/backend/.env
```

### 步骤6：生成数据库Schema文档

```bash
# 使用pgdump生成schema文档
pg_dump -h 139.224.42.111 -U postgres -d crawler_db \
  --schema-only --no-owner --no-privileges \
  -f /Users/kjonekong/Documents/cb-Business/docs/database/schema_dump.sql

# 或者生成格式化的文档
cat > /Users/kjonekong/Documents/cb-Business/docs/database/README.md << 'EOF'
# 数据库文档

## 连接信息

- Host: 139.224.42.111
- Port: 5432
- Database: crawler_db
- 用户: postgres

## 表结构

### users (用户表)
- id: UUID, 主键
- email: VARCHAR(255), 唯一, 非空
- password_hash: VARCHAR(255)
- name: VARCHAR(100)
- phone: VARCHAR(20)
- avatar_url: TEXT
- plan_tier: VARCHAR(20), 默认'free'
- plan_status: VARCHAR(20), 默认'active'
- created_at: TIMESTAMP WITH TIME ZONE
- updated_at: TIMESTAMP WITH TIME ZONE
- last_login_at: TIMESTAMP WITH TIME ZONE
- region_preference: VARCHAR(50)
- currency_preference: VARCHAR(10), 默认'CNY'

### subscriptions (订阅表)
- id: UUID, 主键
- user_id: UUID, 外键→users(id)
- plan_tier: VARCHAR(20), 非空
- status: VARCHAR(20), 默认'active'
- billing_cycle: VARCHAR(10)
- amount: DECIMAL(10,2)
- currency: VARCHAR(10), 默认'CNY'
- started_at: TIMESTAMP WITH TIME ZONE
- expires_at: TIMESTAMP WITH TIME ZONE
- canceled_at: TIMESTAMP WITH TIME ZONE
- auto_renew: BOOLEAN, 默认TRUE
- payment_method: VARCHAR(50)
- external_subscription_id: VARCHAR(255)
- created_at: TIMESTAMP WITH TIME ZONE

[... 其他表类似 ...]

## 索引

- idx_articles_region: articles(region)
- idx_articles_theme: articles(content_theme)
- idx_articles_published: articles(published_at DESC)
- idx_user_usage_user_date: user_usage(user_id, period_date)
EOF
```

---

## 测试要求

### 数据库测试
```sql
-- 测试1：插入测试数据
INSERT INTO users (email, name) VALUES
  ('test@example.com', 'Test User');

-- 测试2：查询测试
SELECT * FROM users WHERE email = 'test@example.com';

-- 测试3：外键测试
INSERT INTO subscriptions (user_id, plan_tier, amount)
  SELECT id, 'pro', 99.00 FROM users WHERE email = 'test@example.com';

-- 测试4：清理测试数据
DELETE FROM subscriptions WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com');
DELETE FROM users WHERE email = 'test@example.com';
```

### Redis测试
```bash
# 测试读写
redis-cli -h 139.224.42.111 -p 6379 -a password << 'EOF'
SET test_key "test_value"
GET test_key
DEL test_key
EOF
```

---

## 提交规范

### Git提交
```bash
cd /Users/kjonekong/Documents/cb-Business

# 添加文件
git add docs/database/ backend/.env.example

# 提交
git commit -m "chore(TASK-003): 完成基础设施配置

- 在crawler_db中创建所有数据库表
- 创建索引优化查询性能
- 配置Redis连接测试
- 创建环境配置模板文件
- 生成数据库Schema文档

数据库表:
- users (用户表)
- subscriptions (订阅表)
- payments (支付记录表)
- user_usage (使用记录表)
- articles (文章表)
- opportunities (机会表)
- risk_alerts (风险预警表)
- cost_references (成本参考表)

验收:
- ✅ 所有表创建成功
- ✅ 索引创建成功
- ✅ Redis连接测试通过
- ✅ 环境配置模板完成

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 不提交的文件
确保 `.env` 文件不被提交：
```bash
# 创建.gitignore（如果不存在）
cat > /Users/kjonekong/Documents/cb-Business/.gitignore << 'EOF'
# 环境变量
.env
.env.local
.env.*.local

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
*.so

# Node
node_modules/
.next/
out/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
```

---

## 进度更新

**开始时间**: [填写开始时间]

**进度记录**:
- [ ] 连接到PostgreSQL数据库
- [ ] 创建所有数据库表
- [ ] 创建索引
- [ ] 验证表结构
- [ ] 测试Redis连接
- [ ] 创建环境配置文件
- [ ] 生成数据库文档

**完成时间**: [填写完成时间]

---

## 问题记录

| 问题描述 | 发现时间 | 解决方案 | 状态 |
|----------|----------|----------|------|
| （如有问题记录在这里） | | | |

---

## 注意事项

1. **安全性**：
   - 不要在任何地方提交真实密码
   - .env文件不要加入git
   - 生产环境的SECRET_KEY必须足够复杂

2. **备份**：
   - 创建表前先备份数据库
   - 记录所有执行的SQL语句

3. **权限**：
   - 确认数据库用户有CREATE权限
   - 确认Redis可访问

---

## 下一步

完成本任务后，**会话2（后端开发线）**可以开始 TASK-002（后端项目初始化）。

*本任务书由主会话（项目经理）创建和维护*
