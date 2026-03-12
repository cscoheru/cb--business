# api/products.py
"""产品 API - 提供产品数据"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from pydantic import BaseModel

from services.oxylabs_product_service import get_product_service, OxylabsProductService

router = APIRouter(prefix="/api/v1/products", tags=["products"])


class ProductResponse(BaseModel):
    """产品响应模型"""
    asin: str
    title: str
    brand: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    reviews_count: int = 0
    images: List[str] = []
    prime: bool = False
    url: str


class CategoryResponse(BaseModel):
    """类别响应模型"""
    id: str
    name: str
    emoji: str
    count: int


class PlatformResponse(BaseModel):
    """平台响应模型"""
    id: str
    name: str
    emoji: str
    countries: List[str]


@router.get("/trending")
async def get_trending_products(
    category: str = Query("electronics", description="产品类别"),
    limit: int = Query(10, description="返回数量", ge=1, le=50),
    force_refresh: bool = Query(False, description="强制刷新缓存")
):
    """
    获取热门产品列表

    支持的类别: electronics, beauty, home, fashion, food, baby, sports, pets
    """
    service = await get_product_service()

    # 不关闭客户端，保持服务实例活跃
    products = await service.get_trending_products(
        category=category,
        limit=limit,
        force_refresh=force_refresh
    )

    return {
        "category": category,
        "products": products,
        "count": len(products)
    }


@router.get("/categories")
async def get_categories():
    """获取产品类别列表"""
    service = await get_product_service()
    categories = await service.get_product_categories()
    return {"categories": categories}


@router.get("/platforms")
async def get_platforms():
    """获取支持的平台列表"""
    service = await get_product_service()
    platforms = await service.get_platforms()
    return {"platforms": platforms}


@router.get("/search")
async def search_products(
    query: str = Query(..., description="搜索关键词", min_length=2),
    category: str = Query("", description="产品类别"),
    limit: int = Query(5, description="返回数量", ge=1, le=20)
):
    """搜索产品"""
    service = await get_product_service()

    try:
        products = await service.search_products(
            query=query,
            category=category,
            limit=limit
        )

        return {
            "query": query,
            "category": category,
            "products": products,
            "count": len(products)
        }
    finally:
        await service.close()
