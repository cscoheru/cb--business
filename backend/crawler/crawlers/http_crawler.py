# crawler/crawlers/http_crawler.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HTTPCrawler:
    """HTTP爬虫"""

    def __init__(self, source_config: Dict[str, Any]):
        self.base_url = source_config["base_url"]
        self.source_name = source_config.get("name", "unknown")
        self.language = source_config.get("language", "zh")
        self.list_url = source_config.get("list_url", "")

    async def fetch(self) -> List[Dict[str, Any]]:
        """抓取文章列表"""
        articles = []

        try:
            list_url = self.base_url + self.list_url
            async with aiohttp.ClientSession() as session:
                async with session.get(list_url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; CBCrawler/1.0)"
                }, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch list from {self.source_name}: status {response.status}")
                        return []

                    html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')

            # 查找文章列表（根据网站结构调整）
            article_elements = soup.select('.article-item, .news-item, article[class*="post"]')

            for element in article_elements[:20]:  # 限制20条
                article = await self._parse_article_element(element)
                if article:
                    articles.append(article)

            logger.info(f"Successfully fetched {len(articles)} articles from {self.source_name}")
            return articles

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching from {self.source_name}")
        except Exception as e:
            logger.error(f"Error fetching from {self.source_name}: {e}")

        return articles

    async def _parse_article_element(self, element) -> Dict[str, Any]:
        """解析文章元素"""
        try:
            # 提取标题
            title_elem = element.find(['h2', 'h3', 'h4', 'a'], class_=lambda x: x and 'title' in x.lower() if x else False)
            if not title_elem:
                title_elem = element.find('a')
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 提取链接
            link_elem = element.find('a', href=True)
            link = link_elem['href'] if link_elem else ""
            if link and not link.startswith('http'):
                link = self.base_url.rstrip('/') + '/' + link.lstrip('/')

            # 提取摘要
            summary_elem = element.find(['p', 'div'], class_=lambda x: x and ('summary' in x.lower() or 'excerpt' in x.lower() or 'description' in x.lower()) if x else False)
            if not summary_elem:
                summary_elem = element.find('p')
            summary = summary_elem.get_text(strip=True)[:500] if summary_elem else ""

            # 提取发布时间
            time_elem = element.find('time')
            published_at = None
            if time_elem and time_elem.get('datetime'):
                published_at = self._parse_datetime(time_elem.get('datetime'))

            article = {
                "title": title,
                "summary": summary,
                "link": link,
                "published_at": published_at,
                "source": self.source_name,
                "language": self.language,
            }

            # 获取完整内容
            if link:
                article["full_content"] = await self._fetch_full_content(link)

            return article

        except Exception as e:
            logger.debug(f"Error parsing article element: {e}")
            return {}

    async def _fetch_full_content(self, url: str) -> Optional[str]:
        """获取完整文章内容"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; CBCrawler/1.0)"
                }, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status != 200:
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 尝试找到文章主体
                    article = soup.find('article')
                    if not article:
                        article = soup.find('div', class_=lambda x: x and 'content' in x.lower() if x else False)
                    if not article:
                        article = soup.find('div', class_=lambda x: x and 'article-content' in x.lower() if x else False)
                    if not article:
                        article = soup.find('main')

                    if article:
                        # 移除广告等无关内容
                        for ad in article.select(['.ad', '.advertisement', '.promo', '.sidebar']):
                            ad.decompose()

                        return article.get_text(strip=True)[:5000]

        except Exception as e:
            logger.debug(f"Error fetching full content from {url}: {e}")

        return None

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """解析日期时间"""
        if not date_str:
            return None
        try:
            # ISO 8601格式
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        return None
