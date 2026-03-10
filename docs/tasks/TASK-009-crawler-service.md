# TASK-009: 爬虫服务实现

> **所属会话**: 会话2（后端开发线）
> **优先级**: P1
> **预计工期**: 4天
> **依赖任务**: TASK-003（基础设施配置）
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

实现数据爬虫服务，从多个数据源（Retail Dive、Shopify Blog、雨果网等）抓取电商相关信息，并使用AI进行分析和分类。

---

## 数据源配置

```python
# crawler/config.py
CRAWLER_SOURCES = {
    "retail_dive": {
        "type": "rss",
        "url": "https://retaildive.com/feed/",
        "update_interval": 3600,  # 1小时
    },
    "shopify_blog": {
        "type": "rss",
        "url": "https://www.shopify.com/blog.xml",
        "update_interval": 3600,
    },
    "cifnews": {
        "type": "http",
        "base_url": "https://www.cifnews.com",
        "update_interval": 7200,  # 2小时
    },
}
```

---

## 爬虫实现

### RSS爬虫

```python
# crawler/crawlers/rss_crawler.py
import feedparser
import asyncio
from typing import List, Dict
from datetime import datetime

class RSSCrawler:
    """RSS爬虫"""

    def __init__(self, source_config: Dict):
        self.url = source_config["url"]
        self.source_name = source_config.get("name", "unknown")

    async def fetch(self) -> List[Dict]:
        """抓取RSS feed"""
        feed = feedparser.parse(self.url)

        articles = []
        for entry in feed.entries[:20]:  # 最新20条
            articles.append({
                "title": entry.get("title"),
                "summary": entry.get("description"),
                "link": entry.get("link"),
                "published_at": entry.get("published"),
                "source": self.source_name,
            })

        return articles
```

### HTTP爬虫

```python
# crawler/crawlers/http_crawler.py
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict

class HTTPCrawler:
    """HTTP爬虫"""

    def __init__(self, source_config: Dict):
        self.base_url = source_config["base_url"]
        self.source_name = source_config.get("name", "unknown")

    async def fetch(self, url: str) -> Dict:
        """抓取单个页面"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; CBCrawler/1.0)"
            }) as response:
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')

        return {
            "title": soup.find("h1").get_text() if soup.find("h1") else "",
            "content": soup.find("article").get_text() if soup.find("article") else "",
            "url": url,
            "source": self.source_name,
        }
```

### AI处理器

```python
# crawler/processors/ai_processor.py
from openai import AsyncOpenAI
from typing import Dict

class AIProcessor:
    """AI内容分析处理器"""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def analyze_article(self, article: Dict) -> Dict:
        """分析文章内容"""
        prompt = f"""
        分析以下电商相关文章，返回JSON格式：

        文章标题：{article['title']}
        文章内容：{article['summary'][:500]}

        请返回：
        {{
            "content_theme": "opportunity/risk/policy/guide",
            "region": "southeast_asia/north_america/europe/latin_america",
            "platform": "amazon/shopee/lazada/other",
            "tags": ["tag1", "tag2"],
            "risk_level": "low/medium/high/critical",
            "opportunity_score": 0.0-1.0
        }}
        """

        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        return json.loads(response.choices[0].message.content)
```

---

## 定时任务

```python
# crawler/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crawler.crawlers.rss_crawler import RSSCrawler
from crawler.crawlers.http_crawler import HTTPCrawler
from crawler.processors.ai_processor import AIProcessor
import asyncio

class CrawlerScheduler:
    """爬虫调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ai_processor = AIProcessor(api_key="your_openai_key")

    async def crawl_job(self, source_name: str):
        """执行爬取任务"""
        config = CRAWLER_SOURCES[source_name]

        if config["type"] == "rss":
            crawler = RSSCrawler(config)
        else:
            crawler = HTTPCrawler(config)

        articles = await crawler.fetch()

        # AI分析
        for article in articles:
            analysis = await self.ai_processor.analyze_article(article)
            article.update(analysis)

        # 保存到数据库
        await self.save_articles(articles)

    def start(self):
        """启动调度器"""
        # 每小时执行一次
        self.scheduler.add_job(
            self.crawl_job,
            'interval',
            hours=1,
            args=['retail_dive']
        )
        self.scheduler.start()
```

---

## 测试

```bash
# 测试RSS爬虫
python crawler/test_rss.py

# 测试AI分析
python crawler/test_ai.py

# 运行调度器
python crawler/main.py
```

---

## 提交规范

```bash
git commit -m "feat(TASK-009): 实现数据爬虫服务

- 实现RSS爬虫（feedparser）
- 实现HTTP爬虫（aiohttp + BeautifulSoup）
- 实现AI内容分析（OpenAI API）
- 实现定时任务调度（APScheduler）
- 配置数据源

数据源:
- Retail Dive (RSS)
- Shopify Blog (RSS)
- 雨果网 (HTTP)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

*本任务书由主会话（项目经理）创建和维护*
