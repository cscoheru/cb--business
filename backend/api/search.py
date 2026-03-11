# api/search.py
from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import List, Optional
from datetime import datetime
import logging

from models.article import Article
from schemas.article import ArticleResponse, ArticleListResponse
from config.database import get_db

router = APIRouter(prefix="/api/v1/search", tags=["search"])
logger = logging.getLogger(__name__)


def calculate_relevance_score(article: Article, keywords: List[str]) -> int:
    """计算相关度分数"""
    score = 0

    title_lower = (article.title or "").lower()
    summary_lower = (article.summary or "").lower()
    source_lower = (article.source or "").lower()

    for keyword in keywords:
        keyword_lower = keyword.lower()

        # 标题完全匹配
        if title_lower == keyword_lower:
            score += 10
        # 标题包含
        elif keyword_lower in title_lower:
            score += 3

        # 摘要包含
        if keyword_lower in summary_lower:
            score += 1

        # 来源包含
        if keyword_lower in source_lower:
            score += 1

        # 标签匹配
        if article.tags:
            import json
            try:
                tags = json.loads(article.tags)
                for tag in tags:
                    if keyword_lower in tag.lower():
                        score += 2
                        break
            except:
                pass

    return score


@router.get("/articles", response_model=ArticleListResponse)
async def search_articles(
    q: Optional[str] = Query(None, description="搜索关键词"),
    region: Optional[str] = Query(None, description="区域筛选"),
    theme: Optional[str] = Query(None, description="主题筛选"),
    sort_by: Optional[str] = Query("relevance", description="排序方式: relevance, latest, oldest"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """搜索文章

    Args:
        q: 搜索关键词，支持多个词空格分隔
        region: 区域筛选 (southeast_asia, north_america, latin_america)
        theme: 主题筛选 (policy, opportunity, risk, guide, platform, logistics)
        sort_by: 排序方式
        page: 页码
        per_page: 每页数量
    """
    # 构建查询条件
    conditions = [Article.is_processed == True]

    # 关键词搜索
    keywords = []
    if q and q.strip():
        keywords = q.strip().split()

        if keywords:
            # 构建OR条件 - 任意字段包含关键词
            search_conditions = []
            for keyword in keywords:
                keyword_lower = f"%{keyword.lower()}%"

                search_conditions.append(
                    or_(
                        func.lower(Article.title).like(keyword_lower),
                        func.lower(Article.summary).like(keyword_lower),
                        func.lower(Article.source).like(keyword_lower),
                        func.lower(Article.tags).like(keyword_lower),
                    )
                )

            if search_conditions:
                # 使用AND连接多个关键词的搜索条件
                conditions.append(and_(*search_conditions))

    # 区域筛选
    if region:
        conditions.append(Article.region == region)

    # 主题筛选
    if theme:
        conditions.append(Article.content_theme == theme)

    # 构建基础查询
    query = select(Article).where(and_(*conditions))

    # 计算总数
    count_query = select(func.count(Article.id)).where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 排序
    if sort_by == "latest":
        query = query.order_by(desc(Article.published_at))
    elif sort_by == "oldest":
        query = query.order_by(Article.published_at)
    else:  # relevance
        # 对于相关度排序，我们需要先获取结果然后计算分数
        # 这里简化为按published_at排序，实际应用中可以在Python中排序
        query = query.order_by(desc(Article.published_at))

    # 分页
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # 执行查询
    result = await db.execute(query)
    articles = result.scalars().all()

    # 转换为响应格式
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

    # 如果按相关度排序，在Python中重新排序
    if sort_by == "relevance" and keywords:
        article_responses.sort(
            key=lambda a: calculate_relevance_score(article, keywords),
            reverse=True
        )

    return ArticleListResponse(
        articles=article_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/filters")
async def get_search_filters():
    """获取可用的搜索筛选选项"""
    return {
        "regions": [
            {"key": "southeast_asia", "label": "东南亚", "emoji": "🌏"},
            {"key": "north_america", "label": "欧美", "emoji": "🇺🇸"},
            {"key": "latin_america", "label": "拉美", "emoji": "🇧🇷"},
        ],
        "themes": [
            {"key": "policy", "label": "政策", "emoji": "📜"},
            {"key": "opportunity", "label": "机会", "emoji": "💡"},
            {"key": "risk", "label": "风险", "emoji": "⚠️"},
            {"key": "guide", "label": "实操", "emoji": "📊"},
            {"key": "platform", "label": "平台", "emoji": "🛒"},
            {"key": "logistics", "label": "物流", "emoji": "🚚"},
        ],
        "sort_options": [
            {"key": "relevance", "label": "相关度"},
            {"key": "latest", "label": "最新"},
            {"key": "oldest", "label": "最早"},
        ],
    }


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="搜索词"),
    db: AsyncSession = Depends(get_db),
):
    """获取搜索建议（自动完成）"""
    keyword_lower = f"%{q.lower()}%"

    # 搜索标题匹配的文章
    result = await db.execute(
        select(Article.title)
        .where(
            and_(
                func.lower(Article.title).like(keyword_lower),
                Article.is_processed == True
            )
        )
        .limit(10)
    )

    titles = result.scalars().all()

    # 搜索来源
    source_result = await db.execute(
        select(Article.source)
        .where(
            and_(
                func.lower(Article.source).like(keyword_lower),
                Article.is_processed == True
            )
        )
        .distinct()
        .limit(5)
    )

    sources = source_result.scalars().all()

    return {
        "titles": list(set(titles)),
        "sources": list(set(sources)),
    }
