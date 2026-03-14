# C-P-I 跨境商机矩阵算法系统 - 实施总结

## 项目背景

用户提出了一个核心问题：**如何调度 OpenClaw + AI 进行动态跟踪，实现从线索到真正商机的演进？**

本系统通过C-P-I (Competition-Potential-Intelligence Gap) 算法矩阵，建立了完整的三层信息处理架构：

```
线索 (Leads) → 商机 (Opportunities) → 机会 (Verified Opportunities)
```

---

## 核心实现

### 1. C-P-I 算法引擎 (`services/opportunity_algorithm.py`)

**公式**:
```
商机综合分 = 0.4×竞争度(C) + 0.4×增长潜力(P) + 0.2×信息差(I)
```

**三维度计算**:

| 维度 | 权重 | 计算公式 | 数据来源 |
|------|------|---------|---------|
| **竞争度 (C)** | 40% | Top10品牌份额×0.7 + CPC出价×0.3 | Amazon产品数据 |
| **增长潜力 (P)** | 40% | 关键词增长×0.6 + 评论速度×0.4 | 文章趋势 + Amazon评论 |
| **信息差 (I)** | 20% | 痛点集中度×100 | AI分析评论情感 |

**商机类型分类**:
- **长尾暴利型**: C低(<60), P中(60-80), I高(>70) - 适合个人卖家
- **类目收割型**: P极高(>90), C高(>70) - 适合资本型卖家
- **技术改良型**: I极高(>85) - 适合工厂型卖家

---

### 2. 信号识别引擎 (`services/signal_recognition.py`)

**职责**: 从海量Cards中识别高潜力信号

**扫描数据源**:
- Cards表中的12个品类卡片 (327条)
- 用户收藏的卡片
- 近24小时新增的卡片

**优先级算法**:
```python
优先级 = C-P-I总分
        + 30 (用户收藏)
        + 20 (I值>80)
        + 15 (C值<50)
```

**输出**: Top N 高潜力信号列表，按优先级排序

---

### 3. 任务生成器 (`services/task_generation.py`)

**职责**: 根据C-P-I分数，生成有针对性的数据采集任务

**智能任务分配**:

| C-P-I分数 | 生成任务 | 优先级 | OpenClaw Channel |
|----------|---------|-------|-----------------|
| C < 65 | 竞争度深度分析 | HIGH | oxylabs-competition-monitor |
| 50 < P < 85 | 增长潜力验证 | MEDIUM | google-trends-monitor |
| I > 75 | 信息差深度分析 | HIGH | amazon-review-scraper |
| C/P中等 | 价格追踪 | LOW | oxylabs-price-tracker |

**AI请求格式**:
```python
{
    "question": "用户最不满意的是什么？",
    "data_needed": ["差评文本", "痛点统计", "集中度"],
    "outcome_format": {
        "top_pain_points": "List[str]",
        "pain_point_concentration": "float (0-1)"
    }
}
```

---

### 4. Opportunities API 集成 (`api/opportunities.py`)

**新增端点**:

#### POST `/api/v1/opportunities/generate-from-cards`
从Cards生成商机，应用C-P-I算法评分

```bash
curl -X POST "https://api.zenconsult.top/api/v1/opportunities/generate-from-cards?limit=10"
```

**响应**:
```json
{
  "success": true,
  "generated_count": 10,
  "opportunities": [
    {
      "card_id": "uuid",
      "opportunity_id": "uuid",
      "opportunity_type": "长尾暴利型",
      "cpi_scores": {
        "total_score": 85.5,
        "competition": {"score": 55, "details": {...}},
        "potential": {"score": 90, "details": {...}},
        "intelligence_gap": {"score": 88, "details": {...}}
      },
      "confidence_score": 0.855
    }
  ]
}
```

#### POST `/api/v1/opportunities/{id}/recalculate-score`
重新计算商机的C-P-I分数（动态更新）

```bash
curl -X POST "https://api.zenconsult.top/api/v1/opportunities/{uuid}/recalculate-score"
```

**响应**:
```json
{
  "success": true,
  "old_confidence": 0.65,
  "new_confidence": 0.855,
  "confidence_change": 0.205,
  "cpi_scores": {...},
  "status_changed": true,
  "new_status": "verifying"
}
```

---

## OpenClaw + AI 协同流程

