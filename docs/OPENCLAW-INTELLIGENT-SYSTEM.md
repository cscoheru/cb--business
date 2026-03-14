# OpenClaw智能数据处理系统

> 创建日期: 2026-03-12
> 目标: 构建基于OpenClaw + GLM-4 Plus的智能数据采集、分析和分类系统

## 系统概述

### 数据源

| 数据源 | 类型 | 频率 | 数据量 | 用途 |
|--------|------|------|--------|------|
| **RSS资讯** | 文章 | 每2小时 | 25+源，500+篇/天 | 行业资讯、政策解读 |
| **Oxylabs API** | 产品数据 | 每小时 | 1000+产品/天 | 价格监控、竞品分析 |
| **Google Trends** | 趋势数据 | 每6小时 | 50+关键词 | 市场趋势、选品参考 |
| **社交媒体** | 用户生成内容 | 每4小时 | Reddit/YouTube | 用户反馈、热门话题 |

### 处理流程

```
原始数据
  ↓
【清洗层】去重、格式化、质量过滤
  ↓
【分析层】AI分类、实体提取、情感分析
  ↓
【归类层】自动匹配频道、类目、关键词
  ↓
【存储层】结构化存储到PostgreSQL
  ↓
【应用层】前端展示、API查询、报告生成
```

---

## 核心组件设计

### 1. AI分析引擎

**目的**: 使用GLM-4 Plus对数据进行智能分析和分类

#### 分析任务

| 任务 | 输入 | 输出 | 频率 |
|------|------|------|------|
| **文章分类** | 资讯文章 | 频道、地区、平台、标签 | 实时 |
| **产品分析** | 产品信息 | 类目、价格段、竞争力评分 | 批量 |
| **关键词提取** | 文本内容 | 5-10个关键词 + 权重 | 实时 |
| **机会评分** | 文章/产品 | 0-1分数 + 理由 | 实时 |
| **趋势预测** | 历史数据 | 未来7天趋势 | 每天 |

### 2. 知识图谱

#### 频道体系

```javascript
// 频道配置
const CHANNELS = {
  'news': {
    name: '行业资讯',
    subchannels: ['policy', 'merger', 'investment', 'regulation']
  },
  'market': {
    name: '市场分析',
    subchannels: ['trends', 'insights', 'reports', 'forecast']
  },
  'platform': {
    name: '平台动态',
    subchannels: ['amazon', 'shopee', 'lazada', 'tiktok']
  },
  'guide': {
    name: '实操指南',
    subchannels: ['seller', 'logistics', 'marketing', 'compliance']
  }
};
```

#### 类目体系

```javascript
// 产品类目树
const CATEGORIES = {
  'electronics': {
    name: '电子产品',
    children: ['phones', 'laptops', 'tablets', 'wearables', 'audio'],
    attributes: ['brand', 'price_range', 'specifications']
  },
  'fashion': {
    name: '服装配饰',
    children: ['clothing', 'shoes', 'accessories', 'bags', 'jewelry'],
    attributes: ['size', 'material', 'style', 'gender']
  },
  'home': {
    name: '家居用品',
    children: ['furniture', 'decor', 'kitchen', 'bedding', 'storage'],
    attributes: ['material', 'color', 'style', 'room']
  },
  'beauty': {
    name: '美妆护理',
    children: ['skincare', 'makeup', 'haircare', 'fragrance', 'tools'],
    attributes: ['skin_type', 'brand', 'concerns', 'organic']
  }
};
```

#### 关键词网络

```javascript
// 关键词图谱
const KEYWORD_GRAPH = {
  'cross-border': {
    related: ['ecommerce', 'international', 'trade', 'logistics'],
    markets: ['southeast_asia', 'latam', 'europe'],
    platforms: ['amazon', 'shopee', 'lazada'],
    score: 0.9
  },
  'amazon_fba': {
    related: ['private_label', 'fulfillment', 'sourcing'],
    markets: ['usa', 'europe'],
    topics: ['selling', 'fees', 'optimization'],
    score: 0.85
  }
  // ... 更多关键词
};
```

