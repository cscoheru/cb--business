# OpenClaw核心架构设计

**文档版本**: 1.0
**创建日期**: 2026-03-13
**状态**: 设计阶段 - 待实施

---

## 架构概述

将OpenClaw定位为**中央数据流协调中心**，统一管理所有数据采集、AI分析和智能内容分发任务。

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Vercel     │  │   Admin UI   │  │   Mobile App │          │
│  │  Frontend    │  │  (Future)    │  │   (Future)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                            │
│  ┌────────────────────────────────────────────────┐              │
│  │         FastAPI (nginx-gateway)                │              │
│  │  - User Auth & Authorization                  │              │
│  │  - API Rate Limiting                           │              │
│  │  - Request Validation                          │              │
│  │  - Response Caching (Redis)                    │              │
│  └────────────────────────────────────────────────┘              │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              OPENCLAW CENTRAL COORDINATION LAYER                  │
│  ┌────────────────────────────────────────────────┐              │
│  │        OpenClaw Gateway (18789)                │              │
│  │  ┌────────────────────────────────────────┐    │              │
│  │  │  Channel Management System             │    │              │
│  │  │  • RSS Crawler Channel                  │    │              │
│  │  │  • Oxylabs Monitor Channel              │    │              │
│  │  │  • Google Trends Channel                │    │              │
│  │  │  • Content Classifier Channel           │    │              │
│  │  │  • Trend Discovery Channel              │    │              │
│  │  │  • Opportunity Scorer Channel           │    │              │
│  │  └────────────────────────────────────────┘    │              │
│  │  ┌────────────────────────────────────────┐    │              │
│  │  │  AI Analysis Engine (GLM-4 Plus)        │    │              │
│  │  │  • Content Classification               │    │              │
│  │  │  • Sentiment Analysis                   │    │              │
│  │  │  • Opportunity Scoring                  │    │              │
│  │  │  • Trend Prediction                     │    │              │
│  │  └────────────────────────────────────────┘    │              │
│  │  ┌────────────────────────────────────────┐    │              │
│  │  │  Scheduler & Orchestration              │    │              │
│  │  │  • Cron-based Scheduling                │    │              │
│  │  │  • Event-driven Triggers                │    │              │
│  │  │  • Retry Logic & Error Handling         │    │              │
│  │  └────────────────────────────────────────┘    │              │
│  └────────────────────────────────────────────────┘              │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCE LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  RSS Feeds   │  │   Oxylabs    │  │Google Trends │          │
│  │  (45 sources)│  │   API        │  │    API       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────┬─────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA STORAGE LAYER                           │
│  ┌────────────────────────────────────────────────┐              │
│  │         PostgreSQL (cbdb)                      │              │
│  │  • articles (raw + AI analyzed)                │              │
│  │  • cards (generated insights)                  │              │
│  │  • products (Oxylabs data + AI scored)         │              │
│  │  • keywords (trend graph)                      │              │
│  │  • trends (historical data)                    │              │
│  └────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## OpenClaw Channels设计

### Channel 1: RSS Crawler Channel
**文件**: `/root/.openclaw/channels/rss-crawler.js`
**调度**: 每2小时 (`0 */2 * * *`)
**超时**: 5分钟
**数据源**: 45个RSS资讯源

```javascript
/**
 * RSS Crawler Channel
 * 从45个RSS源采集电商行业文章
 * 批量调用AI进行内容分类
 * 写入PostgreSQL articles表
 */
```

### Channel 2: Oxylabs Product Monitor Channel
**文件**: `/root/.openclaw/channels/oxylabs-monitor.js`
**调度**: 每小时 (`0 * * * *`)
**超时**: 10分钟
**数据源**: Amazon产品数据 (12个类别)

```javascript
/**
 * Oxylabs Product Monitor
 * 监控12个产品类别的Amazon数据
 * AI分析产品机会评分
 * 写入PostgreSQL products表
 */
```

