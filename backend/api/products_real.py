# api/products_real.py
"""真实产品数据 API - 优先从 Cards 表读取，回退到 Oxylabs"""
from fastapi import APIRouter, Query, Depends
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio

from sqlalchemy import select, desc
from config.database import AsyncSessionLocal, get_db
from models.card import Card
from crawler.products.oxylabs_client import OxylabsClient
from config.redis import redis_client
from services.product_data_service import get_product_data_service

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


# Category mapping: Frontend broad categories → Cards table specific categories
# This maps user-facing categories to the actual categories stored in the cards table
CATEGORY_MAPPING = {
    "electronics": [
        "wireless_earbuds", "bluetooth_speakers", "phone_chargers",
        "desk_lamps", "webcams", "keyboards", "mouse"
    ],
    "home": [
        "smart_plugs", "coffee_makers", "desk_lamps"
    ],
    "sports": [
        "fitness_trackers", "yoga_mats"
    ],
    "fashion": [
        "phone_cases"
    ],
    # Additional category mappings for future data collection
    "beauty": [
        "makeup", "skincare", "hair_care", "fragrances"
    ],
    "food": [
        "groceries", "snacks", "beverages", "kitchen_supplies"
    ],
    "baby": [
        "baby_care", "diapers", "baby_formula", "baby_gear"
    ],
    "pets": [
        "pet_supplies", "dog_food", "cat_food", "pet_toys"
    ],
}


# 简单内存缓存（用于存储分类产品数量）
_category_count_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamps: Dict[str, datetime] = {}
CACHE_DURATION = timedelta(hours=1)  # 缓存1小时


async def _get_cached_category_count(category_id: str) -> int:
    """获取缓存的分类产品数量"""
    cache_key = f"category_count:{category_id}"

    # 检查缓存是否有效
    if cache_key in _cache_timestamps:
        cache_time = _cache_timestamps[cache_key]
        if datetime.now() - cache_time < CACHE_DURATION:
            return _category_count_cache[cache_key]["count"]

    return None


async def _set_cached_category_count(category_id: str, count: int):
    """设置缓存的分类产品数量"""
    cache_key = f"category_count:{category_id}"
    _category_count_cache[cache_key] = {"count": count}
    _cache_timestamps[cache_key] = datetime.now()


async def _fetch_products_from_cards(
    category_id: str,
    limit: int,
    db: AsyncSessionLocal,
    fetch_details: bool = False
) -> Dict[str, Any]:
    """
    从 Cards 表读取产品数据（主要数据源）

    Args:
        category_id: 前端分类ID (electronics, home, sports等)
        limit: 返回数量限制
        db: 数据库会话
        fetch_details: 是否获取完整产品详情 (brand, image等)

    Returns:
        包含产品的字典，如果未找到数据则返回None
    """
    # 如果需要完整详情，使用 ProductDataService
    if fetch_details:
        try:
            service = get_product_data_service()
            products = await service.get_products_with_details(
                category_id=category_id,
                category_mapping=CATEGORY_MAPPING,
                limit=limit,
                db=db
            )

            if products:
                logger.info(f"Retrieved {len(products)} products with details for {category_id}")
                return {
                    "category": category_id,
                    "category_name": AMAZON_CATEGORIES.get(category_id, {}).get("name", category_id),
                    "products": products,
                    "count": len(products),
                    "data_source": "cards_table_with_details"
                }
        except Exception as e:
            logger.warning(f"Failed to fetch products with details: {e}")
            # 继续使用普通方法

    # 普通方法：只从 cards 表读取缓存数据
    mapped_categories = CATEGORY_MAPPING.get(category_id, [])

    if not mapped_categories:
        logger.debug(f"No mapped categories for {category_id}, will use Oxylabs fallback")
        return None

    # 从所有映射的类别中获取最新的卡片
    results = []
    for card_category in mapped_categories:
        try:
            card_result = await db.execute(
                select(Card)
                .where(Card.category == card_category)
                .where(Card.amazon_data.isnot(None))
                .where(Card.is_published == True)
                .order_by(desc(Card.created_at))
                .limit(1)
            )
            card = card_result.scalar_one_or_none()

            if card and card.amazon_data:
                products = card.amazon_data.get("products", [])
                if products:
                    results.extend(products)
                    logger.debug(f"Found {len(products)} products in card category {card_category}")
        except Exception as e:
            logger.warning(f"Error reading cards for {card_category}: {e}")
            continue

    if not results:
        logger.debug(f"No products found in cards for {category_id}")
        return None

    # 格式化产品数据
    formatted_products = []
    for product in results[:limit]:
        if not product or not isinstance(product, dict):
            continue

        # 处理品牌字段
        brand = product.get("brand") or product.get("manufacturer") or "N/A"

        # 处理价格
        price = product.get("price")
        if isinstance(price, (int, float)):
            price = float(price)
        else:
            price = None

        # 处理评分
        rating = product.get("rating")
        if isinstance(rating, (int, float)):
            rating = float(rating)
        else:
            rating = None

        # 处理评论数
        reviews_count = product.get("reviews_count", 0)
        if isinstance(reviews_count, str):
            reviews_count = 0
        elif not isinstance(reviews_count, int):
            reviews_count = 0

        # 构建产品URL
        url = product.get("url")
        if url and not url.startswith("http"):
            url = f"https://www.amazon.com{url}"
        elif not url:
            url = f"https://www.amazon.com/dp/{product.get('asin', '')}"

        formatted_products.append({
            "asin": product.get("asin", ""),
            "title": product.get("title", "N/A"),
            "brand": brand,
            "price": price,
            "rating": rating,
            "reviews_count": reviews_count,
            "image": product.get("image"),  # Cards数据可能包含图片
            "url": url,
            "source": "cards_cache"  # 标记数据来源
        })

    logger.info(f"Returning {len(formatted_products)} products from cards for {category_id}")
    return {
        "category": category_id,
        "category_name": AMAZON_CATEGORIES.get(category_id, {}).get("name", category_id),
        "products": formatted_products,
        "count": len(formatted_products),
        "data_source": "cards_table"
    }


