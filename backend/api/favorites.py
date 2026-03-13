# api/favorites.py
"""用户收藏 API"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from models.user import User
from models.favorite import Favorite
from models.card import Card
from api.dependencies import get_db, get_current_user
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/v1/favorites", tags=["favorites"])


# Schemas
class FavoriteCreate(BaseModel):
    """创建收藏请求"""
    card_id: str


class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: str
    user_id: str
    card_id: str
    created_at: str

    class Config:
        from_attributes = True


class CardFavoriteResponse(BaseModel):
    """带卡片信息的收藏响应"""
    id: str
    card_id: str
    created_at: str
    card: dict


@router.get("", response_model=List[CardFavoriteResponse])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的收藏列表

    返回用户收藏的所有卡片，按收藏时间倒序排列
    """
    result = await db.execute(
        select(Favorite, Card)
        .join(Card, Favorite.card_id == Card.id)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )

    favorites = []
    for favorite, card in result.all():
        favorites.append({
            "id": str(favorite.id),
            "card_id": str(favorite.card_id),
            "created_at": favorite.created_at.isoformat(),
            "card": card.to_dict()
        })

    return favorites


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    添加收藏

    如果用户已经收藏过该卡片，返回已存在的收藏记录
    """
    # 验证卡片是否存在
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
        # 已存在，返回现有记录
        return FavoriteResponse(
            id=str(existing_favorite.id),
            user_id=str(existing_favorite.user_id),
            card_id=str(existing_favorite.card_id),
            created_at=existing_favorite.created_at.isoformat()
        )

    # 创建新收藏
    new_favorite = Favorite(
        user_id=current_user.id,
        card_id=card_id
    )

    db.add(new_favorite)
    await db.commit()
    await db.refresh(new_favorite)

    return FavoriteResponse(
        id=str(new_favorite.id),
        user_id=str(new_favorite.user_id),
        card_id=str(new_favorite.card_id),
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