### Channel 3: Content Classifier Channel
**文件**: `/root/.openclaw/channels/content-classifier.js`
**调度**: 每30分钟 (`*/30 * * * *`)
**超时**: 5分钟

```javascript
/**
 * Content Classifier
 * 获取未分类的文章/产品
 * 批量调用GLM-4 Plus进行分类
 * 更新分类字段: channel, category, keywords, opportunity_score
 */
```

### Channel 4: Trend Discovery Channel
**文件**: `/root/.openclaw/channels/trend-discovery.js`
**调度**: 每6小时 (`0 */6 * * *`)
**超时**: 10分钟

```javascript
/**
 * Trend Discovery & Opportunity Scoring
 * 分析最近7天的高机会文章
 * 发现新兴关键词
 * 识别上升产品
 * 生成AI市场洞察
 */
```

---

## 三大数据流管道

### Flow 1: 文章采集管道

```
OpenClaw RSS Channel (每2小时)
  ↓
45个RSS源 → Python爬虫
  ↓
FastAPI batch endpoint → 原始文章
  ↓
Content Classifier Channel (每30分钟)
  ↓
GLM-4 Plus AI分析:
  - content_theme (opportunity/risk/policy/guide)
  - region (north_america/southeast_asia等)
  - platform (amazon/shopee等)
  - keywords (5-10个标签)
  - opportunity_score (0-1分数)
  ↓
PostgreSQL articles表
  ↓
FastAPI /api/v1/crawler/articles
  ↓
前端文章流
```

### Flow 2: 产品监控管道

```
OpenClaw Oxylabs Channel (每小时)
  ↓
12个类别 → Oxylabs API
  ↓
FastAPI batch endpoint → 原始产品
  ↓
GLM-4 Plus AI分析:
  - category classification
  - price segmentation
  - opportunity scoring
  - competitor analysis
  ↓
PostgreSQL products表
  ↓
Card Generator (使用AI分析结果)
  ↓
生成市场洞察卡片
  ↓
FastAPI /api/v1/cards/daily
  ↓
前端商机卡片
```

### Flow 3: 趋势发现管道

```
OpenClaw Trend Discovery Channel (每6小时)
  ↓
查询PostgreSQL最近高opportunity_score文章
  ↓
分析关键词频率 → 发现新兴趋势
  ↓
识别上升产品 (价格下降/评分上升)
  ↓
GLM-4 Plus生成市场洞察
  ↓
综合评分商业机会
  ↓
PostgreSQL trends表 + keywords表
  ↓
FastAPI /api/v1/trends/keywords
  ↓
前端趋势展示
```

---

## 组件职责划分

| 组件 | 职责 | 不负责 |
|------|------|--------|
| **OpenClaw** | 调度、协调、AI分析 | 用户认证、API网关 |
| **FastAPI** | API网关、认证、业务逻辑 | 数据采集、定时调度 |
| **PostgreSQL** | 数据存储、完整性 | AI分析、外部API调用 |
| **Redis** | 缓存、会话 | 持久化存储 |

---

## 关键接口设计

### OpenClaw → FastAPI (批量写入)

```python
# backend/api/batch_operations.py

@router.post("/articles")
async def batch_create_articles(request: BatchArticleRequest):
    """OpenClaw批量写入文章"""
    pass

@router.post("/products")
async def batch_create_products(request: BatchProductRequest):
    """OpenClaw批量写入产品"""
    pass

@router.post("/classifications")
async def batch_update_classifications(request: BatchClassificationUpdate):
    """OpenClaw批量更新AI分类"""
    pass

@router.get("/unclassified")
async def get_unclassified_items(type: str = "all", limit: int = 100):
    """OpenClaw获取待分类内容"""
    pass
```

### FastAPI → OpenClaw (手动触发)

