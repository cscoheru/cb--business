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
