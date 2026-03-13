# api/batch_operations.py
"""批量操作API - 供OpenClaw调用

OpenClaw Channels通过这些API端点批量写入数据到PostgreSQL。
这些端点专门为高吞吐量批量操作优化。

主要端点:
- POST /api/v1/batch/articles - 批量创建文章
- POST /api/v1/batch/products - 批量创建产品
- POST /api/v1/batch/classifications - 批量更新AI分类
- GET /api/v1/batch/unclassified - 获取待分类内容
- GET /api/v1/batch/status - 获取批量操作状态
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from sqlalchemy import select
from config.database import AsyncSessionLocal, get_db
from models.article import Article
from models.card import Card

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/batch", tags=["batch"])


# ============================================================================
# Request/Response Models
# ============================================================================

class BatchArticleRequest(BaseModel):
    """批量创建文章请求"""
    articles: List[Dict[str, Any]] = Field(
        ...,
        description="文章列表，每个文章包含title, content, url等字段"
    )
    source: str = Field(
        default="openclaw",
        description="数据来源标识"
    )


class BatchProductRequest(BaseModel):
    """批量创建产品请求"""
    products: List[Dict[str, Any]] = Field(
        ...,
        description="产品列表，每个产品包含asin, title, price等字段"
    )
    source: str = Field(
        default="openclaw",
        description="数据来源标识"
    )


class BatchClassificationUpdate(BaseModel):
    """批量更新AI分类请求"""
    updates: List[Dict[str, Any]] = Field(
        ...,
        description="分类更新列表，每项包含id和分类字段"
    )


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    success: bool
    total: int
    created: int
    updated: int
    failed: int
    errors: List[str] = []


class UnclassifiedItemRequest(BaseModel):
    """获取未分类内容请求"""
    type: str = Field(
        default="all",
        description="内容类型: articles, products, 或 all"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=500,
        description="返回数量限制"
    )


# ============================================================================
# Batch Articles Endpoints
# ============================================================================

@router.post("/articles", response_model=BatchOperationResponse)
async def batch_create_articles(
    request: BatchArticleRequest,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    批量创建文章 - OpenClaw RSS Crawler Channel调用

    数据流:
    OpenClaw RSS Channel → 45个RSS源 → 此API → PostgreSQL articles表

    Args:
        request: 包含文章列表的批量请求

    Returns:
        创建统计信息
    """
    try:
        created_count = 0
        updated_count = 0
        failed_count = 0
        errors = []

        for article_data in request.articles:
            try:
                # 检查是否已存在 (通过URL唯一性)
                existing = await db.execute(
                    select(Article).where(Article.url == article_data.get("url"))
                )
                existing_article = existing.scalar_one_or_none()

                if existing_article:
                    # 更新现有文章
                    for key, value in article_data.items():
                        if hasattr(existing_article, key):
                            setattr(existing_article, key, value)
                    existing_article.updated_at = datetime.now()
                    updated_count += 1
                else:
                    # 创建新文章
                    new_article = Article(
                        title=article_data.get("title", ""),
                        summary=article_data.get("summary") or article_data.get("content", "")[:500],
                        full_content=article_data.get("content"),
                        url=article_data.get("url"),
                        source_name=article_data.get("source_name", "OpenClaw"),
                        language=article_data.get("language", "en"),
                        link=article_data.get("url"),
                        published_at=article_data.get("published_at"),
                        created_at=datetime.now()
                    )
                    db.add(new_article)
                    created_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(f"Article {article_data.get('url', 'unknown')}: {str(e)}")
                logger.error(f"Failed to process article: {e}")

        # 提交所有更改
        await db.commit()

        logger.info(
            f"Batch articles: {created_count} created, "
            f"{updated_count} updated, {failed_count} failed"
        )

        return BatchOperationResponse(
            success=True,
            total=len(request.articles),
            created=created_count,
            updated=updated_count,
            failed=failed_count,
            errors=errors[:10]  # 只返回前10个错误
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Batch articles operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Batch Products Endpoints
# ============================================================================

@router.post("/products", response_model=BatchOperationResponse)
async def batch_create_products(
    request: BatchProductRequest,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    批量创建产品 - OpenClaw Oxylabs Monitor Channel调用

    数据流:
    OpenClaw Oxylabs Channel → Oxylabs API → 此API → 存储到Card的amazon_data

    注意: 产品数据存储在cards表的amazon_data字段中，而不是单独的products表

    Args:
        request: 包含产品列表的批量请求

    Returns:
        创建统计信息
    """
    try:
        created_count = 0
        updated_count = 0
        failed_count = 0
        errors = []

        # 按类别分组产品
        products_by_category: Dict[str, List[Dict]] = {}

        for product_data in request.products:
            category = product_data.get("category", "unknown")
            if category not in products_by_category:
                products_by_category[category] = []
            products_by_category[category].append(product_data)

        # 为每个类别创建或更新Card
        for category, products in products_by_category.items():
            try:
                # 检查是否已有该类别最近的Card
                existing = await db.execute(
                    select(Card)
                    .where(Card.category == category)
                    .where(Card.amazon_data.isnot(None))
                    .order_by(Card.created_at.desc())
                    .limit(1)
                )
                existing_card = existing.scalar_one_or_none()

                card_data = {
                    "amazon_data": {
                        "products": products,
                        "fetch_time": datetime.now().isoformat(),
                        "source": "openclaw_oxylabs"
                    },
                    "is_published": True,
                    "updated_at": datetime.now()
                }

                if existing_card:
                    # 更新现有Card
                    for key, value in card_data.items():
                        setattr(existing_card, key, value)
                    updated_count += 1
                else:
                    # 创建新Card
                    new_card = Card(
                        category=category,
                        title=f"{category.replace('_', ' ').title()} Products",
                        content_type="product_data",
                        **card_data,
                        created_at=datetime.now()
                    )
                    db.add(new_card)
                    created_count += 1

            except Exception as e:
                failed_count += len(products)
                errors.append(f"Category {category}: {str(e)}")
                logger.error(f"Failed to process products for {category}: {e}")

        # 提交所有更改
        await db.commit()

        logger.info(
            f"Batch products: {created_count} categories created, "
            f"{updated_count} updated, {failed_count} failed"
        )

        return BatchOperationResponse(
            success=True,
            total=len(products_by_category),
            created=created_count,
            updated=updated_count,
            failed=failed_count,
            errors=errors[:10]
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Batch products operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Batch Classification Endpoints
# ============================================================================

@router.post("/classifications", response_model=BatchOperationResponse)
async def batch_update_classifications(
    request: BatchClassificationUpdate,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    批量更新AI分类 - OpenClaw Content Classifier Channel调用

    数据流:
    OpenClaw AI分析 → 此API → 更新PostgreSQL中的AI字段

    更新的字段:
    - content_theme: 内容主题 (opportunity/risk/policy/guide)
    - region: 地区分类
    - platform: 平台 (amazon/shopee等)
    - keywords: 关键词列表
    - opportunity_score: 机会评分 (0-1)

    Args:
        request: 包含分类更新的批量请求

    Returns:
        更新统计信息
    """
    try:
        updated_count = 0
        failed_count = 0
        errors = []

        for update_data in request.updates:
            try:
                item_id = update_data.get("id")
                item_type = update_data.get("type", "article")

                if item_type == "article":
                    # 更新文章的AI分类
                    result = await db.execute(
                        select(Article).where(Article.id == item_id)
                    )
                    item = result.scalar_one_or_none()

                    if item:
                        item.content_theme = update_data.get("content_theme")
                        item.region = update_data.get("region")
                        item.platform = update_data.get("platform")
                        item.tags = update_data.get("keywords", [])
                        item.opportunity_score = update_data.get("opportunity_score", 0.5)
                        item.risk_level = update_data.get("risk_level")
                        item.is_processed = True
                        updated_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"Article {item_id} not found")

                elif item_type == "card":
                    # 更新Card的AI分类 - 存储在analysis字段中
                    result = await db.execute(
                        select(Card).where(Card.id == item_id)
                    )
                    item = result.scalar_one_or_none()

                    if item:
                        # 更新analysis JSONB字段
                        if not item.analysis:
                            item.analysis = {}
                        item.analysis["content_theme"] = update_data.get("content_theme")
                        item.analysis["region"] = update_data.get("region")
                        item.analysis["platform"] = update_data.get("platform")
                        item.analysis["opportunity_score"] = update_data.get("opportunity_score", 0.5)
                        # keywords可以存储在amazon_data中
                        if item.amazon_data:
                            item.amazon_data["ai_keywords"] = update_data.get("keywords", [])
                            item.amazon_data["ai_analyzed"] = True
                        updated_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"Card {item_id} not found")

            except Exception as e:
                failed_count += 1
                errors.append(f"Update {update_data.get('id')}: {str(e)}")
                logger.error(f"Failed to update classification: {e}")

        # 提交所有更改
        await db.commit()

        logger.info(
            f"Batch classifications: {updated_count} updated, {failed_count} failed"
        )

        return BatchOperationResponse(
            success=True,
            total=len(request.updates),
            created=0,
            updated=updated_count,
            failed=failed_count,
            errors=errors[:10]
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Batch classification update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Query Endpoints
# ============================================================================

@router.get("/unclassified")
async def get_unclassified_items(
    type: str = Query("all", description="内容类型: articles, products, 或 all"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取未分类内容 - OpenClaw Content Classifier Channel调用

    返回需要AI分类的文章或Card数据

    Args:
        type: 内容类型筛选
        limit: 返回数量限制

    Returns:
        待分类的内容列表
    """
    try:
        items = []

        if type in ["all", "articles"]:
            # 获取未AI分析的文章
            result = await db.execute(
                select(Article)
                .where(Article.is_processed == False)
                .order_by(Article.created_at.desc())
                .limit(limit // 2 if type == "all" else limit)
            )
            articles = result.scalars().all()

            for article in articles:
                items.append({
                    "id": article.id,
                    "type": "article",
                    "title": article.title,
                    "summary": article.summary,
                    "url": article.link,
                    "created_at": article.crawled_at.isoformat() if article.crawled_at else article.published_at.isoformat() if article.published_at else None
                })

        if type in ["all", "products"]:
            # 获取未AI分析的Card (产品数据)
            result = await db.execute(
                select(Card)
                .where(Card.amazon_data.isnot(None))
                .order_by(Card.created_at.desc())
                .limit(limit // 2 if type == "all" else limit)
            )
            cards = result.scalars().all()

            for card in cards:
                # 检查是否已经AI分析过
                is_analyzed = card.amazon_data and card.amazon_data.get("ai_analyzed") if card.amazon_data else False
                if not is_analyzed:
                    items.append({
                        "id": card.id,
                        "type": "card",
                        "title": card.title,
                        "category": card.category,
                        "created_at": card.created_at.isoformat()
                    })

        return {
            "success": True,
            "total": len(items),
            "items": items
        }

    except Exception as e:
        logger.error(f"Failed to get unclassified items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_batch_operation_status(
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取批量操作状态统计

    Returns:
        各类数据的统计信息
    """
    try:
        # 统计文章
        article_result = await db.execute(
            select(Article.id)
        )
        total_articles = len(article_result.all())

        analyzed_result = await db.execute(
            select(Article.id).where(Article.is_processed == True)
        )
        analyzed_articles = len(analyzed_result.all())

        # 统计Card
        card_result = await db.execute(
            select(Card.id)
        )
        total_cards = len(card_result.all())

        with_amazon_data_result = await db.execute(
            select(Card.id).where(Card.amazon_data.isnot(None))
        )
        cards_with_products = len(with_amazon_data_result.all())

        return {
            "success": True,
            "statistics": {
                "articles": {
                    "total": total_articles,
                    "processed": analyzed_articles,
                    "pending_analysis": total_articles - analyzed_articles
                },
                "cards": {
                    "total": total_cards,
                    "with_products": cards_with_products
                }
            },
            "data_sources": {
                "openclaw": {
                    "status": "active",
                    "last_sync": datetime.now().isoformat()
                }
            }
        }

    except Exception as e:
        logger.error(f"Failed to get batch operation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
