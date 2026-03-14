# 智能商机跟踪系统实施计划

> **项目代号**: Smart Opportunity System (SOS)
> **目标**: 将Cards从静态信息卡片转型为动态商机跟踪系统
> **核心理念**: AI-OpenClaw智能联盟 - AI主动探索，OpenClaw按需采集

---

## 上下文总结

### 问题背景

**当前系统的问题**：
1. Cards是静态的"信息卡片"，不是动态的商机跟踪
2. Articles（286条）和Cards（327条）完全独立，数据不融合
3. AI分析能力未充分利用（Articles的AI分析结果被忽略）
4. 商机要素不完整：只关注产品，忽略政策、平台、品牌、行业等维度
5. AI是被动分析现有数据，无法主动探索和验证

### 业务愿景

**商机应该像销售漏斗一样演进**：
```
发现期(1000+) → 验证期(100-200) → 评估期(20-50) → 执行期(5-10) → 归档
```

**商机包括多维度要素**：
- 产品机会：爆款产品未进入某地
- 地区政策：消费税降低、自贸协定
- 平台策略：TikTok Shop新政策
- 品牌动态：知名品牌进入新市场
- 行业趋势：消费潮流变化

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI-OpenClaw 智能联盟                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   RSS文章/平台通知 → AI分析 → 发现商机 → 提出数据需求       │
│                                    ↓                        │
│                            OpenClaw智能采集                  │
│                                    ↓                        │
│                            AI更新判断 → 继续验证？            │
│                                    ↓                        │
│                            达到阈值 → 用户决策               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 实施计划（12周）

### Phase 1: 基础设施（Week 1-4）

#### Week 1-2: 数据库与基础API
**目标**: 建立商机数据模型

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 创建business_opportunities表 | migration文件 | 2h |
| 创建data_collection_tasks表 | migration文件 | 1h |
| 更新Card模型（兼容旧数据） | models/card.py | 2h |
| 创建BusinessOpportunity模型 | models/business_opportunity.py | 2h |
| 商机发现API | api/opportunities.py | 3h |
| 商机查询API | api/opportunities.py | 2h |
| 商机状态更新API | api/opportunities.py | 2h |

#### Week 3-4: AI智能分析（MVP）
**目标**: AI能分析信号并创建商机

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 设计AI分析Prompt | prompts/opportunity_analysis.txt | 3h |
| 实现AIOpportunityAnalyzer | services/ai_opportunity_analyzer.py | 4h |
| 信号来源适配（RSS） | services/signal_adapters.py | 2h |
| 信号来源适配（Articles表） | services/signal_adapters.py | 2h |
| 测试AI分析质量 | tests/test_ai_analyzer.py | 2h |

### Phase 2: 智能采集（Week 5-8）

#### Week 5-6: OpenClaw智能Channel
**目标**: OpenClaw能执行AI的数据需求

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 设计采集协议 | docs/ai_openclaw_protocol.md | 2h |
| 创建smart-collector Channel | openclaw/channels/smart-collector.js | 4h |
| 实现SmartSampler | openclaw/lib/smart_sampler.js | 3h |
| Amazon评论采集 | openclaw/lib/collectors/amazon_reviews.js | 3h |
| 价格监控采集 | openclaw/lib/collectors/price_monitor.js | 2h |
| 社交媒体情感采集 | openclaw/lib/collectors/social_sentiment.js | 3h |

#### Week 7-8: 协调器实现
**目标**: AI和OpenClaw能协同工作

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| SmartOrchestrator核心 | services/smart_orchestrator.py | 4h |
| OpenClaw客户端封装 | services/openclaw_client.py | 2h |
| 任务提交与回调 | services/smart_orchestrator.py | 3h |
| AI数据更新逻辑 | services/ai_opportunity_analyzer.py | 3h |
| 错误处理与重试 | services/smart_orchestrator.py | 2h |

### Phase 3: 漏斗管理（Week 9-10）

#### Week 9: 状态机与演进
**目标**: 商机能自动演进

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 商机状态机 | models/business_opportunity.py | 2h |
| 自动演进逻辑 | services/smart_orchestrator.py | 3h |
| 定时任务：漏斗管理 | scheduler/opportunity_tasks.py | 2h |
| 可行性报告生成 | services/feasibility_reporter.py | 4h |

