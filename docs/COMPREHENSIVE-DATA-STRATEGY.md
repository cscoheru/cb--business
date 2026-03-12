# ZenConsult 全方位数据战略（含评论分析）

## 🎯 四大支柱（按优先级）

```
┌─────────────────────────────────────────────────────────────────────┐
│                       ZenConsult 数据战略                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ① 用户评论分析 ⭐⭐⭐⭐⭐ (核心价值)                                 │
│     └─> 真实用户声音 | 产品痛点 | 竞品对比                            │
│                                                                       │
│  ② 产品数据获取 ⭐⭐⭐⭐                                              │
│     └─> 热销榜单 | 价格追踪 | 品类趋势                                │
│                                                                       │
│  ③ 文章来源扩展 ⭐⭐⭐                                                │
│     └─> 行业资讯 | 政策变化 | 专家观点                                 │
│                                                                       │
│  ④ 第三方API集成 ⭐⭐                                                 │
│     └─> 数据补充 | 稳定性保障                                         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ① 用户评论分析（核心创新）

### 为什么评论分析是金矿？

| 数据类型 | 时效性 | 真实性 | 商业价值 | 获取难度 |
|---------|--------|--------|----------|---------|
| **用户评论** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 产品榜单 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 行业文章 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |

### 评论数据能回答的问题

#### 1️⃣ 选品决策
```
❌ 传统方式: "这个品类很火"
✅ 评论分析: "这个产品虽然火，但用户普遍抱怨电池续航问题，
              如果你能解决这个痛点，就是机会"
```

#### 2️⃣ 痛点挖掘
```
用户评论: "用了3个月就坏了"、"客服不回复"、"物流太慢"
↓ AI分析
痛点分类: 质量问题(35%), 售后问题(28%), 物流问题(22%)
↓ 机会发现
解决质量痛点 = 高利润机会
```

#### 3️⃣ 竞品分析
```
竞品A: 4.2星 | 评论发现 → "包装精美但性价比低"
竞品B: 3.8星 | 评论发现 → "便宜但质量不稳定"
你的定位: "质量可靠 + 合理价格 + 超级售后"
```

#### 4️⃣ 趋势预测
```
评论关键词变化:
第1月: "外观好看"(40%), "价格便宜"(30%)
第3月: "电池耐用"(35%), "充电快"(25%)
↓ 趋势预测
用户开始重视功能性，而非外观
↓ 选品建议
选择功能性强的产品
```

---

### 技术方案设计

#### 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         评论数据采集架构                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     数据采集层                                │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │  Amazon 评论  │  Shopee 评论  │  TikTok 评论  │  Lazada 评论  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     数据处理层                                │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │  • 情感分析     │  • 关键词提取   │  • 主题聚类              │   │
│  │  • 翻译(多语言) │  • 去重合并     │  • 质量过滤              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     AI洞察层                                  │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │  • 痛点识别     │  • 竞品对比     │  • 趋势预测              │   │
│  │  • 机会发现     │  • 选品推荐     │  • 风险评估              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     可视化层                                  │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │  词云图  │  情感趋势图  │  竞品对比表  │  机会评分卡          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

#### 数据模型

```sql
-- 产品评论表
CREATE TABLE product_reviews (
    id UUID PRIMARY KEY,

    -- 产品关联
    product_id UUID REFERENCES products(id),
    platform_product_id VARCHAR(200),  -- 平台产品ID

    -- 评论基本信息
    platform VARCHAR(50),              -- amazon, shopee, lazada, tiktok
    country VARCHAR(10),               -- us, th, vn, my...

    -- 评论内容
    review_id VARCHAR(200) UNIQUE,     -- 平台评论ID
    rating INTEGER,                    -- 1-5星
    title TEXT,                        -- 评论标题
    content TEXT,                      -- 评论内容
    translated_content TEXT,           -- 翻译后的内容

    -- 评论元数据
    author_name VARCHAR(200),
    author_verified BOOLEAN,           -- 是否验证购买
    review_date DATE,
    helpful_count INTEGER,             -- 有用投票数
    media_urls JSONB,                  -- 图片/视频URL

    -- AI分析结果
    sentiment DECIMAL(4,3),            -- 情感分数 (-1到1)
    sentiment_label VARCHAR(20),       -- positive/neutral/negative
    keywords JSONB,                    -- 关键词数组
    topics JSONB,                      -- 主题分类
    pain_points JSONB,                 -- 痛点标签
    mentioned_features JSONB,          -- 提到的产品特性

    -- 客服/物流标签
    tags JSONB,                        -- ['质量问题', '物流慢', '客服好'...]

    -- 元数据
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,

    -- 索引
    INDEX idx_reviews_platform_country (platform, country),
    INDEX idx_reviews_product (product_id),
    INDEX idx_reviews_sentiment (sentiment),
    INDEX idx_reviews_date (review_date)
);

-- 评论汇总表（用于快速查询）
CREATE TABLE review_summaries (
    product_id UUID PRIMARY KEY REFERENCES products(id),

    -- 基础统计
    total_reviews INTEGER,
    average_rating DECIMAL(3,2),
    rating_distribution JSONB,         -- {5: 120, 4: 30, ...}

    -- 情感分析
    sentiment_score DECIMAL(4,3),
    positive_ratio DECIMAL(4,3),       -- 好评率
    negative_ratio DECIMAL(4,3),       -- 差评率

    -- 关键词/主题
    top_keywords JSONB,                -- [{word: "质量", count: 120}, ...]
    top_topics JSONB,                  -- [{topic: "电池", sentiment: -0.3}, ...]
    top_pain_points JSONB,             -- [{point: "续航", count: 45, severity: "high"}]

    -- 竞品对比
    vs_competitors JSONB,              -- {competitor_id: {better_at: [...], worse_at: [...]}}

    updated_at TIMESTAMP,

    INDEX idx_summary_product (product_id)
);
```

---

### 具体实现

#### Phase 1: 评论采集器（2周）

```python
# crawler/reviews/amazon_reviews.py

import asyncio
from typing import List, Dict
from bs4 import BeautifulSoup
from httpx import AsyncClient, HTTPError
from urllib.parse import urlencode

class AmazonReviewCrawler:
    """Amazon评论爬虫"""

    async def fetch_reviews(
        self,
        product_id: str,
        country: str = 'us',
        max_pages: int = 10
    ) -> List[Dict]:
        """
        获取Amazon产品评论

        Args:
            product_id: Amazon产品ID (ASIN)
            country: 国家代码 (us, uk, de, jp...)
            max_pages: 最大爬取页数

        Returns:
            评论列表
        """
        base_url = self._get_base_url(country)
        reviews = []

        async with AsyncClient() as client:
            for page in range(1, max_pages + 1):
                params = {
                    'reviewerType': 'all_reviews',
                    'pageNumber': page,
                    'sortBy': 'recent'
                }

                url = f"{base_url}/product-reviews/{product_id}?{urlencode(params)}"

                try:
                    response = await client.get(url, timeout=30)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # 检查是否有评论
                    if not soup.select('[data-hook="review"]'):
                        break

                    # 解析评论
                    page_reviews = self._parse_reviews(soup, product_id, country)
                    reviews.extend(page_reviews)

                    # 避免请求过快
                    await asyncio.sleep(2)

                except HTTPError as e:
                    print(f"Error fetching page {page}: {e}")
                    break

        return reviews

    def _parse_reviews(self, soup: BeautifulSoup, product_id: str, country: str) -> List[Dict]:
        """解析评论HTML"""
        reviews = []

        for review_elem in soup.select('[data-hook="review"]'):
            try:
                # 基本信息
                review_id = review_elem.get('id', '')
                rating = self._extract_rating(review_elem)
                title = self._safe_select(review_elem, '[data-hook="review-title"] span')
                content = self._safe_select(review_elem, '[data-hook="review-body"] span')
                date = self._extract_date(review_elem)
                author = self._safe_select(review_elem, '.a-profile-name')
                verified = 'Verified Purchase' in review_elem.get_text()

                # 有用投票数
                helpful = self._safe_select(review_elem, '[data-hook="helpful-vote-statement"]')
                helpful_count = self._extract_count(helpful) if helpful else 0

                # 图片
                images = [img.get('src') for img in review_elem.select('.review-image-tile img')]

                review = {
                    'review_id': review_id,
                    'platform_product_id': product_id,
                    'platform': 'amazon',
                    'country': country,
                    'rating': rating,
                    'title': title,
                    'content': content,
                    'author_name': author,
                    'author_verified': verified,
                    'review_date': date,
                    'helpful_count': helpful_count,
                    'media_urls': images,
                }

                reviews.append(review)

            except Exception as e:
                print(f"Error parsing review: {e}")
                continue

        return reviews

    def _get_base_url(self, country: str) -> str:
        """获取各国Amazon域名"""
        domains = {
            'us': 'https://www.amazon.com',
            'uk': 'https://www.amazon.co.uk',
            'de': 'https://www.amazon.de',
            'jp': 'https://www.amazon.co.jp',
            'th': 'https://www.amazon.co.th',
            'sg': 'https://www.amazon.sg',
        }
        return domains.get(country, 'https://www.amazon.com')

    def _extract_rating(self, elem) -> int:
        """提取评分"""
        rating_class = elem.select_one('[data-hook="review-star-rating"]')
        if rating_class:
            rating_text = rating_class.get_text()
            return int(rating_text.split('.')[0].replace('(', ''))
        return 0

    def _safe_select(self, elem, selector: str) -> str:
        """安全选择元素"""
        found = elem.select_one(selector)
        return found.get_text(strip=True) if found else ''

    def _extract_date(self, elem) -> str:
        """提取日期"""
        date_elem = elem.select_one('[data-hook="review-date"]')
        if date_elem:
            date_text = date_elem.get_text()
            # "Reviewed in the United States on March 12, 2026"
            # 解析并返回ISO格式
            return date_text
        return None

    def _extract_count(self, text: str) -> int:
        """提取数字"""
        import re
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0


# Shopee评论爬虫
class ShopeeReviewCrawler:
    """Shopee评论爬虫（需要处理API）"""

    async def fetch_reviews(self, shop_id: str, item_id: str, country: str = 'th') -> List[Dict]:
        """
        获取Shopee评论

        Shopee使用API: https://shopee.{country}/api/v4/item/get_comment
        """
        base_url = f"https://shopee.{self._get_domain(country)}"
        api_url = f"{base_url}/api/v4/item/get_comment"

        reviews = []
        offset = 0
        limit = 20  # 每页数量

        while True:
            params = {
                'itemid': item_id,
                'shopid': shop_id,
                'filter': 0,  # 0: 全部, 1: 有图, 2: 好评, 3: 中评, 4: 差评
                'offset': offset,
                'limit': limit,
                'flag': 1,
                'type': 5,
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(api_url, params=params)
                    data = response.json()

                    if 'data' not in data or not data['data']['comments']:
                        break

                    # 解析评论
                    for comment in data['data']['comments']:
                        review = {
                            'review_id': f"{shop_id}_{item_id}_{comment['comment_id']}",
                            'platform_product_id': f"{shop_id}_{item_id}",
                            'platform': 'shopee',
                            'country': country,
                            'rating': comment['rating_star'],
                            'content': comment.get('text', ''),
                            'author_name': comment.get('author', {}).get('username', ''),
                            'review_date': comment.get('ctime'),
                            'media_urls': comment.get('images', []),
                        }
                        reviews.append(review)

                    offset += limit

                    if offset >= data['data']['total']:
                        break

                    await asyncio.sleep(1)

            except Exception as e:
                print(f"Error: {e}")
                break

        return reviews

    def _get_domain(self, country: str) -> str:
        domains = {
            'th': 'co.th',
            'vn': 'vn',
            'my': 'com.my',
            'sg': 'sg',
            'id': 'co.id',
            'ph': 'ph',
        }
        return domains.get(country, 'co.th')
```

#### Phase 2: AI分析引擎（2周）

```python
# analyzers/review_analyzer.py

from typing import List, Dict
import json
from openai import OpenAI
from collections import Counter

class ReviewAnalyzer:
    """评论分析引擎"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def analyze_batch(self, reviews: List[Dict]) -> Dict:
        """
        批量分析评论

        Returns:
            {
                'total_reviews': 100,
                'average_rating': 4.2,
                'sentiment_score': 0.35,
                'top_keywords': [...],
                'pain_points': [...],
                'opportunities': [...],
                'competitor_insights': {...}
            }
        """
        if not reviews:
            return self._empty_result()

        # 基础统计
        result = {
            'total_reviews': len(reviews),
            'average_rating': sum(r['rating'] for r in reviews) / len(reviews),
            'rating_distribution': self._rating_distribution(reviews),
        }

        # 情感分析
        result['sentiment_analysis'] = await self._sentiment_analysis(reviews)

        # 关键词提取
        result['top_keywords'] = self._extract_keywords(reviews)

        # 痛点识别
        result['pain_points'] = await self._identify_pain_points(reviews)

        # 机会发现
        result['opportunities'] = await self._discover_opportunities(reviews)

        # 主题聚类
        result['topics'] = await self._cluster_topics(reviews)

        return result

    async def _sentiment_analysis(self, reviews: List[Dict]) -> Dict:
        """情感分析"""
        positive = neutral = negative = 0
        sentiment_scores = []

        for review in reviews:
            # 使用LLM进行情感分析
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个评论情感分析专家。分析用户评论的情感倾向。"
                    },
                    {
                        "role": "user",
                        "content": f"""
分析以下评论的情感（仅返回JSON，不要其他内容）:

标题: {review.get('title', '')}
内容: {review.get('content', '')}
评分: {review.get('rating', 0)}

返回格式:
{{
    "sentiment": "positive/neutral/negative",
    "score": -1到1之间的分数,
    "key_emotions": ["开心", "失望", "愤怒"...]
}}
"""
                    }
                ],
                temperature=0,
            )

            result = json.loads(response.choices[0].message.content)

            sentiment = result.get('sentiment', 'neutral')
            score = result.get('score', 0)

            if sentiment == 'positive':
                positive += 1
            elif sentiment == 'negative':
                negative += 1
            else:
                neutral += 1

            sentiment_scores.append(score)

        return {
            'positive_ratio': positive / len(reviews),
            'neutral_ratio': neutral / len(reviews),
            'negative_ratio': negative / len(reviews),
            'average_score': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
        }

    def _extract_keywords(self, reviews: List[Dict]) -> List[Dict]:
        """提取高频关键词"""
        import re
        from collections import Counter

        # 停用词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
                    '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                    'you', 'the', 'is', 'a', 'and', 'to', 'of', 'it', 'in', 'that'}

        all_words = []

        for review in reviews:
            content = review.get('content', '')
            # 简单分词（实际应使用jieba或类似工具）
            words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', content)
            all_words.extend([w for w in words if w not in stopwords])

        # 统计词频
        counter = Counter(all_words)

        return [
            {'word': word, 'count': count}
            for word, count in counter.most_common(50)
        ]

    async def _identify_pain_points(self, reviews: List[Dict]) -> List[Dict]:
        """识别产品痛点"""
        # 收集差评（1-3星）
        bad_reviews = [r for r in reviews if r.get('rating', 5) <= 3]

        if not bad_reviews:
            return []

        # 使用LLM总结痛点
        reviews_text = "\n".join([
            f"- {r.get('content', '')}"
            for r in bad_reviews[:20]  # 限制数量
        ])

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是产品痛点分析专家。从用户差评中提取产品痛点。"
                },
                {
                    "role": "user",
                    "content": f"""
分析以下差评，提取产品痛点（仅返回JSON）:

{reviews_text}

返回格式:
{{
    "pain_points": [
        {{
            "point": "痛点描述",
            "severity": "high/medium/low",
            "count": 用户提及次数,
            "examples": ["原文摘录1", "原文摘录2"]
        }}
    ]
}}
"""
                }
            ],
            temperature=0,
        )

        result = json.loads(response.choices[0].message.content)
        return result.get('pain_points', [])

    async def _discover_opportunities(self, reviews: List[Dict]) -> List[Dict]:
        """发现商业机会"""
        # 分析竞品弱点 = 你的机会
        bad_reviews = [r for r in reviews if r.get('rating', 5) <= 3]

        if len(bad_reviews) < 5:
            return []

        reviews_text = "\n".join([
            f"- {r.get('content', '')}"
            for r in bad_reviews[:15]
        ])

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是电商选品专家。从用户抱怨中发现商业机会。"
                },
                {
                    "role": "user",
                    "content": f"""
分析以下差评，发现商业机会（仅返回JSON）:

{reviews_text}

返回格式:
{{
    "opportunities": [
        {{
            "opportunity": "机会描述",
            "priority": "high/medium/low",
            "solution": "可能的解决方案",
            "target_audience": "目标用户群"
        }}
    ]
}}
"""
                }
            ],
            temperature=0.3,
        )

        result = json.loads(response.choices[0].message.content)
        return result.get('opportunities', [])

    async def _cluster_topics(self, reviews: List[Dict]) -> List[Dict]:
        """主题聚类"""
        # 使用LLM对评论进行主题分类
        reviews_sample = reviews[:30]
        reviews_text = "\n".join([
            f"{i+1}. {r.get('content', '')}"
            for i, r in enumerate(reviews_sample)
        ])

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是主题分析专家。将评论按照讨论的主题进行分类。"
                },
                {
                    "role": "user",
                    "content": f"""
将以下评论按主题分类（仅返回JSON）:

{reviews_text}

常见主题类型: 质量问题、物流速度、客服态度、价格性价比、产品功能、使用体验

返回格式:
{{
    "topics": [
        {{
            "topic": "主题名称",
            "description": "主题描述",
            "count": 评论数量,
            "sentiment": "正面/中性/负面",
            "examples": ["原文1", "原文2"]
        }}
    ]
}}
"""
                }
            ],
            temperature=0,
        )

        result = json.loads(response.choices[0].message.content)
        return result.get('topics', [])
```

#### Phase 3: 可视化界面（1周）

```typescript
// components/product/review-insights.tsx

export function ReviewInsights({ productId }: { productId: string }) {
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    fetch(`/api/v1/products/${productId}/review-insights`)
      .then(r => r.json())
      .then(data => setInsights(data));
  }, [productId]);

  if (!insights) return <Loading />;

  return (
    <div className="space-y-6">
      {/* 情感概览 */}
      <Card>
        <h3>用户情感分析</h3>
        <SentimentGauge
          positive={insights.sentiment_analysis.positive_ratio}
          negative={insights.sentiment_analysis.negative_ratio}
        />
      </Card>

      {/* 痛点云图 */}
      <Card>
        <h3>用户痛点</h3>
        <PainPointCloud points={insights.pain_points} />
      </Card>

      {/* 关键词云 */}
      <Card>
        <h3>讨论热点</h3>
        <KeywordCloud words={insights.top_keywords} />
      </Card>

      {/* 机会列表 */}
      <Card>
        <h3>发现的机会</h3>
        <OpportunityList opportunities={insights.opportunities} />
      </Card>

      {/* 时间趋势 */}
      <Card>
        <h3>情感趋势</h3>
        <SentimentTrendChart data={insights.sentiment_timeline} />
      </Card>
    </div>
  );
}
```

---

### 前端展示设计

#### 产品页面增强版

```
┌─────────────────────────────────────────────────────────────────┐
│  无线蓝牙耳机 - 深度分析                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  💡 AI选品建议: 🔥 高潜力 | 竞争: 中等 | 利润: 35-45%            │
│                                                                   │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │  基础数据    │  用户评价    │  痛点分析    │  机会发现    │     │
│  ├─────────────┼─────────────┼─────────────┼─────────────┤     │
│  │ 💰 ¥89     │ ⭐ 4.2星    │ 🔴 电池续航  │ 💡 长续航版  │     │
│  │ 📊 销量5K+  │ 👥 1.2K评价  │ 🟡 偶尔断连  │ 💡 稳定连接  │     │
│  │ 🏅 热销#23  │ 👍 78%好评  │ 🟢 音质好    │ 💡 主动降噪  │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
│                                                                   │
│  🔥 用户痛点Top 5:                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  🔴 电池续航不足 (45%)  ━━━━━━━━━━━━━━━━━  234条        │    │
│  │  "用了2小时就要充电"、"续航虚标"                         │    │
│  │                                                         │    │
│  │  🟡 连接不稳定 (28%)    ━━━━━━━━━━       146条           │    │
│  │  "经常断连"、"连接要等半天"                              │    │
│  │                                                         │    │
│  │  🟢 充电口松动 (15%)    ━━━━━             78条           │    │
│  │  "充电要插好几次"、"接触不良"                            │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  💡 发现的机会:                                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ✨ 解决续航问题                                         │    │
│  │     • 用户愿意多付15-20元购买长续航版本                  │    │
│  │     • 1688类似产品成本差仅5元                           │    │
│  │     → 额外利润空间: 10-15元                             │    │
│  │                                                         │    │
│  │  ✨ 稳定性改进                                          │    │
│  │     • 79%用户提到了连接问题                             │    │
│  │     • 蓝牙5.3芯片成本差仅2元                            │    │
│  │     → 可以作为卖点营销                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  📊 竞品对比:                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  你的产品 vs 竞品A vs 竞品B                              │    │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │    │
│  │  续航时间    ⭐⭐⭐⭐⭐   ⭐⭐⭐      ⭐⭐⭐            │    │
│  │  连接稳定性  ⭐⭐⭐⭐⭐   ⭐⭐⭐⭐    ⭐⭐⭐            │    │
│  │  音质        ⭐⭐⭐⭐     ⭐⭐⭐⭐    ⭐⭐⭐            │    │
│  │  价格        ¥99        ¥89        ¥79                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  🎯 推荐行动:                                                      │
│  1. 找支持蓝牙5.3的供应商（已有2家）                              │
│  2. 在1688搜索"500mah耳机"（找到3款）                             │
│  3. 文案突出"超长续航8小时""不断连"（竞品痛点）                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 实施优先级

### 第1周：评论采集
- [ ] Amazon评论爬虫
- [ ] Shopee评论爬虫
- [ ] 数据表创建
- [ ] 基础API端点

### 第2周：情感分析
- [ ] 情感分析LLM集成
- [ ] 关键词提取
- [ ] 痛点识别
- [ ] 前端情感仪表板

### 第3周：深度洞察
- [ ] 机会发现算法
- [ ] 竞品对比
- [ ] 趋势预测
- [ ] AI选品建议

### 第4周：产品数据
- [ ] Amazon Best Sellers
- [ ] Shopee热销榜
- [ ] 产品-评论关联

### 第5-6周：文章扩展 + API集成
- [ ] 新增20+RSS源
- [ ] RapidAPI集成
- [ ] 数据融合

---

## 预期成果

### 3个月后
- **10万+条评论数据**
- **5000+产品信息**
- **覆盖5个平台、10个国家**
- **实时AI选品建议**

### 6个月后
- **100万+条评论数据**
- **50000+产品信息**
- **覆盖10个平台、20个国家**
- **竞品监控与价格追踪**

---

## 成本估算

| 项目 | 月成本 | 说明 |
|------|-------|------|
| 服务器 | $50 | Railway + Vercel |
| API调用 | $100 | OpenAI GPT-4o-mini |
| 代理IP | $30 | 爬虫防封 |
| 存储 | $20 | PostgreSQL + Pinecone |
| **总计** | **$200/月** | 可支持10万用户 |

---

## 技术风险

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| 反爬虫 | 高 | 使用代理池 + 限流 + API优先 |
| 成本超支 | 中 | 设置API调用上限 + 缓存结果 |
| 数据质量 | 中 | 多源验证 + 异常检测 |
| 法律合规 | 高 | 仅展示公开数据 + 用户协议 |