---

## OpenClaw Channels实现

### Channel 1: Oxylabs产品监控

**文件**: `/root/.openclaw/channels/oxylabs-monitor.js`

```javascript
const axios = require('axios');

// Oxylabs配置
const OXYLABS_CONFIG = {
  baseURL: 'https://realtime.oxylabs.io/v1/queries',
  username: 'fisher_VEpfJ',
  password: 'z7UnsI2Hkug_',
  timeout: 120000 // 2分钟超时
};

// 监控任务配置
const MONITOR_TASKS = [
  {
    id: 'amazon_best_sellers_electronics',
    name: 'Amazon电子产品畅销榜',
    source: 'amazon_bestsellers',
    query: 'https://www.amazon.com/Best-Sellers-Electronics/zgbs/entity-name/172282/ref=zg_bs_pg_1',
    geo_location: '90210',
    parse: true,
    category: 'electronics',
    limit: 50
  },
  {
    id: 'amazon_new_releases_home',
    name: 'Amazon家居新品',
    source: 'amazon_product',
    query: 'B08C7K5ZPN', // ASIN示例
    geo_location: '90210',
    parse: true,
    category: 'home',
    limit: 30
  }
  // ... 更多任务
];

module.exports = async function(context) {
  const results = {
    total: 0,
    success: 0,
    failed: 0,
    products: [],
    errors: []
  };

  // 遍历监控任务
  for (const task of MONITOR_TASKS) {
    try {
      context.log(`🔄 监控: ${task.name}`);

      // 调用Oxylabs API
      const response = await axios.post(OXYLABS_CONFIG.baseURL, {
        source: task.source,
        url: task.query,
        geo_location: task.geo_location,
        parse: task.parse
      }, {
        auth: {
          username: OXYLABS_CONFIG.username,
          password: OXYLABS_CONFIG.password
        },
        timeout: OXYLABS_CONFIG.timeout
      });

      // 等待Oxylabs处理
      const jobId = response.data.id;
      const productData = await pollJobResult(jobId);

      // 提取产品信息
      const products = extractProducts(productData, task);

      // AI分析和分类
      const analyzedProducts = await analyzeProducts(products, context);

      results.success++;
      results.products.push(...analyzedProducts);

      context.log(`✅ ${task.name}: 获取 ${products.length} 个产品`);

    } catch (error) {
      results.failed++;
      results.errors.push({
        task: task.name,
        error: error.message
      });
      context.error(`❌ ${task.name}: ${error.message}`);
    }
  }

  // 批量保存到数据库
  try {
    await context.http.post({
      url: 'http://localhost:8000/api/v1/products/batch',
      headers: { 'Content-Type': 'application/json' },
      json: { products: results.products },
      timeout: 60000
    });

    context.log(`✅ 已保存 ${results.products.length} 个产品到数据库`);
  } catch (error) {
    context.error(`❌ 保存到数据库失败: ${error.message}`);
    throw error;
  }

  return {
    total_tasks: MONITOR_TASKS.length,
    successful: results.success,
    failed: results.failed,
    products_saved: results.products.length,
    summary: `${results.success}/${MONITOR_TASKS.length} 任务成功，${results.products.length} 个产品已保存`
  };
};

// 轮询Oxylabs任务结果
async function pollJobResult(jobId, maxAttempts = 40) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await axios.get(
        `${OXYLABS_CONFIG.baseURL}/${jobId}`,
        {
          auth: {
            username: OXYLABS_CONFIG.username,
            password: OXYLABS_CONFIG.password
          }
        }
      );

      const status = response.data.status;
      if (status === 'done') {
        return response.data.results[0].content;
      } else if (status === 'failed') {
        throw new Error(`Oxylabs任务失败: ${response.data.error}`);
      }

      // 等待3秒后重试
      await new Promise(resolve => setTimeout(resolve, 3000));

    } catch (error) {
      if (i === maxAttempts - 1) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }

  throw new Error('任务超时');
}

// 提取产品信息
function extractProducts(data, task) {
  // 根据Oxylabs返回的数据结构提取产品
  const products = [];

  if (data.product) {
    products.push({
      asin: data.product.asin,
      title: data.product.title,
      price: data.product.pricing?.price,
      rating: data.product.rating,
      reviews_count: data.product.reviews_count,
      url: data.product.url,
      images: data.product.images,
      category: task.category,
      source: 'oxylabs',
      crawled_at: new Date().toISOString()
    });
  }

  // 处理畅销榜（多个产品）
  if (data.results && Array.isArray(data.results)) {
    data.results.forEach(item => {
      if (item.product && item.product.asin) {
        products.push({
          asin: item.product.asin,
          title: item.product.title,
          price: item.product.pricing?.price,
          rating: item.product.rating,
          reviews_count: item.product.reviews_count,
          url: item.product.url,
          images: item.product.images,
          category: task.category,
          source: 'oxylabs',
          crawled_at: new Date().toISOString()
        });
      }
    });
  }

  return products.slice(0, task.limit);
}

// AI分析和分类产品
async function analyzeProducts(products, context) {
  // 调用GLM-4 Plus进行批量分析
  const analysisPrompt = `
