# scheduler/tasks.py
"""定时任务定义"""
import logging
import uuid
from datetime import datetime
from sqlalchemy import select

from models.article import Article, CrawlLog
from crawler.crawlers.rss_crawler import RSSCrawler
from crawler.crawlers.http_crawler import HTTPCrawler
from crawler.processors.ai_processor import AIProcessor, MockAIProcessor
from crawler.config import get_source_config
from config.settings import settings

logger = logging.getLogger(__name__)

# 初始化AI处理器
try:
    zhpu_key = settings.ZHIPU_AI_KEY if settings.ZHIPU_AI_KEY else ""
except AttributeError:
    zhpu_key = ""

if zhpu_key:
    ai_processor = AIProcessor(api_key=zhpu_key)
else:
    ai_processor = MockAIProcessor()


async def execute_crawl(source_name: str) -> dict:
    """执行爬取任务的通用函数"""
    source_config = get_source_config(source_name)

    if not source_config or not source_config.get("enabled"):
        logger.warning(f"数据源 {source_name} 未启用或不存在")
        return {"success": False, "articles_count": 0}

    from config.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        # 检查最近是否爬取过
        from datetime import timedelta
        recent_log = await db.execute(
            select(CrawlLog).where(
                CrawlLog.source == source_name,
                CrawlLog.status == "success",
                CrawlLog.completed_at > datetime.utcnow() - timedelta(minutes=30)
            )
        )
        if recent_log.scalar_one_or_none():
            logger.info(f"数据源 {source_name} 最近已爬取，跳过")
            return {"success": True, "articles_count": 0, "skipped": True}

        # 创建爬取日志
        crawl_log = CrawlLog(
            id=uuid.uuid4(),
            source=source_name,
            status="running",
            articles_count=0,
            started_at=datetime.utcnow()
        )
        db.add(crawl_log)
        await db.commit()

        try:
            # 选择爬虫类型
            if source_config["type"] == "rss":
                crawler = RSSCrawler(source_config)
            elif source_config["type"] == "http":
                crawler = HTTPCrawler(source_config)
            else:
                raise ValueError(f"不支持的爬虫类型: {source_config['type']}")

            # 执行爬取
            articles = await crawler.fetch()
            logger.info(f"从 {source_name} 爬取了 {len(articles)} 篇文章")

            # 处理每篇文章
            processed_count = 0
            new_count = 0
            for article_data in articles:
                # 检查文章是否已存在
                existing = await db.execute(
                    select(Article).where(Article.link == article_data["link"])
                )
                if existing.scalar_one_or_none():
                    continue

                # AI分析
                analysis = await ai_processor.analyze_article(article_data)

                # 创建文章记录
                article = Article(
                    id=uuid.uuid4(),
                    title=article_data.get("title", ""),
                    summary=article_data.get("summary", ""),
                    full_content=article_data.get("full_content", ""),
                    link=article_data["link"],
                    source=article_data.get("source", source_name),
                    language=article_data.get("language", "zh"),
                    author=article_data.get("author", ""),
                    published_at=article_data.get("published_at"),
                    content_theme=analysis.get("content_theme"),
                    region=analysis.get("region"),
                    platform=analysis.get("platform"),
                    tags=str(analysis.get("tags", [])),
                    risk_level=analysis.get("risk_level"),
                    opportunity_score=analysis.get("opportunity_score", 0.0),
                    is_processed=True,
                    is_published=True,  # 定时任务的文章自动发布
                )

                db.add(article)
                processed_count += 1
                new_count += 1

            # 更新爬取日志
            crawl_log.status = "success"
            crawl_log.articles_count = processed_count
            crawl_log.completed_at = datetime.utcnow()

            await db.commit()

            logger.info(f"✅ {source_name} 爬取完成: 新增 {new_count} 篇文章")

            return {
                "success": True,
                "articles_count": processed_count,
                "new_count": new_count
            }

        except Exception as e:
            logger.error(f"❌ {source_name} 爬取失败: {e}")
            crawl_log.status = "failed"
            crawl_log.error_message = str(e)
            await db.commit()

            return {
                "success": False,
                "articles_count": 0,
                "error": str(e)
            }


async def crawl_retail_dive():
    """Retail Dive 定时爬取任务"""
    logger.info("🔍 开始爬取 Retail Dive...")
    result = await execute_crawl("retail_dive")
    logger.info(f"Retail Dive 爬取完成: {result}")


async def crawl_shopify_blog():
    """Shopify Blog 定时爬取任务"""
    logger.info("🔍 开始爬取 Shopify Blog...")
    result = await execute_crawl("shopify_blog")
    logger.info(f"Shopify Blog 爬取完成: {result}")


async def crawl_cifnews():
    """雨果网定时爬取任务"""
    logger.info("🔍 开始爬取雨果网...")
    result = await execute_crawl("cifnews")
    logger.info(f"雨果网爬取完成: {result}")
