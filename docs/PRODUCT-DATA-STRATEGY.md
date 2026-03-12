# ZenConsult 产品数据扩展策略

## 📊 当前问题分析

### 问题1：文章来源数量不足
- **当前**: 16个信息源（15个启用）
- **问题**: 覆盖面有限，尤其东南亚、拉美市场数据偏少
- **影响**: 用户无法获得全面的市场洞察

### 问题2：缺少行业/产品数据（更严重）
- **当前**: 只有资讯文章，没有实际的产品数据
- **用户需求**:
  - 热销产品榜单
  - 品类趋势分析
  - 价格区间数据
  - 竞争对手监控
  - 选品建议
- **痛点**: 类似 SellerSprite 的产品数据平台功能缺失

---

## 🎯 解决方案框架

```
┌─────────────────────────────────────────────────────────────────┐
│                     ZenConsult 数据架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │  资讯文章层    │  │  产品数据层    │  │  市场洞察层    │       │
│  │ (已实现)      │  │  (待实现)     │  │  (AI分析)     │       │
│  ├───────────────┤  ├───────────────┤  ├───────────────┤       │
│  │ • 行业新闻    │  │ • 热销榜单    │  │ • 趋势预测    │       │
│  │ • 政策变化    │  │ • 品类数据    │  │ • 机会评分    │       │
│  │ • 平台动态    │  │ • 价格追踪    │  │ • 选品推荐    │       │
│  │ • 专家观点    │  │ • 竞品监控    │  │ • 风险评估    │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 数据来源扩展方案

### 1. 资讯文章扩展（短期）

#### 东南亚新增来源
| 来源 | 类型 | 覆盖国家 | URL |
|------|------|---------|-----|
| DealStreetAsia | RSS | 东南亚全域 | https://www.dealstreetasia.com/feed/ |
| KrASIA | RSS | 东南亚科技 | https://kr-asia.com/feed |
| Vietnam News | RSS | 越南 | https://vietnamnews.vn/economy/rss |
| Bangkok Post | RSS | 泰国 | https://www.bangkokpost.com/business/data |
| Philippine Daily Inquirer | RSS | 菲律宾 | https://business.inquirer.net/feed |
| Kompas | RSS | 印尼 | https://economia.bisnis.com/feed |

#### 拉美新增来源
| 来源 | 类型 | 覆盖国家 | URL |
|------|------|---------|-----|
| Neobiz | HTTP | 巴西 | https://neobiz.com.br/blog |
| E-commerce Brasil | RSS | 巴西 | https://ecommercebrasil.com.br/feed |
| Webcapitalista | RSS | 拉美 | https://webcapitalista.com/feed |
| Tienda Pago | RSS | 秘鲁/智利 | https://blog.tiendapago.com/feed |

#### 官方平台博客
| 平台 | 类型 | 价值 | URL |
|------|------|------|-----|
| TikTok Shop Blog | RSS | 直播带货趋势 | https://sellertik.tiktok.com/feed |
| Shopee Seller Blog | HTTP | 政策更新 | https://shopee.cn/blog/seller |
| Lazada Seller News | RSS | 平台动态 | https://seller.lazada.com/blog/feed |
| Mercado Libre Blog | RSS | 拉美平台 | https://mercadolibre.com/blog/feed |

---

### 2. 产品数据获取方案（核心）

#### 方案对比

| 方案 | 优点 | 缺点 | 成本 | 推荐度 |
|------|------|------|------|--------|
| **官方API** | 数据准确、稳定、合规 | 申请难、限制多、费用高 | ⭐⭐⭐ | ⭐⭐⭐ |
| **网页爬虫** | 灵活、数据全、免费 | 维护成本高、可能违规 | ⭐ | ⭐⭐⭐⭐ |
| **第三方API** | 开箱即用、稳定 | 费用高、数据依赖 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **混合方案** | 平衡成本与效果 | 实现复杂 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

#### 推荐方案：**混合方案**

```
┌─────────────────────────────────────────────────────────────────┐
│                      混合数据获取架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  免费公共数据  │  │  第三方API     │  │  自建爬虫      │    │
│  │  (低成本)      │  │  (中成本)      │  │  (高投入)      │    │
│  ├────────────────┤  ├────────────────┤  ├────────────────┤    │
│  │ • Best Sellers │  │ • RapidAPI     │  │ • 平台页面     │    │
│  │ • 官方榜单     │  │ • Keepa替代品  │  │ • 价格监控     │    │
│  │ • 趋势报告     │  │ • 数据聚合商   │  │ • 评论分析     │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│           │                    │                    │          │
│           └────────────────────┴────────────────────┘          │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                        │
│              │    统一数据仓库         │                        │
│              │  (PostgreSQL + Pinecone)│                       │
│              └─────────────────────────┘                        │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                        │
│              │   AI分析 & 可视化       │                        │
│              │   (关键词云增强版)      │                        │
│              └─────────────────────────┘                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术实现方案