分析以下${products.length}个产品，为每个产品提供：

1. **主要类目**: electronics, fashion, home, beauty等
2. **子类目**: 具体细分（如phones, clothing等）
3. **价格段**: budget(<$50), mid($50-$200), premium(>$200)
4. **目标人群**: beginners, enthusiasts, professionals等
5. **关键词**: 5-10个相关关键词
6. **机会评分**: 0-1分数（基于竞争度、需求趋势）
7. **推荐理由**: 为什么这个产品值得关注

产品JSON：
${JSON.stringify(products, null, 2)}

请以JSON数组格式返回分析结果：
[
  {
    "asin": "...",
    "category": "...",
    "subcategory": "...",
    "price_segment": "...",
    "target_audience": "...",
    "keywords": ["keyword1", "keyword2", ...],
    "opportunity_score": 0.85,
    "recommendation_reason": "..."
  }
]
`;

  try {
    const response = await context.http.post({
      url: 'http://localhost:18789/api/v1/chat/completions',
      headers: { 'Content-Type': 'application/json' },
      json: {
        model: 'glm/glm-4-plus',
        messages: [
          {
            role: 'system',
            content: '你是跨境电商产品分析专家，擅长从产品信息中提取有价值的商业洞察。'
          },
          {
            role: 'user',
            content: analysisPrompt
          }
        ],
        temperature: 0.3,
        max_tokens: 4000
      },
      timeout: 120000 // 2分钟超时
    });

    const aiAnalysis = JSON.parse(response.choices[0].message.content);

    // 将AI分析结果合并到产品数据
    return products.map((product, index) => ({
      ...product,
      ...aiAnalysis[index],
      ai_analyzed: true,
      ai_analyzed_at: new Date().toISOString()
    }));

  } catch (error) {
    context.error(`AI分析失败: ${error.message}`);
    // 如果AI分析失败，返回原始产品
    return products.map(product => ({
      ...product,
      ai_analyzed: false,
      ai_error: error.message
    }));
  }
}
```

### Channel 2: 智能内容分类

**文件**: `/root/.openclaw/channels/content-classifier.js`

```javascript
module.exports = async function(context) {
  // 获取未分类的文章/产品
  const unclassifiedItems = await getUnclassifiedItems(context);

  if (unclassifiedItems.length === 0) {
    context.log('✅ 所有内容已分类，无需处理');
    return { classified: 0, skipped: 0 };
  }

  context.log(`🔄 开始分类 ${unclassifiedItems.length} 个项目`);

  let classified = 0;
  let skipped = 0;

  // 批量分类（每批10个）
  const batchSize = 10;
  for (let i = 0; i < unclassifiedItems.length; i += batchSize) {
    const batch = unclassifiedItems.slice(i, i + batchSize);

    try {
      const classifications = await classifyBatch(batch, context);

      // 更新数据库
      await updateClassifications(classifications, context);

      classified += batch.length;
      context.log(`✅ 已分类 ${batch.length} 个项目 (${i + batch.length}/${unclassifiedItems.length})`);

    } catch (error) {
      skipped += batch.length;
      context.error(`❌ 批次分类失败: ${error.message}`);
    }
  }

  return {
    classified,
    skipped,
    total: unclassifiedItems.length,
    summary: `${classified}/${unclassifiedItems.length} 个项目已分类`
  };
};

// 获取未分类的内容
async function getUnclassifiedItems(context) {
  try {
    const response = await context.http.get({
      url: 'http://localhost:8000/api/v1/crawler/unclassified',
      params: { limit: 100, type: 'all' }
    });
    return response.data.items || [];
  } catch (error) {
    context.error(`获取未分类内容失败: ${error.message}`);
    return [];
  }
}

// 批量分类
async function classifyBatch(items, context) {
  const classifyPrompt = `
