# crawler/social/reddit_trends.py
"""Reddit 趋势监听器 - 发现电商机会"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import httpx
import re

logger = logging.getLogger(__name__)


@dataclass
class RedditPost:
    """Reddit 帖子数据"""
    title: str
    subreddit: str
    url: str
    score: int  # upvotes
    num_comments: int
    created_utc: float
    author: str
    selftext: Optional[str] = None

    # 提取的关键词和产品
    extracted_keywords: List[str] = None
    mentioned_products: List[str] = None
    opportunity_score: float = 0

    def __post_init__(self):
        if self.extracted_keywords is None:
            self.extracted_keywords = []
        if self.mentioned_products is None:
            self.mentioned_products = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "subreddit": self.subreddit,
            "url": self.url,
            "score": self.score,
            "num_comments": self.num_comments,
            "created_at": datetime.fromtimestamp(self.created_utc).isoformat(),
            "author": self.author,
            "extracted_keywords": self.extracted_keywords,
            "mentioned_products": self.mentioned_products,
            "opportunity_score": self.opportunity_score,
        }


class RedditTrendsMonitor:
    """Reddit 趋势监控器

    监控电商相关的 Subreddit，发现：
    - 热门产品
    - 市场趋势
    - 痛点问题
    - 机会信号
    """

    # 电商相关 Subreddit
    ECOMMERCE_SUBREDDITS = [
        "dropshipping",
        "entrepreneur",
        "FulfillmentByAmazon",
        "juststart",
        "ecommerce",
        "AmazonFBA",
        "OnlineBusiness",
    ]

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        初始化 Reddit 监控器

        注意: 使用公共 Reddit API (无需认证) 有速率限制
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def get_hot_posts(
        self,
        subreddit: str,
        limit: int = 50
    ) -> List[RedditPost]:
        """
        获取 Subreddit 的热门帖子

        Args:
            subreddit: Subreddit 名称
            limit: 返回数量

        Returns:
            帖子列表
        """
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        params = {"limit": limit}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            posts = []

            if "data" in data and "children" in data["data"]:
                for child in data["data"]["children"]:
                    post_data = child.get("data", {})
                    post = RedditPost(
                        title=post_data.get("title", ""),
                        subreddit=post_data.get("subreddit", ""),
                        url=f"https://www.reddit.com{post_data.get('permalink', '')}",
                        score=post_data.get("score", 0),
                        num_comments=post_data.get("num_comments", 0),
                        created_utc=post_data.get("created_utc", 0),
                        author=post_data.get("author", ""),
                        selftext=post_data.get("selftext"),
                    )

                    # 分析帖子
                    post = self._analyze_post(post)
                    posts.append(post)

            logger.info(f"从 r/{subreddit} 获取到 {len(posts)} 个帖子")
            return posts

        except Exception as e:
            logger.error(f"获取 r/{subreddit} 失败: {e}")
            return []

    async def get_new_posts(
        self,
        subreddit: str,
        limit: int = 50
    ) -> List[RedditPost]:
        """获取最新帖子"""
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        params = {"limit": limit}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            posts = []

            if "data" in data and "children" in data["data"]:
                for child in data["data"]["children"]:
                    post_data = child.get("data", {})
                    post = RedditPost(
                        title=post_data.get("title", ""),
                        subreddit=post_data.get("subreddit", ""),
                        url=f"https://www.reddit.com{post_data.get('permalink', '')}",
                        score=post_data.get("score", 0),
                        num_comments=post_data.get("num_comments", 0),
                        created_utc=post_data.get("created_utc", 0),
                        author=post_data.get("author", ""),
                        selftext=post_data.get("selftext"),
                    )

                    post = self._analyze_post(post)
                    posts.append(post)

            return posts

        except Exception as e:
            logger.error(f"获取 r/{subreddit} 新帖子失败: {e}")
            return []

    def _analyze_post(self, post: RedditPost) -> RedditPost:
        """
        分析帖子，提取关键词和产品

        识别:
        - 电商平台关键词 (Amazon, Shopify, 等)
        - 产品类别 (electronics, fashion, 等)
        - 机会信号 (struggling, help, looking for, 等)
        """
        text = f"{post.title} {post.selftext or ''}".lower()

        # 电商平台关键词
        platform_keywords = {
            "amazon": 0,
            "shopify": 0,
            "woocommerce": 0,
            "aliexpress": 0,
            "alibaba": 0,
            "dropshipping": 0,
        }

        # 产品类别关键词
        category_keywords = {
            "electronics": 0,
            "fashion": 0,
            "beauty": 0,
            "home": 0,
            "kitchen": 0,
            "pet": 0,
            "fitness": 0,
        }

        # 机会信号
        opportunity_signals = {
            "help": 0,
            "advice": 0,
            "looking for": 0,
            "struggling": 0,
            "how do i": 0,
            "best way to": 0,
            "any tips": 0,
            "success story": 0,
        }

        # 统计关键词出现次数
        keywords_found = set()

        for keyword in platform_keywords:
            if keyword in text:
                platform_keywords[keyword] = text.count(keyword)
                keywords_found.add(keyword)

        for keyword in category_keywords:
            if keyword in text:
                category_keywords[keyword] = text.count(keyword)
                keywords_found.add(keyword)

        for signal in opportunity_signals:
            if signal in text:
                opportunity_signals[signal] = text.count(signal)

        post.extracted_keywords = list(keywords_found)

        # 计算机会评分
        # 基于互动量 (score + comments)
        engagement_score = min((post.score + post.num_comments) / 100, 50)

        # 基于机会信号
        signal_score = min(sum(opportunity_signals.values()) * 10, 30)

        # 基于平台相关性
        platform_score = min(len([k for k, v in platform_keywords.items() if v > 0]) * 5, 20)

        post.opportunity_score = engagement_score + signal_score + platform_score

        return post

    async def monitor_all_subreddits(
        self,
        limit_per_subreddit: int = 25
    ) -> Dict[str, List[RedditPost]]:
        """监控所有电商相关 Subreddit"""
        results = {}

        for subreddit in self.ECOMMERCE_SUBREDDITS:
            try:
                posts = await self.get_hot_posts(subreddit, limit_per_subreddit)
                results[subreddit] = posts

                # 避免请求过快
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"监控 r/{subreddit} 失败: {e}")
                results[subreddit] = []

        return results

    async def find_opportunities(
        self,
        min_score: float = 40,
        min_engagement: int = 50
    ) -> List[Dict[str, Any]]:
        """
        发现电商机会

        Args:
            min_score: 最小机会评分
            min_engagement: 最小互动量

        Returns:
            机会列表
        """
        results = await self.monitor_all_subreddits(limit_per_subreddit=50)

        all_posts = []
        for subreddit, posts in results.items():
            all_posts.extend(posts)

        # 筛选高机会帖子
        opportunities = [
            p for p in all_posts
            if p.opportunity_score >= min_score
            and (p.score + p.num_comments) >= min_engagement
        ]

        # 按评分排序
        opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)

        # 生成报告
        return [
            {
                "title": opp.title,
                "subreddit": opp.subreddit,
                "url": opp.url,
                "score": opp.score,
                "num_comments": opp.num_comments,
                "opportunity_score": opp.opportunity_score,
                "keywords": opp.extracted_keywords,
            }
            for opp in opportunities[:20]
        ]


# ==================== 测试代码 ====================

async def test_reddit_monitor():
    """测试 Reddit 监控器"""
    monitor = RedditTrendsMonitor()

    try:
        # 测试单个 Subreddit
        posts = await monitor.get_hot_posts("dropshipping", limit=10)

        print(f"\n=== r/dropshipping 热门帖子 ===")
        for i, post in enumerate(posts[:5], 1):
            print(f"\n{i}. {post.title}")
            print(f"   评分: {post.score} | 评论: {post.num_comments}")
            print(f"   机会评分: {post.opportunity_score:.1f}")
            if post.extracted_keywords:
                print(f"   关键词: {', '.join(post.extracted_keywords)}")

        # 查找机会
        opportunities = await monitor.find_opportunities(min_score=30)

        print(f"\n\n=== 发现的机会 ({len(opportunities)}) ===")
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n{i}. {opp['title'][:60]}...")
            print(f"   Subreddit: r/{opp['subreddit']}")
            print(f"   机会评分: {opp['opportunity_score']:.1f}")
            print(f"   链接: {opp['url']}")

    finally:
        await monitor.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(test_reddit_monitor())