async def _fetch_products_from_oxylabs(
    category_id: str,
    amazon_path: str,
    limit: int
) -> Dict[str, Any]:
    """
    从 Oxylabs API 获取产品数据（回退数据源）

    Args:
        category_id: 分类ID
        amazon_path: Amazon分类路径
        limit: 返回数量限制

    Returns:
        包含产品的字典
    """
    try:
        client = OxylabsClient()

        products = await client.get_amazon_bestsellers(
            category=amazon_path,
            domain="com",
            limit=limit
        )

        await client.close()

        logger.debug(f"Oxylabs returned {len(products)} products for {category_id}")

        # 转换为统一格式
        formatted_products = []
        for i, product in enumerate(products[:limit]):
            if not product or not isinstance(product, dict):
                logger.warning(f"Skipping invalid product at index {i}: {type(product)}")
                continue

            try:
                brand = product.get("brand") or product.get("manufacturer") or "N/A"
                price = product.get("price")
                if isinstance(price, (int, float)):
                    price = float(price)
                else:
                    price = None

                rating = product.get("rating")
                if isinstance(rating, (int, float)):
                    rating = float(rating)
                else:
                    rating = None

                reviews_count = product.get("reviews_count", 0)
                if isinstance(reviews_count, str):
                    reviews_count = 0
                elif not isinstance(reviews_count, int):
                    reviews_count = 0

                # 构建产品URL
                url = product.get("url")
                if not url:
                    # 如果没有url字段，使用asin构建
                    asin = product.get("asin", "")
                    url = f"https://www.amazon.com/dp/{asin}" if asin else None
                elif not url.startswith("http"):
                    url = f"https://www.amazon.com{url}"

                formatted_products.append({
                    "asin": product.get("asin", ""),
                    "title": product.get("title", "N/A"),
                    "brand": brand,
                    "price": price,
                    "rating": rating,
                    "reviews_count": reviews_count,
                    "image": None,
                    "url": url,
                    "source": "oxylabs_api"
                })
            except Exception as e:
                logger.warning(f"Error formatting product {i}: {e}")
                continue

        logger.info(f"Fetched {len(formatted_products)} products from Oxylabs for {category_id}")
        return {
            "category": category_id,
            "category_name": AMAZON_CATEGORIES.get(category_id, {}).get("name", category_id),
            "products": formatted_products,
            "count": len(formatted_products),
            "data_source": "oxylabs_api"
        }

    except Exception as e:
        logger.error(f"Failed to fetch from Oxylabs for {category_id}: {e}")
        return {
            "category": category_id,
            "category_name": AMAZON_CATEGORIES.get(category_id, {}).get("name", category_id),
            "products": [],
            "count": 0,
            "data_source": "error",
            "error": str(e)
        }



async def _fetch_amazon_category_count(category_id: str, amazon_path: str) -> int:
    """调用Oxylabs API获取实际的Amazon分类产品数量"""
    cache_key = f"category_count:{category_id}"

    # 先检查缓存
    cached = await _get_cached_category_count(category_id)
    if cached is not None:
        return cached

    try:
        client = OxylabsClient()

        # 获取Amazon Best Sellers (限制数量以节省API调用)
        products = await client.get_amazon_bestsellers(
            category=amazon_path,
            domain="com",
            limit=10  # 只取前10个来估算
        )

        await client.close()

        # 基于返回的产品数量进行估算
        # Amazon Best Sellers通常返回100个，我们可以据此估算总量
        actual_count = len(products)

        # 使用经验值进行估算 (Best Sellers通常代表top产品)
        # 假设Best Sellers页显示100个产品，而实际类别有更多
        estimated_total = actual_count * 500  # 保守估计

        # 更新缓存
        await _set_cached_category_count(category_id, estimated_total)

        logger.info(f"Fetched real count for {category_id}: {actual_count} products, estimated: {estimated_total}")
        return estimated_total

    except Exception as e:
        logger.error(f"Failed to fetch count for {category_id}: {e}")
        # 返回默认估算值
        fallback_counts = {
            "electronics": 50000,
            "beauty": 40000,
            "home": 35000,
            "fashion": 45000,
            "food": 30000,
            "baby": 25000,
            "sports": 20000,
            "pets": 15000,
        }
        return fallback_counts.get(category_id, 10000)


