# api/favorites.py
"""用户收藏 API - 支持卡片和机会的收藏"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_
from typing import List, Optional, Union, Dict, Any
from models.user import User
from models.favorite import Favorite
from models.card import Card
from models.business_opportunity import BusinessOpportunity
from api.dependencies import get_db, get_current_user
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/v1/favorites", tags=["favorites"])


# Schemas
class FavoriteCreate(BaseModel):
    """创建收藏请求 - 支持卡片或机会"""
    card_id: Optional[str] = None
    opportunity_id: Optional[str] = None


class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: str
    user_id: str
    card_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class CardFavoriteResponse(BaseModel):
    """带卡片信息的收藏响应"""
    id: str
    card_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    created_at: str
    card: Optional[dict] = None
    opportunity: Optional[dict] = None


@router.get("", response_model=List[CardFavoriteResponse])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的收藏列表

    返回用户收藏的所有卡片和机会，按收藏时间倒序排列
    """
    # 获取所有收藏记录
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    favorites = result.scalars().all()

    favorites_data = []
    for favorite in favorites:
        item_data = {
            "id": str(favorite.id),
            "card_id": str(favorite.card_id) if favorite.card_id else None,
            "opportunity_id": str(favorite.opportunity_id) if favorite.opportunity_id else None,
            "created_at": favorite.created_at.isoformat(),
        }

        # 如果是卡片收藏，加载卡片数据
        if favorite.card_id:
            card = await db.get(Card, favorite.card_id)
            if card:
                item_data["card"] = card.to_dict()

        # 如果是机会收藏，加载机会数据
        elif favorite.opportunity_id:
            opportunity = await db.get(BusinessOpportunity, favorite.opportunity_id)
            if opportunity:
                item_data["opportunity"] = opportunity.to_dict()

        favorites_data.append(item_data)

    return favorites_data


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    添加收藏 - 支持卡片或机会

    如果用户已经收藏过该卡片/机会，返回已存在的收藏记录
    """
    # 验证至少提供了一个目标
    if not favorite_data.card_id and not favorite_data.opportunity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供 card_id 或 opportunity_id"
        )

    # 同时提供则报错
    if favorite_data.card_id and favorite_data.opportunity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能同时提供 card_id 和 opportunity_id"
        )

    # 处理卡片收藏
    if favorite_data.card_id:
        try:
            card_id = uuid.UUID(favorite_data.card_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的卡片ID格式"
            )

        card = await db.get(Card, card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="卡片不存在"
            )

        # 检查是否已经收藏
        existing_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.card_id == card_id
            )
        )
        existing_favorite = existing_result.scalar_one_or_none()

        if existing_favorite:
            return FavoriteResponse(
                id=str(existing_favorite.id),
                user_id=str(existing_favorite.user_id),
                card_id=str(existing_favorite.card_id),
                opportunity_id=None,
                created_at=existing_favorite.created_at.isoformat()
            )

        # 创建新收藏
        new_favorite = Favorite(
            user_id=current_user.id,
            card_id=card_id,
            opportunity_id=None
        )

    # 处理机会收藏
    else:
        try:
            opportunity_id = uuid.UUID(favorite_data.opportunity_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的机会ID格式"
            )

        opportunity = await db.get(BusinessOpportunity, opportunity_id)
        if not opportunity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="商机不存在"
            )

        # 检查是否已经收藏
        existing_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.opportunity_id == opportunity_id
            )
        )
        existing_favorite = existing_result.scalar_one_or_none()

        if existing_favorite:
            return FavoriteResponse(
                id=str(existing_favorite.id),
                user_id=str(existing_favorite.user_id),
                card_id=None,
                opportunity_id=str(existing_favorite.opportunity_id),
                created_at=existing_favorite.created_at.isoformat()
            )

        # 创建新收藏
        new_favorite = Favorite(
            user_id=current_user.id,
            card_id=None,
            opportunity_id=opportunity_id
        )

    db.add(new_favorite)
    await db.commit()
    await db.refresh(new_favorite)

    return FavoriteResponse(
        id=str(new_favorite.id),
        user_id=str(new_favorite.user_id),
        card_id=str(new_favorite.card_id) if new_favorite.card_id else None,
        opportunity_id=str(new_favorite.opportunity_id) if new_favorite.opportunity_id else None,
        created_at=new_favorite.created_at.isoformat()
    )


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(
    favorite_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除收藏

    只能删除自己的收藏
    """
    try:
        fav_id = uuid.UUID(favorite_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的收藏ID格式"
        )

    # 查找收藏记录
    result = await db.execute(
        select(Favorite).where(
            Favorite.id == fav_id,
            Favorite.user_id == current_user.id
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏记录不存在或无权删除"
        )

    await db.execute(
        delete(Favorite).where(Favorite.id == fav_id)
    )
    await db.commit()

    return None


@router.delete("/card/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite_by_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    通过卡片ID删除收藏

    提供更便捷的删除方式，前端只需知道card_id即可取消收藏
    """
    try:
        card_uuid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的卡片ID格式"
        )

    # 执行删除
    result = await db.execute(
        delete(Favorite).where(
            Favorite.card_id == card_uuid,
            Favorite.user_id == current_user.id
        )
    )

    await db.commit()

    # 如果没有删除任何记录，返回404
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏记录不存在"
        )

    return None


@router.get("/check/{card_id}")
async def check_favorite(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    检查是否已收藏某张卡片

    返回是否已收藏的布尔值
    """
    try:
        card_uuid = uuid.UUID(card_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的卡片ID格式"
        )

    result = await db.execute(
        select(Favorite).where(
            Favorite.card_id == card_uuid,
            Favorite.user_id == current_user.id
        )
    )
    favorite = result.scalar_one_or_none()

    return {
        "is_favorite": favorite is not None,
        "favorite_id": str(favorite.id) if favorite else None
    }


@router.delete("/opportunity/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite_by_opportunity(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    通过机会ID删除收藏

    提供更便捷的删除方式，前端只需知道opportunity_id即可取消收藏
    """
    try:
        opportunity_uuid = uuid.UUID(opportunity_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的机会ID格式"
        )

    # 执行删除
    result = await db.execute(
        delete(Favorite).where(
            Favorite.opportunity_id == opportunity_uuid,
            Favorite.user_id == current_user.id
        )
    )

    await db.commit()

    # 如果没有删除任何记录，返回404
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏记录不存在"
        )

    return None


@router.get("/check/opportunity/{opportunity_id}")
async def check_opportunity_favorite(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    检查是否已收藏某个机会

    返回是否已收藏的布尔值
    """
    try:
        opportunity_uuid = uuid.UUID(opportunity_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的机会ID格式"
        )

    result = await db.execute(
        select(Favorite).where(
            Favorite.opportunity_id == opportunity_uuid,
            Favorite.user_id == current_user.id
        )
    )
    favorite = result.scalar_one_or_none()

    return {
        "is_favorite": favorite is not None,
        "favorite_id": str(favorite.id) if favorite else None
    }