你是跨境电商内容分类专家。请将以下${items.length}个内容项目分类到正确的频道、类目和关键词。

## 频道体系
1. **news** - 行业资讯（政策、并购、投资、监管）
2. **market** - 市场分析（趋势、洞察、报告、预测）
3. **platform** - 平台动态（Amazon、Shopee、Lazada、TikTok Shop）
4. **guide** - 实操指南（卖家、物流、营销、合规）

## 类目体系
- electronics（电子产品）
- fashion（服装配饰）
- home（家居用品）
- beauty（美妆护理）
- 其他...

## 地区分类
- southeast_asia（东南亚）
- north_america（北美）
- europe（欧洲）
- latin_america（拉美）
- china（中国）

## 平台分类
- amazon, shopee, lazada, tiktok, 其他

## 输出格式
请对每个项目返回：
{
  "id": "项目ID",
  "channel": "频道(news/market/platform/guide)",
  "category": "类目",
  "country": "国家代码",
  "platform": "平台(如适用)",
  "keywords": ["关键词1", "关键词2", ...],
  "opportunity_score": 0-1分数,
  "content_theme": "内容主题(policy/opportunity/guide/risk等)"
}

待分类内容JSON：
${JSON.stringify(items.map(item => ({
  id: item.id,
  title: item.title,
  summary: item.summary || item.description,
  content: item.full_content || item.content
})), null, 2)}
`;

  try {
    const response = await context.http.post({
      url: 'http://localhost:18789/api/v1/chat/completions',
      headers: { 'Content-Type': 'application/json' },
      json: {
        model: 'glm/glm-4-plus',
        messages: [
          {
            role: 'system',
            content: '你是跨境电商内容分类专家，精通将各种内容分类到正确的频道和类目。'
          },
          {
            role: 'user',
            content: classifyPrompt
          }
        ],
        temperature: 0.2, // 降低温度以获得更一致的结果
        max_tokens: 6000
      },
      timeout: 180000 // 3分钟超时
    });

    const classifications = JSON.parse(response.choices[0].message.content);
    return classifications;

  } catch (error) {
    context.error(`分类失败: ${error.message}`);
    throw error;
  }
}

// 更新数据库中的分类
async function updateClassifications(classifications, context) {
  await context.http.post({
    url: 'http://localhost:8000/api/v1/crawler/batch-update',
    headers: { 'Content-Type': 'application/json' },
    json: { updates: classifications }
  });
}
```

### Channel 3: 趋势发现与机会识别

**文件**: `/root/.openclaw/channels/trend-discovery.js`