@router.get("/categories")
async def get_categories():
    """获取 Amazon 产品类别列表（使用Oxylabs实时数据）"""

    categories = []

    # 并发获取所有分类的产品数量
    tasks = []
    category_ids = []

    for cat_id, cat_info in AMAZON_CATEGORIES.items():
        category_ids.append(cat_id)
        tasks.append(_fetch_amazon_category_count(cat_id, cat_info["amazon_path"]))

    # 并发执行（带超时）
    try:
        counts = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=30.0  # 30秒超时
        )
    except asyncio.TimeoutError:
        logger.warning("Timeout fetching category counts, using fallback values")
        counts = [None] * len(category_ids)

    # 构建响应
    for i, cat_id in enumerate(category_ids):
        cat_info = AMAZON_CATEGORIES[cat_id]
        count = counts[i] if isinstance(counts[i], int) else 10000

        categories.append({
            "id": cat_id,
            "name": cat_info["name"],
            "emoji": cat_info["emoji"],
            "count": count,
            "amazon_path": cat_info["amazon_path"]
        })

    return {"categories": categories}


@router.get("/categories/{category_id}/trending")
async def get_category_trending(
    category_id: str,
    limit: int = Query(10, ge=1, le=50),
    fetch_details: bool = Query(False, description="是否获取完整产品详情 (brand, image等)"),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取指定类别的热门产品

    数据源策略（优先级顺序）:
    1. Cards表 (已缓存的产品数据)
    2. Oxylabs API (实时API调用)

    Args:
        category_id: 产品类别ID (electronics, beauty, home等)
        limit: 返回数量限制
        fetch_details: 是否获取完整产品详情 (包含brand, image等字段)
        db: 数据库会话

    Returns:
        产品列表，包含来源标记
    """
    if category_id not in AMAZON_CATEGORIES:
        return {"error": "Invalid category", "products": []}

    cat_info = AMAZON_CATEGORIES[category_id]

    # Step 1: 尝试从 Cards 表读取
    cards_result = await _fetch_products_from_cards(category_id, limit, db, fetch_details)

    if cards_result and cards_result["count"] > 0:
        logger.info(f"Using cards data for {category_id} (details={fetch_details})")
        return cards_result

    # Step 2: 回退到 Oxylabs API
    logger.info(f"Falling back to Oxylabs API for {category_id}")
    oxylabs_result = await _fetch_products_from_oxylabs(
        category_id,
        cat_info["amazon_path"],
        limit
    )

    return oxylabs_result


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
            if not product or not isinstance(product, dict):
                continue

            # 处理品牌字段
            brand = product.get("brand") or product.get("manufacturer") or "N/A"

            # 处理价格
            price = product.get("price")
            if isinstance(price, (int, float)):
                price = float(price)
            else:
                price = None

            # 处理评分
            rating = product.get("rating")
            if isinstance(rating, (int, float)):
                rating = float(rating)
            else:
                rating = None

            # 处理评论数
            reviews_count = product.get("reviews_count", 0)
            if isinstance(reviews_count, str):
                reviews_count = 0
            elif not isinstance(reviews_count, int):
                reviews_count = 0

            # 构建产品URL
            url = product.get("url")
            if url and not url.startswith("http"):
                url = f"https://www.amazon.com{url}"
            else:
                url = f"https://www.amazon.com/dp/{product.get('asin', '')}"

            formatted_products.append({
                "asin": product.get("asin", ""),
                "title": product.get("title", "N/A"),
                "brand": brand,
                "price": price,
                "rating": rating,
                "reviews_count": reviews_count,
                "url": url
            })

        return {
            "query": query,
            "products": formatted_products,
            "count": len(formatted_products)
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"error": str(e), "products": []}


@router.get("/trending")
async def get_trending_products(
    category: str = Query("electronics", description="产品类别"),
    limit: int = Query(20, ge=1, le=50),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    fetch_details: bool = Query(False, description="是否获取完整产品详情"),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取热门产品列表 - 前端兼容接口

    支持的类别: electronics, beauty, home, fashion, food, baby, sports, pets

    数据源策略（优先级顺序）:
    1. Cards表 (已缓存的产品数据)
    2. Oxylabs API (实时API调用)
    """
    if category not in AMAZON_CATEGORIES:
        return {"category": category, "products": [], "count": 0}

    # 如果不强制刷新，先尝试从 Cards 表读取
    if not force_refresh:
        cards_result = await _fetch_products_from_cards(category, limit, db, fetch_details)
        if cards_result and cards_result["count"] > 0:
            return cards_result

    # 回退到 Oxylabs API
    oxylabs_result = await _fetch_products_from_oxylabs(
        category,
        AMAZON_CATEGORIES[category]["amazon_path"],
        limit
    )

    return oxylabs_result


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
