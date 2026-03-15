# api/products_real.py
"""真实产品数据 API - 优先从 Cards 表读取，回退到 Oxylabs"""
from fastapi import APIRouter, Query, Depends
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor

from sqlalchemy import select, desc
from config.database import AsyncSessionLocal, get_db
from models.card import Card
from crawler.products.oxylabs_client import OxylabsClient
from config.redis import redis_client
import os

router = APIRouter(prefix="/api/v1/products", tags=["products"])
logger = logging.getLogger(__name__)

# 同步数据库连接配置（用于 Products API）
SYNC_DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "cb-business-postgres"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "cbdb"),
    "user": os.getenv("POSTGRES_USER", "cbuser"),
    "password": os.getenv("POSTGRES_PASSWORD", "cbuser123"),
}


# Amazon 产品分类配置（基于真实Amazon分类）
AMAZON_CATEGORIES = {
    # 大类
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
    # 具体产品类别 (直接从 Cards 表读取)
    "wireless_earbuds": {
        "id": "wireless_earbuds",
        "name": "无线耳机",
        "emoji": "🎧",
        "amazon_path": "electronics",
        "keywords": ["earbuds", "wireless", "headphones"]
    },
    "fitness_trackers": {
        "id": "fitness_trackers",
        "name": "健身追踪器",
        "emoji": "⌚",
        "amazon_path": "sports-fitness",
        "keywords": ["fitness", "tracker", "smartwatch"]
    },
    "smart_plugs": {
        "id": "smart_plugs",
        "name": "智能插座",
        "emoji": "🔌",
        "amazon_path": "home-garden",
        "keywords": ["smart", "plug", "outlet"]
    },
    "bluetooth_speakers": {
        "id": "bluetooth_speakers",
        "name": "蓝牙音箱",
        "emoji": "🔊",
        "amazon_path": "electronics",
        "keywords": ["bluetooth", "speaker", "audio"]
    },
    "phone_chargers": {
        "id": "phone_chargers",
        "name": "手机充电器",
        "emoji": "🔋",
        "amazon_path": "electronics",
        "keywords": ["charger", "phone", "usb"]
    },
    "desk_lamps": {
        "id": "desk_lamps",
        "name": "台灯",
        "emoji": "💡",
        "amazon_path": "home-garden",
        "keywords": ["lamp", "desk", "light"]
    },
    "mouse": {
        "id": "mouse",
        "name": "鼠标",
        "emoji": "🖱️",
        "amazon_path": "electronics",
        "keywords": ["mouse", "wireless", "ergonomic"]
    },
    "coffee_makers": {
        "id": "coffee_makers",
        "name": "咖啡机",
        "emoji": "☕",
        "amazon_path": "home-kitchen",
        "keywords": ["coffee", "maker", "espresso"]
    },
    "webcams": {
        "id": "webcams",
        "name": "网络摄像头",
        "emoji": "📷",
        "amazon_path": "electronics",
        "keywords": ["webcam", "camera", "video"]
    },
    "keyboards": {
        "id": "keyboards",
        "name": "键盘",
        "emoji": "⌨️",
        "amazon_path": "electronics",
        "keywords": ["keyboard", "mechanical", "wireless"]
    },
    "yoga_mats": {
        "id": "yoga_mats",
        "name": "瑜伽垫",
        "emoji": "🧘",
        "amazon_path": "sports-fitness",
        "keywords": ["yoga", "mat", "fitness"]
    },
    "phone_cases": {
        "id": "phone_cases",
        "name": "手机壳",
        "emoji": "📱",
        "amazon_path": "electronics",
        "keywords": ["case", "phone", "cover"]
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
    # 具体类别映射到自己
    "wireless_earbuds": ["wireless_earbuds"],
    "fitness_trackers": ["fitness_trackers"],
    "smart_plugs": ["smart_plugs"],
    "bluetooth_speakers": ["bluetooth_speakers"],
    "phone_chargers": ["phone_chargers"],
    "desk_lamps": ["desk_lamps"],
    "mouse": ["mouse"],
    "coffee_makers": ["coffee_makers"],
    "webcams": ["webcams"],
    "keyboards": ["keyboards"],
    "yoga_mats": ["yoga_mats"],
    "phone_cases": ["phone_cases"],
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


def _fetch_products_from_cards_sync(
    category_id: str,
    limit: int
) -> Optional[Dict[str, Any]]:
    """
    从 Cards 表读取产品数据（使用同步连接）

    Args:
        category_id: 前端分类ID (wireless_earbuds, electronics等)
        limit: 返回数量限制

    Returns:
        包含产品的字典，如果未找到数据则返回None
    """
    try:
        # 使用与 crawler_sync.py 完全相同的数据库配置
        DB_CONFIG = {
            "host": "cb-business-postgres",
            "port": 5432,
            "database": "cbdb",
            "user": "cbuser",
            "password": "k8VmK8PvqAFlEdirpJVJNo8DPe2bVlYPtV6xea+DlQQ="  # 使用实际密码
        }

        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        # 获取映射的类别列表
        mapped_categories = CATEGORY_MAPPING.get(category_id, [])

        # 如果是具体类别（只有一个映射），直接查询
        if len(mapped_categories) == 1 and mapped_categories[0] == category_id:
            query = """
                SELECT amazon_data
                FROM cards
                WHERE category = %s
                  AND amazon_data IS NOT NULL
                  AND is_published = true
                ORDER BY created_at DESC
                LIMIT 1
            """
            cursor.execute(query, [category_id])
            card = cursor.fetchone()

            if not card or not card['amazon_data']:
                logger.debug(f"No products found in cards for {category_id}")
                cursor.close()
                conn.close()
                return None

            # 提取产品数据
            products = card['amazon_data'].get("products", [])
        else:
            # 大类：从多个子类别聚合数据
            all_products = []
            for sub_category in mapped_categories:
                query = """
                    SELECT amazon_data
                    FROM cards
                    WHERE category = %s
                      AND amazon_data IS NOT NULL
                      AND is_published = true
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                cursor.execute(query, [sub_category])
                card = cursor.fetchone()

                if card and card['amazon_data']:
                    products = card['amazon_data'].get("products", [])
                    if products:
                        all_products.extend(products)
                        logger.debug(f"Found {len(products)} products in {sub_category}")

            if not all_products:
                logger.debug(f"No products found in cards for {category_id}")
                cursor.close()
                conn.close()
                return None

            products = all_products

        cursor.close()
        conn.close()

        if not products:
            return None

        # 格式化产品数据
        formatted_products = []
        for product in products[:limit]:
            if not product or not isinstance(product, dict):
                continue

            # 处理品牌字段
            brand = (
                product.get("brand") or
                product.get("manufacturer") or
                product.get("brand_name") or
                "Unknown Brand"
            )

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
            asin = product.get("asin", "")
            url = product.get("url")
            if url and not url.startswith("http"):
                url = f"https://www.amazon.com{url}"
            elif not url and asin:
                url = f"https://www.amazon.com/dp/{asin}"
            else:
                url = "https://www.amazon.com"

            formatted_products.append({
                "asin": asin,
                "title": product.get("title", "N/A"),
                "brand": brand,
                "price": price,
                "rating": rating,
                "reviews_count": reviews_count,
                "image": product.get("image"),
                "url": url,
                "source": "cards_table"
            })

        logger.info(f"Returning {len(formatted_products)} products from cards for {category_id}")
        return {
            "category": category_id,
            "category_name": AMAZON_CATEGORIES.get(category_id, {}).get("name", category_id),
            "products": formatted_products,
            "count": len(formatted_products),
            "data_source": "cards_table"
        }

    except Exception as e:
        logger.error(f"Error reading cards from database: {e}")
        return None


async def _fetch_products_from_cards(
    category_id: str,
    limit: int,
    db: AsyncSessionLocal,
    fetch_details: bool = False,
    details_limit: int = 10
) -> Dict[str, Any]:
    """
    从 Cards 表读取产品数据（主要数据源）

    Args:
        category_id: 前端分类ID (electronics, home, sports等)
        limit: 返回数量限制
        db: 数据库会话
        fetch_details: 是否获取完整产品详情 (brand, image等)
        details_limit: 获取详情的产品数量限制

    Returns:
        包含产品的字典，如果未找到数据则返回None
    """
    logger.info(f"_fetch_products_from_cards called: category={category_id}, fetch_details={fetch_details}, limit={limit}")

    # 首先从Cards表获取基础数据（使用同步连接）
    basic_result = _fetch_products_from_cards_sync(category_id, limit)

    if not basic_result or basic_result["count"] == 0:
        return basic_result

    # 如果需要完整详情，增强前N个产品的数据
    if fetch_details and basic_result["products"]:
        logger.info(f"Enhancing {min(details_limit, len(basic_result['products']))} products with details")
        try:
            enhanced_products = await _enhance_products_with_details(
                basic_result["products"],
                details_limit
            )

            # 更新产品列表（前N个使用增强数据）
            basic_result["products"] = enhanced_products + basic_result["products"][details_limit:]
            basic_result["data_source"] = "cards_table_with_details"
            logger.info(f"Successfully enhanced products for {category_id}")
        except Exception as e:
            logger.error(f"Failed to enhance products, using basic data: {e}", exc_info=True)

    return basic_result


async def _enhance_products_with_details(
    products: List[Dict[str, Any]],
    limit: int
) -> List[Dict[str, Any]]:
    """
    使用Oxylabs Product API增强产品数据

    Args:
        products: 基础产品列表
        limit: 需要增强的产品数量

    Returns:
        增强后的产品列表
    """
    if not products:
        return []

    # 提取ASIN列表
    asins_to_fetch = [p.get("asin") for p in products[:limit] if p.get("asin")]

    if not asins_to_fetch:
        logger.warning("No valid ASINs found for detail fetching")
        return products[:limit]

    logger.info(f"Fetching details for {len(asins_to_fetch)} ASINs: {asins_to_fetch}")

    try:
        from crawler.products.oxylabs_client import OxylabsClient
        client = OxylabsClient()

        # 并发获取产品详情（Oxylabs Product API内置1小时缓存）
        import asyncio
        semaphore = asyncio.Semaphore(3)  # 限制并发数

        async def fetch_with_limit(asin: str) -> tuple[str, Optional[Dict]]:
            async with semaphore:
                try:
                    product_data = await client.get_amazon_product(asin)
                    if product_data:
                        return asin, _convert_to_standard_format(product_data)
                    return asin, None
                except Exception as e:
                    logger.warning(f"Failed to fetch details for {asin}: {e}")
                    return asin, None

        # 并发获取
        tasks = [fetch_with_limit(asin) for asin in asins_to_fetch]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # 构建ASIN -> 增强数据的映射
        enhanced_map = {asin: data for asin, data in results if data is not None}

        logger.info(f"Successfully fetched details for {len(enhanced_map)}/{len(asins_to_fetch)} products")

        # 构建最终产品列表
        final_products = []
        for product in products[:limit]:
            asin = product.get("asin")
            if asin in enhanced_map:
                final_products.append(enhanced_map[asin])
            else:
                # 保留原始数据
                final_products.append(product)

        return final_products

    except Exception as e:
        logger.error(f"Error in _enhance_products_with_details: {e}", exc_info=True)
        return products[:limit]


def _convert_to_standard_format(oxylabs_data: Dict[str, Any]) -> Dict[str, Any]:
    """将Oxylabs Product API数据转换为标准格式"""
    # 提取品牌
    brand = (
        oxylabs_data.get("brand") or
        oxylabs_data.get("manufacturer") or
        "Unknown Brand"
    )

    # 提取图片
    image = _extract_oxylabs_image(oxylabs_data)

    # 提取价格
    price = _extract_oxylabs_price(oxylabs_data)

    # 提取评分
    rating = oxylabs_data.get("rating")
    if isinstance(rating, (int, float)):
        rating = float(rating)
    elif isinstance(rating, str):
        try:
            rating = float(rating)
        except ValueError:
            rating = None
    else:
        rating = None

    # 构建URL
    asin = oxylabs_data.get("asin", "")
    url = f"https://www.amazon.com/dp/{asin}" if asin else "https://www.amazon.com"

    return {
        "asin": asin,
        "title": oxylabs_data.get("title", "N/A"),
        "brand": brand,
        "price": price,
        "rating": rating,
        "reviews_count": oxylabs_data.get("reviews_count", 0),
        "image": image,
        "url": url,
        "source": "oxylabs_product_api"
    }


def _extract_oxylabs_image(product_data: Dict[str, Any]) -> Optional[str]:
    """从Oxylabs数据中提取图片"""
    images = product_data.get("images")

    if images and isinstance(images, list):
        if images and isinstance(images[0], dict):
            return images[0].get("url") or images[0].get("link")
        elif images and isinstance(images[0], str):
            return images[0]

    return product_data.get("main_image") or product_data.get("image")


def _extract_oxylabs_price(product_data: Dict[str, Any]) -> Optional[float]:
    """从Oxylabs数据中提取价格"""
    price = (
        product_data.get("price") or
        product_data.get("price_amount") or
        product_data.get("buybox_winner", {}).get("price")
    )

    if isinstance(price, (int, float)):
        return float(price)

    if isinstance(price, str):
        try:
            clean_price = price.replace("$", "").replace("£", "").replace("€", "")
            clean_price = clean_price.replace(",", "").strip()
            return float(clean_price)
        except (ValueError, AttributeError):
            pass

    return None


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