```javascript
module.exports = async function(context) {
  context.log('🔍 开始趋势发现分析');

  const trends = {
    emerging_keywords: [],
    rising_products: [],
    market_insights: [],
    opportunities: []
  };

  // 1. 分析关键词趋势
  trends.emerging_keywords = await discoverTrendingKeywords(context);

  // 2. 识别上升产品
  trends.rising_products = await identifyRisingProducts(context);

  // 3. 生成市场洞察
  trends.market_insights = await generateMarketInsights(context);

  // 4. 识别机会
  trends.opportunities = await identifyOpportunities(context);

  // 保存趋势报告
  await saveTrendReport(trends, context);

  context.log(`✅ 发现 ${trends.emerging_keywords.length} 个新兴关键词`);
  context.log(`✅ 识别 ${trends.rising_products.length} 个上升产品`);
  context.log(`✅ 生成 ${trends.market_insights.length} 条市场洞察`);

  return trends;
};

// 发现趋势关键词
async function discoverTrendingKeywords(context) {
  // 查询最近7天的高机会文章
  const recentArticles = await context.http.get({
    url: 'http://localhost:8000/api/v1/crawler/articles',
    params: {
      days: 7,
      min_opportunity_score: 0.7,
      per_page: 100
    }
  });

  // 提取并统计关键词
  const keywordFrequency = {};
  recentArticles.data.articles.forEach(article => {
    if (article.tags && Array.isArray(article.tags)) {
      article.tags.forEach(tag => {
        keywordFrequency[tag] = (keywordFrequency[tag] || 0) + 1;
      });
    }
  });

  // 找出高频关键词
  const trendingKeywords = Object.entries(keywordFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([keyword, count]) => ({
      keyword,
      frequency: count,
      trend: 'rising'
    }));

  return trendingKeywords;
}

// 识别上升产品
async function identifyRisingProducts(context) {
  // 查询最近价格下降或评分上升的产品
  const products = await context.http.get({
    url: 'http://localhost:8000/api/v1/products/trending',
    params: {
      sort_by: 'price_drop',
      days: 7,
      per_page: 50
    }
  });

  return products.data.products.map(product => ({
    asin: product.asin,
    title: product.title,
    price_change: product.price_change_percent,
    rating_change: product.rating_change,
    category: product.category,
    opportunity_score: product.opportunity_score || 0.5
  }));
}

// 生成市场洞察
async function generateMarketInsights(context) {
  const insightPrompt = `
基于以下数据生成跨境电商市场洞察：

1. 最近7天的热门关键词
2. 上升产品趋势
3. 价格变化情况
4. 各地区动态

请生成5-10条高质量的市场洞察，每条包含：
- **洞察标题**: 简洁有力
- **详细说明**: 具体分析
- **行动建议**: 卖家可以做什么
- **影响地区**: 受影响的地区
- **机会评分**: 0-1分数

以JSON数组格式返回。
`;

  const response = await context.http.post({
    url: 'http://localhost:18789/api/v1/chat/completions',
    headers: { 'Content-Type': 'application/json' },
    json: {
      model: 'glm/glm-4-plus',
      messages: [
        {
          role: 'system',
          content: '你是跨境电商市场分析专家，擅长从数据中发现商业机会。'
        },
        {
          role: 'user',
          content: insightPrompt
        }
      ],
      temperature: 0.4,
      max_tokens: 3000
    }
  });

  return JSON.parse(response.choices[0].message.content);
}

// 识别机会
async function identifyOpportunities(context) {
  // 综合分析数据，识别高价值机会
  const opportunities = [];

  // 机会1: 新兴关键词 + 低竞争
  const emergingKeywords = await discoverTrendingKeywords(context);
  emergingKeywords.slice(0, 5).forEach(keyword => {
    if (keyword.frequency > 3 && keyword.trend === 'rising') {
      opportunities.push({
        type: 'keyword',
        title: `关键词 "${keyword.keyword}" 正在上升`,
        description: `过去7天出现 ${keyword.frequency} 次，趋势明显`,
        potential: 'high',
        action: `考虑开发相关产品或创建相关内容`
      });
    }
  });

  return opportunities;
}

// 保存趋势报告
async function saveTrendReport(trends, context) {
  await context.http.post({
    url: 'http://localhost:8000/api/v1/trends/report',
    headers: { 'Content-Type': 'application/json' },
    json: {
      report_date: new Date().toISOString().split('T')[0],
      data: trends
    }
  });
}
```

---

## 数据库表设计

