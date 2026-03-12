# ZenConsult 可落地实施方案（信息源优先）

## 🎯 核心问题：信息源获取

| 数据类型 | 可行性 | 成本 | 推荐方案 |
|---------|--------|------|---------|
| **文章资讯** | ⭐⭐⭐⭐⭐ | $0 | RSS订阅（立即可用）|
| **Shopee评论** | ⭐⭐⭐ | $0 | 官方API（需卖家账号）|
| **Lazada评论** | ⭐⭐⭐ | $0 | 官方API（需卖家账号）|
| **TikTok评论** | ⭐⭐ | 中等 | 较难获取 |
| **Amazon评论** | ⭐ | 高 | 第三方API（$49+/月）|
| **产品榜单** | ⭐⭐⭐ | 低 | 公共爬虫 |
| **价格追踪** | ⭐⭐⭐⭐ | 低 | 有免费API |

---

## 📋 分阶段实施路线

### Phase 1: 立即可用（第1周）✅

#### 1.1 文章资讯扩展（零成本）

**新增30+个RSS源**，立即充实内容：

```python
# crawler/config.py - 新增RSS源

NEW_SOURCES = {
    # === 东南亚科技媒体 ===
    "dealstreet_asia": {
        "name": "DealStreetAsia",
        "type": "rss",
        "url": "https://www.dealstreetasia.com/feed/",
        "enabled": True,
        "region": "southeast_asia",
        "language": "en"
    },
    "krasia": {
        "name": "KrASIA",
        "type": "rss",
        "url": "https://kr-asia.com/feed",
        "enabled": True,
        "region": "southeast_asia",
        "language": "en"
    },
    "techinasia": {
        "name": "Tech in Asia",
        "type": "rss",
        "url": "https://www.techniasia.com/feed",
        "enabled": True,
        "region": "southeast_asia",
        "language": "en"
    },
    "e27": {
        "name": "e27",
        "type": "rss",
        "url": "https://e27.co/feed",
        "enabled": True,
        "region": "southeast_asia",
        "language": "en"
    },

    # === 东南亚本地媒体 ===
    "vietnam_news": {
        "name": "Vietnam News",
        "type": "rss",
        "url": "https://vietnamnews.vn/economy/rss",
        "enabled": True,
        "region": "southeast_asia",
        "language": "en",
        "country_focus": "vn"
    },
    "bangkok_post": {
        "name": "Bangkok Post",
        "type": "rss",
        "url": "https://www.bangkokpost.com/rss/data/business.xml",
        "enabled": True,
        "region": "southeast_asia",
        "language": "en",
        "country_focus": "th"
    },
    "kompas": {
        "name": "Kompas",
        "type": "rss",
        "url": "https://ecomedia.kompas.com/feed",
        "enabled": True,
        "region": "southeast_asia",
        "language": "id",
        "country_focus": "id"
    },
    "philstar": {
        "name": "Philippine Star",
        "type": "rss",
        "url": "https://www.philstar.com/business/rss",
        "enabled": True,
        "region": "southeast_asia",
        "language": "en",
        "country_focus": "ph"
    },

    # === 拉美市场 ===
    "neobiz": {
        "name": "Neobiz",
        "type": "rss",
        "url": "https://neobiz.com.br/blog/feed",
        "enabled": True,
        "region": "latin_america",
        "language": "pt",
        "country_focus": "br"
    },
    "ecommerce_brasil": {
        "name": "E-commerce Brasil",
        "type": "rss",
        "url": "https://ecommercebrasil.com.br/feed",
        "enabled": True,
        "region": "latin_america",
        "language": "pt",
        "country_focus": "br"
    },
    "webcapitalista": {
        "name": "Webcapitalista",
        "type": "rss",
        "url": "https://webcapitalista.com/feed",
        "enabled": True,
        "region": "latin_america",
        "language": "es"
    },

    # === 平台官方博客 ===
    "tiktok_seller_blog": {
        "name": "TikTok Shop Blog",
        "type": "rss",
        "url": "https://sellertik.tiktok.com/feed",
        "enabled": True,
        "region": "global",
        "language": "en"
    },
    "shopify_blog": {
        "name": "Shopify Blog",
        "type": "rss",
        "url": "https://www.shopify.com/blog.xml",
        "enabled": True,
        "region": "global",
        "language": "en"
    },

    # === 电商研究 ===
    "internet_retailing": {
        "name": "Internet Retailing",
        "type": "rss",
        "url": "https://www.internetretailing.com/feed",
        "enabled": True,
        "region": "global",
        "language": "en"
    },
    "retail_touch_points": {
        "name": "Retail TouchPoints",
        "type": "rss",
        "url": "https://retailtouchpoints.com/feed",
        "enabled": True,
        "region": "global",
        "language": "en"
    },
}
```

