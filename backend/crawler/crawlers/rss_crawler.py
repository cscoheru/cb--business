# crawler/crawlers/rss_crawler.py
import feedparser
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class RSSCrawler:
    """RSS爬虫"""

    def __init__(self, source_config: Dict[str, Any]):
        self.url = source_config["url"]
        self.source_name = source_config.get("name", "unknown")
        self.language = source_config.get("language", "en")
        self.max_articles = source_config.get("max_articles", 20)

    async def fetch(self) -> List[Dict[str, Any]]:
        """抓取RSS feed"""
        articles = []

        try:
            # 使用aiohttp获取RSS内容
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch RSS from {self.source_name}: status {response.status}")
                        return []

                    rss_content = await response.text()

            # 解析RSS
            feed = feedparser.parse(rss_content)

            for entry in feed.entries[:self.max_articles]:
                # 提取文章内容
                article = {
                    "title": self._clean_text(entry.get("title", "")),
                    "summary": self._clean_text(entry.get("description", "")),
                    "link": entry.get("link", ""),
                    "published_at": self._parse_date(entry.get("published")),
                    "updated_at": self._parse_date(entry.get("updated")),
                    "author": entry.get("author", ""),
                    "tags": [tag.term for tag in entry.get("tags", [])],
                    "source": self.source_name,
                    "language": self.language,
                    "raw_data": str(entry),  # 保存原始数据用于调试
                }

                # 如果有内容，尝试获取完整文章
                if article["link"]:
                    article["full_content"] = await self._fetch_full_content(article["link"])

                articles.append(article)

            logger.info(f"Successfully fetched {len(articles)} articles from {self.source_name}")
            return articles

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching RSS from {self.source_name}")
        except Exception as e:
            logger.error(f"Error fetching RSS from {self.source_name}: {e}")

        return articles

    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        # 移除HTML标签
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        # 移除多余空白
        text = " ".join(text.split())
        return text[:1000]  # 限制长度

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        except (ValueError, TypeError):
            try:
                return datetime.strptime(date_str[:25], "%Y-%m-%dT%H:%M:%S%z")
            except:
                pass
        return None

    async def _fetch_full_content(self, url: str) -> Optional[str]:
        """获取完整文章内容"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status != 200:
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 尝试找到文章主体
                    article = soup.find('article')
                    if not article:
                        article = soup.find('div', class_=lambda x: x and 'content' in x.lower() if x else False)
                    if not article:
                        article = soup.find('main')

                    if article:
                        return self._clean_text(article.get_text())

        except Exception as e:
            logger.debug(f"Error fetching full content from {url}: {e}")

        return None