### 完整数据流

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 线索发现层 (Lead Discovery)                              │
│    • Card生成器每日生成12品类卡片                           │
│    • 用户收藏感兴趣的卡片                                   │
│    • RSS爬虫补充市场资讯                                     │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. AI信号分析层 (Signal Analysis)                           │
│    • SignalRecognitionEngine扫描所有Cards                  │
│    • 应用C-P-I算法初步评分                                  │
│    • 识别高潜力信号 (Score > 70)                            │
│    • 创建BusinessOpportunity (状态: POTENTIAL)              │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 任务生成层 (Task Generation)                             │
│    • DataCollectionTaskGenerator分析C-P-I三维度            │
│    • 识别需要验证的数据点                                   │
│    • 生成有针对性的数据采集任务                             │
│    • 任务优先级排序 (I值高 > C值低 > P值波动)               │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. OpenClaw数据采集层 (Data Collection)                     │
│    • Competition Monitor: 分析Top10品牌份额                │
│    • Review Sentiment Analyzer: AI情感分析差评             │
│    • Google Trends Monitor: 监控关键词趋势                 │
│    • Price Tracker: 追踪价格波动                           │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 验证数据融合层 (Data Fusion)                              │
│    • OpenClaw回调FastAPI端点                                │
│    • Dynamic Score Updater重新计算C-P-I分数                │
│    • 更新置信度历史记录                                     │
│    • 判断状态演进条件                                       │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. 商机决策层 (Opportunity Decision)                         │
│    • AI生成可行性报告                                       │
│    • 用户仪表板展示三维度变化趋势                           │
│    • 智能推荐行动建议                                       │
│    • 状态演进: POTENTIAL → VERIFYING → ASSESSING → EXECUTING │
└─────────────────────────────────────────────────────────────┘
```

---

## 使用示例

### 示例1: 用户收藏触发的商机验证

```python
# 1. 用户收藏"无线耳机"卡片
POST /api/v1/favorites
{"card_id": "uuid"}

# 2. SignalRecognitionEngine检测到收藏
#    应用C-P-I算法:
#    C = 65分, P = 82分, I = 78分
#    Total = 75.8分 → 高潜力信号

# 3. 自动创建商机
BusinessOpportunity(
    status=POTENTIAL,
    confidence_score=0.758
)

# 4. 生成验证任务
DataCollectionTask(
    task_type='intelligence_gap_analysis',  # I值高，重点验证
    priority=HIGH,
    channel_name='amazon-review-scraper'
)

# 5. OpenClaw执行任务
#    采集Top10产品的3星以下评论200条
#    AI分析痛点: "电池续航"、"音质断连"、"佩戴不适"
#    痛点集中度: 68%

# 6. 回调更新分数
POST /api/v1/opportunities/callbacks/task-completed
{
    "task_id": "uuid",
    "result": {
        "pain_point_concentration": 0.68,
        "top_pain_points": ["电池续航", "音质断连"]
    }
}

# 7. 重新计算C-P-I分数
#    新I值 = 82分 (↑4分)
#    新Total = 77.6分 (↑1.8分)
#    状态演进: POTENTIAL → VERIFYING

# 8. 6小时后，Competition Monitor返回
#    Top10品牌份额下降到45% (↓5%)
#    新C值 = 70分 (↑5分)
#    新Total = 80.8分 (↑3.2分)
#    状态演进: VERIFYING → ASSESSING

# 9. AI生成可行性报告
{
    "recommendation": "切入长续航+舒适佩戴的差异化产品",
    "estimated_margin": "35-45%",
    "time_to_market": "3-4个月",
    "investment_required": "$50,000-$80,000"
}

# 10. 状态演进: ASSESSING → EXECUTING (等待用户决策)
```

---

## 部署检查清单

### 后端部署 (HK服务器)

- [ ] 上传 `services/opportunity_algorithm.py`
- [ ] 上传 `services/signal_recognition.py`
- [ ] 上传 `services/task_generation.py`
- [ ] 上传更新后的 `api/opportunities.py`
- [ ] 重启Docker容器: `docker restart cb-business-api-fixed`

### OpenClaw部署 (HK服务器)

- [ ] 安装OpenClaw: `npm install -g openclaw`
- [ ] 创建配置文件: `~/.openclaw/channels/competition-monitor.js`
- [ ] 创建配置文件: `~/.openclaw/channels/review-sentiment.js`
- [ ] 设置定时任务: `openclaw schedule:create`

### 数据库准备

- [ ] 确保 `business_opportunities` 表存在
- [ ] 确保 `data_collection_tasks` 表存在
- [ ] 验证外键关系正确

### 测试验证

- [ ] 运行算法测试: `python tests/test_cpi_algorithm.py`
- [ ] 测试生成商机API
- [ ] 测试重新计分API
- [ ] 验证OpenClaw通道执行

---

## 监控指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| 线索识别率 | C-P-I总分>70的线索占比 | > 30% |
| 任务成功率 | OpenClaw任务完成率 | > 90% |
| 分数提升率 | 验证后分数提升幅度 | > 15% |
| 状态演进率 | POTENTIAL→ASSESSING转化率 | > 40% |
| 用户采纳率 | EXECUTING状态商机数 | > 20% |

---

## 下一步工作

### 短期 (本周)
1. 部署新代码到HK服务器
2. 运行算法测试验证正确性
3. 创建OpenClaw Channel配置文件

### 中期 (下周)
1. 实现OpenClaw回调端点
2. 实现状态机自动演进逻辑
3. 前端展示C-P-I三维度分数

### 长期 (后续)
1. AI生成可行性报告
2. 用户决策交互界面
3. 数据可视化图表

---

**文档版本**: 1.0
**创建日期**: 2026-03-14
**状态**: ✅ 代码完成，待部署测试
