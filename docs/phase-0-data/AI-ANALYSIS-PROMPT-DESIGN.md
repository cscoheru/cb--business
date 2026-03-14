# Phase 0 Day 2: AI Analysis Prompt Design

> **Purpose**: Design GLM-4 prompts for market analysis based on collected data

---

## Prompt 1: Product Category Market Analysis

### Input Data Structure

```json
{
  "category": "Wireless Earbuds",
  "market_data": {
    "market_size": "$30.5B by 2030",
    "cagr": "24.28%",
    "regional_distribution": {
      "north_america": "30.5%",
      "asia_pacific": "44.57%"
    }
  },
  "amazon_products": [
    {
      "title": "Anker Soundcore Liberty 4",
      "price": 79.99,
      "rating": 4.5,
      "reviews_count": 12453
    }
  ],
  "user_reviews": [
    "Easy to lose earbuds",
    "Connection drops sometimes",
    "Great ANC",
    "Battery lasts 8 hours"
  ],
  "web_search_insights": {
    "price_sensitivity": "Sweet spot $40-60",
    "top_complaints": ["Lost earbuds", "Connection issues"],
    "unmet_needs": ["Anti-loss design"]
  }
}
```

### GLM-4 Analysis Prompt

```markdown
你是一位跨境电商市场分析专家。请分析以下产品类目的市场机会。

## 产品类目：{category}

### 一、市场趋势数据
{market_data}

### 二、Amazon热销产品数据（Top 20）
{amazon_products_table}

### 三、用户评论分析（来自Reddit、YouTube、Amazon）

#### 正面反馈（Top 10）：
{positive_reviews}

#### 负面反馈（Top 10）：
{negative_reviews}

#### 价格敏感度分析：
{price_sensitivity_data}

### 四、市场趋势（Google Trends）
- 过去12个月搜索趋势：{search_trend_change}
- 热门地区：{top_regions}

---

## 请以JSON格式返回分析结果：

```json
{
  "market_overview": {
    "market_size": "市场规模和增长数据总结",
    "growth_potential": "high/medium/low",
    "growth_stage": "emerging/growing/mature/saturated"
  },

  "product_strengths": [
    "优点1：基于用户反馈",
    "优点2：提及频率最高的功能"
  ],

  "product_weaknesses": [
    "缺点1：用户抱怨最多的痛点",
    "缺点2：普遍存在的问题"
  ],

  "price_analysis": {
    "overall_sensitivity": "high/medium/low",
    "acceptable_range": "$X-$Y",
    "sweet_spot": "$X-$Y (最佳价格区间)",
    "too_expensive_above": "$Z (超过此价格被认为太贵)",
    "budget_threshold": "$X (预算产品上限)"
  },

  "unmet_needs": [
    "需求1：未被满足的用户痛点",
    "需求2：用户渴望但市场没有提供好的解决方案"
  ],

  "regional_preferences": {
    "southeast_asia": {
      "preferences": "偏好描述",
      "price_sensitivity": "high/medium/low",
      "key_features": "该地区最看重的功能"
    },
    "north_america": {
      "preferences": "偏好描述",
      "price_sensitivity": "high/medium/low",
      "key_features": "该地区最看重的功能"
    },
    "europe": {
      "preferences": "偏好描述",
      "price_sensitivity": "high/medium/low",
      "key_features": "该地区最看重的功能"
    }
  },

  "use_cases": [
    "使用场景1：用户最常见的使用方式",
    "使用场景2：特定用户群体"
  ],

  "competitive_landscape": {
    "market_fragmentation": "high/medium/low (市场分散程度)",
    "dominant_players": ["品牌1", "品牌2"],
    "opportunity_areas": ["细分机会1", "细分机会2"]
  },

  "opportunity_assessment": {
    "opportunity_score": 0-100,
    "confidence_level": 0-1,
    "market_readiness": "early/growing/mature",
    "entry_difficulty": "easy/medium/hard",
    "competition_level": "low/medium/high"
  },

  "recommended_strategy": {
    "target_price_range": "$X-$Y",
    "target_markets": ["市场1", "市场2"],
    "core_selling_points": ["卖点1", "卖点2"],
    "differentiation_strategy": "差异化策略描述",
    "risk_factors": ["风险1", "风险2"]
  },

  "data_quality_assessment": {
    "data_sources": ["来源1", "来源2"],
    "missing_data": ["缺失数据1"],
    "reliability_score": 0-100,
    "confidence_explanation": "解释可靠性和局限性"
  },

  "key_insights": [
    "关键洞察1：最重要的发现",
    "关键洞察2：反直觉或容易被忽视的点"
  ]
}
```

## 分析要求：

1. **基于数据**：所有结论必须有数据支持，不要凭空猜测
2. **诚实透明**：如果数据不足，明确说明，不要过度推断
3. **区分事实与推断**：明确标注哪些是观察到的数据，哪些是AI分析
4. **标注可靠性**：每个结论都标注可靠性评分（0-100）
5. **指出局限性**：明确说明缺失的数据和分析的局限性
6. **提供行动建议**：给出具体的、可操作的建议，而不是泛泛而谈

## 输出格式：
- 使用上面的JSON结构
- 所有文本使用中文
- 评分和价格保留原始数字格式
- 布尔值使用 true/false
```

