# api/unified_favorites.py
"""统一收藏 API - 支持Card和Opportunity的跨系统收藏"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Literal
from pydantic import BaseModel
import uuid

from config.database import AsyncSessionLocal, get_db
from models.user import User
from models.favorite import Favorite
from models.card import Card
from models.business_opportunity import BusinessOpportunity
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/favorites", tags=["favorites"])


class UnifiedFavoriteRequest(BaseModel):
    """统一收藏请求"""
    item_type: Literal['card', 'opportunity']  # 收藏类型
    item_id: str  # 项目ID


class UnifiedFavoriteResponse(BaseModel):
    """统一收藏响应"""
    success: bool
    item_type: str
    item_id: str
    is_favorite: bool
    message: str


@router.post("/toggle")
async def toggle_unified_favorite(
    request: UnifiedFavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    统一收藏切换API

    支持Card和Opportunity的收藏，自动检测当前状态并切换
    """
    try:
        item_uuid = uuid.UUID(request.item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的ID格式")

    if request.item_type == 'card':
        # 检查Card是否存在
        card = await db.get(Card, item_uuid)
        if not card:
            raise HTTPException(status_code=404, detail="卡片不存在")

        # 检查是否已收藏
        existing = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.card_id == item_uuid
            )
        )
        favorite = existing.scalar_one_or_none()

        if favorite:
            # 取消收藏
            await db.delete(favorite)
            await db.commit()
            return UnifiedFavoriteResponse(
                success=True,
                item_type='card',
                item_id=request.item_id,
                is_favorite=False,
                message='已取消收藏'
            )
        else:
            # 添加收藏
            new_favorite = Favorite(
                user_id=current_user.id,
                card_id=item_uuid
            )
            db.add(new_favorite)
            await db.commit()
            return UnifiedFavoriteResponse(
                success=True,
                item_type='card',
                item_id=request.item_id,
                is_favorite=True,
                message='已添加收藏'
            )

    elif request.item_type == 'opportunity':
        # 检查Opportunity是否存在
        opportunity = await db.get(BusinessOpportunity, item_uuid)
        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")

        # 使用user_interactions字段保存收藏状态
        if not opportunity.user_interactions:
            opportunity.user_interactions = {}

        is_saved = opportunity.user_interactions.get('saved', False)

        if is_saved:
            # 取消收藏
            opportunity.user_interactions['saved'] = False
            message = '已取消收藏'
            is_favorite = False
        else:
            # 添加收藏
            opportunity.user_interactions['saved'] = True
            opportunity.user_interactions['saved_at'] = func.now()
            message = '已添加收藏'
            is_favorite = True

        await db.commit()

        return UnifiedFavoriteResponse(
            success=True,
            item_type='opportunity',
            item_id=request.item_id,
            is_favorite=is_favorite,
            message=message
        )

    else:
        raise HTTPException(status_code=400, detail="无效的收藏类型")


@router.get("/count")
async def get_favorites_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取用户总收藏数（Card + Opportunity）

    返回统一的收藏计数，用于顶部导航栏显示
    """
    # Card收藏数
    card_count_result = await db.execute(
        select(func.count(Favorite.id)).where(
            Favorite.user_id == current_user.id,
            Favorite.card_id.isnot(None)
        )
    )
    card_count = card_count_result.scalar() or 0

    # Opportunity收藏数（从user_interactions中统计）
    opp_count_result = await db.execute(
        select(func.count(BusinessOpportunity.id)).where(
            BusinessOpportunity.user_id == current_user.id,
            BusinessOpportunity.user_interactions['saved'].astext == 'true'
        )
    )
    opp_count = opp_count_result.scalar() or 0

    total_count = card_count + opp_count

    return {
        'success': True,
        'count': total_count,
        'card_count': card_count,
        'opportunity_count': opp_count
    }


@router.get("/check/{item_type}/{item_id}")
async def check_unified_favorite(
    item_type: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    检查项目是否已收藏

    支持Card和Opportunity两种类型
    """
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的ID格式")

    if item_type == 'card':
        result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.card_id == item_uuid
            )
        )
        favorite = result.scalar_one_or_none()

        return {
            'is_favorite': favorite is not None,
            'favorite_id': str(favorite.id) if favorite else None
        }

    elif item_type == 'opportunity':
        opportunity = await db.get(BusinessOpportunity, item_uuid)
        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")

        is_saved = opportunity.user_interactions.get('saved', False) if opportunity.user_interactions else False

        return {
            'is_favorite': is_saved,
            'favorite_id': None  # Opportunity不使用单独的favorite表
        }

    else:
        raise HTTPException(status_code=400, detail="无效的收藏类型")


@router.get("")
async def get_all_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取所有收藏（Card + Opportunity）

    返回统一的收藏列表
    """
    favorites = {
        'cards': [],
        'opportunities': []
    }

    # 获取Card收藏
    card_result = await db.execute(
        select(Favorite, Card)
        .join(Card, Favorite.card_id == Card.id)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )

    for favorite, card in card_result.all():
        favorites['cards'].append({
            'type': 'card',
            'id': str(card.id),
            'title': card.title,
            'category': card.category,
            'created_at': favorite.created_at.isoformat(),
            'data': card.to_dict()
        })

    # 获取Opportunity收藏
    from sqlalchemy import cast
    opp_result = await db.execute(
        select(BusinessOpportunity)
        .where(
            BusinessOpportunity.user_id == current_user.id,
            cast(BusinessOpportunity.user_interactions['saved'], type(None)) == True  # JSONB查询
        )
        .order_by(BusinessOpportunity.updated_at.desc())
    )

    for opp in opp_result.scalars().all():
        favorites['opportunities'].append({
            'type': 'opportunity',
            'id': str(opp.id),
            'title': opp.title,
            'status': opp.status.value if hasattr(opp.status, 'value') else opp.status,
            'opportunity_type': opp.opportunity_type.value if hasattr(opp.opportunity_type, 'value') else opp.opportunity_type,
            'confidence_score': opp.confidence_score,
            'created_at': opp.created_at.isoformat(),
            'data': opp.to_dict_include_related()
        })

    return {
        'success': True,
        'total_count': len(favorites['cards']) + len(favorites['opportunities']),
        'favorites': favorites
    }
