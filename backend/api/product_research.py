# api/product_research.py
"""产品选品 API - 类似 SellerSprite 的选品逻辑"""
from fastapi import APIRouter, Query, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import logging

from config.database import get_db
from crawler.products.oxylabs_client import OxylabsClient
from models.article import Article

router = APIRouter(prefix="/api/v1/products", tags=["products"])
logger = logging.getLogger(__name__)


# 产品类目配置（基于Amazon类目树）
AMAZON_CATEGORIES = {
    "electronics": {
        "name": "电子产品",
        "name_en": "Electronics",
        "emoji": "📱",
        "node_id": "172282",  # Electronics node ID
        "subcategories": {
            "computers": "电脑",
            "phones": "手机",
            "cameras": "相机",
            "audio": "音频",
            "tv": "电视"
        }
    },
    "beauty": {
        "name": "美妆",
        "name_en": "Beauty",
        "emoji": "💄",
        "node_id": "11055991",
        "subcategories": {
            "makeup": "彩妆",
            "skincare": "护肤",
            "fragrance": "香水",
            "hair_care": "护发"
        }
    },
    "home": {
        "name": "家居",
        "name_en": "Home & Kitchen",
        "emoji": "🏠",
        "node_id": "1063498",
        "subcategories": {
            "furniture": "家具",
            "kitchen": "厨房",
            "bedding": "家纺",
            "decor": "装饰"
        }
    },
    "fashion": {
        "name": "服饰",
        "name_en": "Fashion",
        "emoji": "👗",
        "node_id": "11450847011",
        "subcategories": {
            "clothing": "服装",
            "shoes": "鞋靴",
            "jewelry": "珠宝",
            "bags": "包包"
        }
    },
    "sports": {
        "name": "运动",
        "name_en": "Sports",
        "emoji": "⚽",
        "node_id": "3375251",
        "subcategories": {
            "fitness": "健身",
            "outdoor": "户外",
            "camping": "露营",
            "cycling": "骑行"
        }
    },
}


@router.get("/categories")
async def get_categories():
    """获取产品类目列表（基于Amazon类目）"""
    categories = []

    for cat_id, cat_info in AMAZON_CATEGORIES.items():
        # 估算产品数量（基于Amazon Best Sellers数据）
        estimated_count = {
            "electronics": 100000,
            "beauty": 80000,
            "home": 90000,
            "fashion": 120000,
            "sports": 60000,
        }.get(cat_id, 50000)

        categories.append({
            "id": cat_id,
            "name": cat_info["name"],
            "name_en": cat_info["name_en"],
            "emoji": cat_info["emoji"],
            "count": estimated_count,
            "subcategories": cat_info["subcategories"]
        })

    return {"categories": categories}