### products表（产品数据）

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asin VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    brand VARCHAR(100),

    -- 分类信息
    category VARCHAR(50),
    subcategory VARCHAR(50),
    keywords TEXT[],
    tags TEXT[],

    -- 价格信息
    price DECIMAL(10,2),
    price_segment VARCHAR(20),
    currency VARCHAR(3) DEFAULT 'USD',

    -- 评分信息
    rating DECIMAL(3,2),
    reviews_count INTEGER,

    -- 来源信息
    source VARCHAR(50),
    url VARCHAR(1000),
    images TEXT[],

    -- AI分析
    ai_analyzed BOOLEAN DEFAULT FALSE,
    opportunity_score DECIMAL(3,2),
    target_audience VARCHAR(100),
    recommendation_reason TEXT,

    -- 趋势数据
    price_trend DECIMAL(5,2),
    ranking_trend INTEGER,
    competitor_count INTEGER,

    -- 时间戳
    crawled_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,

    -- 索引
    CONSTRAINT products_asin_key UNIQUE (asin)
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_opportunity_score ON products(opportunity_score DESC);
CREATE INDEX idx_products_crawled_at ON products(crawled_at DESC);
```

### keywords表（关键词图谱）

```sql
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) UNIQUE NOT NULL,

    -- 关系网络
    related_keywords TEXT[],
    related_markets TEXT[],
    related_platforms TEXT[],

    -- 趋势数据
    frequency INTEGER DEFAULT 0,
    trend VARCHAR(20), -- 'rising', 'stable', 'declining'
    trend_score DECIMAL(3,2),

    -- 商业价值
    opportunity_score DECIMAL(3,2),
    competition_level VARCHAR(20),
    search_volume INTEGER,

    -- 时间
    first_seen_at TIMESTAMP WITH TIME ZONE,
    last_seen_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_keywords_trend ON keywords(trend_score DESC);
CREATE INDEX idx_keywords_opportunity ON keywords(opportunity_score DESC);
```

---

## OpenClaw配置

### channels.json（完整配置）

```json
{
  "version": 1,
  "channels": [
    {
      "id": "rss-crawler",
      "name": "RSS资讯爬虫",
      "module": "./channels/rss-crawler.js",
      "enabled": true,
      "schedule": "0 */2 * * *",
      "timeout": 300000
    },
    {
      "id": "oxylabs-monitor",
      "name": "产品监控（Oxylabs）",
      "module": "./channels/oxylabs-monitor.js",
      "enabled": true,
      "schedule": "0 * * * *",
      "timeout": 600000
    },
    {
      "id": "content-classifier",
      "name": "智能内容分类",
      "module": "./channels/content-classifier.js",
      "enabled": true,
      "schedule": "30 * * * * *",
      "timeout": 300000
    },
    {
      "id": "trend-discovery",
      "name": "趋势发现与机会识别",
      "module": "./channels/trend-discovery.js",
      "enabled": true,
      "schedule": "0 */6 * * *",
      "timeout": 600000
    }
  ]
}
```

---

## API端点需求

需要在FastAPI中添加以下端点：

### 批量操作端点

```python
# api/batch_operations.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/api/v1/batch", tags=["batch"])

@router.post("/articles")
async def batch_create_articles(
    articles: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """批量创建文章"""
    # 批量插入逻辑
    pass

@router.post("/products")
async def batch_create_products(
    products: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """批量创建产品"""
    # 批量插入逻辑
    pass

@router.get("/unclassified")
async def get_unclassified_items(
    type: str = "all",
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取未分类的内容"""
    # 查询逻辑
    pass

@router.post("/batch-update")
async def batch_update_classifications(
    updates: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """批量更新分类"""
    # 更新逻辑
    pass
```

---

## 实施步骤

### 阶段1：基础搭建（1-2天）

1. ✅ 创建数据库表结构
2. ✅ 创建OpenClaw channels
3. ✅ 实现AI分析功能

### 阶段2：测试验证（1天）

1. ✅ 手动测试Oxylabs channel
2. ✅ 验证AI分类准确性
3. ✅ 测试趋势发现

### 阶段3：生产部署（1天）

1. ✅ 配置定时调度
2. ✅ 设置监控告警
3. ✅ 性能优化

---

**文档版本**: 1.0
**创建日期**: 2026-03-12
