# OpenClaw回调端点集成文档

**版本**: 1.0
**完成日期**: 2026-03-14

## 概述

OpenClaw回调端点实现了OpenClaw Gateway与FastAPI之间的双向通信，当OpenClaw Channel完成数据采集任务后，可以自动回调FastAPI通知结果，实现数据采集的闭环。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenClaw Gateway                        │
│                    (HK服务器: 端口18789)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Channel执行引擎                                        │  │
│  │  • RSS Crawler (每2小时)                               │  │
│  │  • Oxylabs Monitor (每小时)                             │  │
│  │  • Content Classifier (每30分钟)                        │  │
│  │  • Trend Discovery (每6小时)                            │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                         │ 执行完成                            │
│                         ▼                                    │
│              ┌─────────────────────┐                       │
│              │  HTTP POST Callback │                       │
│              └─────────────────────┘                       │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Container                        │
│                   (cb-network: 端口8000)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/openclaw/callback/channel                │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │ 1. 验证回调数据                                   │   │  │
│  │  │ 2. 记录到 crawl_logs 表                           │   │  │
│  │  │ 3. 更新 DataCollectionTask                         │   │  │
│  │  │ 4. 触发智能编排服务处理结果                         │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  智能编排服务 (SmartOrchestrator)                      │  │
│  │  • 分析采集结果                                        │  │
│  │  • 更新商机置信度                                      │  │
│  │  • 检查是否需要更多数据                                │  │
│  │  • 执行状态自动演进                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## API端点

### 1. Channel回调端点

**端点**: `POST /api/v1/openclaw/callback/channel`

**用途**: 接收OpenClaw Channel执行完成的通知

**请求格式**:
```json
{
  "channel_id": "rss-crawler",
  "execution_id": "exec-1234567890",
  "status": "success",
  "started_at": "2026-03-14T10:00:00Z",
  "completed_at": "2026-03-14T10:05:00Z",
  "duration_ms": 300000,
  "result": {
    "total_fetched": 70,
    "total_pushed": 70,
    "sources": 5
  },
  "error": null,
  "stats": {
    "sources": 5,
    "successful": 4,
    "failed": 1
  }
}
```

**字段说明**:
- `channel_id`: 执行的Channel ID
- `execution_id`: 唯一的执行ID
- `status`: 执行状态 (`success`, `failed`, `partial`)
- `result`: 成功时的执行结果
- `error`: 失败时的错误信息
- `stats`: 统计信息（采集数量、成功率等）

**响应格式**:
```json
{
  "success": true,
  "message": "Callback processed successfully",
  "processed": true
}
```

### 2. 回调历史端点

**端点**: `GET /api/v1/openclaw/callback/history`

**参数**:
- `channel_id` (可选): 过滤特定Channel
- `limit` (可选): 返回记录数 (默认: 20)

**响应格式**:
```json
{
  "success": true,
  "count": 5,
  "history": [
    {
      "source": "openclaw-rss-crawler",
      "status": "success",
      "articles_count": 70,
      "error_message": null,
      "completed_at": "2026-03-14T10:05:00+00:00"
    }
  ]
}
```

## 数据库表

### crawl_logs

记录所有Channel执行历史：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| source | String(100) | Channel标识 (如 `openclaw-rss-crawler`) |
| status | String(20) | 状态 (`success`, `failed`, `running`) |
| articles_count | Integer | 采集的文章/产品数量 |
| error_message | Text | 错误信息 (如果失败) |
| started_at | DateTime | 开始时间 |
| completed_at | DateTime | 完成时间 |

### business_opportunities.data_collection_tasks

数据采集任务表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| opportunity_id | UUID | 关联的商机ID |
| task_type | String | 任务类型 (`market_scan`, `price_analysis`, 等) |
| status | String | 状态 (`pending`, `running`, `completed`, `failed`) |
| result | JSONB | 采集结果数据 |
| error_message | Text | 错误信息 |
| ai_request | JSONB | AI原始请求 (包含execution_id) |

## 测试

### 手动测试

```bash
# 测试成功回调
curl -X POST https://api.zenconsult.top/api/v1/openclaw/callback/channel \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "rss-crawler",
    "execution_id": "exec-test-123",
    "status": "success",
    "started_at": "2026-03-14T10:00:00Z",
    "completed_at": "2026-03-14T10:05:00Z",
    "duration_ms": 300000,
    "result": {"total_fetched": 10},
    "stats": {"sources": 5}
  }'

# 查询回调历史
curl https://api.zenconsult.top/api/v1/openclaw/callback/history?limit=10
```

### 自动化测试

运行测试脚本：
```bash
cd backend/tests
chmod +x test_openclaw_callback.sh
./test_openclaw_callback.sh
```

## 部署状态

### ✅ 已完成

1. **回调端点实现** - `backend/api/openclaw_integration.py`
2. **数据库记录** - 自动记录到 `crawl_logs` 表
3. **任务状态更新** - 更新 `DataCollectionTask`
4. **智能编排集成** - 触发后续处理
5. **历史记录查询** - 支持按Channel过滤
6. **测试验证** - 本地和HK服务器测试通过

### 📊 测试结果

- ✅ 成功回调: 正常记录到数据库
- ✅ 失败回调: 正确记录错误信息
- ✅ 历史查询: 返回正确的历史记录
- ✅ Channel过滤: 按Channel ID过滤正常工作

## 后续优化

### 短期 (1周内)

1. **签名验证**: 添加回调签名验证，确保回调来自OpenClaw Gateway
2. **重试机制**: 如果回调失败，OpenClaw Gateway应该有重试机制
3. **性能监控**: 记录回调处理时间，监控性能

### 中期 (2-4周)

4. **实时通知**: 使用WebSocket实时推送Channel执行状态
5. **批量回调**: 支持批量Channel执行结果的批量回调
6. **错误分析**: 分析失败回调，识别常见问题

### 长期 (1-2月)

7. **自适应调度**: 根据Channel历史成功率动态调整调度频率
8. **预测性维护**: 基于历史数据预测Channel可能失败的时间

## 相关文件

- **API端点**: `backend/api/openclaw_integration.py`
- **智能编排**: `backend/services/smart_orchestrator.py`
- **数据库模型**: `backend/models/article.py` (CrawlLog)
- **测试脚本**: `backend/tests/test_openclaw_callback.sh`

---

**维护者**: Claude Code
**最后更新**: 2026-03-14