#### Week 10: 用户交互
**目标**: 用户能参与商机筛选

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 用户反馈API | api/opportunities.py | 2h |
| 收藏/标记功能 | api/opportunities.py | 1h |
| 笔记功能 | api/opportunities.py | 1h |
| 批量操作API | api/opportunities.py | 2h |

### Phase 4: 前端与优化（Week 11-12）

#### Week 11: 前端界面
**目标**: 用户能看到商机漏斗

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 商机会看板 | app/opportunities/page.tsx | 4h |
| 漏斗视图组件 | components/opportunities/funnel-view.tsx | 3h |
| 商机详情页 | app/opportunities/[id]/page.tsx | 3h |
| 验证进度展示 | components/opportunities/verification-tracker.tsx | 2h |

#### Week 12: 集成与优化
**目标**: 系统稳定运行

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 与现有Cards整合 | api/cards.py | 3h |
| 性能优化 | - | 4h |
| 监控与告警 | monitoring/opportunity_monitor.py | 2h |
| 文档完善 | docs/api/opportunities.md | 2h |

---

## 数据模型设计

### business_opportunities表

```sql
CREATE TABLE business_opportunities (
    -- 基本信息
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'potential',
    opportunity_type VARCHAR(50) NOT NULL,

    -- 商机要素（多维度）
    elements JSONB NOT NULL DEFAULT '{}',

    -- AI分析
    ai_insights JSONB NOT NULL DEFAULT '{}',
    confidence_score FLOAT NOT NULL DEFAULT 0.5,

    -- 用户交互
    user_interactions JSONB DEFAULT '{}',

    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_status (status),
    INDEX idx_type (opportunity_type),
    INDEX idx_confidence (confidence_score),
    INDEX idx_created (created_at)
);
```

### elements JSONB结构

```json
{
  "product": {
    "asin": "B09XXX",
    "title": "产品标题",
    "category": "electronics",
    "opportunity_reason": "爆款未进入东南亚"
  },
  "region": {
    "country": "MY",
    "opportunity_reason": "消费税降低5%"
  },
  "platform": {
    "name": "TikTok Shop",
    "opportunity_reason": "新物流政策降低成本"
  },
  "policy": {
    "description": "RCEP自贸协定",
    "impact": "关税减免"
  },
  "brand": {
    "name": "Anker",
    "opportunity_reason": "计划进入新市场"
  },
  "industry": {
    "sector": "美妆",
    "trend": "天然有机产品需求增长"
  }
}
```

### ai_insights JSONB结构

```json
{
  "why_opportunity": "AI推理过程",
  "key_assumptions": ["假设1", "假设2"],
  "verification_needs": ["需要验证的问题"],
  "missing_information": ["缺失的信息"],
  "data_requirements": [
    {
      "priority": "high",
      "question": "用户评价如何？",
      "data_needed": "产品评论",
      "source_suggestion": "Amazon"
    }
  ],
  "confidence_history": [
    {"from": 0.5, "to": 0.7, "reason": "新数据验证"}
  ],
  "feasibility_report": {}
}
```

---

## AI-OpenClaw通信协议

### AI → OpenClaw: 数据请求

```json
{
  "request_id": "uuid",
  "opportunity_id": "uuid",
  "priority": "high|medium|low",
  "question": "Anker在马来西亚的用户满意度如何？",
  "data_needed": {
    "type": "product_reviews",
    "scope": {
      "brand": "Anker",
      "region": "MY",
      "category": "electronics"
    },
    "constraints": {
      "sample_size": 100,
      "time_range": "last_6_months",
      "verified_only": true
    }
  },
  "outcome_format": {
    "structure": "structured",
    "key_fields": ["sentiment", "rating", "price", "complaints"],
    "aggregation": "summary"
  }
}
```

### OpenClaw → AI: 采集结果

```json
{
  "request_id": "uuid",
  "status": "completed",
  "results": {
    "summary": {
      "total_items": 245,
      "quality_score": 0.85,
      "avg_rating": 4.3,
      "sentiment_distribution": {
        "positive": 0.75,
        "neutral": 0.15,
        "negative": 0.10
      }
    },
    "data": [
      {
        "asin": "B09XXX",
        "rating": 4.5,
        "sentiment": "positive",
        "key_complaints": ["价格偏高", "续航一般"],
        "date": "2025-03-01"
      }
    ],
    "metadata": {
      "sources": ["amazon_reviews"],
      "collection_time": "2025-03-13T10:00:00Z",
      "limitations": ["部分产品无评论"]
    }
  }
}
```

