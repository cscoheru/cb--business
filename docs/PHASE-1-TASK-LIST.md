# Phase 1 完整任务清单

> **目标**: 每日生成3张信息卡片，验证用户是否愿意看
> **周期**: 2周
> **包含**: 功能开发 + 数据库迁移 + 架构优化

---

## 📋 Week 1: 基础设施 + 数据采集

### Day 1: 性能优化（不迁移数据库）

**任务1.1: Redis缓存层**
- [ ] 创建缓存服务 `backend/services/cache.py`
- [ ] Oxylabs数据添加Redis缓存 (TTL=1小时)
- [ ] API响应数据添加Redis缓存 (TTL=5分钟)
- [ ] 测试缓存命中/未命中

**任务1.2: 数据库连接池优化**
- [ ] 优化数据库连接池配置
- [ ] 增加pool_size到20
- [ ] 添加pool_pre_ping检查
- [ ] 测试连接性能

**任务1.3: 添加数据库索引**
- [ ] 分析现有查询模式
- [ ] 为常用查询字段添加索引
- [ ] 测试查询性能提升

**预期产出**: API响应时间降低50%，数据库压力降低90%

---

### Day 2: Scheduler持久化 + Redis缓存

**任务2.1: Scheduler改用PostgreSQL**
- [ ] 修改 `backend/scheduler/scheduler.py`
- [ ] 从 `MemoryJobStore` 改为 `SQLAlchemyJobStore`
- [ ] 配置连接到HK PostgreSQL
- [ ] 测试定时任务持久化

**任务2.2: Redis缓存Oxylabs数据**
- [ ] 创建缓存服务 `backend/services/cache.py`
- [ ] 为 `OxylabsClient.get_amazon_product` 添加缓存层
- [ ] 设置TTL = 1小时
- [ ] 测试缓存命中/未命中

**预期产出**: 定时任务持久化，API调用减少90%

---

### Day 3: 每日卡片数据模型

**任务3.1: 创建cards表**
```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200),
    category VARCHAR(50),
    content JSONB,
    analysis JSONB,
    amazon_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    is_published BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_cards_created_at ON cards(created_at DESC);
CREATE INDEX idx_cards_category ON cards(category);
CREATE INDEX idx_cards_published ON cards(is_published, published_at);
```

**任务3.2: SQLAlchemy模型**
- [ ] 创建 `backend/models/card.py`
- [ ] 定义Card模型
- [ ] 添加CRUD方法

**预期产出**: cards表创建完成，模型定义完成

---

### Day 4-5: 数据采集管道

**任务4.1: 复用OxylabsClient**
- [ ] 确认 `OxylabsClient` 正常工作
- [ ] 测试3个品类数据获取

**任务4.2: 创建卡片生成服务**
- [ ] 创建 `backend/services/card_generator.py`
- [ ] 实现 `fetch_category_data(category)` 函数
- [ ] 实现 `analyze_with_ai(category, data)` 函数
- [ ] 实现 `generate_card(category)` 函数

**任务4.3: 添加定时任务**
- [ ] 在 `scheduler/tasks.py` 添加 `generate_daily_cards()` 任务
- [ ] 配置每天8点执行
- [ ] 测试任务执行

**预期产出**: 每日自动生成3张卡片

---

## 📋 Week 2: API + 前端 + 部署

### Day 6: Cards API端点

**任务6.1: 创建cards API**
- [ ] 创建 `backend/api/cards.py`
- [ ] 实现 `GET /api/v1/cards/daily` - 获取今日卡片
- [ ] 实现 `GET /api/v1/cards/{id}` - 获取单张卡片
- [ ] 实现 `GET /api/v1/cards/history` - 历史卡片列表
- [ ] 实现 `POST /api/v1/cards/{id}/like` - 收藏功能

**任务6.2: 集成到主API**
- [ ] 在 `backend/api/__init__.py` 注册cards路由
- [ ] 测试所有端点

**预期产出**: Cards API可用

---

### Day 7-8: 前端卡片展示