```python
# backend/api/openclaw_integration.py

OPENCLAW_BASE_URL = "http://103.59.103.85:18789"

@router.post("/trigger/{channel_id}")
async def trigger_openclaw_channel(channel_id: str):
    """手动触发OpenClaw Channel"""
    pass

@router.get("/channels/status")
async def get_channels_status():
    """获取所有Channel状态"""
    pass
```

---

## 迁移路径

### Phase 1: 双轨运行 (Week 1)
- APScheduler继续运行
- OpenClaw Channels部署为"影子模式"
- 比较数据质量，验证一致性
- **零生产影响**

### Phase 2: 逐步迁移 (Week 2-3)
1. 迁移RSS爬取 → OpenClaw
2. 监控48小时
3. 迁移产品监控 → OpenClaw
4. 监控48小时
5. 迁移卡片生成 → OpenClaw

### Phase 3: 完全切换 (Week 4)
- 禁用APScheduler
- 删除旧调度器代码
- 激活DataSourceRegistry (与OpenClaw集成)

### Phase 4: 优化 (Week 5+)
- 调优OpenClaw调度时间
- 优化AI提示词
- 添加更多数据源Channel

---

## 实施文件清单

### 需要创建的文件

| 文件 | 用途 | 优先级 |
|------|------|--------|
| `/root/.openclaw/channels/rss-crawler.js` | RSS爬虫Channel | P0 |
| `/root/.openclaw/channels/oxylabs-monitor.js` | 产品监控Channel | P0 |
| `/root/.openclaw/channels/content-classifier.js` | 内容分类Channel | P1 |
| `/root/.openclaw/channels/trend-discovery.js` | 趋势发现Channel | P1 |
| `backend/api/batch_operations.py` | 批量操作API | P0 |
| `backend/api/openclaw_integration.py` | OpenClaw集成API | P1 |
| `backend/services/openclaw_client.py` | OpenClaw客户端封装 | P1 |

### 需要修改的文件

| 文件 | 修改内容 | 优先级 |
|------|---------|--------|
| `backend/api/__init__.py` | 移除APScheduler启动代码 | P2 |
| `backend/scheduler/scheduler.py` | 标记为废弃 | P2 |
| `backend/main.py` | 移除调度器初始化 | P2 |
| `backend/services/card_generator.py` | 使用OpenClaw数据 | P1 |

---

## 监控与告警

### OpenClaw健康检查
```bash
# 检查OpenClaw状态
curl http://103.59.103.85:18789/health

# 检查Channel状态
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://103.59.103.85:18789/api/channels

# 查看Channel日志
openclaw logs <channel-id>
```

### 数据新鲜度监控
```python
# 检查数据是否过期
async def check_data_freshness():
    latest_article = await db.execute(
        select(Article).order_by(desc(Article.created_at)).limit(1)
    )

    if latest_article.created_at < datetime.now() - timedelta(hours=3):
        # 触发告警并手动触发Channel
        await trigger_openclaw_channel("rss-crawler")
```

---

## 回滚策略

### 立即回滚 (关键问题)
```bash
# 禁用OpenClaw Channels
ssh hk-jump
cd ~/.openclaw
# 编辑channels.json，设置所有"enabled": false
systemctl restart openclaw

# 重新启用APScheduler
cd /opt/cb-business-repo/backend
git checkout main.py
docker restart cb-business-api
```

### 渐进回滚 (小问题)
- 只禁用有问题的Channel
- APScheduler继续处理该任务
- 修复OpenClaw Channel后重新迁移

---

## 成功标准

### 技术指标
- OpenClaw Channels成功率 > 95%
- 数据新鲜度 < 2小时
- AI分类准确率 > 85%
- API响应时间 < 500ms (p95)
- 零数据丢失

### 业务指标
- 用户体验不变或改善
- 支持工单无增加
- 数据更新更快 (2h → 30min)
- AI洞察更准确 (统一GLM-4 Plus)
- 运维成本降低

---

**预计实施时间**: 4-5周
**风险评估**: 中等 (有完整回滚方案)
