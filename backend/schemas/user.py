# schemas/user.py
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Any, Optional
from models.user import PlanTier, PlanStatus
import uuid


class UserBase(BaseModel):
    """用户基础信息"""
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    region_preference: Optional[str] = None
    currency_preference: str = "CNY"


class Token(BaseModel):
    """认证令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserCreate(UserBase):
    """创建用户请求"""
    password: str


class UserCreateWithPlan(UserCreate):
    """创建用户请求（含计划选择）"""
    plan_choice: Optional[str] = "trial"  # 'free' or 'trial', default to trial


class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """用户响应"""
    id: str
    plan_tier: PlanTier
    plan_status: PlanStatus
    created_at: datetime
    last_login_at: Optional[datetime] = None

    @field_validator('id', mode='before')
    @classmethod
    def validate_id(cls, v: Any) -> str:
        """Convert UUID to string during validation"""
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True
