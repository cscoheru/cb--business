# services/signal_adapters.py
"""信号适配器 - 将各种来源的信号转换为统一格式"""

import logging
import uuid
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from models.article import Article

logger = logging.getLogger(__name__)


class SignalAdapter:
    """信号适配器基类"""

    def to_signal(self, raw_data: Any) -> Dict[str, Any]:
        """
        将原始数据转换为标准信号格式

        Args:
            raw_data: 原始数据

        Returns:
            标准格式的信号
        """
        raise NotImplementedError


class RSSArticleSignalAdapter(SignalAdapter):
    """RSS文章信号适配器"""

    def to_signal(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """将RSS文章转换为信号"""
        return {
            "type": "rss_article",
            "title": article_data.get("title", ""),
            "content": article_data.get("summary") or article_data.get("content", ""),
            "source": article_data.get("source_name") or article_data.get("source", "RSS"),
            "published_at": article_data.get("published_at"),
            "url": article_data.get("link") or article_data.get("url", ""),
            "raw_data": article_data
        }


class DatabaseArticleSignalAdapter(SignalAdapter):
    """数据库文章信号适配器"""

    def __init__(self, db: AsyncSessionLocal):
        self.db = db

    async def to_signal(self, article: Article) -> Dict[str, Any]:
        """将数据库中的Article转换为信号"""
        # 构建内容
        content = article.summary or ""
        if article.full_content:
            content += "\n\n" + article.full_content

        # 如果有AI分析，添加到信号中
        ai_context = {}
        if article.content_theme:
            ai_context["content_theme"] = article.content_theme
        if article.region:
            ai_context["region"] = article.region
        if article.platform:
            ai_context["platform"] = article.platform
        if article.opportunity_score:
            ai_context["opportunity_score"] = article.opportunity_score

        return {
            "type": "database_article",
            "title": article.title,
            "content": content[:2000],  # 限制长度
            "source": article.source,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "url": article.link,
            "article_id": str(article.id),
            "ai_analysis": ai_context,
            "raw_data": {
                "id": str(article.id),
                "language": article.language,
                "is_processed": article.is_processed
            }
        }

    async def extract_high_opportunity_signals(
        self,
        min_score: float = 0.6,
        limit: int = 50,
        hours_ago: int = 24
    ) -> List[Dict[str, Any]]:
        """
        提取高机会分数的文章信号

        Args:
            min_score: 最小机会分数
            limit: 最大提取数量
            hours_ago: 只提取最近N小时的文章

        Returns:
            信号列表
        """
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

            result = await self.db.execute(
                select(Article)
                .where(
                    and_(
                        Article.published_at >= time_threshold,
                        Article.opportunity_score >= min_score,
                        Article.content_theme.in_(["opportunity", "policy", "platform"])
                    )
                )
                .order_by(Article.opportunity_score.desc())
                .limit(limit)
            )

            articles = result.scalars().all()
            signals = []

            for article in articles:
                signal = await self.to_signal(article)
                signals.append(signal)

            logger.info(f"提取了 {len(signals)} 个高机会信号 (score>={min_score})")
            return signals

        except Exception as e:
            logger.error(f"高机会信号提取失败: {e}")
            return []

    async def extract_by_theme(
        self,
        theme: str,
        limit: int = 20,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """按主题提取信号"""
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(days=7)

            result = await self.db.execute(
                select(Article)
                .where(
                    and_(
                        Article.content_theme == theme,
                        Article.published_at >= time_threshold,
                        Article.opportunity_score >= min_score
                    )
                )
                .order_by(Article.opportunity_score.desc())
                .limit(limit)
            )

            articles = result.scalars().all()
            signals = []

            for article in articles:
                signal = await self.to_signal(article)
                signals.append(signal)

            logger.info(f"按主题 '{theme}' 提取了 {len(signals)} 个信号")
            return signals

        except Exception as e:
            logger.error(f"按主题提取信号失败: {e}")
            return []

    async def extract_by_region(
        self,
        region: str,
        limit: int = 20,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """按地区提取信号"""
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(days=7)

            result = await self.db.execute(
                select(Article)
                .where(
                    and_(
                        Article.region == region,
                        Article.published_at >= time_threshold,
                        Article.opportunity_score >= min_score
                    )
                )
                .order_by(Article.opportunity_score.desc())
                .limit(limit)
            )

            articles = result.scalars().all()
            signals = []

            for article in articles:
                signal = await self.to_signal(article)
                signals.append(signal)

            logger.info(f"按地区 '{region}' 提取了 {len(signals)} 个信号")
            return signals

        except Exception as e:
            logger.error(f"按地区提取信号失败: {e}")
            return []

    async def stream_signals(
        self,
        batch_size: int = 50,
        min_score: float = 0.5,
        callback=None
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        流式处理大量信号

        Args:
            batch_size: 每批处理的信号数量
            min_score: 最小机会分数
            callback: 可选的回调函数，接收每批信号

        Yields:
            信号批次
        """
        offset = 0

        while True:
            try:
                result = await self.db.execute(
                    select(Article)
                    .where(
                        and_(
                            Article.opportunity_score >= min_score,
                            Article.content_theme.in_(["opportunity", "policy", "platform"])
                        )
                    )
                    .order_by(Article.opportunity_score.desc())
                    .offset(offset)
                    .limit(batch_size)
                )

                articles = result.scalars().all()

                if not articles:
                    break

                signals = []
                for article in articles:
                    signal = await self.to_signal(article)
                    signals.append(signal)

                if signals:
                    if callback:
                        await callback(signals)
                    yield signals

                offset += batch_size

                # 如果返回的数量少于batch_size，说明已经到底了
                if len(articles) < batch_size:
                    break

            except Exception as e:
                logger.error(f"流式信号提取失败 (offset={offset}): {e}")
                break


class PlatformNotificationAdapter(SignalAdapter):
    """平台通知信号适配器"""

    def to_signal(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """将平台通知转换为信号"""
        return {
            "type": "platform_notification",
            "title": notification.get("title", ""),
            "content": notification.get("message", "") or notification.get("description", ""),
            "source": notification.get("platform", "Platform"),
            "published_at": notification.get("timestamp") or notification.get("date"),
            "severity": notification.get("severity", "info"),
            "raw_data": notification
        }


class UserReportedSignalAdapter(SignalAdapter):
    """用户上报信号适配器"""

    def to_signal(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """将用户上报转换为信号"""
        return {
            "type": "user_report",
            "title": report.get("title", "用户上报的商机"),
            "content": report.get("description", ""),
            "source": f"user_{report.get('user_id', 'unknown')}",
            "published_at": report.get("created_at"),
            "user_confidence": report.get("confidence", 0.5),
            "raw_data": report
        }


class ProductMonitorSignalAdapter(SignalAdapter):
    """产品监控信号适配器"""

    def to_signal(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """将产品监控数据转换为信号"""
        title = product_data.get("title", "")
        price = product_data.get("price")
        rating = product_data.get("rating")
        sales_rank = product_data.get("sales_rank")

        # 判断是否有机会信号
        opportunity_indicators = []
        if price and price < 20:
            opportunity_indicators.append("低价产品")
        if rating and rating > 4.5:
            opportunity_indicators.append("高评分")
        if sales_rank and sales_rank < 100:
            opportunity_indicators.append("热销产品")

        return {
            "type": "product_monitor",
            "title": f"{title} - {', '.join(opportunity_indicators) if opportunity_indicators else '产品监控'}",
            "content": f"产品监控发现：价格{price}，评分{rating}，排名{sales_rank}",
            "source": "product_monitor",
            "published_at": product_data.get("monitored_at"),
            "asin": product_data.get("asin"),
            "opportunity_indicators": opportunity_indicators,
            "raw_data": product_data
        }


class SignalAdapterFactory:
    """信号适配器工厂"""

    @staticmethod
    def get_adapter(signal_type: str, **kwargs) -> SignalAdapter:
        """
        根据信号类型获取对应的适配器

        Args:
            signal_type: 信号类型
            **kwargs: 额外参数（如db session）

        Returns:
            对应的SignalAdapter实例
        """
        adapters = {
            "rss_article": RSSArticleSignalAdapter,
            "database_article": DatabaseArticleSignalAdapter,
            "platform_notification": PlatformNotificationAdapter,
            "user_report": UserReportedSignalAdapter,
            "product_monitor": ProductMonitorSignalAdapter
        }

        adapter_class = adapters.get(signal_type)
        if not adapter_class:
            logger.warning(f"Unknown signal type: {signal_type}, using base adapter")
            return SignalAdapter()

        # 如果适配器需要db参数
        if signal_type == "database_article":
            db = kwargs.get("db")
            if not db:
                raise ValueError("DatabaseArticleSignalAdapter requires db parameter")
            return adapter_class(db)

        return adapter_class()

    @staticmethod
    async def from_article_id(article_id: str, db: AsyncSessionLocal) -> Optional[Dict[str, Any]]:
        """
        从文章ID创建信号

        Args:
            article_id: 文章ID
            db: 数据库session

        Returns:
            信号字典，如果文章不存在则返回None
        """
        try:
            result = await db.execute(
                select(Article).where(Article.id == article_id)
            )
            article = result.scalar_one_or_none()

            if not article:
                logger.warning(f"Article not found: {article_id}")
                return None

            adapter = DatabaseArticleSignalAdapter(db)
            return await adapter.to_signal(article)

        except Exception as e:
            logger.error(f"Failed to create signal from article {article_id}: {e}")
            return None


# 批量转换函数
async def batch_convert_articles(
    articles: list,
    db: AsyncSessionLocal,
    limit: int = 100
) -> list:
    """
    批量转换文章为信号

    Args:
        articles: Article对象列表
        db: 数据库session
        limit: 最大转换数量

    Returns:
        信号列表
    """
    adapter = DatabaseArticleSignalAdapter(db)
    signals = []

    for i, article in enumerate(articles[:limit]):
        try:
            signal = await adapter.to_signal(article)
            signals.append(signal)
        except Exception as e:
            logger.error(f"Failed to convert article {article.id}: {e}")
            continue

    logger.info(f"批量转换完成: {len(signals)}/{len(articles[:limit])} 成功")
    return signals
