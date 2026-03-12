# api/products.py
"""产品数据API"""

import logging
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from models.product import Product
from config.database import get_db
from sqlalchemy import select, and_, desc, func

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/products", tags=["products"])

# 可选的 Oxylabs 集成
try:
    from crawler.products.oxylabs_client import OxylabsClient
    OXYLABS_AVAILABLE = True
    logger.info("Oxylabs integration enabled")
except ImportError as e:
    OXYLABS_AVAILABLE = False
    logger.warning(f"Oxylabs not available: {e}")


@router.get("/trending")
async def get_trending_products(
    platform: Optional[str] = Query(None, description="平台筛选"),
    country: Optional[str] = Query(None, description="国家代码筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    min_price: Optional[float] = Query(None, description="最低价格"),
    max_price: Optional[float] = Query(None, description="最高价格"),
    min_sold: Optional[int] = Query(None, description="最低销量"),
    sort_by: str = Query("sold_count", description="排序字段"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取热销商品列表"""
    # 构建查询条件
    conditions = []

    if platform:
        conditions.append(Product.platform == platform)

    if country:
        conditions.append(Product.country == country)

    if category:
        conditions.append(Product.category == category)

    if min_price:
        conditions.append(Product.price >= min_price)

    if max_price:
        conditions.append(Product.price <= max_price)

    if min_sold:
        conditions.append(Product.sold_count >= min_sold)

    # 构建查询
    query = select(Product).where(and_(*conditions)) if conditions else select(Product)

    # 排序
    if sort_by == "sold_count":
        query = query.order_by(desc(Product.sold_count))
    elif sort_by == "price":
        query = query.order_by(Product.price)
    elif sort_by == "rating":
        query = query.order_by(desc(Product.rating))
    elif sort_by == "reviews_count":
        query = query.order_by(desc(Product.reviews_count))

    # 计算总数
    count_query = select(func.count(Product.id)).select_from(
        query.alias('subquery')
    ) if conditions else select(func.count(Product.id))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # 执行查询
    result = await db.execute(query)
    products = result.scalars().all()

    # 转换为响应格式
    return {
        "products": [
            {
                "id": str(p.id),
                "title": p.title,
                "price": p.price,
                "original_price": p.original_price,
                "sold_count": p.sold_count,
                "rating": p.rating,
                "reviews_count": p.reviews_count,
                "platform": p.platform,
                "country": p.country,
                "category": p.category,
                "image_url": p.image_url,
                "product_url": p.product_url,
                "opportunity_score": p.opportunity_score,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/platforms")
async def get_available_platforms():
    """获取可用的平台列表"""
    return {
        "platforms": [
            {
                "id": "shopee",
                "name": "Shopee",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "logo": "🟠",
            },
            {
                "id": "amazon",
                "name": "Amazon",
                "countries": ["us", "th", "sg", "vn"],
                "logo": "📦",
            },
            {
                "id": "lazada",
                "name": "Lazada",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "logo": "🛍️",
            },
            {
                "id": "tiktok",
                "name": "TikTok Shop",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "logo": "🎬",
            },
        ]
    }


@router.get("/countries")
async def get_available_countries():
    """获取支持的国家列表"""
    return {
        "countries": [
            {"code": "th", "name": "Thailand", "flag": "🇹🇭", "region": "southeast_asia"},
            {"code": "vn", "name": "Vietnam", "flag": "🇻🇳", "region": "southeast_asia"},
            {"code": "my", "name": "Malaysia", "flag": "🇲🇾", "region": "southeast_asia"},
            {"code": "sg", "name": "Singapore", "flag": "🇸🇬", "region": "southeast_asia"},
            {"code": "id", "name": "Indonesia", "flag": "🇮🇩", "region": "southeast_asia"},
            {"code": "ph", "name": "Philippines", "flag": "🇵🇭", "region": "southeast_asia"},
            {"code": "us", "name": "United States", "flag": "🇺🇸", "region": "north_america"},
            {"code": "br", "name": "Brazil", "flag": "🇧🇷", "region": "latin_america"},
            {"code": "mx", "name": "Mexico", "flag": "🇲x️", "region": "latin_america"},
        ]
    }


@router.get("/stats")
async def get_products_stats(db: AsyncSession = Depends(get_db)):
    """获取产品数据统计"""
    # 总产品数
    total_result = await db.execute(select(func.count(Product.id)))
    total = total_result.scalar() or 0

    # 按平台统计
    platform_stats = {}
    for platform in ["shopee", "amazon", "lazada", "tiktok"]:
        result = await db.execute(
            select(func.count(Product.id)).where(Product.platform == platform)
        )
        platform_stats[platform] = result.scalar() or 0

    # 按国家统计
    country_stats = {}
    for country in ["th", "vn", "my", "sg", "id", "ph", "us", "br"]:
        result = await db.execute(
            select(func.count(Product.id)).where(Product.country == country)
        )
        count = result.scalar() or 0
        if count > 0:
            country_stats[country] = count

    # 按分类统计
    category_stats = {}
    categories = await db.execute(
        select(Product.category, func.count(Product.id))
        .group_by(Product.category)
        .limit(10)
    )
    for cat, count in categories:
        if cat:
            category_stats[cat] = count

    return {
        "total_products": total,
        "platform_breakdown": platform_stats,
        "country_breakdown": country_stats,
        "category_breakdown": category_stats,
    }


@router.post("/trigger/shopee")
async def trigger_shopee_crawl(
    country: str = Query(..., description="国家代码"),
    max_products: int = Query(50, description="最大商品数量")
):
    """手动触发Shopee商品爬取"""
    from crawler.products.shopee_trending import ShopeeTrendingCrawler

    results = []

    try:
        async with ShopeeTrendingCrawler() as crawler:
            products = await crawler.fetch_trending_products(
                country=country,
                max_products=max_products
            )

            # 这里应该保存到数据库
            # TODO: 实现数据库保存逻辑

            results = [
                {
                    "title": p.title,
                    "price": p.price,
                    "sold_count": p.sold_count,
                    "rating": p.rating,
                }
                for p in products
            ]

        return {
            "success": True,
            "country": country,
            "count": len(results),
            "products": results[:10],  # 返回前10个作为示例
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


@router.post("/trigger/amazon")
async def trigger_amazon_crawl(
    country: str = Query("us", description="国家代码 (us, th, sg, vn)"),
    category: str = Query(None, description="分类 (electronics, home, fashion, etc.)"),
    max_products: int = Query(20, description="最大商品数量")
):
    """手动触发Amazon Best Sellers商品爬取 (Playwright - Railway 不可用)"""
    from crawler.products.amazon_bestsellers import AmazonBestSellersCrawler

    try:
        async with AmazonBestSellersCrawler() as crawler:
            products = await crawler.fetch_bestsellers(
                country=country,
                category=category,
                max_products=max_products
            )

            # 转换为响应格式
            results = [
                {
                    "asin": p.asin,
                    "title": p.title,
                    "price": p.price,
                    "original_price": p.original_price,
                    "rating": p.rating,
                    "reviews_count": p.reviews_count,
                    "rank": p.rank,
                    "image_url": p.image_url,
                    "product_url": p.product_url,
                    "is_prime": p.is_prime,
                    "is_amazon_choice": p.is_amazon_choice,
                }
                for p in products
            ]

        return {
            "success": True,
            "country": country.upper(),
            "category": category or "all",
            "count": len(results),
            "products": results[:10],  # 返回前10个作为示例
        }

    except Exception as e:
        logger.error(f"Amazon爬取失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


# ==================== Oxylabs API 端点 (推荐) ====================

@router.get("/oxylabs/product/{asin}")
async def get_amazon_product_oxylabs(
    asin: str,
    domain: str = Query("com", description="Amazon 域名 (com, co.uk, de, jp)"),
):
    """
    使用 Oxylabs API 获取 Amazon 产品详情

    示例: GET /api/v1/products/oxylabs/product/B07FZ8S74R
    """
    if not OXYLABS_AVAILABLE:
        return {
            "success": False,
            "error": "Oxylabs integration not available",
            "asin": asin
        }

    client = OxylabsClient()

    try:
        product = await client.get_amazon_product(asin, domain=domain)

        if not product:
            return {
                "success": False,
                "error": "Product not found",
                "asin": asin
            }

        return {
            "success": True,
            "asin": product.get("asin"),
            "title": product.get("title"),
            "brand": product.get("brand"),
            "price": product.get("price"),
            "rating": product.get("rating"),
            "reviews_count": product.get("reviews_count"),
            "images": product.get("images", [])[:5],  # 最多5张图
            "bullet_points": product.get("bullet_points", [])[:3],  # 最多3条
            "stock": product.get("stock"),
            "url": product.get("url"),
        }

    except Exception as e:
        logger.error(f"Oxylabs API 错误: {e}")
        return {
            "success": False,
            "error": str(e),
            "asin": asin
        }
    finally:
        await client.close()


@router.get("/oxylabs/search")
async def search_amazon_oxylabs(
    query: str = Query(..., description="搜索关键词"),
    domain: str = Query("com", description="Amazon 域名"),
    category: str = Query("aps", description="分类 ID"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    使用 Oxylabs API 搜索 Amazon 产品

    示例: GET /api/v1/products/oxylabs/search?query=wireless+charger
    """
    if not OXYLABS_AVAILABLE:
        return {
            "success": False,
            "error": "Oxylabs integration not available",
            "products": []
        }

    client = OxylabsClient()

    try:
        products = await client.search_amazon(
            query=query,
            domain=domain,
            category=category,
            limit=limit
        )

        return {
            "success": True,
            "query": query,
            "count": len(products),
            "products": [
                {
                    "asin": p.get("asin"),
                    "title": p.get("title"),
                    "price": p.get("price"),
                    "rating": p.get("rating"),
                    "reviews_count": p.get("reviews_count"),
                    "url": p.get("url"),
                }
                for p in products
            ]
        }

    except Exception as e:
        logger.error(f"Oxylabs 搜索错误: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }
    finally:
        await client.close()


@router.get("/oxylabs/bestsellers")
async def get_amazon_bestsellers_oxylabs(
    category: str = Query("electronics", description="分类名称"),
    domain: str = Query("com", description="Amazon 域名"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    使用 Oxylabs API 获取 Amazon Best Sellers

    示例: GET /api/v1/products/oxylabs/bestsellers?category=electronics
    """
    if not OXYLABS_AVAILABLE:
        return {
            "success": False,
            "error": "Oxylabs integration not available",
            "products": []
        }

    client = OxylabsClient()

    try:
        products = await client.get_amazon_bestsellers(
            category=category,
            domain=domain,
            limit=limit
        )

        return {
            "success": True,
            "category": category,
            "domain": domain,
            "count": len(products),
            "products": [
                {
                    "asin": p.get("asin"),
                    "title": p.get("title"),
                    "price": p.get("price"),
                    "rating": p.get("rating"),
                    "reviews_count": p.get("reviews_count"),
                    "url": p.get("url"),
                }
                for p in products
            ]
        }

    except Exception as e:
        logger.error(f"Oxylabs Best Sellers 错误: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }
    finally:
        await client.close()
