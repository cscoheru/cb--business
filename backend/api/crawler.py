# api/crawler.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import json
import logging
import asyncio

from models.user import User
from models.article import Article, CrawlLog
from schemas.article import (
    ArticleResponse,
    ArticleListResponse,
    CrawlTriggerResponse,
    CrawlStatusResponse,
)
from config.database import get_db
from api.dependencies import get_current_user, require_pro_user
from crawler.crawlers.rss_crawler import RSSCrawler
from crawler.crawlers.http_crawler import HTTPCrawler
from crawler.processors.ai_processor import AIProcessor, MockAIProcessor
from crawler.config import get_enabled_sources, get_source_config
from config.settings import settings

router = APIRouter(prefix="/api/v1/crawler", tags=["crawler"])

# 配置日志
logger = logging.getLogger(__name__)

# 初始化AI处理器 (安全地获取ZHIPU_AI_KEY)
try:
    zhpu_key = settings.ZHIPU_AI_KEY if settings.ZHIPU_AI_KEY else ""
except AttributeError:
    zhpu_key = ""

if zhpu_key:
    ai_processor = AIProcessor(api_key=zhpu_key)
else:
    ai_processor = MockAIProcessor()

# 存储正在运行的后台任务
running_tasks = {}


@router.post("/trigger/{source_name}", response_model=CrawlTriggerResponse)
async def trigger_crawl(
    source_name: str,
    current_user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
):
    """触发爬取任务"""
    # 检查数据源配置
    source_config = get_source_config(source_name)
    if not source_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SOURCE_NOT_FOUND", "message": f"未找到数据源: {source_name}"}
        )

    if not source_config.get("enabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SOURCE_DISABLED", "message": f"数据源已禁用: {source_name}"}
        )

    # 检查是否有正在进行的爬取任务
    recent_log = await db.execute(
        select(CrawlLog).where(
            and_(
                CrawlLog.source == source_name,
                CrawlLog.status == "success",
                CrawlLog.completed_at > datetime.utcnow() - timedelta(minutes=5)
            )
        ).order_by(desc(CrawlLog.completed_at))
    )
    if recent_log.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RECENTLY_CRAWLED", "message": "该数据源最近刚爬取过，请稍后再试"}
        )

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

    # 创建真正的后台任务
    task = asyncio.create_task(execute_crawl_task(source_name, str(crawl_log.id)))
    running_tasks[source_name] = task

    return CrawlTriggerResponse(
        success=True,
        message="爬取任务已启动",
        source=source_name,
        articles_count=0,
        started_at=datetime.utcnow()
    )


