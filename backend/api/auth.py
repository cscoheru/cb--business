# api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User, PlanTier, PlanStatus
from models.subscription import Subscription
from schemas.user import UserCreate, UserCreateWithPlan, UserLogin, UserResponse, Token
from utils.auth import verify_password, get_password_hash, create_access_token
from api.dependencies import get_db
from datetime import timedelta, datetime, timezone
from config.settings import settings
from config.subscriptions import get_trial_duration_days
import uuid

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreateWithPlan,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册 - 支持选择计划类型

    plan_choice选项:
    - 'trial': 试用版（默认）- 14天完整功能体验
    - 'free': 免费版 - 基础功能永久使用

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

    # 获取计划选择（默认试用版）
    plan_choice = user_data.plan_choice or "trial"

    # 创建新用户
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        plan_tier=PlanTier.FREE,  # 初始为free，下面根据plan_choice调整
        plan_status=PlanStatus.ACTIVE,
        registration_plan_choice=plan_choice  # 记录用户注册时的选择
    )

    # 根据用户选择设置计划
    if plan_choice == "trial":
        # 先将用户添加到session，再由TrialManager更新并提交
        db.add(new_user)
        # 使用TrialManager创建试用用户
        from services.trial_manager import TrialManager
        trial_manager = TrialManager(db)
        new_user = await trial_manager.create_trial_subscription(new_user)
        # TrialManager已经commit了，所以不需要再次commit
    else:
        # 免费用户，无需订阅记录
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

    # 创建试用订阅记录（仅试用用户）
    if plan_choice == "trial":
        trial_subscription = Subscription(
            id=uuid.uuid4(),
            user_id=new_user.id,
            plan_tier=PlanTier.TRIAL.value,
            status="active",
            billing_cycle=None,  # 试用期无计费周期
            amount=0,
            currency="CNY",
            started_at=datetime.now(timezone.utc),
            expires_at=new_user.trial_ends_at,
            auto_renew=False,
            payment_method=None
        )
        db.add(trial_subscription)
        await db.commit()
        await db.refresh(new_user)

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
