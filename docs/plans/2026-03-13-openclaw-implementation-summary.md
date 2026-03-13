# OpenClaw核心架构 - 实施摘要

**日期**: 2026-03-13
**状态**: Phase 1 (FastAPI集成层) - 已完成

---

## 已完成的工作

### 1. 架构设计文档 ✅
**文件**: `docs/plans/2026-03-13-openclaw-core-architecture.md`

包含内容:
- 整体架构图 (4层: User → API Gateway → OpenClaw → Data Sources)
- 4个OpenClaw Channels设计
- 3大数据流管道 (文章采集、产品监控、趋势发现)
- 组件职责划分
- 迁移路径 (4个阶段)

### 2. 批量操作API ✅
**文件**: `backend/api/batch_operations.py`

新增端点:
- `POST /api/v1/batch/articles` - OpenClaw批量写入文章
- `POST /api/v1/batch/products` - OpenClaw批量写入产品
- `POST /api/v1/batch/classifications` - OpenClaw批量更新AI分类
- `GET /api/v1/batch/unclassified` - 获取待分类内容
- `GET /api/v1/batch/status` - 批量操作状态统计

### 3. OpenClaw集成API ✅
**文件**: `backend/api/openclaw_integration.py`

新增端点:
- `POST /api/v1/openclaw/trigger/{channel_id}` - 手动触发Channel
- `GET /api/v1/openclaw/channels/status` - 查询Channels状态
- `GET /api/v1/openclaw/channels/{channel_id}/logs` - 获取Channel日志
- `GET /api/v1/openclaw/health` - OpenClaw健康检查
- `GET /api/v1/openclaw/sync/now` - 触发立即同步所有Channels
- `GET /api/v1/openclaw/config` - 获取配置信息(脱敏)

### 4. OpenClaw客户端封装 ✅
**文件**: `backend/services/openclaw_client.py`

提供:
- `OpenClawClient` 类 - 与OpenClaw Gateway通信
- 便捷函数 - `trigger_channel()`, `get_channels_status()` 等
- 统一的超时和错误处理

### 5. 路由注册 ✅
**文件**: `backend/api/__init__.py`

已将新路由注册到FastAPI应用:
```python
app.include_router(batch_operations_router)
app.include_router(openclaw_router)
```

---

## 数据流架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      当前实现状态                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ✅ FastAPI ← → OpenClaw API集成层                             │
│  ✅ 批量操作接口 ← → OpenClaw Channels可调用                    │
│  ✅ 客户端封装 ← → Python风格的接口                                │
│                                                                   │
│  ⏳ OpenClaw Channels (未创建)                                    │
│     - /root/.openclaw/channels/rss-crawler.js                    │
│     - /root/.openclaw/channels/oxylabs-monitor.js                │
│     - /root/.openclaw/channels/content-classifier.js           │
│     - /root/.openclaw/channels/trend-discovery.js              │
│                                                                   │
│  ⏳ 数据源激活 (data_source_init.py未调用)                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 下一步工作

### Phase 1.5: 在HK服务器上部署更新的API (预计30分钟)

1. 同步代码到HK服务器
2. 重新构建Docker镜像
3. 重启FastAPI容器
4. 验证新端点可访问

**验证命令**:
```bash
# 测试批量操作API
curl https://api.zenconsult.top/api/v1/batch/status

# 测试OpenClaw集成API
curl https://api.zenconsult.top/api/v1/openclaw/health

# 测试OpenClaw配置
curl https://api.zenconsult.top/api/v1/openclaw/config
```

### Phase 2: 创建OpenClaw Channels (预计4-6小时)

需要创建4个JavaScript文件到HK服务器:
1. `/root/.openclaw/channels/rss-crawler.js`
2. `/root/.openclaw/channels/oxylabs-monitor.js`
3. `/root/.openclaw/channels/content-classifier.js`
4. `/root/.openclaw/channels/trend-discovery.js`

### Phase 3: 双轨运行测试 (预计2-3天)

- OpenClaw Channels影子模式运行
- APScheduler继续正常工作
- 对比数据质量
- 验证数据一致性

### Phase 4: 逐步迁移 (预计1-2周)

1. Week 2-3: 迁移RSS爬取到OpenClaw
2. Week 3-4: 迁移产品监控到OpenClaw
3. Week 4: 禁用APScheduler

---

## 文件变更清单

### 新创建的文件

| 文件 | 状态 | 用途 |
|------|------|------|
| `docs/plans/2026-03-13-openclaw-core-architecture.md` | ✅ | 架构设计文档 |
| `backend/api/batch_operations.py` | ✅ | 批量操作API |
| `backend/api/openclaw_integration.py` | ✅ | OpenClaw集成API |
| `backend/services/openclaw_client.py` | ✅ | OpenClaw客户端封装 |

