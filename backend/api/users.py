# api/users.py
from fastapi import APIRouter, Depends
from models.user import User
from schemas.user import UserResponse
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)
