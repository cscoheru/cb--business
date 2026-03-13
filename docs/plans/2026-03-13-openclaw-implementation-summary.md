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