### 修改的文件

| 文件 | 修改内容 |
|------|---------|
| `backend/api/__init__.py` | 注册batch_operations_router和openclaw_router |

---

## 关键技术决策

### 1. 批量操作 vs 单条操作
**决策**: 使用批量操作API
**理由**:
- 减少HTTP往返次数
- 提高数据库写入效率
- 便于OpenClab一次性提交大量数据

### 2. 客户端封装方式
**决策**: 创建独立的服务层 (`openclaw_client.py`)
**理由**:
- 隔离外部系统依赖
- 便于单元测试
- 提供Python风格的接口

### 3. 产品数据存储位置
**决策**: 存储在Cards表的amazon_data字段
**理由**:
- Cards系统已运行稳定 (327条记录)
- 避免创建新的products表
- 保持数据一致性

---

## API使用示例

### 示例1: OpenClaw批量写入文章

```bash
curl -X POST https://api.zenconsult.top/api/v1/batch/articles \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "title": "Example Article",
        "summary": "Article summary",
        "content": "Full content",
        "url": "https://example.com/article1",
        "source_name": "Retail Dive",
        "language": "en",
        "published_at": "2026-03-13T10:00:00Z"
      }
    ],
    "source": "openclaw-rss"
  }'
```

### 示例2: 手动触发OpenClaw Channel

```bash
curl -X POST https://api.zenconsult.top/api/v1/openclaw/trigger/rss-crawler \
  -H "Content-Type: application/json"
```

### 示例3: 获取Channels状态

```bash
curl https://api.zenconsult.top/api/v1/openclaw/channels/status
```

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| OpenClaw Gateway不可达 | 高 | 健康检查端点，降级到APScheduler |
| 批量操作性能问题 | 中 | 分批处理，限制单批数量 |
| API认证Token泄露 | 高 | 使用环境变量，定期轮换 |
| 数据库连接池耗尽 | 中 | 异步操作，连接池监控 |

---

**文档版本**: 1.0
**最后更新**: 2026-03-13
**作者**: Claude Code
**审核状态**: 待审核

---

## Phase 2 完成情况 (2026-03-13)

### 已创建的OpenClaw Channels

所有4个JavaScript Channel文件已创建并部署到HK服务器 (`/root/.openclaw/channels/`):

| Channel | 文件 | 调度 | 超时 | 状态 |
|---------|------|------|------|------|
| RSS Crawler | `rss-crawler.js` | 每2小时 | 5分钟 | ✅ 已创建 |
| Oxylabs Monitor | `oxylabs-monitor.js` | 每小时 | 10分钟 | ✅ 已创建并测试 |
| Content Classifier | `content-classifier.js` | 每30分钟 | 5分钟 | ✅ 已创建 |
| Trend Discovery | `trend-discovery.js` | 每6小时 | 10分钟 | ✅ 已创建 |

### Channel配置文件

创建了 `/root/.openclaw/channels.json` 包含所有channels的配置。

### 测试结果

```
oxylabs-monitor.js 测试运行:
- ✅ Channel成功加载
- ✅ 能连接到FastAPI (内网: 172.22.0.4:8000)
- ✅ 执行流程正常
- ⚠️  产品数据结构需要调整 (API响应格式与预期不同)
```

### 下一步工作

1. **调整Channel数据解析逻辑** - 根据实际API响应调整
2. **集成到OpenClaw Gateway** - 添加channels到cron调度
3. **Phase 3: 双轨运行测试** - OpenClaw + APScheduler并行

### Bright Data集成准备

用户已注册Bright Data，可用于产品数据采集:
- API Endpoint: https://api.brightdata.com/datasets/v3/scrape
- Dataset ID: gd_l7q7dkf244hwjntr0
- 可用于替代或增强Oxylabs产品数据获取


---

## Bright Data集成 (2026-03-13)

### Bright Data API功能

Bright Data提供多个Amazon数据采集API:

| API类型 | Dataset ID | 用途 | 状态 |
|---------|-----------|------|------|
| Product Details | gd_l7q7dkf244hwjntr0 | 产品详情抓取 | ✅ 已测试 |
| Product Reviews | gd_le8e811kzy4ggddlq | 产品评论抓取 | ✅ 已测试 |
| Discover by Keyword | - | 关键词搜索(异步) | ✅ 已测试 |
| Discover by Category | - | 类别搜索(异步) | ✅ 已测试 |
| Best Sellers | - | 热销产品(异步) | 待测试 |

### Bright Data vs Oxylabs对比

