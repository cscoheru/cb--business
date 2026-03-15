# services/rss_matcher.py
"""RSS 关键词匹配服务

将 Cards 与相关 RSS 文章进行匹配，用于展示层补充信息。
注意：RSS 数据仅用于展示，不进入 CPI AI 分析。
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


@dataclass
class MatchedArticle:
    """匹配的文章"""
    id: str
    title: str
    summary: Optional[str]
    link: str
    source: str
    published_at: Optional[str]
    relevance_score: float  # 相关度 0-1
    matched_keywords: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "link": self.link,
            "source": self.source,
            "published_at": self.published_at,
            "relevance_score": round(self.relevance_score, 2),
            "matched_keywords": self.matched_keywords,
        }


class RSSMatcher:
    """RSS 文章匹配器"""

    # 品类关键词映射
    CATEGORY_KEYWORDS = {
        "wireless_earbuds": [
            "无线耳机", "蓝牙耳机", "earbuds", "earphones", "TWS",
            "AirPods", "降噪耳机", "noise canceling"
        ],
        "smart_plugs": [
            "智能插座", "smart plug", "smart outlet", "智能家居",
            "home automation", "插座"
        ],
        "fitness_trackers": [
            "健身追踪器", "运动手环", "fitness tracker", "fitness band",
            "智能手环", "小米手环", "Fitbit", "健康监测"
        ],
        "phone_chargers": [
            "手机充电器", "充电器", "phone charger", "充电头",
            "快充", "fast charger", "无线充电", "wireless charger"
        ],
        "desk_lamps": [
            "台灯", "LED台灯", "desk lamp", "台灯",
            "护眼灯", "阅读灯", "office lamp"
        ],
        "phone_cases": [
            "手机壳", "手机套", "phone case", "phone cover",
            "保护壳", "protective case"
        ],
        "yoga_mats": [
            "瑜伽垫", "yoga mat", "运动垫", "exercise mat",
            "健身垫", "yoga"
        ],
        "coffee_makers": [
            "咖啡机", "coffee maker", "咖啡壶", "coffee machine",
            "espresso", "滴漏咖啡"
        ],
        "bluetooth_speakers": [
            "蓝牙音箱", "bluetooth speaker", "无线音箱",
            "portable speaker", "JBL", "小爱音箱"
        ],
        "webcams": [
            "摄像头", "webcam", "网络摄像头", "web camera",
            "视频会议", "直播摄像头"
        ],
        "keyboards": [
            "机械键盘", "keyboard", "键盘", "mechanical keyboard",
            "gaming keyboard", "办公键盘"
        ],
        "mouse": [
            "鼠标", "mouse", "wireless mouse", "无线鼠标",
            "gaming mouse", "游戏鼠标"
        ],
    }

    # 通用行业关键词（用于匹配更广泛的趋势）
    GENERAL_KEYWORDS = [
        "电商", "跨境电商", "选品", "亚马逊", "Amazon",
        "东南亚市场", "电商趋势", "消费电子",
        "e-commerce", "cross-border", "marketplace",
        # 新增电商通用关键词
        "出海", "外贸", "进出口", "供应链", "物流",
        "TikTok", "Shopee", "Lazada", "Temu", "Shein",
        "零售", "批发", "B2B", "B2C", "DTC",
        # 产品通用词
        "产品", "销量", "爆款", "新品", "测评",
        "review", "best seller", "trending", "hot sale",
        # 市场趋势词
        "市场", "趋势", "增长", "下滑", "机遇",
        "market", "trend", "growth", "opportunity"
    ]

    def __init__(self, min_relevance: float = 0.3, max_articles: int = 10):
        """
        初始化匹配器

        Args:
            min_relevance: 最小相关度阈值
            max_articles: 最大返回文章数
        """
        self.min_relevance = min_relevance
        self.max_articles = max_articles

    async def find_related_articles(
        self,
        card_id: str,
        category: str,
        title: str,
        content_keywords: Optional[List[str]] = None,
    ) -> List[MatchedArticle]:
        """
        查找与卡片相关的文章

        Args:
            card_id: 卡片 ID
            category: 品类
            title: 卡片标题
            content_keywords: 从内容中提取的关键词

        Returns:
            匹配的文章列表
        """
        from models.article import Article
        from config.database import get_db

        # 获取关键词
        keywords = self._build_keywords(category, title, content_keywords)

        if not keywords:
            return []

        # 从数据库查询文章
        matched = []
        try:
            async for db in get_db():
                # 查询最近 30 天的文章
                since = datetime.utcnow() - timedelta(days=30)

                # 使用 PostgreSQL 全文搜索或 LIKE 查询
                articles = await db.execute(
                    Article.__table__.select().where(
                        Article.crawled_at >= since,
                        Article.is_processed == True
                    ).limit(100)
                )

                for article in articles:
                    relevance, matched_kw = self._calculate_relevance(
                        article,
                        keywords
                    )

                    if relevance >= self.min_relevance:
                        matched.append(MatchedArticle(
                            id=str(article.id),
                            title=article.title,
                            summary=article.summary,
                            link=article.link,
                            source=article.source,
                            published_at=article.published_at.isoformat() if article.published_at else None,
                            relevance_score=relevance,
                            matched_keywords=matched_kw,
                        ))

                break  # 只需要一个 db session

        except Exception as e:
            logger.error(f"Failed to query articles: {e}")
            # 返回空列表而不是抛出异常

        # 按相关度排序并限制数量
        matched.sort(key=lambda x: x.relevance_score, reverse=True)
        return matched[:self.max_articles]

    def _build_keywords(
        self,
        category: str,
        title: str,
        content_keywords: Optional[List[str]] = None,
    ) -> List[str]:
        """构建搜索关键词列表"""
        keywords = []

        # 添加品类关键词
        if category in self.CATEGORY_KEYWORDS:
            keywords.extend(self.CATEGORY_KEYWORDS[category])

        # 从标题提取关键词
        if title:
            # 简单分词（可以改进为 NLP）
            title_words = re.findall(r'[\w\u4e00-\u9fff]+', title)
            keywords.extend([w for w in title_words if len(w) >= 2])

        # 添加内容关键词
        if content_keywords:
            keywords.extend(content_keywords)

        # 添加通用关键词
        keywords.extend(self.GENERAL_KEYWORDS)

        # 去重
        return list(set(keywords))

    def _calculate_relevance(
        self,
        article: Any,
        keywords: List[str]
    ) -> tuple[float, List[str]]:
        """
        计算文章与关键词的相关度

        Returns:
            (relevance_score, matched_keywords)
        """
        matched = []

        # 合并文章文本
        text = f"{article.title or ''} {article.summary or ''}"
        text_lower = text.lower()

        # 检查每个关键词
        for kw in keywords:
            if kw.lower() in text_lower:
                matched.append(kw)

        if not matched:
            return 0.0, []

        # 计算相关度
        # 考虑因素：
        # 1. 匹配关键词数量
        # 2. 关键词在标题中的权重更高
        relevance = len(matched) / len(keywords)

        # 标题匹配加成
        title_lower = (article.title or "").lower()
        title_matches = sum(1 for kw in matched if kw.lower() in title_lower)
        if title_matches > 0:
            relevance += 0.2 * (title_matches / len(matched))

        return min(1.0, relevance), matched

    def get_trending_articles(
        self,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取热门文章（用于首页展示）

        Args:
            category: 可选的品类筛选
            limit: 返回数量

        Returns:
            热门文章列表
        """
        # TODO: 实现基于阅读量/互动量的热门文章排序
        # 目前返回最近的匹配文章
        return []


# 全局实例
rss_matcher = RSSMatcher()


# 便捷函数
async def get_related_news_for_card(
    card_id: str,
    category: str,
    title: str = "",
    content_keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    获取卡片相关资讯的便捷函数

    注意：此数据仅用于展示，不进入 CPI AI 分析

    Args:
        card_id: 卡片ID
        category: 品类
        title: 卡片标题（可选）
        content_keywords: 内容关键词（可选）

    Returns:
        匹配的文章列表
    """
    articles = await rss_matcher.find_related_articles(
        card_id=card_id,
        category=category,
        title=title,
        content_keywords=content_keywords,
    )
    return [a.to_dict() for a in articles]