---

## 关键技术决策

### 1. AI模型选择
- **使用**: GLM-4 Plus (已有)
- **备用**: GPT-4o (更贵但更稳定)
- **理由**: 已有API接入，支持JSON输出

### 2. 数据采集策略
- **原则**: 智能采样，不盲目爬取
- **方法**: 分层采样 + 时间采样
- **目标**: 用最少数据获得最大洞察

### 3. 状态机设计
```
potential → verifying → assessing → executing → archived
    ↓          ↓           ↓          ↓
  ignored   failed      failed     succeeded
```

### 4. 兼容性策略
- 保留原有Cards表
- 新建BusinessOpportunities表
- 逐步迁移数据
- 前期双轨运行

---

## 成功指标

### 技术指标
- [ ] AI分析准确率 > 80%
- [ ] 数据采集成功率 > 90%
- [ ] 商机验证周期 < 48小时
- [ ] API响应时间 < 500ms (p95)

### 业务指标
- [ ] 发现商机数量 > 100/月
- [ ] 验证通过率 > 30%
- [ ] 用户反馈收集率 > 50%
- [ ] 系统可用性 > 99%

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| AI判断不准确 | 中 | 高 | 持续prompt调优 + 用户反馈 |
| 数据采集失败 | 中 | 中 | 多数据源备份 + Fallback |
| 性能问题 | 低 | 中 | 缓存 + 异步处理 |
| 用户不接受 | 低 | 高 | MVP验证 + 迭代优化 |

---

## 下一步

1. **立即可做**: 创建数据库migration ✅ (已完成)
2. **需要决策**: AI模型配置、采集预算
3. **阻塞事项**: OpenClaw访问权限

---

## 📊 实施进度追踪 (2026-03-14更新)

### 整体进度: 15%

```
Phase 1 [██░░░░░░░░░] 20%  |  基础设施
Phase 2 [█░░░░░░░░░░] 10%  |  智能采集
Phase 3 [░░░░░░░░░░░] 0%   |  漏斗管理
Phase 4 [░░░░░░░░░░░] 0%   |  前端界面
```

### Phase 1: 基础设施 (Week 1-4) - 20% 完成

#### Week 1-2: 数据库与基础API
| 任务 | 文件 | 预计时间 | 状态 |
|------|------|---------|------|
| 创建business_opportunities表 | migration文件 | 2h | ✅ 已完成 |
| 创建data_collection_tasks表 | migration文件 | 1h | ✅ 已完成 |
| 更新Card模型（兼容旧数据） | models/card.py | 2h | 🟡 待开始 |
| 创建BusinessOpportunity模型 | models/business_opportunity.py | 2h | ✅ 已完成 |
| 商机发现API | api/opportunities.py | 3h | ❌ 待开始 |
| 商机查询API | api/opportunities.py | 2h | ❌ 待开始 |
| 商机状态更新API | api/opportunities.py | 2h | ❌ 待开始 |

