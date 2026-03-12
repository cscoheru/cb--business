# api/social.py
"""社交媒体趋势 API"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
import logging

from crawler.social.reddit_trends import RedditTrendsMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/social", tags=["social"])


@router.get("/reddit/hot")
async def get_reddit_hot_posts(
    subreddit: str = Query("dropshipping", description="Subreddit 名称"),
    limit: int = Query(25, ge=1, le=100, description="返回数量")
):
    """获取 Reddit 热门帖子"""
    monitor = RedditTrendsMonitor()

    try:
        posts = await monitor.get_hot_posts(subreddit, limit)

        return {
            "success": True,
            "subreddit": subreddit,
            "count": len(posts),
            "posts": [p.to_dict() for p in posts],
        }

    except Exception as e:
        logger.error(f"获取 Reddit 热门帖子失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await monitor.close()


@router.get("/reddit/opportunities")
async def find_reddit_opportunities(
    min_score: float = Query(40, ge=0, le=100, description="最小机会评分"),
    min_engagement: int = Query(50, ge=0, description="最小互动量")
):
    """
    发现 Reddit 上的电商机会

    监控多个电商相关 Subreddit，发现：
    - 产品趋势
    - 市场需求
    - 痛点问题
    """
    monitor = RedditTrendsMonitor()

    try:
        opportunities = await monitor.find_opportunities(
            min_score=min_score,
            min_engagement=min_engagement
        )

        return {
            "success": True,
            "count": len(opportunities),
            "opportunities": opportunities,
        }

    except Exception as e:
        logger.error(f"发现机会失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await monitor.close()


@router.get("/reddit/subreddits")
async def get_monitored_subreddits():
    """获取监控的 Subreddit 列表"""
    return {
        "subreddits": [
            {"name": "dropshipping", "description": "Dropshipping 业务讨论"},
            {"name": "entrepreneur", "description": "创业者社区"},
            {"name": "FulfillmentByAmazon", "description": "Amazon FBA 卖家"},
            {"name": "juststart", "description": "新手创业者"},
            {"name": "ecommerce", "description": "电商综合讨论"},
            {"name": "AmazonFBA", "description": "Amazon FBA 专门讨论"},
            {"name": "OnlineBusiness", "description": "在线业务"},
        ]
    }


@router.get("/trends")
async def get_social_trends(
    platform: str = Query("reddit", description="平台: reddit"),
    limit: int = Query(20, ge=1, le=50, description="返回数量")
):
    """
    获取社交媒体电商趋势

    综合多个 Subreddit 和关键词，发现当前热门趋势
    """
    if platform == "reddit":
        return await get_reddit_opportunities(min_score=30, min_engagement=50)
    else:
        return {
            "success": False,
            "message": f"平台 '{platform}' 尚未支持",
            "trends": []
        }