**任务7.1: 创建卡片页面**
- [ ] 创建 `frontend/app/cards/page.tsx` - 卡片列表页
- [ ] 创建 `frontend/app/cards/[id]/page.tsx` - 卡片详情页
- [ ] 添加导航菜单

**任务7.2: 创建卡片组件**
- [ ] 创建 `frontend/components/cards/card.tsx` - 单张卡片
- [ ] 创建 `frontend/components/cards/grid.tsx` - 网格布局
- [ ] 使用Phase 0的HTML卡片样式

**任务7.3: API集成**
- [ ] 更新 `frontend/lib/api.ts` 添加cards API调用
- [ ] 实现数据获取逻辑
- [ ] 添加loading和error处理

**预期产出**: 前端正常展示卡片

---

### Day 9: 用户互动功能

**任务9.1: 收藏功能**
- [ ] 前端添加收藏按钮
- [ ] 实现收藏API调用
- [ ] 添加收藏列表页面

**任务9.2: 分享功能**
- [ ] 添加分享按钮
- [ ] 实现复制链接功能
- [ ] 生成分享摘要

**预期产出**: 用户可以收藏和分享卡片

---

### Day 10: 测试和部署

**任务10.1: 本地测试**
- [ ] 端到端测试完整流程
- [ ] 测试定时任务执行
- [ ] 测试API响应性能

**任务10.2: 生产部署**
- [ ] 更新HK服务器Docker容器
- [ ] 部署Frontend到Vercel
- [ ] 验证生产环境正常

**任务10.3: 监控验证**
- [ ] 检查API响应时间 (< 500ms)
- [ ] 检查数据库连接正常
- [ ] 检查定时任务执行日志

**预期产出**: 生产环境可用

---

## 🎯 成功标准

### Week 1结束时
- [x] Redis缓存层正常工作
- [x] API响应时间降低50%
- [x] Scheduler任务持久化
- [x] Oxylabs缓存生效 (90%命中率)
- [x] Cards表创建完成
- [x] 定时任务每天生成卡片
- [x] 继续使用阿里云PostgreSQL (稳定可靠)

### Week 2结束时
- [x] Cards API全部端点可用
- [x] 前端正常展示卡片
- [x] 用户可以收藏/分享
- [x] 生产环境部署完成
- [x] API响应时间 < 500ms

---

## 📁 新增文件清单

```
backend/
├── models/
│   └── card.py                 # 🆕 卡片模型
├── api/
│   └── cards.py                # 🆕 卡片API
├── services/
│   ├── card_generator.py       # 🆕 卡片生成
│   └── cache.py                # 🆕 缓存服务
└── migrations/
    └── create_cards_table.sql  # 🆕 数据库迁移

frontend/
├── app/
│   └── cards/
│       ├── page.tsx           # 🆕 卡片列表
│       └── [id]/
│           └── page.tsx       # 🆕 卡片详情
└── components/
    └── cards/
        ├── card.tsx           # 🆕 卡片组件
        └── grid.tsx           # 🆕 网格布局
```

---

## 🔄 修改文件清单

```
backend/
├── scheduler/scheduler.py      # 📝 改用SQLAlchemyJobStore
├── crawler/products/oxylabs_client.py  # 📝 添加缓存
└── api/__init__.py             # 📝 注册cards路由

frontend/
├── app/layout.tsx              # 📝 添加导航
└── lib/api.ts                  # 📝 添加cards API
```

---

## ⚡ 关键路径 (Critical Path)

```
Day 1: 性能优化 → 无阻塞，并行开发
        ↓
Day 2: Scheduler持久化 → 阻塞定时任务
        ↓
Day 3-5: 数据采集管道 → 阻塞前端展示
        ↓
Day 6-10: API + 前端 + 部署 → 并行开发
```

**优势**: 无需停机，Day 1优化可与其他工作并行

---

## 🚀 立即开始

**第1步**: 创建缓存服务 (Day 1) - 无需停机，立即可做

**第2步**: 我创建具体的优化代码

---

**确认后立即开始？**
