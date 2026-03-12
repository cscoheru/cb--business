# api/trends.py
"""趋势分析 API"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import logging

from crawler.trends.google_trends import (
    GoogleTrendsClient,
    AITrendAnalyzer,
    TrendTopic,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trends", tags=["trends"])


@router.get("/realtime")
async def get_realtime_trends(
    country: str = Query("us", description="国家代码: us, th, vn, my, sg, id, ph, br, mx"),
    category: str = Query("all", description="分类: all, shopping, electronics, fashion, home, beauty"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
):
    """
    获取 Google 实时搜索趋势

    返回当前热门搜索关键词和趋势数据
    """
    client = GoogleTrendsClient()

    try:
        topics = await client.get_realtime_trends(
            country=country,
            category=category,
            max_results=limit
        )

        return {
            "country": country.upper(),
            "category": category,
            "count": len(topics),
            "trends": [t.to_dict() for t in topics],
        }

    except Exception as e:
        logger.error(f"获取实时趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.close()


@router.get("/analyze")
async def analyze_trends(
    country: str = Query("us", description="国家代码"),
    category: str = Query("all", description="分类"),
    min_score: float = Query(60, ge=0, le=100, description="最小机会评分"),
):
    """
    分析趋势并发现产品机会

    使用 AI 分析实时趋势，计算机会评分，生成产品建议
    """
    analyzer = AITrendAnalyzer()

    try:
        report = await analyzer.discover_product_opportunities(
            country=country,
            category=category,
            min_score=min_score
        )

        return report

    except Exception as e:
        logger.error(f"趋势分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/{keyword}")
async def get_topic_details(
    keyword: str,
    country: str = Query("us", description="国家代码"),
):
    """
    获取关键词的详细趋势数据

    包括相关主题、搜索兴趣随时间变化等
    """
    client = GoogleTrendsClient()
    analyzer = AITrendAnalyzer()

    try:
        # 获取相关主题
        related = await client.get_related_topics(keyword, country)

        # 创建基础主题对象
        topic = TrendTopic(
            title=keyword,
            volume=0,
            traffic=0,
            related_queries=[],
            timestamp=None,  # type: ignore
        )

        # AI 分析
        analyzed = await analyzer.analyze_topic(topic)

        return {
            "keyword": keyword,
            "country": country.upper(),
            "analysis": analyzed.to_dict(),
            "related_topics": related,
        }

    except Exception as e:
        logger.error(f"获取关键词详情失败 ({keyword}): {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.close()


@router.get("/countries")
async def get_supported_countries():
    """获取支持的国家列表"""
    return {
        "countries": [
            {"code": "us", "name": "United States", "flag": "🇺🇸"},
            {"code": "th", "name": "Thailand", "flag": "🇹🇭"},
            {"code": "vn", "name": "Vietnam", "flag": "🇻🇳"},
            {"code": "my", "name": "Malaysia", "flag": "🇲🇾"},
            {"code": "sg", "name": "Singapore", "flag": "🇸🇬"},
            {"code": "id", "name": "Indonesia", "flag": "🇮🇩"},
            {"code": "ph", "name": "Philippines", "flag": "🇵🇭"},
            {"code": "br", "name": "Brazil", "flag": "🇧🇷"},
            {"code": "mx", "name": "Mexico", "flag": "🇲x️"},
        ]
    }


@router.get("/categories")
async def get_supported_categories():
    """获取支持的分类列表"""
    return {
        "categories": [
            {"code": "all", "name": "All Categories", "icon": "📊"},
            {"code": "shopping", "name": "Shopping", "icon": "🛒"},
            {"code": "electronics", "name": "Electronics", "icon": "📱"},
            {"code": "fashion", "name": "Fashion", "icon": "👗"},
            {"code": "home", "name": "Home & Garden", "icon": "🏠"},
            {"code": "beauty", "name": "Beauty", "icon": "💄"},
            {"code": "toys", "name": "Toys & Games", "icon": "🎮"},
            {"code": "sports", "name": "Sports", "icon": "⚽"},
        ]
    }


@router.get("/opportunities")
async def get_product_opportunities(
    country: str = Query("us", description="国家代码"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
):
    """
    获取高评分产品机会

    综合分析后的高机会产品推荐
    """
    analyzer = AITrendAnalyzer()

    try:
        report = await analyzer.discover_product_opportunities(
            country=country,
            category="all",
            min_score=50  # 降低阈值以获取更多结果
        )

        # 按评分排序，返回前 N 个
        opportunities = sorted(
            report['opportunities'],
            key=lambda x: x.get('opportunity_score', 0),
            reverse=True
        )[:limit]

        return {
            "country": country.upper(),
            "generated_at": report['generated_at'],
            "opportunities": opportunities,
        }

    except Exception as e:
        logger.error(f"获取产品机会失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