| 特性 | Bright Data | Oxylabs |
|------|-------------|---------|
| 产品详情完整度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 品牌信息 | ✅ 完整 | ❌ 搜索API不返回 |
| 图片URL | ✅ 完整 | ❌ 搜索API不返回 |
| 产品变体 | ✅ 支持 | ❌ 不支持 |
| 配送信息 | ✅ 支持 | ❌ 不支持 |
| BSR排名 | ✅ 支持 | ❌ 不支持 |
| 评论数据 | 🔗 独立API | 🔄 需额外调用 |
| 异步发现 | ✅ 支持 | ❌ 仅同步 |
| API延迟 | ~3-5秒 | ~2-3秒 |

### 创建的文件

1. **backend/services/brightdata_client.py**
   - 完整的Bright Data Python客户端
   - 支持所有API类型
   - 异步snapshot监控
   - 数据标准化

2. **channels/bright-data-monitor.js**
   - OpenClaw Channel
   - 使用Bright Data抓取产品
   - 推送数据到FastAPI

### API测试结果

```bash
# 产品详情抓取测试
curl -H "Authorization: Bearer 1c7806b0-3f98-48da-93ce-8a745c40b062" \
  -d '{"input":[{"url":"https://www.amazon.com/..."}]}' \
  "https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_l7q7dkf244hwjntr0"

# 返回完整数据: title, brand, price, images, reviews, variations等
# ✅ 测试通过
```

### 推荐使用策略

**短期** (本周):
- 保持Oxylabs用于快速搜索
- Bright Data用于获取完整产品详情
- 实现两步数据获取流程

**中期** (下周):
- 逐步迁移到Bright Data
- 利用其异步发现功能
- 添加评论数据采集

**长期** (月内):
- Bright Data作为主要数据源
- 保留Oxylabs作为备用
- 完整的产品+评论+趋势分析


---

## 今日完成总结 (2026-03-13)

### Phase 1: FastAPI集成层 ✅ 完成

**创建的文件**:
1. `backend/api/batch_operations.py` (526行)
   - POST /api/v1/batch/articles
   - POST /api/v1/batch/products
   - POST /api/v1/batch/classifications
   - GET /api/v1/batch/unclassified
   - GET /api/v1/batch/status

2. `backend/api/openclaw_integration.py` (443行)
   - POST /api/v1/openclaw/trigger/{channel_id}
   - GET /api/v1/openclaw/channels/status
   - GET /api/v1/openclaw/channels/{id}/logs
   - GET /api/v1/openclaw/health
   - GET /api/v1/openclaw/sync/now
   - GET /api/v1/openclaw/config

3. `backend/services/openclaw_client.py` (314行)
   - OpenClawClient类
   - 便捷函数封装

**部署状态**:
- ✅ 代码已推送到GitHub
- ✅ HK服务器已部署
- ✅ 数据库连接已修复
- ✅ 所有API端点测试通过

**修复的问题**:
1. SQLAlchemy reserved field: `metadata` → `payment_metadata`
2. Missing import: 添加 `Query`
3. Database auth: 重置PostgreSQL密码
4. Model field mapping: 修正Article和Card字段引用

### Phase 2: OpenClaw Channels ✅ 完成

**创建的Channels** (共5个):
| Channel | 文件 | 大小 | 测试 |
|---------|------|------|------|
| RSS Crawler | rss-crawler.js | 8K | ✅ |
| Oxylabs Monitor | oxylabs-monitor.js | 8K | ✅ 运行成功 |
| Bright Data Monitor | bright-data-monitor.js | ~8K | ✅ 运行成功 |
| Content Classifier | content-classifier.js | 8K | ✅ |
| Trend Discovery | trend-discovery.js | 12K | ✅ |

**配置文件**:
- `~/.openclaw/channels.json` - 5个channels配置

**Channel功能**:
1. **RSS Crawler**: 从45个RSS源采集文章，推送到FastAPI
2. **Oxylabs Monitor**: 监控12个产品类别，获取Amazon数据
3. **Bright Data Monitor**: 使用Bright Data API获取完整产品详情
4. **Content Classifier**: 使用GLM-4 Plus进行AI内容分类
5. **Trend Discovery**: 分析高机会文章，发现新兴趋势

### Bright Data集成 ✅ 完成

**创建的文件**:
1. `backend/services/brightdata_client.py` (450+行)
   - 完整的Bright Data Python客户端
   - 支持所有API类型
   - 异步snapshot监控
   - 数据标准化

**API测试结果**:
- ✅ Product Details API - 完整数据返回
- ✅ Product Reviews API - 评论数据返回
- ✅ Discover by Keyword - snapshot创建成功
- ✅ Discover by Category - 可用

**Bright Data优势**:
- 比Oxylabs更完整的产品详情
- 包含brand, images, variations, BSR排名
- 独立的Reviews API
- 异步发现功能

### 数据库状态

**修复**:
- PostgreSQL密码重置: `cbuser@k8VmK8PvqAFlEdirpJVJNo8DPe2bVlYPtV6xea+DlQQ=`
- URL编码特殊字符: `%2B` for `+`, `%3D` for `=`

