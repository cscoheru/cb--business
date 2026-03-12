# api/crawler.py
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Optional
import logging
import json

from models.article import Article
from schemas.article import ArticleResponse, ArticleListResponse
from config.database import get_db

router = APIRouter(prefix="/api/v1/crawler", tags=["crawler"])
logger = logging.getLogger(__name__)


@router.get("/articles", response_model=ArticleListResponse)
async def get_articles(
    region: Optional[str] = Query(None, description="区域筛选"),
    country: Optional[str] = Query(None, description="国家代码筛选"),
    theme: Optional[str] = Query(None, description="主题筛选"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取文章列表（支持筛选）"""
    # 构建查询条件
    conditions = [Article.is_processed == True]

    if region:
        conditions.append(Article.region == region)

    if country:
        conditions.append(Article.country == country)

    if theme:
        conditions.append(Article.content_theme == theme)

    if platform:
        conditions.append(Article.platform == platform)

    # 构建查询
    query = select(Article).where(and_(*conditions))

    # 计算总数
    count_query = select(func.count(Article.id)).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 排序和分页
    query = query.order_by(desc(Article.published_at))
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # 执行查询
    result = await db.execute(query)
    articles = result.scalars().all()

    # 转换为响应格式
    article_responses = []
    for article in articles:
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
            country=article.country,
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
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)):
    """获取单篇文章详情"""
    result = await db.execute(
        select(Article).where(
            and_(
                Article.id == article_id,
                Article.is_processed == True
            )
        )
    )
    article = result.scalar_one_or_none()

    if not article:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Article not found")

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
        country=article.country,
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


@router.post("/trigger")
async def trigger_all_crawlers():
    """手动触发所有启用的爬虫"""
    from scheduler.tasks import execute_crawl
    from crawler.config import get_enabled_sources
    
    sources = get_enabled_sources()
    results = {}
    
    for source_name, config in sources.items():
        try:
            result = await execute_crawl(source_name)
            results[source_name] = result
        except Exception as e:
            logger.error(f"触发爬虫 {source_name} 失败: {e}")
            results[source_name] = {"success": False, "error": str(e)}
    
    total_new = sum(r.get("new_count", 0) for r in results.values())
    
    return {
        "success": True,
        "message": f"爬取完成，共新增 {total_new} 篇文章",
        "results": results
    }


@router.post("/trigger/{source_name}")
async def trigger_single_crawler(source_name: str):
    """手动触发单个爬虫"""
    from scheduler.tasks import execute_crawl
    
    result = await execute_crawl(source_name)
    
    return {
        "success": True,
        "source": source_name,
        "result": result
    }


@router.get("/status")
async def get_crawler_status():
    """获取爬虫状态"""
    from crawler.config import CRAWLER_SOURCES

    return {
        "sources": [
            {
                "name": config["name"],
                "type": config["type"],
                "enabled": config.get("enabled", False),
                "language": config.get("language", "unknown")
            }
            for name, config in CRAWLER_SOURCES.items()
        ]
    }


@router.post("/reprocess")
async def reprocess_articles(db: AsyncSession = Depends(get_db)):
    """重新处理所有文章，更新缺失的country字段和其他分类"""
    from crawler.processors.ai_processor import MockAIProcessor
    import json

    processor = MockAIProcessor()

    # 查找所有需要处理的文章（country为null的文章优先）
    result = await db.execute(
        select(Article).where(
            (Article.country == None) | (Article.region == 'global')
        ).limit(200)  # 限制每次处理数量，避免超时
    )
    articles = result.scalars().all()

    updated_count = 0
    for article in articles:
        try:
            # 重新分析文章
            article_data = {
                "title": article.title,
                "summary": article.summary or "",
                "full_content": article.full_content or "",
                "source": article.source
            }

            analysis = await processor.analyze_article(article_data)

            # 更新字段 - 添加country字段
            article.region = analysis.get("region", article.region)
            article.country = analysis.get("country", article.country)  # ✅ 添加country更新
            article.content_theme = analysis.get("content_theme", article.content_theme)
            article.platform = analysis.get("platform", article.platform)
            article.risk_level = analysis.get("risk_level", article.risk_level)
            article.opportunity_score = analysis.get("opportunity_score", article.opportunity_score)

            # 只在有新标签时才更新tags
            new_tags = analysis.get("tags", ["跨境电商"])
            try:
                existing_tags = json.loads(article.tags) if article.tags else []
                combined_tags = list(set(existing_tags + new_tags))
                article.tags = json.dumps(combined_tags)
            except:
                article.tags = json.dumps(new_tags)

            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to process article {article.id}: {e}")
            continue

    # 提交更改
    await db.commit()

    return {
        "success": True,
        "message": f"成功重新处理 {updated_count} 篇文章",
        "updated_count": updated_count,
        "total_articles": len(articles)
    }


@router.get("/reprocess/status")
async def reprocess_status(db: AsyncSession = Depends(get_db)):
    """检查文章处理状态"""
    # 统计总数
    count_result = await db.execute(select(func.count(Article.id)))
    total = count_result.scalar() or 0

    # 统计country为null的文章数
    null_country_result = await db.execute(
        select(func.count(Article.id)).where(Article.country == None)
    )
    null_country = null_country_result.scalar() or 0

    # 统计region为global的文章数
    global_region_result = await db.execute(
        select(func.count(Article.id)).where(Article.region == 'global')
    )
    global_region = global_region_result.scalar() or 0

    # 按region统计
    region_stats = {}
    for region in ['southeast_asia', 'north_america', 'latin_america', 'global']:
        result = await db.execute(
            select(func.count(Article.id)).where(Article.region == region)
        )
        region_stats[region] = result.scalar() or 0

    return {
        "total_articles": total,
        "null_country_count": null_country,
        "global_region_count": global_region,
        "region_breakdown": region_stats,
        "needs_reprocess": null_country + global_region
    }
