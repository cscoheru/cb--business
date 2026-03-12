# api/opportunities.py
"""产品机会分析 API"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
import logging

from analyzer.scoring import OpportunityScoringEngine, analyze_product_opportunity
from crawler.products.amazon_bestsellers import AmazonBestSellersCrawler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])


@router.post("/score")
async def score_product(
    product_data: Dict[str, Any],
    include_trends: bool = Query(False, description="是否包含 Google Trends 数据")
):
    """
    对单个产品进行机会评分

    请求体示例:
    {
        "title": "Product Name",
        "price": 29.99,
        "rating": 4.5,
        "reviews_count": 1234,
        "rank": 15,
        "sold_count": 500,
        "is_prime": true,
        "is_amazon_choice": false
    }
    """
    try:
        engine = OpportunityScoringEngine()
        score_result = engine.score_amazon_product(product_data)

        return {
            "success": True,
            "product_title": product_data.get("title", ""),
            "score": score_result.to_dict(),
        }

    except Exception as e:
        logger.error(f"评分失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/batch")
async def score_products_batch(
    products: List[Dict[str, Any]]
):
    """
    批量评分产品

    请求体示例:
    {
        "products": [
            {"title": "Product 1", "price": 29.99, ...},
            {"title": "Product 2", "price": 49.99, ...}
        ]
    }
    """
    try:
        engine = OpportunityScoringEngine()
        results = engine.batch_score_products(products)

        return {
            "success": True,
            "count": len(results),
            "products": results,
        }

    except Exception as e:
        logger.error(f"批量评分失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze")
async def analyze_market_opportunities(
    country: str = Query("us", description="国家代码"),
    category: str = Query(None, description="产品分类"),
    limit: int = Query(20, ge=1, le=100, description="分析产品数量")
):
    """
    分析市场机会

    综合 Amazon Best Sellers 和 AI 评分，发现高机会产品
    """
    try:
        # 1. 获取 Amazon Best Sellers
        async with AmazonBestSellersCrawler() as crawler:
            amazon_products = await crawler.fetch_bestsellers(
                country=country,
                category=category,
                max_products=limit
            )

        if not amazon_products:
            return {
                "success": False,
                "message": "未能获取产品数据",
                "opportunities": []
            }

        # 2. 批量评分
        engine = OpportunityScoringEngine()
        products_data = [p.to_dict() for p in amazon_products]
        scored_products = engine.batch_score_products(products_data)

        # 3. 筛选高机会产品 (分数 > 60)
        high_opportunities = [
            p for p in scored_products
            if p["opportunity_score"]["total_score"] > 60
        ]

        # 4. 生成报告
        report = {
            "success": True,
            "country": country.upper(),
            "category": category or "all",
            "analyzed_at": None,  # Will be set below
            "total_products_analyzed": len(scored_products),
            "high_opportunity_count": len(high_opportunities),
            "average_score": sum(p["opportunity_score"]["total_score"] for p in scored_products) / len(scored_products) if scored_products else 0,
            "top_opportunities": high_opportunities[:10],
        }

        return report

    except Exception as e:
        logger.error(f"市场机会分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def generate_opportunity_report(
    country: str = Query("us", description="国家代码"),
    min_score: float = Query(60, ge=0, le=100, description="最小机会评分")
):
    """
    生成产品机会报告

    返回详细的市场分析报告，包括:
    - 高机会产品列表
    - 评分分布统计
    - 关键洞察
    """
    try:
        # 获取并评分产品
        async with AmazonBestSellersCrawler() as crawler:
            products = await crawler.fetch_bestsellers(
                country=country,
                category="electronics",
                max_products=50
            )

        engine = OpportunityScoringEngine()
        products_data = [p.to_dict() for p in products]
        scored = engine.batch_score_products(products_data)

        # 筛选高机会产品
        opportunities = [p for p in scored if p["opportunity_score"]["total_score"] >= min_score]

        # 生成统计
        score_ranges = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "below_60": 0,
        }

        for product in scored:
            score = product["opportunity_score"]["total_score"]
            if score >= 90:
                score_ranges["90-100"] += 1
            elif score >= 80:
                score_ranges["80-89"] += 1
            elif score >= 70:
                score_ranges["70-79"] += 1
            elif score >= 60:
                score_ranges["60-69"] += 1
            else:
                score_ranges["below_60"] += 1

        # 提取关键洞察
        all_recommendations = []
        all_risk_factors = []

        for product in opportunities[:20]:
            all_recommendations.extend(product["opportunity_score"]["recommendations"])
            all_risk_factors.extend(product["opportunity_score"]["risk_factors"])

        # 统计最常见的建议和风险
        from collections import Counter
        top_recommendations = [r for r, _ in Counter(all_recommendations).most_common(5)]
        top_risks = [r for r, _ in Counter(all_risk_factors).most_common(5)]

        return {
            "success": True,
            "country": country.upper(),
            "min_score": min_score,
            "summary": {
                "total_analyzed": len(scored),
                "high_opportunities": len(opportunities),
                "score_distribution": score_ranges,
                "average_score": sum(p["opportunity_score"]["total_score"] for p in scored) / len(scored) if scored else 0,
            },
            "top_recommendations": top_recommendations,
            "top_risk_factors": top_risks,
            "opportunities": opportunities[:10],
        }

    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/distribution")
async def get_score_distribution(
    country: str = Query("us", description="国家代码")
):
    """获取评分分布统计"""
    try:
        async with AmazonBestSellersCrawler() as crawler:
            products = await crawler.fetch_bestsellers(
                country=country,
                category="electronics",
                max_products=50
            )

        engine = OpportunityScoringEngine()
        products_data = [p.to_dict() for p in products]
        scored = engine.batch_score_products(products_data)

        # 计算分布
        scores = [p["opportunity_score"]["total_score"] for p in scored]

        if not scores:
            return {
                "success": True,
                "message": "无产品数据",
                "distribution": {}
            }

        # 统计各维度平均值
        avg_demand = sum(p["opportunity_score"]["demand_score"] for p in scored) / len(scored)
        avg_competition = sum(p["opportunity_score"]["competition_score"] for p in scored) / len(scored)
        avg_profitability = sum(p["opportunity_score"]["profitability_score"] for p in scored) / len(scored)
        avg_trend = sum(p["opportunity_score"]["trend_score"] for p in scored) / len(scored)
        avg_quality = sum(p["opportunity_score"]["quality_score"] for p in scored) / len(scored)

        return {
            "success": True,
            "country": country.upper(),
            "total_products": len(scored),
            "average_scores": {
                "total": sum(scores) / len(scores),
                "demand": avg_demand,
                "competition": avg_competition,
                "profitability": avg_profitability,
                "trend": avg_trend,
                "quality": avg_quality,
            },
            "score_ranges": {
                "90-100": len([s for s in scores if s >= 90]),
                "80-89": len([s for s in scores if 80 <= s < 90]),
                "70-79": len([s for s in scores if 70 <= s < 80]),
                "60-69": len([s for s in scores if 60 <= s < 70]),
                "below_60": len([s for s in scores if s < 60]),
            },
        }

    except Exception as e:
        logger.error(f"获取评分分布失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