**预期成果**:
- 从134篇文章 → 1000+篇文章/月
- 零成本，立即可用

---

### Phase 2: Shopee官方API（第2-3周）⭐推荐

**关键发现**: Shopee有官方评论API！**`v2.product.get_comment`**

**获取方式**:
1. 注册Shopee开放平台账号: https://open.shopee.com/
2. 创建应用获取API Key
3. 需要一个测试店铺（可以自己开）

**实施步骤**:

```python
# crawler/reviews/shopee_official.py

import hashlib
import hmac
import time
import httpx
from typing import List, Dict

class ShopeeOfficialReviewCrawler:
    """使用Shopee官方API获取评论"""

    def __init__(self, partner_id: str, partner_key: str, shop_id: str):
        self.partner_id = partner_id
        self.partner_key = partner_key
        self.shop_id = shop_id
        self.base_url = "https://partner.shopeemobile.com"  # 或根据地区调整

    def _generate_signature(self, path: str, body: str = "") -> str:
        """生成API签名"""
        base_string = f"{self.partner_id}{path}{int(time.time())}{body}"
        signature = hmac.new(
            self.partner_key.encode(),
            base_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    async def get_reviews(
        self,
        item_id: str,
        page_size: int = 50,
        max_pages: int = 20
    ) -> List[Dict]:
        """
        获取商品评论

        官方文档: https://open.shopee.com/documents/v2/v2.product.get_comment
        """
        path = "/api/v2/product/get_comment"
        reviews = []

        for page in range(1, max_pages + 1):
            # 构建请求参数
            params = {
                "partner_id": self.partner_id,
                "timestamp": int(time.time()),
                "access_token": self.access_token,  # 需要获取
                "shop_id": self.shop_id,
                "item_id": item_id,
                "page_size": page_size,
                "page_no": page,
                "flag": 0,  # 0: 全部评论
            }

            # 生成签名
            base_string = f"{self.partner_id}{path}{params['timestamp']}{''}"
            sign = hmac.new(
                self.partner_key.encode(),
                base_string.encode(),
                hashlib.sha256
            ).hexdigest()
            params["sign"] = sign

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}{path}",
                        params=params,
                        timeout=30
                    )

                    if response.status_code != 200:
                        break

                    data = response.json()

                    if "error" in data:
                        break

                    # 解析评论
                    for comment in data.get("data", {}).get("comments", []):
                        review = {
                            "review_id": comment.get("comment_id"),
                            "platform_product_id": item_id,
                            "platform": "shopee",
                            "rating": comment.get("rating_star"),
                            "content": comment.get("text"),
                            "author_name": comment.get("author", {}).get("username"),
                            "review_date": comment.get("ctime"),
                            "media_urls": comment.get("images", []),
                            # Shopee特有字段
                            "isEdited": comment.get("is_edit", False),
                            "item_variant": comment.get("item_item_variant"),
                        }
                        reviews.append(review)

                    # 检查是否还有更多
                    if len(data.get("data", {}).get("comments", [])) < page_size:
                        break

                    await asyncio.sleep(0.5)  # 避免限流

            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                break

        return reviews

    async def search_products_by_keyword(self, keyword: str, country: str = "th") -> List[str]:
        """
        通过关键词搜索商品，获取item_id列表

        这是获取商品评论的前提
        """
        # 使用Shopee搜索API
        path = "/api/v2/product/search_item"
        # ... 实现搜索逻辑
        pass
```

**成本**:
- 开发测试店铺: 免费注册
- API调用: 免费（有速率限制）

**预期成果**:
- 每月获取10万+条Shopee评论
- 涵盖6个东南亚国家

---

