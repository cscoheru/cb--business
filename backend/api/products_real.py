# api/products_real.py
"""真实产品数据 API - 使用 Oxylabs 获取 Amazon 产品数据"""
from fastapi import APIRouter, Query
from typing import List, Dict, Any
import logging

from crawler.products.oxylabs_client import OxylabsClient

router = APIRouter(prefix="/api/v1/products", tags=["products"])
logger = logging.getLogger(__name__)


# Amazon 产品分类配置（基于真实Amazon分类）
AMAZON_CATEGORIES = {
    "electronics": {
        "id": "electronics",
        "name": "电子",
        "emoji": "📱",
        "amazon_path": "electronics",
        "keywords": ["smartphone", "laptop", "tablet", "headphones", "camera"]
    },
    "beauty": {
        "id": "beauty",
        "name": "美妆",
        "emoji": "💄",
        "amazon_path": "beauty",
        "keywords": ["makeup", "skincare", "cosmetics", "fragrance"]
    },
    "home": {
        "id": "home",
        "name": "家居",
        "emoji": "🏠",
        "amazon_path": "home-garden",
        "keywords": ["furniture", "kitchen", "bedding", "decor"]
    },
    "fashion": {
        "id": "fashion",
        "name": "服饰",
        "emoji": "👗",
        "amazon_path": "fashion",
        "keywords": ["clothing", "shoes", "jewelry", "handbags"]
    },
    "food": {
        "id": "food",
        "name": "食品",
        "emoji": "🍜",
        "amazon_path": "grocery",
        "keywords": ["snacks", "beverage", "organic", "gourmet"]
    },
    "baby": {
        "id": "baby",
        "name": "母婴",
        "emoji": "👶",
        "amazon_path": "baby-products",
        "keywords": ["diapers", "formula", "toys", "strollers"]
    },
    "sports": {
        "id": "sports",
        "name": "运动",
        "emoji": "⚽",
        "amazon_path": "sports-fitness",
        "keywords": ["fitness", "outdoor", "camping", "cycling"]
    },
    "pets": {
        "id": "pets",
        "name": "宠物",
        "emoji": "🐕",
        "amazon_path": "pets",
        "keywords": ["dog", "cat", "pet supplies", "aquarium"]
    },
}


@router.get("/categories")
async def get_categories():
    """获取 Amazon 产品类别列表（基于真实分类）"""

    # 模拟从 Amazon Best Sellers 获取每个类别的产品数量
    # 实际部署时可以缓存这些数据，定期更新
    categories = []

    for cat_id, cat_info in AMAZON_CATEGORIES.items():
        # 这里使用估算值，实际可以通过 Oxylabs API 获取实时数据
        # Amazon 各类别的大致产品数量（基于 Best Sellers 排名）
        estimated_count = {
            "electronics": 50000,
            "beauty": 40000,
            "home": 35000,
            "fashion": 45000,
            "food": 30000,
            "baby": 25000,
            "sports": 20000,
            "pets": 15000,
        }.get(cat_id, 10000)

        categories.append({
            "id": cat_id,
            "name": cat_info["name"],
            "emoji": cat_info["emoji"],
            "count": estimated_count,
            "amazon_path": cat_info["amazon_path"]
        })

    return {"categories": categories}


@router.get("/categories/{category_id}/trending")
async def get_category_trending(
    category_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    """获取指定类别的热门产品（使用 Oxylabs）"""

    if category_id not in AMAZON_CATEGORIES:
        return {"error": "Invalid category", "products": []}

    cat_info = AMAZON_CATEGORIES[category_id]

    try:
        client = OxylabsClient()

        # 获取 Amazon Best Sellers
        products = await client.get_amazon_bestsellers(
            category=cat_info["amazon_path"],
            domain="com",
            limit=limit
        )

        await client.close()

        # 转换为统一格式
        formatted_products = []
        for product in products[:limit]:
            formatted_products.append({
                "asin": product.get("asin"),
                "title": product.get("title"),
                "brand": product.get("brand"),
                "price": product.get("price"),
                "rating": product.get("rating"),
                "reviews_count": product.get("reviews_count", 0),
                "image": product.get("images", [{}])[0].get("url") if product.get("images") else None,
                "url": f"https://www.amazon.com/dp/{product.get('asin')}"
            })

        return {
            "category": category_id,
            "category_name": cat_info["name"],
            "products": formatted_products,
            "count": len(formatted_products)
        }

    except Exception as e:
        logger.error(f"Failed to fetch trending products for {category_id}: {e}")
        return {"error": str(e), "products": []}


@router.get("/search")
async def search_products(
    query: str = Query(..., min_length=2),
    category: str = Query(None, description="产品类别"),
    limit: int = Query(10, ge=1, le=20)
):
    """搜索 Amazon 产品"""

    try:
        client = OxylabsClient()

        # 使用 Amazon Search API
        products = await client.search_amazon(
            query=query,
            domain="com",
            category=AMAZON_CATEGORIES.get(category, {}).get("amazon_path") if category else None,
            limit=limit
        )

        await client.close()

        # 转换为统一格式
        formatted_products = []
        for product in products:
            formatted_products.append({
                "asin": product.get("asin"),
                "title": product.get("title"),
                "brand": product.get("brand"),
                "price": product.get("price"),
                "rating": product.get("rating"),
                "reviews_count": product.get("reviews_count", 0),
                "url": f"https://www.amazon.com/dp/{product.get('asin')}"
            })

        return {
            "query": query,
            "products": formatted_products,
            "count": len(formatted_products)
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"error": str(e), "products": []}


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
                "domains": ["amazon.com", "amazon.co.th", "amazon.co.jp", "amazon.sg"]
            },
            {
                "id": "shopee",
                "name": "Shopee",
                "emoji": "🛍️",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "domains": ["shopee.co.th", "shopee.vn", "shopee.com.my"]
            },
            {
                "id": "lazada",
                "name": "Lazada",
                "emoji": "🛒",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "domains": ["lazada.co.th", "lazada.vn", "lazada.com.my"]
            },
            {
                "id": "tiktok",
                "name": "TikTok Shop",
                "emoji": "🎵",
                "countries": ["th", "vn", "my", "sg", "id", "ph"],
                "domains": ["shop.tiktok.com"]
            }
        ]
    }
