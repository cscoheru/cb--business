# api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User, PlanTier, PlanStatus
from models.subscription import Subscription
from schemas.user import UserCreate, UserLogin, UserResponse, Token
from utils.auth import verify_password, get_password_hash, create_access_token
from api.dependencies import get_db
from datetime import timedelta, datetime, timezone
from config.settings import settings
from config.subscriptions import get_trial_duration_days
import uuid

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册 - 新用户自动获得14天试用版

    试用期包含:
    - 完整的 Pro 功能
    - 14天后自动降级为 Free 版
    - 可随时升级到 Pro 版
    """
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 计算试用期结束时间
    trial_duration = get_trial_duration_days()
    trial_ends_at = datetime.now(timezone.utc) + timedelta(days=trial_duration)

    # 创建新用户（默认试用版）
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        plan_tier=PlanTier.TRIAL,
        plan_status=PlanStatus.ACTIVE,
        trial_ends_at=trial_ends_at
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 创建试用订阅记录
    trial_subscription = Subscription(
        id=uuid.uuid4(),
        user_id=new_user.id,
        plan_tier=PlanTier.TRIAL.value,
        status="active",
        billing_cycle=None,  # 试用期无计费周期
        amount=0,
        currency="CNY",
        started_at=datetime.now(timezone.utc),
        expires_at=trial_ends_at,
        auto_renew=False,
        payment_method=None
    )
    db.add(trial_subscription)
    await db.commit()

    # 生成访问令牌
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    # 查找用户
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )

    # 生成访问令牌（将UUID转换为字符串存储在JWT中）
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )
