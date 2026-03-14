# api/opportunities.py - TEMPORARY VERSION
"""产品机会分析 API - 维护模式"""

from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])

# TEMPORARY: Return maintenance message for all endpoints
@router.get("/funnel")
async def get_opportunity_funnel():
    """获取商机漏斗数据 - 维护模式"""
    return {
        "success": True,
        "funnel": {
            "potential": {"count": 0, "avg_confidence": 0},
            "verifying": {"count": 0, "avg_confidence": 0},
            "assessing": {"count": 0, "avg_confidence": 0},
            "executing": {"count": 0, "avg_confidence": 0},
        },
        "total": 0,
        "message": "智能商机跟踪功能正在维护中，请稍后再试。您可以先查看商机卡片功能。"
    }

@router.get("")
async def list_opportunities(
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(20)
):
    """获取商机列表 - 维护模式"""
    return {
        "success": True,
        "opportunities": [],
        "total": 0,
        "skip": skip,
        "limit": limit,
        "message": "智能商机跟踪功能正在维护中，请稍后再试。您可以先查看商机卡片功能。"
    }

@router.get("/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    """获取商机详情 - 维护模式"""
    return {
        "success": False,
        "message": "智能商机跟踪功能正在维护中，请稍后再试。"
    }