@router.get("/status/{source_name}", response_model=CrawlStatusResponse)
async def get_crawl_status(
    source_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取爬取状态"""
    source_config = get_source_config(source_name)
    if not source_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SOURCE_NOT_FOUND", "message": f"未找到数据源: {source_name}"}
        )

    # 获取最新的爬取记录
    result = await db.execute(
        select(CrawlLog).where(CrawlLog.source == source_name).order_by(desc(CrawlLog.started_at))
    )
    log = result.scalar_one_or_none()

    if not log:
        return CrawlStatusResponse(
            source=source_name,
            status="never",
            last_crawl_at=None,
            articles_count=0,
            next_crawl_at=None
        )

    # 计算下次爬取时间
    interval = source_config.get("update_interval", 3600)
    next_crawl_at = log.completed_at + timedelta(seconds=interval) if log.completed_at else None

    return CrawlStatusResponse(
        source=source_name,
        status=log.status,
        last_crawl_at=log.completed_at,
        articles_count=log.articles_count or 0,
        next_crawl_at=next_crawl_at
    )


@router.get("/sources", response_model=List[str])
async def list_sources(current_user: User = Depends(get_current_user)):
    """获取所有可用数据源"""
    sources = list(get_enabled_sources().keys())
    return sources


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    page: int = 1,
    per_page: int = 20,
    theme: Optional[str] = None,
    region: Optional[str] = None,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取文章列表（公开访问）"""
    # 构建查询
    conditions = []

    if theme:
        conditions.append(Article.content_theme == theme)
    if region:
        conditions.append(Article.region == region)
    if platform:
        conditions.append(Article.platform == platform)

    # 只返回已处理的文章
    conditions.append(Article.is_processed == True)

    # 计算总数
    count_query = select(func.count(Article.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    else:
        count_query = count_query.where(Article.is_processed == True)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页查询
    offset = (page - 1) * per_page

    query = select(Article).where(Article.is_processed == True)
    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(desc(Article.published_at)).offset(offset).limit(per_page)

    result = await db.execute(query)
    articles = result.scalars().all()

    # Convert database models to response format
    article_responses = []
    for article in articles:
        import json
        tags_list = []
        try:
            if article.tags:
                tags_list = json.loads(article.tags)
        except:
            pass

        article_responses.append(ArticleResponse(
            id=str(article.id),
            title=article.title,
            summary=article.summary,
            full_content=article.full_content,
            link=article.link,
            source=article.source,
            language=article.language,
            content_theme=article.content_theme,
            region=article.region,
            platform=article.platform,
            tags=tags_list,
            risk_level=article.risk_level,
            opportunity_score=article.opportunity_score,
            author=article.author,
            published_at=article.published_at,
            crawled_at=article.crawled_at,
            is_processed=article.is_processed,
            is_published=article.is_published,
        ))

    return ArticleListResponse(
        articles=article_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取文章详情（公开访问）"""
    import uuid

    try:
        article_id_uuid = uuid.UUID(article_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ID", "message": "无效的文章ID"}
        )

    article = await db.get(Article, article_id_uuid)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ARTICLE_NOT_FOUND", "message": "文章不存在"}
        )

    # Convert database model to response format
    import json
    tags_list = []
    try:
        if article.tags:
            tags_list = json.loads(article.tags)
    except:
        pass

    return ArticleResponse(
        id=str(article.id),
        title=article.title,
        summary=article.summary,
        full_content=article.full_content,
        link=article.link,
        source=article.source,
        language=article.language,
        content_theme=article.content_theme,
        region=article.region,
        platform=article.platform,
        tags=tags_list,
        risk_level=article.risk_level,
        opportunity_score=article.opportunity_score,
        author=article.author,
        published_at=article.published_at,
        crawled_at=article.crawled_at,
        is_processed=article.is_processed,
        is_published=article.is_published,
    )


async def execute_crawl_task(
    source_name: str,
    log_id: str,
    db: AsyncSession
):
    """执行爬取任务（后台任务）"""
    from config.database import AsyncSessionLocal

    source_config = get_source_config(source_name)

    async with AsyncSessionLocal() as db:
        # 获取日志记录
        result = await db.execute(select(CrawlLog).where(CrawlLog.id == uuid.UUID(log_id)))
        crawl_log = result.scalar_one_or_none()

        if not crawl_log:
            logger.error(f"Crawl log not found: {log_id}")
            return

        try:
            # 选择爬虫类型
            if source_config["type"] == "rss":
                crawler = RSSCrawler(source_config)
            elif source_config["type"] == "http":
                crawler = HTTPCrawler(source_config)
            else:
                raise ValueError(f"Unsupported crawler type: {source_config['type']}")

            # 执行爬取
            articles = await crawler.fetch()

            # 处理每篇文章
            processed_count = 0
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
                    tags=json.dumps(analysis.get("tags", [])),
                    risk_level=analysis.get("risk_level"),
                    opportunity_score=analysis.get("opportunity_score", 0.0),
                    is_processed=True,
                    is_published=False,  # 需要审核后发布
                )

                db.add(article)
                processed_count += 1

            # 更新爬取日志
            crawl_log.status = "success"
            crawl_log.articles_count = processed_count
            crawl_log.completed_at = datetime.utcnow()

            await db.commit()

            logger.info(f"Crawl task completed for {source_name}: {processed_count} articles processed")

        except Exception as e:
            logger.error(f"Crawl task failed for {source_name}: {e}")
            crawl_log.status = "failed"
            crawl_log.error_message = str(e)
            await db.commit()