---

## Prompt 2: Cross-Category Comparison

After analyzing 3 categories, use this prompt to compare:

```markdown
基于之前对3个产品类目的分析，请进行横向对比：

## 产品类目：
1. 无线耳机 (Wireless Earbuds)
2. 智能插座 (Smart Plugs)
3. 健身追踪器 (Fitness Trackers)

## 请以JSON格式返回对比分析：

```json
{
  "comparison_matrix": {
    "market_growth": {
      "highest": "类目名称",
      "lowest": "类目名称",
      "ranking": ["1.类目(XX%)", "2.类目(XX%)", "3.类目(XX%)"]
    },
    "competition_level": {
      "most_competitive": "类目",
      "least_competitive": "类目"
    },
    "price_sensitivity": {
      "most_sensitive": "类目",
      "least_sensitive": "类目"
    },
    "opportunity_score": {
      "highest": "类目 (分数)",
      "lowest": "类目 (分数)"
    }
  },

  "top_opportities": [
    {
      "category": "类目",
      "opportunity": "具体机会描述",
      "reason": "推荐理由"
    }
  ],

  "risks": [
    {
      "category": "类目",
      "risk": "风险描述",
      "mitigation": "缓解策略"
    }
  ],

  "strategic_recommendations": {
    "best_category_for_new_seller": "类目",
    "easiest_entry": "类目",
    "highest_potential": "类目",
    "rational": "推荐理由"
  }
}
```
```

---

## Data Preparation for AI Analysis

### From Day 1 Collected Data:

1. **Wireless Earbuds** (Most Complete)
   - Market size: $30.5B, CAGR 24.28%
   - User reviews: Rich data from Reddit/YouTube
   - Price sensitivity: $40-60 sweet spot
   - Unmet needs: Anti-loss, stable connection

2. **Smart Plugs** (Market Data)
   - Market growth: +$22.79B (2024-2028)
   - CAGR: 25.7-26.1%
   - User reviews: Limited (needs Amazon API)

3. **Fitness Trackers** (Market Data)
   - Market: $323.47B forecast
   - CAGR: 18-22%
   - User reviews: Limited (needs Amazon API)

---

## Day 2 Execution Plan

### Step 1: Run Oxylabs Fetcher (Now)
```bash
python3 pyStcratch/phase0/oxylabs_amazon_fetcher.py
```

Expected output:
- `amazon_wireless_earbuds.json`
- `amazon_smart_plug.json`
- `amazon_fitness_tracker.json`

### Step 2: Merge Day 1 + Day 2 Data
Combine web search insights with Amazon product data

### Step 3: Run GLM-4 Analysis
Execute prompt with merged data

### Step 4: Validate Quality
- Are insights valuable?
- Is analysis accurate?
- Would a seller find this useful?

---

## Success Criteria for Day 2

| Criterion | Target | Status |
|-----------|--------|--------|
| Oxylabs API successful | Fetch 50+ products | ⏳ Pending |
| Data quality | Valid prices/ratings | ⏳ Pending |
| GLM-4 analysis | Professional insights | ⏳ Pending |
| JSON output | Valid structured data | ⏳ Pending |

---

**Created**: 2026-03-12
**Next**: Run Oxylabs fetcher and prepare GLM-4 input