### Phase 1: 免费公共数据（快速启动）

#### 1.1 Amazon Best Sellers 爬虫

```python
# crawler/products/amazon_best_sellers.py

import asyncio
from typing import List, Dict
from bs4 import BeautifulSoup
from httpx import AsyncClient

class AmazonBestSellersCrawler:
    """Amazon Best Sellers 榜单爬虫"""

    CATEGORIES = {
        'th': {
            'url': 'https://www.amazon.co.th/Best-Sellers/zgbs/ref=zg_bs_unv_0_th_1',
            'name': 'Amazon Thailand'
        },
        'sg': {
            'url': 'https://www.amazon.sg/Best-Sellers/zgbs/ref=zg_bs_sg_1',
            'name': 'Amazon Singapore'
        },
        # ... 更多国家
    }

    async def fetch_category(self, country: str, category: str = 'all') -> List[Dict]:
        """获取指定国家的热销榜单"""
        config = self.CATEGORIES.get(country)
        if not config:
            return []

        async with AsyncClient() as client:
            response = await client.get(config['url'])
            soup = BeautifulSoup(response.text, 'html.parser')

            products = []
            for item in soup.select('.zg-item-immersion')[:50]:  # Top 50
                product = {
                    'rank': item.select_one('.zg-badge-text')?.text,
                    'title': item.select_one('div[data-cy="title-recipe-title"]')?.text.strip(),
                    'price': item.select_one('.a-price-whole')?.text,
                    'rating': item.select_one('.a-icon-alt')?.text,
                    'reviews_count': item.select_one('.a-size-base')?.text,
                    'link': item.select_one('a.a-link-normal')?.get('href'),
                    'image': item.select_one('.a-dynamic-image')?.get('src'),
                    'country': country,
                    'platform': 'amazon',
                    'category': category,
                }
                products.append(product)

            return products
```

#### 1.2 Shopee 热销榜爬虫

```python
# crawler/products/shopee_trending.py

class ShopeeTrendingCrawler:
    """Shopee 热销商品爬虫"""

    MARKETS = {
        'th': 'https://shopee.co.th',
        'vn': 'https://shopee.vn',
        'my': 'https://shopee.com.my',
        'sg': 'https://shopee.sg',
        'id': 'https://shopee.co.id',
        'ph': 'https://shopee.ph',
    }

    async def fetch_trending(self, country: str, category: str = None) -> List[Dict]:
        """
        获取Shopee热销榜单

        注意: Shopee是动态渲染页面，需要使用 Playwright 或 API
        """
        # 方法1: 使用Playwright (推荐)
        # 方法2: 分析API调用（需要逆向工程）
        pass
```

#### 1.3 TikTok Shop 热门商品

```python
# crawler/products/tiktok_shop.py

class TikTokShopCrawler:
    """TikTok Shop 热门商品爬虫"""

    async def fetch_trending_products(self, country: str) -> List[Dict]:
        """
        获取TikTok Shop热门商品

        数据来源:
        - TikTok Shop Discovery页
        - 热门直播间的商品
        - 达人推荐商品
        """
        pass
```

### Phase 2: 第三方API集成（稳定数据）

#### 2.1 RapidAPI 集成

**推荐API**:
1. **Real-Time Product Search** ([RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-product-search))
   - 免费额度: 100次/月
   - 功能: 实时产品搜索、价格比较

