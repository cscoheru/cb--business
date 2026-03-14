# AI-OpenClaw 通信协议设计

## 概述

本文档定义了AI分析器与OpenClaw采集系统之间的通信协议，实现智能联盟的数据交互。

## 协议原则

1. **单向请求**: AI发起请求，OpenClaw执行并返回结果
2. **JSON格式**: 所有消息使用JSON格式
3. **异步处理**: 采集任务异步执行，通过回调通知完成
4. **错误容忍**: 采集失败不应阻塞系统运行
5. **数据质量**: 采集结果包含质量评估元数据

---

## 消息格式定义

### 1. 数据采集请求 (AI → OpenClaw)

```json
{
  "version": "1.0",
  "request_id": "uuid-v4",
  "timestamp": "2025-03-13T10:00:00Z",
  "priority": "high|medium|low",

  "opportunity": {
    "id": "商机ID",
    "type": "product|policy|platform|...",
    "title": "商机标题"
  },

  "ai_request": {
    "question": "AI想回答的问题",
    "purpose": "验证什么假设",
    "context": {
      "current_confidence": 0.6,
      "key_assumptions": ["假设1", "假设2"],
      "previous_findings": "之前的发现"
    }
  },

  "data_needed": {
    "type": "采集类型",
    "scope": {
      "brand": "品牌名（可选）",
      "region": "地区代码（可选）",
      "category": "品类（可选）",
      "platform": "平台名（可选）",
      "keywords": ["关键词1", "关键词2"]
    },

    "constraints": {
      "sample_size": 50,
      "time_range": "last_30_days",
      "quality_threshold": 0.8,
      "filters": [
        {"field": "verified_purchase", "value": true},
        {"field": "min_rating", "value": 3.5}
      ]
    },

    "sampling_strategy": {
      "method": "representative|random|stratified",
      "layers": [
        {
          "name": "高评分产品",
          "criteria": {"rating": "4.5-5.0"},
          "sample_size": 15
        }
      ]
    }
  },

  "expected_outcome": {
    "format": "structured|raw",
    "key_fields": ["字段1", "字段2"],
    "aggregation": "itemized|summary|both",
    "max_items": 100
  },

  "callback": {
    "url": "https://api.zenconsult.top/api/v1/opportunities/callback",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer token"
    }
  }
}
```

### 2. 采集结果 (OpenClaw → AI)

```json
{
  "version": "1.0",
  "request_id": "uuid-v4",
  "task_id": "openclaw-task-id",
  "timestamp": "2025-03-13T10:05:00Z",

  "status": "completed|partial|failed",

  "result": {
    "summary": {
      "total_items": 245,
      "successful_items": 240,
      "quality_score": 0.85,
      "completeness": 0.92,
      "data_sources": ["Amazon Reviews", "Shopee Products"],
      "collection_duration_seconds": 45
    },

    "data": [
      {
        "id": "item-1",
        "source": "amazon_reviews",
        "content": {...},
        "metadata": {
          "collected_at": "2025-03-13T10:02:00Z",
          "confidence": 0.9
        }
      }
    ],

    "aggregated": {
      "sentiment_distribution": {
        "positive": 0.75,
        "neutral": 0.15,
        "negative": 0.10
      },
      "key_metrics": {
        "avg_rating": 4.3,
        "avg_price": 25.99,
        "top_keywords": ["质量好", "性价比高", "物流快"]
      }
    }
  },

  "metadata": {
    "channels_used": ["amazon-reviews-channel"],
    "api_calls": 50,
    "cost_estimate": "$0.50",
    "limitations": [
      "部分产品无评论",
      "只能获取近6个月数据"
    ],
    "warnings": [
      "Anker品牌部分产品数据缺失"
    ]
  }
}
```

### 3. 错误响应 (OpenClaw → AI)

```json
{
  "version": "1.0",
  "request_id": "uuid-v4",
  "task_id": "openclaw-task-id",
  "timestamp": "2025-03-13T10:05:00Z",

  "status": "failed",

  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API调用频率超限",
    "details": {
      "retry_after": 3600,
      "suggested_action": "1小时后重试"
    }
  },

  "partial_result": {
    "has_partial_data": true,
    "data_items": 10,
    "data": [...]
  }
}
```

### 4. AI反馈 (AI → OpenClaw)