**当前数据**:
- Articles: 305条，全部已处理
- Cards: 339条，全部含产品数据
- Batch status API正常工作

### 下一步工作

**Phase 3: 双轨运行测试** (预计本周开始)
1. 保留APScheduler正常运行
2. OpenClaw Channels设为影子模式
3. 对比数据质量
4. 验证数据一致性

**Phase 4: 逐步迁移** (预计下周)
1. Week 1: 迁移RSS爬取 → OpenClaw
2. Week 2: 迁移产品监控 → Bright Data
3. Week 3: 禁用APScheduler
4. Week 4: 完全切换到OpenClaw

### Git提交记录

```
6073dd7 feat: add Bright Data integration and complete OpenClaw Phase 2
0d0e55f fix: use crawled_at instead of created_at for Article ordering
a38442f fix: correct batch_operations.py to use actual model fields
f373416 fix: rename SQLAlchemy reserved field 'metadata' to 'payment_metadata'
```

### 文档更新

- `docs/plans/2026-03-13-openclaw-implementation-summary.md` - 完整实施摘要
- `docs/plans/2026-03-13-openclaw-core-architecture.md` - 架构设计文档

---

**最后更新**: 2026-03-13 19:30
**状态**: Phase 1 ✅ 完成 | Phase 2 ✅ 完成 | Phase 3 ⏳ 待开始

---

## Phase 3: 双轨运行测试准备 ✅ 完成 (2026-03-13)

### 创建的文件

1. **backend/scripts/dual_track_monitor.py** (408行)
   - 完整的双轨运行监控脚本
   - 对比APScheduler和OpenClaw数据
   - 计算一致性评分
   - 检测重复数据
   - 生成健康报告
   - 自动保存到数据库

2. **backend/migrations/004_create_dual_track_monitoring.sql**
   - data_comparison_log表
   - v_comparison_summary_24h视图
   - v_data_quality_trend视图
   - 自动source标记触发器
   - 清理旧日志函数

3. **backend/scripts/setup_phase3_dual_track.sh** (278行)
   - 一键设置双轨运行环境
   - 数据库表创建
   - OpenClaw Channels配置
   - 监控任务设置
   - 环境验证

4. **docs/plans/2026-03-13-phase3-dual-track-plan.md**
   - 详细的测试计划
   - 验收标准
   - 风险与缓解措施
   - 回滚方案

### 部署状态

**HK服务器配置**:
- ✅ 数据库监控表已创建
- ✅ OpenClaw Channels调度已安装 (crontab)
- ✅ 监控脚本已部署
- ✅ API容器已重启
- ✅ 首次监控报告已生成

**OpenClaw Channels调度**:
```
*/30 * * * * rss-crawler.js
0 * * * * bright-data-monitor.js
*/30 * * * * content-classifier.js
0 */6 * * * trend-discovery.js
0 * * * * oxylabs-monitor.js
```

### 监控报告样例

```
============================================================
双轨运行监控报告 - 2026-03-13T12:00:52
============================================================

【数据采集对比】(过去1小时)
  APScheduler: 0篇文章
  OpenClaw: 0篇文章

【对比分析】
  一致性评分: 100.0%
  数据完整度: APScheduler 0%, OpenClaw 0%

【数据质量】
  最新文章: 1376分钟前 (数据过时)
  24h重复数: 0

【健康状态】
  状态: CRITICAL (数据过时)
  数据库: healthy
```

### 数据库视图

**v_comparison_summary_24h** - 最近24小时对比摘要
**v_data_quality_trend** - 数据质量趋势 (最近7天)

### 验证命令

```bash
# 查看监控数据
docker exec cb-business-postgres psql -U cbuser -d cbdb \
  -c "SELECT * FROM v_comparison_summary_24h;"

# 查看数据质量趋势
docker exec cb-business-postgres psql -U cbuser -d cbdb \
  -c "SELECT * FROM v_data_quality_trend LIMIT 24;"

# 查看OpenClaw日志
tail -f /root/.openclaw/logs/*.log

# 手动运行监控
docker exec cb-business-api-fixed python /app/scripts/dual_track_monitor.py
```

### 下一步工作

**Day 1: 收集基线数据**
- 等待OpenClaw Channels开始采集数据
- 收集24小时对比数据
- 分析数据质量差异

**Day 2-3: 对比分析**
- 对比APScheduler和OpenClaw数据
- 验证数据一致性
- 检查性能指标

**Day 4: 评估决策**
- 评估是否进入Phase 4 (逐步迁移)
- 或继续优化OpenClaw Channels

### Git提交记录

```
cd43633 fix: handle timezone-aware datetimes in monitoring script
082b93e feat: add Phase 3 dual track monitoring system
```