@router.get("/research")
async def research_products(
    # 基础筛选条件
    category: str = Query(None, description="产品类目"),
    min_price: float = Query(None, description="最低价格"),
    max_price: float = Query(None, description="最高价格"),
    min_rating: float = Query(None, description="最低评分"),
    min_reviews: int = Query(None, description="最低评论数"),

    # BSR筛选
    min_bsr: int = Query(None, description="最低BSR排名"),
    max_bsr: int = Query(None, description="最高BSR排名"),

    # 卖家筛选
    max_sellers: int = Query(None, description="最大卖家数量"),
    seller_type: str = Query(None, description="卖家类型：AMZ/FBA/FBM"),

    # 利润筛选
    max_fba_fee: float = Query(None, description="最大FBA费用"),
    min_margin: float = Query(None, description="最低毛利率(%)"),

    # 上架时间
    launch_days_min: int = Query(None, description="最小上架天数"),
    launch_days_max: int = Query(None, description="最大上架天数"),

    # 排序和分页
    sort_by: str = Query("sales", description="排序字段：sales/revenue/bsr/price/margin"),
    sort_order: str = Query("desc", description="排序方向：asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    产品选品 - 类似 SellerSprite 的筛选逻辑

    参数说明：
    - category: 产品类目 (electronics/beauty/home/fashion/sports)
    - min_price/max_price: 价格区间筛选
    - min_rating: 最低评分 (4.0-5.0)
    - min_reviews: 最低评论数
    - min_bsr/max_bsr: BSR排名区间
    - max_sellers: 最大卖家数量（1=垄断产品）
    - seller_type: 卖家类型 (AMZ=Amazon自营/FBA=亚马逊配送/FBM=自发货)
    - sort_by: 排序字段
    """

    # TODO: 实际实现需要：
    # 1. 从数据库或缓存获取产品数据
    # 2. 根据筛选条件过滤
    # 3. 按指定字段排序
    # 4. 分页返回

    # 临时返回模拟数据
    products = [
        {
            "asin": "B0989C1LNK",
            "title": "Christmas Hat, Santa Hats for Adults & Kids",
            "brand": "BSVI",
            "price": 9.98,
            "rating": 4.3,
            "reviews_count": 3603,
            "bsr": 1656,
            "bsr_category": "#2 in Party Headwear",
            "monthly_sales": 10040,
            "monthly_revenue": 100199,
            "fba_fee": 4.23,
            "margin_pct": 43,
            "sellers_count": 1,
            "seller_type": "FBA",
            "launch_date": "2021-08-02",
            "variations_count": 7,
            "images": ["https://example.com/image.jpg"],
            "url": "https://www.amazon.com/dp/B0989C1LNK",
            "opportunity_score": 0.85,
            "competition_level": "low"
        },
        {
            "asin": "B0D69WKFHJ",
            "title": "Ogrmar 2 Pcs Plush Turkey Hat",
            "brand": "Ogrmar",
            "price": 19.99,
            "rating": 4.7,
            "reviews_count": 130,
            "bsr": 37900,
            "bsr_category": "#53 in Party Headwear",
            "monthly_sales": 6181,
            "monthly_revenue": 123558,
            "fba_fee": 7.13,
            "margin_pct": 49,
            "sellers_count": 1,
            "seller_type": "FBA",
            "launch_date": "2024-08-31",
            "variations_count": 1,
            "images": [],
            "url": "https://www.amazon.com/dp/B0D69WKFHJ",
            "opportunity_score": 0.75,
            "competition_level": "low"
        }
    ]

    return {
        "products": products,
        "total": len(products),
        "page": page,
        "per_page": per_page,
        "filters": {
            "category": category,
            "price_range": f"${min_price or 0} - ${max_price or 999}",
            "rating": f"{min_rating or 0}+ stars" if min_rating else None
        }
    }


@router.get("/market-analysis")
async def get_market_analysis(
    category: str = Query(..., description="产品类目"),
    db: AsyncSession = Depends(get_db)
):
    """
    市场分析 - 分析指定类目的市场情况

    返回：
    - 市场规模
    - Top产品列表
    - 竞争分析
    - 价格分布
    - 评分分布
    """

    # 从文章中提取市场洞察
    result = await db.execute(
        select(Article.content_theme, func.count(Article.id))
        .where(
            and_(
                Article.is_processed == True,
                Article.content_theme.isnot(None)
            )
        )
        .group_by(Article.content_theme)
    )

    theme_stats = result.all()

    # 按主题统计文章数
    market_insights = {
        theme: count for theme, count in theme_stats
    }

    # 分析市场趋势
    total_articles = sum(market_insights.values())

    return {
        "category": category,
        "category_name": AMAZON_CATEGORIES.get(category, {}).get("name", category),
        "market_size": {
            "total_articles": total_articles,
            "insights": market_insights
        },
        "top_themes": sorted(
            [{"theme": k, "count": v} for k, v in market_insights.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10],
        "recommendations": generate_market_recommendations(category, market_insights)
    }


def generate_market_recommendations(category: str, insights: Dict[str, int]) -> List[str]:
    """生成市场建议"""
    recommendations = []

    top_theme = max(insights.items(), key=lambda x: x[1])[0] if insights else None

    if top_theme == "opportunity":
        recommendations.append("该市场机会类产品较多，建议关注新兴趋势产品")
    elif top_theme == "policy":
        recommendations.append("政策变化频繁，建议密切关注各国电商政策动态")
    elif top_theme == "risk":
        recommendations.append("风险类产品需要谨慎，建议充分评估市场风险")

    # 通用建议
    recommendations.append(f"建议深入调研{AMAZON_CATEGORIES.get(category, {}).get('name', category)}类目的细分市场")
    recommendations.append("关注季节性产品，把握销售旺季")
    recommendations.append("分析竞品评论，发现用户痛点")

    return recommendations


@router.get("/trending")
async def get_trending_products(
    category: str = Query("electronics", description="产品类目"),
    limit: int = Query(10, ge=1, le=50),
    time_range: str = Query("30d", description="时间范围：7d/30d/90d")
):
    """
    获取热门产品 - 基于销售增长趋势

    参数：
    - category: 产品类目
    - limit: 返回数量
    - time_range: 时间范围
    """

    try:
        client = OxylabsClient()

        # 获取 Amazon Best Sellers
        products = await client.get_amazon_bestsellers(
            category=AMAZON_CATEGORIES.get(category, {}).get("node_id", "electronics"),
            domain="com",
            limit=limit
        )

        await client.close()

        # 转换为标准格式
        formatted_products = []
        for p in products[:limit]:
            formatted_products.append({
                "asin": p.get("asin"),
                "title": p.get("title"),
                "brand": p.get("brand"),
                "price": p.get("price", {}).get("value") if isinstance(p.get("price"), dict) else p.get("price"),
                "rating": p.get("rating"),
                "reviews_count": p.get("reviews_count", 0),
                "image": p.get("images", [{}])[0].get("url") if p.get("images") else None,
                "url": f"https://www.amazon.com/dp/{p.get('asin')}",
                "trending_score": calculate_trending_score(p)
            })

        return {
            "category": category,
            "time_range": time_range,
            "products": formatted_products,
            "count": len(formatted_products)
        }

    except Exception as e:
        logger.error(f"Failed to fetch trending products: {e}")
        return {"error": str(e), "products": []}


def calculate_trending_score(product: Dict) -> float:
    """计算产品热度评分"""
    score = 0.0

    # 评论数权重
    reviews = product.get("reviews_count", 0)
    score += min(reviews / 1000, 0.3) * 0.3

    # 评分权重
    rating = product.get("rating", 0)
    score += (rating / 5) * 0.3

    # 价格权重（适中价格更受欢迎）
    price = product.get("price", {}).get("value") if isinstance(product.get("price"), dict) else product.get("price", 0)
    if 10 <= price <= 50:
        score += 0.2
    elif price < 10:
        score += 0.1

    # 基础分
    score += 0.2

    return round(score, 2)


@router.get("/platforms")
async def get_platforms():
    """获取支持的电商平台列表"""
    return {
        "platforms": [
            {
                "id": "amazon",
                "name": "Amazon",
                "emoji": "🛒",
                "countries": ["us", "th", "vn", "my", "sg", "id", "ph"],
                "domains": ["amazon.com", "amazon.co.th", "amazon.co.jp"],
                "features": ["FBA", "Prime", "Global Selling"]
            },
            {
                "id": "shopee",
                "name": "Shopee",
                "emoji": "🛍️",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "domains": ["shopee.co.th", "shopee.vn"],
                "features": ["Free Shipping", "Flash Sale", "Coin Cashback"]
            },
            {
                "id": "lazada",
                "name": "Lazada",
                "emoji": "🛒",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "domains": ["lazada.co.th", "lazada.vn"],
                "features": ["LazMall", "Choice", "Free Shipping"]
            },
            {
                "id": "tiktok",
                "name": "TikTok Shop",
                "emoji": "🎵",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "domains": ["shop.tiktok.com"],
                "features": ["Live Streaming", "Affiliate", "Viral Marketing"]
            }
        ]
    }