### Phase 3: 公共产品数据（第3-4周）

**Amazon Best Sellers** - 公开页面，较易爬取：

```python
# crawler/products/amazon_bestsellers.py

class AmazonBestSellersCrawler:
    """
    Amazon Best Sellers 爬虫

    策略: 使用浏览器自动化 + 代理IP池
    注意: 仅获取公开的榜单数据，不爬取评论
    """

    async def fetch_best_sellers(
        self,
        category: str,
        country: str = "us",
        top_n: int = 100
    ) -> List[Dict]:
        """
        获取Best Sellers榜单

        注意: 这是公开数据，反爬虫压力较小
        """
        category_urls = {
            "electronics": "/Best-Sellers-Electronics/zgbs",
            "home_kitchen": "/Best-Sellers-Home-Kitchen/zgbs",
            # ... 更多分类
        }

        # 使用 Playwright (支持JavaScript渲染)
        from playwright.async_api import async_playwright

        products = []

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            url = f"https://www.amazon.{self._get_domain(country)}{category_urls[category]}"
            await page.goto(url)

            # 等待页面加载
            await page.wait_for_selector('.zg-item-immersion')

            # 提取商品信息
            items = await page.query_selector_all('.zg-item-immersion')

            for item in items[:top_n]:
                product = {
                    "rank": await page.evaluate('(el) => el.querySelector(".zg-badge-text")?.textContent', item),
                    "title": await page.evaluate('(el) => el.querySelector("div[data-cy=title-recipe-title]")?.textContent', item),
                    "price": await page.evaluate('(el) => el.querySelector(".a-price-whole")?.textContent', item),
                    "rating": await page.evaluate('(el) => el.querySelector(".a-icon-alt")?.textContent', item),
                    "link": await page.evaluate('(el) => el.querySelector("a.a-link-normal")?.href', item),
                    "image": await page.evaluate('(el) => el.querySelector(".a-dynamic-image")?.src', item),
                    "country": country,
                    "platform": "amazon",
                }
                products.append(product)

            await browser.close()

        return products
```

**成本**:
- Playwright: 免费
- 代理IP（可选）: $30/月

---

### Phase 4: Amazon评论API（可选，第5周+）

**第三方API对比**:

| 服务商 | 价格 | 免费额度 | 推荐度 |
|--------|------|---------|--------|
| **Oxylabs** | $49/月起 | 10,000次试用 | ⭐⭐⭐⭐ |
| **Rainforest API** | $99/月起 | 100次免费 | ⭐⭐⭐ |
| **SerpAPI** | $50/月起 | 100次搜索 | ⭐⭐⭐ |
| **ScraperAPI** | $29/月起 | 1000次请求 | ⭐⭐⭐⭐ |

**推荐: Oxylabs**（性价比最高）

```python
# integrations/oxylabs_client.py

import httpx

class OxylabsAmazonClient:
    """Oxylabs Amazon评论API客户端"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.base_url = "https://realtime.oxylabs.io/v1/queries"

    async def get_amazon_reviews(
        self,
        asin: str,
        country: str = "us",
        max_reviews: int = 100
    ) -> List[Dict]:
        """
        使用Oxylabs获取Amazon评论

        价格: 约$0.05/100条评论
        """
        payload = {
            "source": "amazon_product_reviews",
            "query": asin,
            "geo_location": country,
            "parse": True,
            "context": [
                {
                    "key": "max_reviews",
                    "value": max_reviews
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json=payload,
                auth=(self.username, self.password),
                timeout=60
            )

            data = response.json()
            return self._parse_reviews(data.get("results", []))
```

**成本估算**:
- $49/月 = 49,000次请求
- 假设每次获取50条评论 = 可获取2,450,000条评论/月
- 每条评论成本: $0.02

---

## 🎯 现实的MVP方案

### 最小可行产品（4周完成）

**第1周**: 文章扩展
- 新增30+ RSS源
- 文章量达到1000+/月
- 成本: $0

**第2周**: Shopee评论API
- 注册Shopee开发者账号
- 实现评论获取
- 目标: 5万条评论/月
- 成本: $0

**第3周**: 公共产品数据
- Amazon Best Sellers爬虫
- Shopee热销榜
- 目标: 5000+产品
- 成本: $0-30

**第4周**: AI分析 + 可视化
- 情感分析
- 关键词云
- 痛点识别
- 前端展示

**总投入**: $30/月（可选的代理IP）
**总产出**:
- 1000+文章/月
- 5万+评论/月
- 5000+产品信息
- AI选品建议

---

## 💰 成本对比：自建 vs 第三方

| 方案 | 月成本 | 优势 | 劣势 |
|------|-------|------|------|
| **全自建** | $30 | 长期成本低 | 维护工作量大 |
| **全第三方API** | $300+ | 稳定可靠 | 成本高 |
| **混合方案** | $100 | 平衡 | 需要技术能力 |

**推荐**: 混合方案
- 文章: 自建RSS（$0）
- Shopee: 官方API（$0）
- Amazon: Oxylabs（$49/月，按需）
- 产品榜单: 自建爬虫（$0-30）

---

## 📊 数据来源优先级矩阵

```
                    实现难度
                      │
          容易        │     困难
                      │
    ┌─────────────────┼─────────────────┐
 高 │  RSS文章        │  Amazon评论API  │
价   │  (立即可用)    │  ($49+/月)      │
值   ├─────────────────┼─────────────────┤
 低 │  Shopee热销榜   │  亚马逊自建爬虫  │
     │  (免费)        │  (不推荐)        │
    └─────────────────┴─────────────────┘
```

**推荐路径**（从左到右，从上到下）:
1. ✅ RSS文章 - 立即做
2. ✅ Shopee热销榜 - 第2周
3. ✅ Shopee评论API - 第2-3周
4. ⚠️ Amazon评论API - 视预算而定（第5周+）
5. ❌ 亚马逊自建爬虫 - 不推荐

---

## 🚀 立即行动清单

### 今天就能做的事：

**1. 扩展文章来源（30分钟）**
```bash
# 编辑 crawler/config.py，添加上面的30个新RSS源
git add crawler/config.py
git commit -m "feat: add 30+ new RSS sources"
git push
```

**2. 注册Shopee开放平台（15分钟）**
1. 访问 https://open.shopee.com/
2. 注册账号
3. 创建应用
4. 获取API密钥

**3. 测试Shopee API（1小时）**
```python
# 创建测试脚本
# crawler/reviews/test_shopee_api.py

import httpx

async def test_shopee_api():
    # 使用你的API密钥
    partner_id = "your_partner_id"
    partner_key = "your_partner_key"
    shop_id = "your_shop_id"

    crawler = ShopeeOfficialReviewCrawler(partner_id, partner_key, shop_id)
    reviews = await crawler.get_reviews(item_id="test_item_id", max_pages=1)

    print(f"获取到 {len(reviews)} 条评论")
    for review in reviews[:3]:
        print(f"- {review['rating']}星: {review['content'][:50]}")

# 运行测试
asyncio.run(test_shopee_api())
```

---

## 📈 预期成果对比

| 指标 | 当前 | 4周后 | 12周后 |
|------|------|-------|--------|
| 文章/月 | 134 | 1000+ | 3000+ |
| 评论/月 | 0 | 50,000+ | 200,000+ |
| 产品数 | 0 | 5,000+ | 50,000+ |
| 覆盖国家 | 6 | 10+ | 20+ |
| 月成本 | $0 | $30-100 | $100-300 |

---

**Sources**:
- [Shopee Open Platform Developer Guide](https://open.shopee.com/developer-guide/4)
- [Shopee Product Comments API](https://open.shopee.com/documents/v2/v2.product.get_comment)
- [Lazada API Documentation](https://open.lazada.com/apps/doc/api)
- [TikTok Shop Developer Guide](https://partner.tiktokshop.com/docv2/page/tts-developer-guide)
- [Oxylabs Amazon Scraper API](https://oxylabs.io/products/scraper-api/ecommerce/amazon)
- [Easyparser vs Rainforest API vs Oxylabs Comparison](https://easyparser.com/blog/easyparser-vs-rainforest-vs-oxylabs)
- [Top 5 Amazon Scraper APIs](https://trajectdata.com/top-5-amazon-scraper-apis/)
- [Cheapest SERP API Comparison 2026](https://proxies.sx/blog/cheapest-serp-api-comparison-2026)