2. **Amazon Product Data** ([RapidAPI](https://rapidapi.com/opus-serve-opus-serve-default/api/amazon-product-data6))
   - 功能: 产品趋势分析、消费者情感分析

```python
# integrations/rapidapi_client.py

import httpx

class RapidAPIProductClient:
    """RapidAPI 产品数据客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://real-time-product-search.p.rapidapi.com"

    async def search_products(self, query: str, country: str = 'us') -> List[Dict]:
        """搜索产品"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                params={
                    'q': query,
                    'country': country,
                    'language': 'en'
                },
                headers={
                    'X-RapidAPI-Key': self.api_key,
                    'X-RapidAPI-Host': 'real-time-product-search.p.rapidapi.com'
                }
            )
            return response.json().get('data', [])
```

### Phase 3: AI增强分析（智能洞察）

```python
# processors/product_insight.py

class ProductInsightAnalyzer:
    """产品洞察分析器"""

    async def analyze_trending_products(self, products: List[Dict]) -> Dict:
        """
        分析热销产品趋势

        输出:
        {
            'top_categories': [...],  # 热门品类
            'price_ranges': {...},    # 价格分布
            'emerging_trends': [...], # 新兴趋势
            'opportunities': [...],   # 机会点
        }
        """
        pass

    async def recommend_products(self, country: str, budget: float) -> List[Dict]:
        """
        根据国家+预算推荐产品

        考虑因素:
        - 市场需求
        - 竞争程度
        - 利润空间
        - 供应链难度
        """
        pass
```

---

## 🗄️ 数据模型设计

### Product 表（产品数据）

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- 产品分类
    category VARCHAR(100),           -- 一级分类（如：电子产品）
    subcategory VARCHAR(100),        -- 二级分类（如：手机配件）
    tags JSONB,                      -- 标签数组

    -- 价格信息
    price DECIMAL(10,2),
    price_range VARCHAR(50),         -- 价格区间（如：$10-50）

    -- 平台信息
    platform VARCHAR(50),            -- amazon, shopee, lazada...
    country VARCHAR(10),             -- us, th, vn, my...
    platform_product_id VARCHAR(200),-- 平台产品ID

    -- 销售指标
    rank INTEGER,                    -- 排名
    sales_count INTEGER,             -- 销量（估算）
    rating DECIMAL(3,2),             -- 评分
    reviews_count INTEGER,           -- 评论数

    -- 趋势数据
    trend_rank INTEGER,              -- 趋势排名
    trend_direction VARCHAR(10),     -- up/down/stable
    trend_days INTEGER,              -- 榜单停留天数

    -- 图片/链接
    image_url TEXT,
    product_url TEXT,

    -- 元数据
    source VARCHAR(100),             -- 数据来源
    crawled_at TIMESTAMP,
    updated_at TIMESTAMP,

    -- AI分析
    opportunity_score DECIMAL(3,2),  -- 机会评分
    difficulty_score DECIMAL(3,2),   -- 难度评分
    profit_margin DECIMAL(5,2),      -- 预估利润率
    ai_insights JSONB,               -- AI分析结果
);

CREATE INDEX idx_products_platform_country ON products(platform, country);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_trend_rank ON products(trend_rank);
```

---

## 📊 关键词云 2.0 设计

### 当前 vs 目标

| 维度 | 当前（文章版） | 目标（产品+文章） |
|------|--------------|------------------|
| **国家** | 显示国家列表 | 显示国家 + 市场规模 |
| **平台** | 平台标签 | 平台 + 热销品类 |
| **品类** | 静态标签 | 实际热销品类 |
| **信息源** | 文章来源 | 文章 + 产品榜单 |
| **数据** | 134篇文章 | 数万产品数据 |

### 新UI设计

```
┌─────────────────────────────────────────────────────────────┐
│  🌍 东南亚市场                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🇹🇭 泰国  |  市场规模: $190亿  |  产品数: 15,234        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 热门品类: 美妆(35%), 电子产品(25%), 家居(18%)        │  │
│  │                                                      │  │
│  │ 📱 Shopee  |  🛍️ Lazada  |  🎬 TikTok Shop          │  │
│  │ 5,234商品   3,102商品      2,456商品               │  │
│  │                                                      │  │
│  │ 热销商品:                                           │  │
│  │ • 无线蓝牙耳机 (¥89)  ↗️ 热度上升                   │  │
│  │ • 韩式护肤套装 (¥156)  🔥 新晋爆款                  │  │
│  │ • 智能手表带 (¥45)   💰 高利润                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  🇻🇳 越南  |  市场规模: $130亿  |  产品数: 12,890        │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 实施路线图

### Sprint 1: 基础爬虫（2周）
- [ ] Amazon Best Sellers 爬虫
- [ ] 数据表结构设计与创建
- [ ] 基础API端点（产品列表、详情）
- [ ] 前端产品展示页面

**目标**: 获取前1000个产品数据

### Sprint 2: 多平台扩展（2周）
- [ ] Shopee 热销榜爬虫
- [ ] TikTok Shop 商品爬虫
- [ ] 数据清洗与去重
- [ ] 品类自动分类

**目标**: 覆盖3个平台，10,000+ 产品

### Sprint 3: 第三方API（1周）
- [ ] RapidAPI 集成
- [ ] 价格监控功能
- [ ] 趋势追踪

**目标**: 数据稳定性和准确性提升

### Sprint 4: AI分析（2周）
- [ ] 产品趋势分析
- [ ] 机会评分算法
- [ ] 选品推荐引擎

**目标**: 提供智能洞察

### Sprint 5: 前端升级（1周）
- [ ] 关键词云2.0
- [ ] 产品对比功能
- [ ] 市场分析仪表板

**目标**: 完整的用户体验

---

## 💡 创新功能

### 1. 实时选品助手
```typescript
// 用户输入: "我想在泰国卖美妆产品，预算5000元"
// 系统输出:
{
  "recommended_products": [
    {
      "name": "韩式护肤套装",
      "estimated_profit": "35%",
      "monthly_sales": "5000+",
      "competition": "medium",
      "supplier_links": ["1688", "Alibaba"]
    }
  ],
  "market_insights": {
    "trending_keywords": ["护肤", "面膜", "精华液"],
    "best_price_range": "¥100-200",
    "top_platforms": ["Shopee", "TikTok Shop"]
  }
}
```

### 2. 竞品监控
```typescript
// 监控指定产品的价格、销量、评论变化
{
  "product_id": "xxx",
  "competitors": [
    {
      "seller": "Seller A",
      "price": "¥89",
      "sales": "1200/月",
      "rating": 4.8
    }
  ]
}
```

### 3. 跨平台套利检测
```typescript
// 发现同一产品在不同平台的价格差异
{
  "product": "无线蓝牙耳机",
  "price_difference": {
    "shopee": "¥89",
    "lazada": "¥105",
    "tiktok": "¥95"
  },
  "opportunity": "从Shopee采购，在Lazada销售"
}
```

---

## 📖 参考资源

### 技术文档
- [Amazon SP-API 文档](https://developer-docs.amazon.com/sp-api)
- [ScrapeGraphAI 教程](https://scrapegraphai.com/blog/ai-web-scraping)
- [Web Scraping vs API 2026指南](https://scrapewise.ai/blogs/web-scraping-vs-api-retail-data-2026-guide)

### 数据平台
- [RapidAPI - 实时产品搜索](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-product-search)
- [SellerSprite](https://www.sellersprite.com/) - 亚马逊产品研究
- [Helium 10](https://www.helium10.com/) - 亚马逊工具套件

### 行业报告
- [Google e-Conomy SEA Report](https://www.thinkwithgoogle.com/)
- [Temasek SEA e-Commerce Report](https://www.temasek.com/)
- [Bain Southeast Asia Consumer Insights](https://www.bain.com/)

---

## ⚠️ 风险与注意事项

### 法律风险
- **爬虫合规性**: 确保遵守 `robots.txt` 和服务条款
- **数据保护**: GDPR、CCPA等隐私法规
- **API使用**: 遵守平台API使用政策

### 技术风险
- **反爬虫机制**: IP封禁、验证码、动态渲染
- **数据质量**: 假数据、价格不一致、销量造假
- **维护成本**: 网站结构变化需要更新爬虫

### 商业风险
- **竞争压力**: 已有成熟产品（SellerSprite, Jungle Scout）
- **数据更新**: 需要持续更新保持数据新鲜度
- **用户教育**: 用户可能更信任成熟产品

---

## 🎯 成功指标

| 指标 | 目标 (3个月) | 目标 (6个月) |
|------|-------------|-------------|
| 产品数据量 | 50,000+ | 500,000+ |
| 覆盖平台 | 5个 | 10+个 |
| 覆盖国家 | 10个 | 20+个 |
| 数据更新频率 | 每日 | 每小时 |
| 用户留存率 | 20% | 40% |
| API调用量 | 10K/天 | 100K/天 |