```json
{
  "version": "1.0",
  "request_id": "uuid-v4",
  "task_id": "openclaw-task-id",
  "timestamp": "2025-03-13T10:10:00Z",

  "feedback": {
    "usefulness_score": 0.85,
    "quality_rating": "excellent|good|fair|poor",
    "relevance": "high|medium|low",

    "impact": {
      "confidence_before": 0.6,
      "confidence_after": 0.78,
      "change_reasoning": "数据验证了核心假设",
      "verified_assumptions": ["假设1", "假设2"],
      "refuted_assumptions": []
    },

    "next_needs": {
      "require_more_data": false,
      "suggested_improvements": [
        "建议增加竞品对比",
        "可以添加价格历史分析"
      ]
    },

    "user_feedback": {
      "satisfied": true,
      "notes": "数据质量很好"
    }
  }
}
```

---

## 采集类型定义

| 类型 | 说明 | 数据源 | 采样建议 |
|------|------|--------|---------|
| `product_reviews` | 产品评论 | Amazon, Shopee, Lazada | 分层采样50-100条 |
| `price_monitoring` | 价格监控 | Amazon, Shopee | 每日采样 |
| `competitor_analysis` | 竞品分析 | 多平台 | Top 20产品 |
| `social_sentiment` | 社交情感 | TikTok, Instagram | 最近7天，100条 |
| `policy_details` | 政策详情 | 官方网站 | 完整文档 |
| `search_trends` | 搜索趋势 | Google Trends | 月度数据 |
| `market_metrics` | 市场指标 | 平台API | 聚合数据 |

---

## 优先级定义

| 优先级 | 说明 | 响应时间 | 重试策略 |
|--------|------|---------|---------|
| `high` | 验证核心假设 | < 30分钟 | 立即重试3次 |
| `medium` | 辅助验证 | < 2小时 | 延迟重试2次 |
| `low` | 锦上添花 | < 24小时 | 单次尝试 |

---

## 回调机制

### 回调端点实现

```python
@router.post("/opportunities/callback")
async def handle_collection_callback(callback_data: Dict):
    """
    处理OpenClaw采集完成的回调
    """
    request_id = callback_data.get("request_id")
    task_id = callback_data.get("task_id")
    status = callback_data.get("status")

    # 查找对应的任务
    task = await get_task_by_request_id(request_id)

    if status == "completed":
        # 通知AI分析器处理新数据
        await ai_analyzer.process_collection_result(
            task.opportunity_id,
            callback_data["result"]
        )
    elif status == "failed":
        # 记录错误，考虑降级方案
        logger.error(f"Collection failed: {callback_data['error']}")
        await handle_collection_failure(task, callback_data["error"])
```

---

## 错误处理

### 错误代码

| 代码 | 说明 | 处理方式 |
|------|------|---------|
| `RATE_LIMIT_EXCEEDED` | API频率限制 | 延迟重试 |
| `INVALID_CREDENTIALS` | 认证失败 | 告警并停止 |
| `SOURCE_UNAVAILABLE` | 数据源不可用 | 尝试备用源 |
| `INSUFFICIENT_DATA` | 数据不足 | 扩大采样范围 |
| `TIMEOUT` | 超时 | 重试或使用部分数据 |

### 降级策略

1. **主要数据源失败** → 尝试备用数据源
2. **无法采集到足够数据** → 使用已有数据 + 降低置信度
3. **采集超时** → 使用部分数据 + 标记不确定性
4. **连续失败** → 暂停该类采集，告警

---

## 安全考虑

1. **认证**: 所有回调请求必须验证签名
2. **加密**: 敏感数据使用HTTPS传输
3. **限流**: 单个IP/用户的请求频率限制
4. **审计**: 记录所有请求和响应

---

## 版本控制

- 当前版本: 1.0
- 兼容性: 向后兼容
- 升级策略: 废弃字段保留2个版本周期

---

## 示例场景

### 场景1：验证产品机会

```
AI: "我需要验证Anker在马来西亚的用户满意度"
 ↓ 发送采集请求
OpenClaw: "收到，开始采集Amazon和Shopee的评论"
 ↓ 45秒后
OpenClaw: "采集完成，共245条评论，平均评分4.3"
 ↓ 发送结果
AI: "数据很好，置信度从0.6提升到0.78，不需要更多数据"
```

### 场景2：采集失败

```
AI: "我需要获取TikTok Shop的政策文档"
 ↓ 发送采集请求
OpenClaw: "源站不可用"
 ↓ 发送错误响应
AI: "使用备用方案：搜索相关新闻"
 ↓ 发送新的采集请求
OpenClaw: "找到了3篇相关文章"
```

---

**文档版本**: 1.0
**最后更新**: 2025-03-13