#### Week 3-4: AI智能分析（MVP）
| 任务 | 文件 | 预计时间 | 状态 |
|------|------|---------|------|
| 设计AI分析Prompt | prompts/opportunity_analysis.txt | 3h | ❌ 待开始 |
| 实现AIOpportunityAnalyzer | services/ai_opportunity_analyzer.py | 4h | ❌ 待开始 (#44) |
| 信号来源适配（RSS） | services/signal_adapters.py | 2h | ❌ 待开始 (#43) |
| 信号来源适配（Articles表） | services/signal_adapters.py | 2h | ❌ 待开始 (#43) |
| 测试AI分析质量 | tests/test_ai_analyzer.py | 2h | ❌ 待开始 |

### Phase 2: 智能采集 (Week 5-8) - 10% 完成

#### Week 5-6: OpenClaw智能Channel
| 任务 | 文件 | 预计时间 | 状态 |
|------|------|---------|------|
| 设计采集协议 | docs/plan/ai_openclaw_protocol.md | 2h | ✅ 已完成 |
| 创建smart-collector Channel | openclaw/channels/smart-collector.js | 4h | ❌ 待开始 (#36) |
| 实现SmartSampler | openclaw/lib/smart_sampler.js | 3h | ❌ 待开始 (#36) |
| Amazon评论采集 | openclaw/lib/collectors/amazon_reviews.js | 3h | ❌ 待开始 |
| 价格监控采集 | openclaw/lib/collectors/price_monitor.js | 2h | ❌ 待开始 |
| 社交媒体情感采集 | openclaw/lib/collectors/social_sentiment.js | 3h | ❌ 待开始 |

#### Week 7-8: 协调器实现
| 任务 | 文件 | 预计时间 | 状态 |
|------|------|---------|------|
| SmartOrchestrator核心 | services/smart_orchestrator.py | 4h | ❌ 待开始 (#38) |
| OpenClaw客户端封装 | services/openclaw_client.py | 2h | 🟡 部分完成 |
| 任务提交与回调 | services/smart_orchestrator.py | 3h | ❌ 待开始 (#38, #42) |
| AI数据更新逻辑 | services/ai_opportunity_analyzer.py | 3h | ❌ 待开始 |
| 错误处理与重试 | services/smart_orchestrator.py | 2h | ❌ 待开始 |

### Phase 3: 漏斗管理 (Week 9-10) - 0% 完成

#### Week 9: 状态机与演进
| 任务 | 文件 | 预计时间 | 状态 |
|------|------|---------|------|
| 商机状态机 | models/business_opportunity.py | 2h | ✅ 已完成 |
| 自动演进逻辑 | services/smart_orchestrator.py | 3h | ❌ 待开始 |
| 定时任务：漏斗管理 | scheduler/opportunity_tasks.py | 2h | ❌ 待开始 (#41) |
| 可行性报告生成 | services/feasibility_reporter.py | 4h | ❌ 待开始 |

#### Week 10: 用户交互
| 任务 | 文件 | 预计时间 | 状态 |
|------|------|---------|------|
| 用户反馈API | api/opportunities.py | 2h | ❌ 待开始 (#39) |
| 收藏/标记功能 | api/opportunities.py | 1h | ❌ 待开始 (#39) |
| 笔记功能 | api/opportunities.py | 1h | ❌ 待开始 (#39) |
| 批量操作API | api/opportunities.py | 2h | ❌ 待开始 (#39) |

### Phase 4: 前端与优化 (Week 11-12) - 0% 完成

#### Week 11: 前端界面
| 任务 | 文件 | 预计时间 | 状态 |
|------|------|---------|------|
| 商机会看板 | app/opportunities/page.tsx | 4h | ❌ 待开始 (#40) |
| 漏斗视图组件 | components/opportunities/funnel-view.tsx | 3h | ❌ 待开始 (#40) |
| 商机详情页 | app/opportunities/[id]/page.tsx | 3h | ❌ 待开始 (#45) |
| 验证进度展示 | components/opportunities/verification-tracker.tsx | 2h | ❌ 待开始 (#37) |

#### Week 12: 集成与优化
| 任务 | 文件 | 预计时间 | 状态 |
|------|------|---------|------|
| 与现有Cards整合 | api/cards.py | 3h | ❌ 待开始 |
| 性能优化 | - | 4h | ❌ 待开始 |
| 监控与告警 | monitoring/opportunity_monitor.py | 2h | ❌ 待开始 |
| 文档完善 | docs/api/opportunities.md | 2h | ❌ 待开始 |

### 依赖关系图

```
Phase 1 基础设施
├─ 数据库 ✅ ─┐
├─ 模型 ✅ ───┤
└─ APIs ❌ ──┘
              ↓
Phase 2 智能采集
├─ AI Analyzer ❌ ─┐
├─ Signal Adapter ❌─┼─> Orchestrator ❌
└─ OpenClaw ❌ ────┘
                      ↓
Phase 3 漏斗管理
├─ Funnel Manager ❌ ─┐
└─ User Interaction ❠┘
                         ↓
Phase 4 前端
├─ Board UI ❌
├─ Detail Page ❌
└─ Tracker UI ❌

图例: ✅ 已完成 | 🟡 部分完成 | ❌ 待开始
```

---

**文档版本**: 1.1
**创建日期**: 2026-03-13
**最后更新**: 2026-03-14
