# api/cards.py
"""信息卡片 API"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from sqlalchemy import select, desc
from config.database import AsyncSessionLocal, get_db
from models.card import Card

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])


@router.get("/daily")
async def get_daily_cards(
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD), 默认今天（按需生成）"),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取每日3张信息卡片（按需生成模式）

    新模式：用户每次访问都会看到最新的数据
    - 30分钟内：返回缓存的卡片（快速）
    - 30分钟后：自动重新生成新卡片
    - Oxylabs API失败时：返回最新的可用卡片

    Args:
        date: 日期，不传则按需生成最新

    Returns:
        最新的3张卡片
    """
    try:
        # 如果指定了历史日期，从数据库查询
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
                start_of_day = target_date.replace(hour=0, minute=0, second=0)
                end_of_day = target_date.replace(hour=23, minute=59, second=59)

                result = await db.execute(
                    select(Card)
                    .where(Card.created_at >= start_of_day)
                    .where(Card.created_at <= end_of_day)
                    .where(Card.is_published == True)
                    .order_by(Card.created_at)
                )
                cards = result.scalars().all()

                return {
                    "success": True,
                    "date": date,
                    "count": len(cards),
                    "cards": [card.to_dict() for card in cards],
                    "mode": "历史数据"
                }

            except ValueError:
                raise HTTPException(status_code=400, detail="无效的日期格式，请使用 YYYY-MM-DD")

        # 按需生成模式：获取最新卡片
        from services.card_generator import get_cards_for_user

        result = await get_cards_for_user()

        return {
            "success": True,
            "count": result["count"],
            "cards": result["cards"],
            "mode": "实时生成",
            "cache_info": result.get("cache_info", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取每日卡片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_cards(
    limit: int = Query(3, ge=1, le=10, description="返回数量"),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取最新的N张卡片

    Args:
        limit: 返回数量，默认3张

    Returns:
        最新的卡片列表
    """
    try:
        result = await db.execute(
            select(Card)
            .where(Card.is_published == True)
            .order_by(desc(Card.created_at))
            .limit(limit)
        )

        cards = result.scalars().all()

        return {
            "success": True,
            "count": len(cards),
            "cards": [card.to_dict() for card in cards]
        }

    except Exception as e:
        logger.error(f"获取最新卡片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{card_id}")
async def get_card(
    card_id: str,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取单张卡片详情

    Args:
        card_id: 卡片ID

    Returns:
        卡片详情，并增加浏览次数
    """
    try:
        result = await db.execute(
            select(Card).where(Card.id == card_id)
        )

        card = result.scalar_one_or_none()

        if not card:
            raise HTTPException(status_code=404, detail="卡片不存在")

        # 增加浏览次数
        card.views += 1
        await db.commit()

        return {
            "success": True,
            "card": card.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取卡片详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{card_id}/like")
async def like_card(
    card_id: str,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    收藏/取消收藏卡片

    Args:
        card_id: 卡片ID

    Returns:
        更新后的收藏状态
    """
    try:
        result = await db.execute(
            select(Card).where(Card.id == card_id)
        )

        card = result.scalar_one_or_none()

        if not card:
            raise HTTPException(status_code=404, detail="卡片不存在")

        # 切换收藏状态
        card.likes += 1

        await db.commit()

        return {
            "success": True,
            "card_id": card_id,
            "likes": card.likes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"收藏卡片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_card_history(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    category: Optional[str] = Query(None, description="品类筛选"),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取历史卡片列表

    Args:
        skip: 跳过数量
        limit: 返回数量
        category: 品类筛选

    Returns:
        历史卡片列表
    """
    try:
        query = select(Card).where(Card.is_published == True)

        # 品类筛选
        if category:
            query = query.where(Card.category == category)

        # 排序和分页
        query = query.order_by(desc(Card.created_at))

        result = await db.execute(
            query.offset(skip).limit(limit)
        )

        cards = result.scalars().all()

        # 获取总数
        count_result = await db.execute(
            select(Card.id).where(Card.is_published == True)
        )
        total = len(count_result.all())

        return {
            "success": True,
            "total": total,
            "skip": skip,
            "limit": limit,
            "cards": [card.to_dict() for card in cards]
        }

    except Exception as e:
        logger.error(f"获取历史卡片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview")
async def get_cards_overview(
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取卡片统计概览

    Returns:
        统计数据
    """
    try:
        # 总卡片数
        total_result = await db.execute(
            select(Card.id)
        )
        total = len(total_result.all())

        # 已发布卡片数
        published_result = await db.execute(
            select(Card.id).where(Card.is_published == True)
        )
        published = len(published_result.all())

        # 今日卡片数
        today = datetime.now().replace(hour=0, minute=0, second=0)
        today_result = await db.execute(
            select(Card.id)
            .where(Card.created_at >= today)
            .where(Card.is_published == True)
        )
        today_count = len(today_result.all())

        # 各品类统计
        category_stats = {}
        for cat_key in ['wireless_earbuds', 'smart_plugs', 'fitness_trackers']:
            cat_result = await db.execute(
                select(Card.id)
                .where(Card.category == cat_key)
                .where(Card.is_published == True)
            )
            category_stats[cat_key] = len(cat_result.all())

        # 总浏览量和收藏数
        stats_result = await db.execute(
            select(Card)
        )
        all_cards = stats_result.scalars().all()

        total_views = sum(card.views for card in all_cards)
        total_likes = sum(card.likes for card in all_cards)

        return {
            "success": True,
            "overview": {
                "total_cards": total,
                "published_cards": published,
                "today_cards": today_count,
                "total_views": total_views,
                "total_likes": total_likes,
                "category_breakdown": category_stats
            }
        }

    except Exception as e:
        logger.error(f"获取统计概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
