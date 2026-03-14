# 会员升级系统实施计划

**创建时间**: 2026-03-14
**版本**: 1.0
**状态**: 待实施

---

## 目录
1. [上下文与背景](#上下文与背景)
2. [问题定义](#问题定义)
3. [设计决策](#设计决策)
4. [系统架构](#系统架构)
5. [实施计划](#实施计划)
6. [测试方案](#测试方案)
7. [风险评估](#风险评估)
8. [成功指标](#成功指标)

---

## 上下文与背景

### 产品定位

**ZenConsult** 是一个面向跨境电商商机的AI驱动SaaS平台，核心价值在于：

1. **智能商机发现** - 通过AI分析市场数据，自动发现有潜力的商业机会
2. **商机生命周期管理** - 支持商机从发现到执行的5阶段流转
3. **数据驱动的决策支持** - 提供产品、市场、政策等多维度数据分析

### 当前用户规模

- **注册用户**: 少于100人（早期阶段）
- **日活跃用户**: 待统计
- **付费转化率**: 待统计

### 商业目标

1. **短期目标**（1-3个月）：
   - 建立清晰的用户分层体系
   - 优化免费到付费的转化路径
   - 提高用户注册转化率

2. **中期目标**（3-6个月）：
   - 实现月付费用户 > 50人
   - 免费用户到试用用户转化率 > 20%
   - 试用用户到付费用户转化率 > 30%

3. **长期目标**（6-12个月）：
   - 建立可持续的订阅收入模式
   - 用户LTV（生命周期价值） > CAC（获客成本）
   - 月度经常性收入（MRR） > ¥50,000

---

## 问题定义

### 当前痛点

#### 1. 用户分层不清晰

**现状问题**：
```
未注册用户 → 注册（自动试用14天） → 试用结束 → ？
```

**核心矛盾**：
- 免费版和试用版的获取门槛相同（都无需支付）
- 试用版只是"免费版plus"，没有明确的升级动机
- 用户混淆：既可以是免费用户，也可以是试用用户，为什么选择其中一个？

#### 2. 转化路径模糊

**问题表现**：
- 未登录用户 → 注册 → 自动试用 → 试用结束 → 降级免费 → ？
- 缺少主动引导升级的机制
- 没有创造"损失厌恶"心理的机制

#### 3. 权限控制缺失

**技术问题**：
- 未登录用户可以查看所有内容（没有差异化体验）
- 免费用户和试用用户的权限边界不清晰
- 商机阶段的权限控制未实现

### 用户需求分析

#### 未注册用户

**需求**：
- 了解产品价值
- 评估是否值得注册
- 低门槛探索

**期望体验**：
- 可以浏览公开内容（卡片、资讯）
- 看到"升级可以获得什么"的提示
- 收藏感兴趣的卡片（引导注册）

#### 免费用户

**需求**：
- 体验基础功能
- 了解高级功能价值
- 决定是否升级

**期望体验**：
- 功能受限但不至于无法使用
- 清晰的升级提示
- 看到"升级后可以做什么"的对比

#### 试用用户

**需求**：
- 完整体验产品价值
- 验证产品是否解决业务问题
- 决定是否付费

**期望体验**：
- 无功能限制
- 每日提醒剩余天数
- 平滑的试用到期过渡

#### Pro用户

**需求**：
- 持续获得价值
- 稳定的服务体验
- 增值服务

**期望体验**：
- 完整功能无限制
- 优先支持
- 新功能优先体验

---

## 设计决策

### 决策记录

#### 决策1: 转化门槛设计

**选项对比**：

| 方案 | 优点 | 缺点 | 转化率预期 |
|------|------|------|-----------|
| A. 支付1元获试用 | 筛选高意向用户 | 转化漏斗长，可能降低整体注册率 | 1-3% |
| **B. 免费试用+支付验证** | 平衡筛选和转化 | 需要在付费时验证支付方式 | **5-10%** |
| C. 企业邮箱验证 | 无支付门槛，筛选B2B用户 | 可能错过个人创业者 | 3-5% |

**最终选择**: **方案B - 免费试用+支付验证**

**理由**：
1. 降低注册门槛，提高整体转化率
2. 在关键付费节点验证支付方式
3. 平衡用户规模和质量

#### 决策2: 试用紧迫感机制

**选项对比**：

| 方案 | 优点 | 缺点 | 用户体验 |
|------|------|------|---------|
| A. 虚拟货币扣款 | 创造损失厌恶 | 技术复杂，法律风险 | 复杂 |
| **B. 每日提醒** | 简单直接，保留紧迫感 | 缺少金钱损失感 | **良好** |
| C. 阶梯式功能减少 | 动态调整体验 | 可能引起用户不满 | 中等 |

**最终选择**: **方案B - 每日提醒**

**理由**：
1. 技术实现简单
2. 无法律合规风险
3. 清晰传达时间紧迫性

#### 决策3: 试用性能控制

**选项对比**：

| 方案 | 优点 | 缺点 | 技术复杂度 |
|------|------|------|-----------|
| A. 服务端延迟 | 实现简单 | 影响用户体验，可能被识别 | 低 |
| B. 功能限速 | 不影响单次体验 | 限制连续操作 | 中 |
| **C. 不限速** | 用户体验最好 | 无性能差异的试用限制 | **低** |

**最终选择**: **方案C - 不限速**

**理由**：
1. 试用期应提供最佳体验，创造价值依赖
2. 通过时间限制而非性能限制创造升级动力
3. 简化技术实现

### 用户分层设计

基于以上决策，最终用户分层设计如下：

| 用户类型 | 获取方式 | 核心权益 | 主要限制 | 转化目标 |
|---------|---------|---------|---------|---------|
| **未注册用户** | 访问网站 | 浏览公开内容、临时收藏 | 无法查看详情、只能看商机第一阶段 | 引导注册 |
| **免费用户** | 注册时选择免费版 | 基础功能、查看商机第一阶段 | API调用限制、卡片浏览限制 | 升级到试用 |
| **试用用户** | 注册时选择试用版 | Pro完整功能14天 | 14天时间限制、每日提醒 | 升级到Pro |
| **Pro用户** | 支付订阅 | 完整功能无限使用 | 无 | 长期留存 |

### 权限矩阵

```yaml
卡片浏览:
  未注册: 可浏览列表，不可查看详情
  免费: 可查看详情（每日限额）
  试用: 无限制
  Pro: 无限制

收藏功能:
  未注册: 本地临时存储（清除后丢失）
  免费: 云端存储
  试用: 云端存储
  Pro: 云端存储

商机管理:
  未注册: 只能查看第一阶段（发现期）
  免费: 可以查看第一阶段，但不能管理
  试用: 完整管理（5阶段流转）
  Pro: 完整管理

API调用:
  未注册: N/A（未登录）
  免费: 10次/天
  试用: 无限制
  Pro: 无限制

AI分析:
  未注册: 不可用
  免费: 不可用
  试用: 可用
  Pro: 可用
```

---

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户层                               │
│  未注册用户 | 免费用户 | 试用用户 | Pro用户                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       权限控制层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 前端权限控制 │  │ 后端API权限 │  │ 数据库权限验证      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       业务逻辑层                             │
│  ┌───────────┐  ┌──────────┐  ┌────────────┐  ┌─────────┐ │
│  │ 用户管理   │  │ 订阅管理 │  │ 商机管理    │  │ 卡片管理 │ │
│  └───────────┘  └──────────┘  └────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       数据存储层                             │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌─────────┐  │
│  │ PostgreSQL│  │   Redis  │  │ Airwallex  │  │ 第三方  │  │
│  └──────────┘  └──────────┘  └────────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. 用户模型扩展

**User模型新增字段**：
```python
class User(Base):
    # 现有字段...
    plan_tier = Column(String(20), default="free")  # free, trial, pro
    plan_status = Column(String(20), default="active")  # active, trial_ended, canceled
    trial_ends_at = Column(DateTime(timezone=True))

    # 新增字段
    registration_plan_choice = Column(String(20))  # 注册时选择的计划
    trial_reminder_shown = Column(DateTime(timezone=True))  # 上次显示试用提醒的日期
```

#### 2. 商机模型扩展

**BusinessOpportunity模型新增字段**：
```python
class BusinessOpportunity(Base):
    # 现有字段...

    # 新增字段
    is_locked = Column(Boolean, default=False)  # 是否因试用到期而锁定
    locked_at = Column(DateTime(timezone=True))  # 锁定时间
```

#### 3. 权限检查服务

```python
class PermissionService:
    """统一的权限检查服务"""

    async def check_card_detail_access(self, user: User, card_id: str) -> AccessResult:
        """检查卡片详情访问权限"""
        pass

    async def check_opportunity_access(self, user: User, opp_id: str) -> OpportunityAccessResult:
        """检查商机访问权限"""
        pass

    async def check_api_rate_limit(self, user: User, endpoint: str) -> RateLimitResult:
        """检查API调用频率限制"""
        pass
```

#### 4. 试用管理服务

```python
class TrialManager:
    """试用管理服务"""

    async def create_trial_user(self, user_data: UserCreate) -> User:
        """创建试用用户"""
        trial_ends_at = datetime.now(timezone.utc) + timedelta(days=14)
        return User(
            ...,
            plan_tier='trial',
            trial_ends_at=trial_ends_at
        )

    async def check_trial_expiry(self, user: User) -> bool:
        """检查试用是否到期"""
        if user.plan_tier != 'trial':
            return False
        return datetime.now(timezone.utc) > user.trial_ends_at

    async def expire_trial(self, user: User):
        """试用到期处理"""
        user.plan_tier = 'free'
        user.plan_status = 'trial_ended'
        # 锁定所有活跃商机
        await self._lock_user_opportunities(user.id)

    async def _lock_user_opportunities(self, user_id: str):
        """锁定用户的所有商机"""
        opportunities = await get_user_opportunities(user_id)
        for opp in opportunities:
            if opp.status != 'archived':
                opp.is_locked = True
                opp.locked_at = datetime.now(timezone.utc)
```

### 数据库Schema变更

```sql
-- 用户表新增字段
ALTER TABLE users ADD COLUMN registration_plan_choice VARCHAR(20);
ALTER TABLE users ADD COLUMN trial_reminder_shown TIMESTAMP WITH TIME ZONE;

-- 商机表新增字段
ALTER TABLE business_opportunities ADD COLUMN is_locked BOOLEAN DEFAULT FALSE;
ALTER TABLE business_opportunities ADD COLUMN locked_at TIMESTAMP WITH TIME ZONE;

-- 创建索引
CREATE INDEX idx_business_opportunities_locked
  ON business_opportunities(is_locked, user_id)
  WHERE is_locked = TRUE;

CREATE INDEX idx_users_trial_ends_at
  ON users(trial_ends_at)
  WHERE plan_tier = 'trial';

-- 创建每日API调用统计表
CREATE TABLE daily_api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    usage_date DATE NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    call_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, usage_date, endpoint)
);

CREATE INDEX idx_daily_api_usage_user_date
  ON daily_api_usage(user_id, usage_date);

-- 创建每日卡片浏览统计表
CREATE TABLE daily_card_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    view_date DATE NOT NULL,
    card_id UUID NOT NULL REFERENCES cards(id),
    view_count INTEGER DEFAULT 1,
    first_viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, view_date, card_id)
);

CREATE INDEX idx_daily_card_views_user_date
  ON daily_card_views(user_id, view_date);
```

---

## 实施计划

### Phase 1: 后端基础设施（预计3-5天）

#### 1.1 数据库迁移

**文件**: `backend/migrations/versions/001_add_membership_fields.py`

```python
def upgrade():
    # 添加用户字段
    op.add_column('users', sa.Column('registration_plan_choice', sa.String(20)))
    op.add_column('users', sa.Column('trial_reminder_shown', sa.TIMESTAMP(timezone=True)))

    # 添加商机字段
    op.add_column('business_opportunities', sa.Column('is_locked', sa.Boolean, default=False))
    op.add_column('business_opportunities', sa.Column('locked_at', sa.TIMESTAMP(timezone=True)))

    # 创建索引
    op.create_index('idx_business_opportunities_locked', 'business_opportunities',
                   ['is_locked', 'user_id'])

    # 创建统计表
    op.create_table('daily_api_usage', ...)
    op.create_table('daily_card_views', ...)
```

**验证**:
```bash
# 运行迁移
alembic upgrade head

# 验证表结构
psql -d cbdb -c "\d users"
psql -d cbdb -c "\d business_opportunities"
```

#### 1.2 权限服务实现

**文件**: `backend/services/permission_service.py`

```python
from enum import Enum
from typing import Optional
from models.user import User
from models.business_opportunity import BusinessOpportunity

class AccessLevel(str, Enum):
    FULL = "full"           # 完全访问
    VIEW_ONLY = "view_only" # 只读
    LOCKED = "locked"       # 锁定
    DENIED = "denied"       # 拒绝访问

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_opportunity_access(
        self,
        user: Optional[User],
        opportunity: BusinessOpportunity
    ) -> dict:
        """
        获取商机访问权限

        返回:
        {
            'access_level': 'full' | 'view_only' | 'locked' | 'denied',
            'can_view': bool,
            'can_manage': bool,
            'reason': str | None,
            'upgrade_required': bool
        }
        """
        # 未登录用户
        if not user:
            if opportunity.status == 'potential':
                return {
                    'access_level': AccessLevel.VIEW_ONLY,
                    'can_view': True,
                    'can_manage': False,
                    'reason': 'auth_required',
                    'upgrade_required': True
                }
            return {
                'access_level': AccessLevel.DENIED,
                'can_view': False,
                'can_manage': False,
                'reason': 'auth_required',
                'upgrade_required': True
            }

        # 免费用户
        if user.plan_tier == 'free':
            if opportunity.status == 'potential':
                return {
                    'access_level': AccessLevel.VIEW_ONLY,
                    'can_view': True,
                    'can_manage': False,
                    'reason': 'upgrade_required',
                    'upgrade_required': True
                }
            return {
                'access_level': AccessLevel.DENIED,
                'can_view': False,
                'can_manage': False,
                'reason': 'upgrade_required',
                'upgrade_required': True
            }

        # 试用用户
        if user.plan_tier == 'trial':
            # 检查试用是否到期
            if await self._is_trial_expired(user):
                return {
                    'access_level': AccessLevel.LOCKED,
                    'can_view': True,
                    'can_manage': False,
                    'reason': 'trial_expired',
                    'upgrade_required': True
                }
            # 试用期内
            return {
                'access_level': AccessLevel.FULL,
                'can_view': True,
                'can_manage': True,
                'upgrade_required': False
            }

        # Pro用户
        return {
            'access_level': AccessLevel.FULL,
            'can_view': True,
            'can_manage': True,
            'upgrade_required': False
        }

    async def _is_trial_expired(self, user: User) -> bool:
        """检查试用是否到期"""
        if user.plan_tier != 'trial' or not user.trial_ends_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > user.trial_ends_at
```

#### 1.3 试用管理服务

**文件**: `backend/services/trial_manager.py`

```python
from datetime import datetime, timezone, timedelta
from typing import Optional
from models.user import User
from models.business_opportunity import BusinessOpportunity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class TrialManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_trial_subscription(
        self,
        user: User,
        duration_days: int = 14
    ) -> BusinessOpportunity:
        """创建试用订阅"""
        trial_ends_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

        user.plan_tier = 'trial'
        user.plan_status = 'active'
        user.trial_ends_at = trial_ends_at
        user.registration_plan_choice = 'trial'

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def expire_trial(self, user: User):
        """试用到期处理"""
        # 降级用户
        user.plan_tier = 'free'
        user.plan_status = 'trial_ended'

        # 锁定所有活跃商机
        await self._lock_user_opportunities(user.id)

        await self.db.commit()

    async def _lock_user_opportunities(self, user_id: str):
        """锁定用户的所有商机"""
        result = await self.db.execute(
            select(BusinessOpportunity).where(
                BusinessOpportunity.user_id == user_id,
                BusinessOpportunity.status != 'archived'
            )
        )
        opportunities = result.scalars().all()

        now = datetime.now(timezone.utc)
        for opp in opportunities:
            opp.is_locked = True
            opp.locked_at = now

        await self.db.commit()

    async def get_trial_status(self, user: User) -> dict:
        """获取试用状态"""
        if user.plan_tier != 'trial':
            return {
                'is_trial': False,
                'days_remaining': None
            }

        if not user.trial_ends_at:
            return {
                'is_trial': True,
                'days_remaining': 0
            }

        now = datetime.now(timezone.utc)
        if user.trial_ends_at > now:
            days_remaining = (user.trial_ends_at - now).days
            return {
                'is_trial': True,
                'days_remaining': days_remaining,
                'trial_ends_at': user.trial_ends_at.isoformat(),
                'is_expired': False
            }
        else:
            return {
                'is_trial': True,
                'days_remaining': 0,
                'trial_ends_at': user.trial_ends_at.isoformat(),
                'is_expired': True
            }
```

#### 1.4 API更新

**文件**: `backend/api/auth.py`

```python
@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreateWithPlan,  # 新增plan_choice字段
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册

    plan_choice选项:
    - 'free': 免费版，基础功能
    - 'trial': 试用版，14天完整体验
    """
    from services.trial_manager import TrialManager

    plan_choice = user_data.plan_choice or 'trial'  # 默认试用版

    # 检查邮箱是否已注册
    existing_user = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(400, "邮箱已被注册")

    # 创建用户
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        registration_plan_choice=plan_choice
    )

    if plan_choice == 'trial':
        # 创建试用用户
        trial_manager = TrialManager(db)
        new_user = await trial_manager.create_trial_subscription(new_user)
    else:
        # 创建免费用户
        new_user.plan_tier = 'free'
        new_user.plan_status = 'active'

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 生成token
    access_token = create_access_token(data={"sub": str(new_user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
            "plan_tier": new_user.plan_tier,
            "trial_ends_at": new_user.trial_ends_at.isoformat() if new_user.trial_ends_at else None
        }
    }
```

**文件**: `backend/api/opportunities.py`

```python
@router.get("/{opportunity_id}")
async def get_opportunity_detail(
    opportunity_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取商机详情（带权限检查）"""
    from services.permission_service import PermissionService

    # 获取商机
    opportunity = await db.get(BusinessOpportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(404, "商机不存在")

    # 权限检查
    perm_service = PermissionService(db)
    access = await perm_service.get_opportunity_access(current_user, opportunity)

    if not access['can_view']:
        raise HTTPException(403, access.get('reason', '无权访问'))

    return {
        "opportunity": opportunity.to_dict(),
        "access": {
            "can_view": access['can_view'],
            "can_manage": access['can_manage'],
            "is_locked": access.get('access_level') == AccessLevel.LOCKED,
            "upgrade_required": access.get('upgrade_required', False)
        }
    }

@router.post("/{opportunity_id}/transition")
async def transition_opportunity(
    opportunity_id: str,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """商机状态流转（需要管理权限）"""
    from services.permission_service import PermissionService

    # 获取商机
    opportunity = await db.get(BusinessOpportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(404, "商机不存在")

    # 权限检查
    perm_service = PermissionService(db)
    access = await perm_service.get_opportunity_access(current_user, opportunity)

    if not access['can_manage']:
        raise HTTPException(403, access.get('reason', '无权管理此商机'))

    # 验证状态转换
    if not opportunity.can_transition_to(new_status):
        raise HTTPException(400, f"不能从{opportunity.status}转换到{new_status}")

    # 执行转换
    opportunity.status = new_status
    await db.commit()

    return {"success": True, "new_status": new_status}
```

### Phase 2: 前端用户体验（预计3-5天）

#### 2.1 注册页面改进

**文件**: `frontend/app/register/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth-context';
import { Check } from 'lucide-react';

type PlanChoice = 'free' | 'trial';

const planDetails = {
  free: {
    name: '免费版',
    description: '基础功能，永久使用',
    features: [
      '10次/天 API调用',
      '3张卡片/天浏览',
      '查看商机第一阶段',
      '基础成本计算器'
    ],
    disabledFeatures: [
      'AI机会分析',
      '数据导出',
      '商机管理'
    ],
    color: 'border-gray-200',
    activeColor: 'border-primary bg-primary/5'
  },
  trial: {
    name: '试用版',
    description: '14天完整体验',
    badge: '推荐',
    badgeColor: 'bg-green-500',
    features: [
      '无限API调用',
      '无限卡片浏览',
      '完整商机管理',
      'AI机会分析',
      '数据导出',
      '供应商数据库'
    ],
    color: 'border-gray-200',
    activeColor: 'border-green-500 bg-green-500/5'
  }
};

export default function RegisterPage() {
  const router = useRouter();
  const { register, user } = useAuth();
  const [planChoice, setPlanChoice] = useState<PlanChoice>('trial');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 已登录用户重定向
  useEffect(() => {
    if (user) {
      router.push('/dashboard');
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (user) {
      setError('您已登录，请先退出');
      return;
    }

    if (password !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    if (password.length < 6) {
      setError('密码长度至少为6位');
      return;
    }

    setLoading(true);

    try {
      await register(email, password, name, planChoice);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold">创建您的账户</h2>
          <p className="mt-2 text-muted-foreground">
            选择适合您的计划开始使用
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 计划选择 */}
          <div>
            <label className="block text-sm font-medium mb-3">
              选择您的计划
            </label>
            <div className="space-y-3">
              {(Object.keys(planDetails) as PlanChoice[]).map((plan) => {
                const details = planDetails[plan];
                const isSelected = planChoice === plan;

                return (
                  <button
                    key={plan}
                    type="button"
                    onClick={() => setPlanChoice(plan)}
                    className={`w-full p-4 border-2 rounded-lg text-left transition-all ${
                      isSelected ? details.activeColor : details.color
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-lg">
                            {details.name}
                          </h3>
                          {details.badge && (
                            <span className={`text-xs ${details.badgeColor} text-white px-2 py-0.5 rounded`}>
                              {details.badge}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {details.description}
                        </p>

                        {/* 功能列表 */}
                        <ul className="mt-3 space-y-1">
                          {details.features.map((feature, idx) => (
                            <li key={idx} className="text-xs text-gray-700 flex items-center gap-1">
                              <Check className="h-3 w-3 text-green-500" />
                              {feature}
                            </li>
                          ))}
                        </ul>

                        {/* 不可用功能 */}
                        {details.disabledFeatures && details.disabledFeatures.length > 0 && (
                          <ul className="mt-2 space-y-1">
                            {details.disabledFeatures.map((feature, idx) => (
                              <li key={idx} className="text-xs text-gray-400">
                                ✕ {feature}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>

                      {isSelected && (
                        <Check className={`h-5 w-5 ${plan === 'trial' ? 'text-green-500' : 'text-primary'}`} />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          {/* 用户信息表单 */}
          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium mb-2">
                姓名
              </label>
              <input
                id="name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="您的姓名"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-2">
                邮箱地址
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-2">
                密码
              </label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="至少6位密码"
              />
            </div>

            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium mb-2">
                确认密码
              </label>
              <input
                id="confirm-password"
                type="password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="再次输入密码"
              />
            </div>
          </div>

          {/* 服务条款 */}
          <div className="text-sm text-muted-foreground">
            注册即表示您同意我们的{' '}
            <a href="/terms" className="text-primary hover:underline">
              服务条款
            </a>{' '}
            和{' '}
            <a href="/privacy" className="text-primary hover:underline">
              隐私政策
            </a>
          </div>

          {/* 提交按钮 */}
          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={loading}
          >
            {loading ? '注册中...' : planChoice === 'trial' ? '开始14天试用' : '创建免费账户'}
          </Button>

          {/* 登录链接 */}
          <div className="text-center text-sm text-muted-foreground">
            已有账户？{' '}
            <a href="/login" className="font-medium text-primary hover:underline">
              立即登录
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}
```

#### 2.2 试用提醒组件

**文件**: `frontend/components/trial/TrialReminderBanner.tsx`

```typescript
'use client';

import Link from 'next/link';
import { AlertCircle } from 'lucide-react';

interface TrialReminderBannerProps {
  trialEndsAt: string;
  daysRemaining: number;
}

export function TrialReminderBanner({
  trialEndsAt,
  daysRemaining
}: TrialReminderBannerProps) {
  // 根据剩余天数设置提醒级别
  const getReminderConfig = () => {
    if (daysRemaining <= 0) {
      return {
        level: 'expired',
        bgColor: 'bg-gray-600',
        text: '试用期已结束，升级到Pro继续使用',
        icon: AlertCircle
      };
    } else if (daysRemaining <= 3) {
      return {
        level: 'high',
        bgColor: 'bg-red-500',
        text: `试用期还剩${daysRemaining}天！立即升级享受完整功能`,
        icon: AlertCircle
      };
    } else if (daysRemaining <= 7) {
      return {
        level: 'medium',
        bgColor: 'bg-yellow-500',
        text: `试用期还剩${daysRemaining}天，升级享Pro完整功能`,
        icon: null
      };
    } else {
      return {
        level: 'low',
        bgColor: 'bg-blue-500',
        text: `试用期还剩${daysRemaining}天`,
        icon: null
      };
    }
  };

  const config = getReminderConfig();
  const Icon = config.icon;

  return (
    <div className={`${config.bgColor} text-white px-4 py-2`}>
      <div className="max-w-7xl mx-auto flex items-center justify-center gap-3 text-sm">
        {Icon && <Icon className="h-4 w-4" />}
        <span className="font-medium">{config.text}</span>
        {' '}|{' '}
        <Link
          href="/pricing"
          className="underline hover:text-white/80 transition-colors"
        >
          立即升级
        </Link>
      </div>
    </div>
  );
}
```

#### 2.3 商机权限UI

**文件**: `frontend/app/opportunities/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Lock, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';

interface OpportunityAccess {
  can_view: boolean;
  can_manage: boolean;
  is_locked?: boolean;
  upgrade_required?: boolean;
  reason?: string;
}

interface Opportunity {
  id: string;
  title: string;
  description: string;
  status: 'potential' | 'verifying' | 'assessing' | 'executing' | 'archived';
  created_at: string;
}

export default function OpportunitiesPage() {
  const { user, isAuthenticated } = useAuth();
  const [opportunities, setOpportunities] = useState<{
    data: Opportunity[];
    access: Record<string, OpportunityAccess>;
  }>({ data: [], access: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOpportunities();
  }, [isAuthenticated, user]);

  const fetchOpportunities = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/v1/opportunities', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        }
      });

      if (response.ok) {
        const data = await response.json();
        setOpportunities(data);
      }
    } catch (error) {
      console.error('Failed to fetch opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8">加载中...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">商机管理</h1>
        <p className="text-muted-foreground mt-2">
          管理您的商业机会，追踪从发现到执行的完整流程
        </p>
      </div>

      {/* 未登录提示 */}
      {!isAuthenticated && (
        <Card className="p-8 text-center mb-8">
          <h2 className="text-xl font-semibold mb-2">登录查看商机</h2>
          <p className="text-muted-foreground mb-4">
            注册后即可查看商机第一阶段（发现期）
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register?plan=trial">
              <Button className="bg-green-500 hover:bg-green-600">
                开始14天试用
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline">
                已有账户？登录
              </Button>
            </Link>
          </div>
        </Card>
      )}

      {/* 商机列表 */}
      <div className="grid gap-6">
        {opportunities.data.map((opp) => {
          const access = opportunities.access[opp.id];

          return (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              access={access}
              userTier={user?.plan_tier}
            />
          );
        })}
      </div>
    </div>
  );
}

interface OpportunityCardProps {
  opportunity: Opportunity;
  access?: OpportunityAccess;
  userTier?: string;
}

function OpportunityCard({ opportunity, access, userTier }: OpportunityCardProps) {
  const isLocked = access?.is_locked;
  const canManage = access?.can_manage;
  const upgradeRequired = access?.upgrade_required;

  return (
    <Card className={`relative p-6 ${isLocked ? 'opacity-60 bg-gray-50' : ''}`}>
      {/* 锁定遮罩 */}
      {isLocked && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/50 z-10 rounded-lg">
          <div className="bg-white p-6 rounded-lg shadow-lg text-center max-w-sm">
            <Lock className="h-8 w-8 text-gray-400 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-700 mb-2">
              试用期已结束
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              商机已锁定，升级到Pro解锁商机管理
            </p>
            <Link href="/pricing">
              <Button className="w-full">
                立即升级
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* 商机内容 */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold">{opportunity.title}</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {opportunity.description}
          </p>
        </div>

        {/* 状态标签 */}
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
          opportunity.status === 'potential' ? 'bg-blue-100 text-blue-700' :
          opportunity.status === 'verifying' ? 'bg-yellow-100 text-yellow-700' :
          opportunity.status === 'assessing' ? 'bg-purple-100 text-purple-700' :
          opportunity.status === 'executing' ? 'bg-green-100 text-green-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {opportunity.status}
        </span>
      </div>

      {/* 权限提示 */}
      {!canManage && !isLocked && upgradeRequired && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-center gap-2 text-sm text-yellow-800">
            <AlertCircle className="h-4 w-4" />
            <span>
              {userTier === 'free'
                ? '升级到试用版或Pro版管理商机'
                : '升级到Pro版管理商机'}
            </span>
          </div>
          <Link href="/pricing" className="text-xs text-yellow-700 hover:underline mt-2 block">
            查看定价 →
          </Link>
        </div>
      )}

      {/* 商机操作按钮（仅可管理时显示） */}
      {canManage && !isLocked && (
        <div className="mt-4 flex gap-2">
          <Button size="sm" variant="outline">
            查看详情
          </Button>
          <Button size="sm">
            推进商机
          </Button>
        </div>
      )}
    </Card>
  );
}
```

#### 2.4 SEO顶部Banner

**文件**: `frontend/components/seo/TopBanner.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface BannerConfig {
  text: string;
  link: string;
  bgClass: string;
}

const banners: BannerConfig[] = [
  {
    text: '🚀 新用户注册即送14天Pro试用，体验完整功能',
    link: '/register?plan=trial',
    bgClass: 'bg-gradient-to-r from-blue-600 to-blue-700'
  },
  {
    text: '📊 AI驱动的跨境电商商机发现，立即开始',
    link: '/pricing',
    bgClass: 'bg-gradient-to-r from-green-600 to-green-700'
  },
  {
    text: '💡 每日更新精选商机卡片，助力业务增长',
    link: '/cards',
    bgClass: 'bg-gradient-to-r from-purple-600 to-purple-700'
  },
  {
    text: '⚡ 限时优惠：年度订阅省2个月，立即升级',
    link: '/pricing?billing=yearly',
    bgClass: 'bg-gradient-to-r from-orange-600 to-orange-700'
  }
];

export function TopBanner() {
  const [currentBanner, setCurrentBanner] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentBanner((prev) => (prev + 1) % banners.length);
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  const banner = banners[currentBanner];

  return (
    <Link href={banner.link} className="block hover:opacity-95 transition-opacity">
      <div className={`${banner.bgClass} text-white text-center py-2 px-4 text-sm`}>
        {banner.text}
      </div>
    </Link>
  );
}
```

**集成到布局**：

**文件**: `frontend/app/layout.tsx`

```typescript
import { TopBanner } from '@/components/seo/TopBanner';
import { Header } from '@/components/layout/Header';
import { TrialReminderBanner } from '@/components/trial/TrialReminderBanner';
import { useAuth } from '@/lib/auth-context';

export function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <TopBanner />
        <Header />
        <TrialReminderBannerWrapper />
        <main>{children}</main>
      </body>
    </html>
  );
}

function TrialReminderBannerWrapper() {
  const { user } = useAuth();

  if (user?.plan_tier === 'trial' && user?.trial_ends_at) {
    const daysRemaining = Math.ceil(
      (new Date(user.trial_ends_at) - new Date()) / (1000 * 60 * 60 * 24)
    );
    return <TrialReminderBanner trialEndsAt={user.trial_ends_at} daysRemaining={daysRemaining} />;
  }

  return null;
}
```

#### 2.5 卡片详情引导

**文件**: `frontend/components/cards/CardAuthModal.tsx`

```typescript
'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import Link from 'next/link';

interface CardAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CardAuthModal({ isOpen, onClose }: CardAuthModalProps) {
  const router = useRouter();

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="text-center p-6">
        <h2 className="text-xl font-bold mb-2">查看详情需要登录</h2>
        <p className="text-muted-foreground mb-6">
          注册后即可查看卡片详情，新用户可获得14天完整试用
        </p>

        <div className="space-y-3">
          <Link href="/register?plan=trial" className="block" onClick={onClose}>
            <Button className="w-full bg-green-500 hover:bg-green-600" size="lg">
              开始14天试用
            </Button>
          </Link>

          <Link href="/register?plan=free" className="block" onClick={onClose}>
            <Button variant="outline" className="w-full" size="lg">
              免费注册
            </Button>
          </Link>

          <div className="text-sm text-muted-foreground">
            已有账户？{' '}
            <Link href="/login" className="text-primary hover:underline" onClick={onClose}>
              立即登录
            </Link>
          </div>
        </div>

        {/* 试用版特权 */}
        <div className="mt-6 pt-6 border-t text-left">
          <h3 className="font-semibold mb-3 text-sm">试用版特权</h3>
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              无限查看卡片详情
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              完整商机管理功能
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              AI机会分析
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              数据导出功能
            </li>
          </ul>
        </div>
      </div>
    </Modal>
  );
}
```

### Phase 3: 定时任务（预计1-2天）

**文件**: `backend/cron/trial_expiry_job.py`

```python
"""
试用到期定时任务
每天凌晨检查并处理试用到期的用户
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from services.trial_manager import TrialManager
from database import get_db

import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def expire_trials_job():
    """处理试用到期的用户"""
    from datetime import datetime, timezone

    logger.info("Starting trial expiry job...")

    try:
        async for db in get_db():
            # 查找所有试用到期但状态仍为trial的用户
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(User).where(
                    User.plan_tier == 'trial',
                    User.trial_ends_at <= now,
                    User.plan_status == 'active'
                )
            )
            expired_users = result.scalars().all()

            logger.info(f"Found {len(expired_users)} expired trial users")

            if not expired_users:
                logger.info("No expired trials to process")
                return

            trial_manager = TrialManager(db)

            for user in expired_users:
                try:
                    logger.info(f"Expiring trial for user {user.id}")
                    await trial_manager.expire_trial(user)
                    logger.info(f"Successfully expired trial for user {user.id}")

                    # TODO: 发送邮件通知
                    # await send_trial_ended_email(user.email)

                except Exception as e:
                    logger.error(f"Failed to expire trial for user {user.id}: {e}")

            await db.commit()
            logger.info(f"Successfully processed {len(expired_users)} expired trials")
            break

    except Exception as e:
        logger.error(f"Trial expiry job failed: {e}")

# 配置定时任务：每天凌晨0点执行
scheduler.add_job(
    expire_trials_job,
    'cron',
    hour=0,
    minute=0,
    id='expire_trials',
    replace_existing=True
)

def start_scheduler():
    """启动定时任务调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("Trial expiry scheduler started")

def stop_scheduler():
    """停止定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Trial expiry scheduler stopped")
```

**集成到应用启动**：

**文件**: `backend/main.py`

```python
from cron.trial_expiry_job import start_scheduler, stop_scheduler

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 启动定时任务
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    # 停止定时任务
    stop_scheduler()
```

### Phase 4: 集成测试（预计2-3天）

#### 4.1 后端API测试

**文件**: `backend/tests/test_membership_api.py`

```python
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta

class TestMembershipAPI:
    """会员系统API测试"""

    async def test_register_free_user(self, client: AsyncClient):
        """测试注册免费用户"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "free@example.com",
                "password": "test123",
                "name": "Free User",
                "plan_choice": "free"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["plan_tier"] == "free"
        assert data["user"]["trial_ends_at"] is None

    async def test_register_trial_user(self, client: AsyncClient):
        """测试注册试用用户"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "trial@example.com",
                "password": "test123",
                "name": "Trial User",
                "plan_choice": "trial"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["plan_tier"] == "trial"
        assert data["user"]["trial_ends_at"] is not None

        # 验证试用结束时间大约是14天后
        trial_ends_at = datetime.fromisoformat(data["user"]["trial_ends_at"])
        expected_end = datetime.now(timezone.utc) + timedelta(days=14)
        assert abs((trial_ends_at - expected_end).total_seconds()) < 60

    async def test_free_user_opportunity_access(self, client: AsyncClient, free_user_token):
        """测试免费用户的商机访问权限"""
        # 只能查看第一阶段商机
        response = await client.get(
            "/api/v1/opportunities/potential-opp-id",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access"]["can_view"] == True
        assert data["access"]["can_manage"] == False

        # 不能查看其他阶段商机
        response = await client.get(
            "/api/v1/opportunities/verifying-opp-id",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 403

    async def test_trial_user_opportunity_access(self, client: AsyncClient, trial_user_token):
        """测试试用用户的商机访问权限"""
        response = await client.get(
            "/api/v1/opportunities/any-opp-id",
            headers={"Authorization": f"Bearer {trial_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access"]["can_view"] == True
        assert data["access"]["can_manage"] == True

    async def test_trial_expiry(self, client: AsyncClient, trial_user_token):
        """测试试用到期"""
        # 模拟试用到期
        # ... (创建已过期的试用用户)

        response = await client.get(
            "/api/v1/opportunities/any-opp-id",
            headers={"Authorization": f"Bearer {expired_trial_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access"]["can_view"] == True
        assert data["access"]["can_manage"] == False
        assert data["access"]["is_locked"] == True

    async def test_unauthenticated_opportunity_access(self, client: AsyncClient):
        """测试未登录用户的商机访问权限"""
        response = await client.get("/api/v1/opportunities/potential-opp-id")
        assert response.status_code == 200
        data = response.json()
        assert data["access"]["can_view"] == True
        assert data["access"]["can_manage"] == False
        assert data["access"]["upgrade_required"] == True

        response = await client.get("/api/v1/opportunities/verifying-opp-id")
        assert response.status_code == 403
```

#### 4.2 前端E2E测试

**文件**: `frontend/tests/e2e/membership.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('会员系统E2E测试', () => {
  test('未注册用户浏览体验', async ({ page }) => {
    await page.goto('/');

    // 可以浏览首页
    await expect(page.locator('h1')).toContainText('ZenConsult');

    // 可以浏览卡片列表
    await page.goto('/cards');
    await expect(page.locator('.card')).toHaveCount(12);

    // 点击详情需要登录
    await page.click('.card:first-child text=查看详情');
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await expect(page.locator('text=查看详情需要登录')).toBeVisible();
  });

  test('注册流程 - 选择试用版', async ({ page }) => {
    await page.goto('/register');

    // 选择试用版
    await page.click('button:has-text("试用版")');

    // 填写表单
    await page.fill('#name', 'Test User');
    await page.fill('#email', `trial-${Date.now()}@example.com`);
    await page.fill('#password', 'test123');
    await page.fill('#confirm-password', 'test123');

    // 提交
    await page.click('button:has-text("开始14天试用")');

    // 跳转到dashboard
    await expect(page).toHaveURL('/dashboard');

    // 验证试用状态
    await page.goto('/dashboard/settings');
    await expect(page.locator('text=试用版')).toBeVisible();
    await expect(page.locator('text=/还剩.*天/')).toBeVisible();
  });

  test('注册流程 - 选择免费版', async ({ page }) => {
    await page.goto('/register');

    // 选择免费版
    await page.click('button:has-text("免费版")');

    // 填写表单
    await page.fill('#name', 'Free User');
    await page.fill('#email', `free-${Date.now()}@example.com`);
    await page.fill('#password', 'test123');
    await page.fill('#confirm-password', 'test123');

    // 提交
    await page.click('button:has-text("创建免费账户")');

    // 跳转到dashboard
    await expect(page).toHaveURL('/dashboard');
  });

  test('试用提醒横幅', async ({ page, context }) => {
    // 登录试用用户
    const trialToken = await getTrialUserToken();
    await context.addCookies([
      { name: 'auth_token', value: trialToken, domain: 'localhost', path: '/' }
    ]);

    await page.goto('/');

    // 验证试用提醒横幅显示
    await expect(page.locator('text=试用期还剩')).toBeVisible();
  });

  test('商机权限控制', async ({ page, context }) => {
    // 登录免费用户
    const freeToken = await getFreeUserToken();
    await context.addCookies([
      { name: 'auth_token', value: freeToken, domain: 'localhost', path: '/' }
    ]);

    await page.goto('/opportunities');

    // 验证只能查看第一阶段商机
    await expect(page.locator('text=升级到试用版或Pro版管理商机')).toBeVisible();
  });
});
```

---

## 测试方案

### 测试场景清单

#### 1. 未注册用户场景

| 场景 | 操作 | 预期结果 |
|------|------|---------|
| 浏览首页 | 访问 `/` | 正常显示，顶部显示SEO Banner |
| 浏览卡片列表 | 访问 `/cards` | 正常显示所有卡片 |
| 点击卡片详情 | 点击"查看详情" | 弹出登录引导模态框 |
| 收藏卡片 | 点击收藏按钮 | 提示登录 |
| 浏览商机 | 访问 `/opportunities` | 显示登录提示，只能看到第一阶段商机 |

#### 2. 免费用户场景

| 场景 | 操作 | 预期结果 |
|------|------|---------|
| 注册免费版 | 选择免费版注册 | 创建免费用户，跳转dashboard |
| 查看卡片详情 | 点击详情 | 可以查看（有每日限额） |
| 超过浏览限额 | 超过10次/天 | 提示升级 |
| 查看商机 | 访问 `/opportunities` | 只能看到第一阶段 |
| 管理商机 | 尝试推进商机 | 提示升级 |

#### 3. 试用用户场景

| 场景 | 操作 | 预期结果 |
|------|------|---------|
| 注册试用版 | 选择试用版注册 | 创建试用用户，试用14天 |
| 查看试用提醒 | 访问任意页面 | 顶部显示试用天数提醒 |
| 查看卡片详情 | 点击详情 | 无限制查看 |
| 管理商机 | 推进商机状态 | 可以完整管理5阶段 |
| 试用到期 | 14天后 | 自动降级，商机锁定 |

#### 4. Pro用户场景

| 场景 | 操作 | 预期结果 |
|------|------|---------|
| 升级Pro | 通过支付升级 | 成为Pro用户 |
| 查看卡片 | 浏览卡片 | 无限制 |
| 管理商机 | 推进商机 | 完整权限 |
| API调用 | 调用API | 无限制 |

### 测试数据准备

```sql
-- 创建测试用户
INSERT INTO users (id, email, name, password_hash, plan_tier, trial_ends_at) VALUES
  ('11111111-1111-1111-1111-111111111111', 'free@test.com', 'Free User', '...', 'free', NULL),
  ('22222222-2222-2222-2222-222222222222', 'trial@test.com', 'Trial User', '...', 'trial', NOW() + INTERVAL '14 days'),
  ('33333333-3333-3333-3333-333333333333', 'expired-trial@test.com', 'Expired Trial User', '...', 'trial', NOW() - INTERVAL '1 day'),
  ('44444444-4444-4444-4444-444444444444', 'pro@test.com', 'Pro User', '...', 'pro', NULL);

-- 创建测试商机
INSERT INTO business_opportunities (id, user_id, title, status) VALUES
  ('00000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Potential Opp', 'potential'),
  ('00000000-0000-0000-0000-000000000002', '22222222-2222-2222-2222-222222222222', 'Verifying Opp', 'verifying'),
  ('00000000-0000-0000-0000-000000000003', '22222222-2222-2222-2222-222222222222', 'Locked Opp', 'assessing');
```

### 性能测试

```bash
# 使用Locust进行负载测试
locust -f backend/tests/load/test_membership_api.py --host=https://api.zenconsult.top

# 测试场景：
# 1. 并发注册请求（100用户/秒）
# 2. 并发商机查询请求（500用户/秒）
# 3. 权限检查性能（目标：<50ms响应时间）
```

---

## 风险评估

### 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 数据库迁移失败 | 高 | 低 | 1. 备份数据库 2. 在测试环境先验证 3. 准备回滚脚本 |
| 权限检查性能问题 | 中 | 中 | 1. 使用Redis缓存权限 2. 数据库索引优化 3. 异步权限检查 |
| 定时任务执行失败 | 中 | 低 | 1. 添加失败重试机制 2. 监控告警 3. 手动执行备用方案 |
| 前端状态不同步 | 低 | 中 | 1. 使用React Query管理状态 2. 定期刷新用户状态 |

### 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 用户转化率下降 | 高 | 中 | 1. A/B测试新注册流程 2. 优化文案和UI 3. 提供更多价值证明 |
| 试用用户流失 | 高 | 高 | 1. 优化产品价值 2. 增加试用中期引导 3. 优惠升级策略 |
| 收入下降 | 高 | 低 | 1. 保留Pro付费路径 2. 优化定价策略 3. 增值服务 |

### 合规风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 数据隐私 | 高 | 低 | 1. 遵守GDPR/CCPA 2. 用户数据加密 3. 隐私政策更新 |
| 虚假宣传 | 中 | 低 | 1. 实事求是的营销文案 2. 明确试用期条款 3. 用户协议更新 |

---

## 成功指标

### 北极星指标

**试用用户30天付费转化率**
- 目标：> 30%
- 当前：待统计
- 测量：试用用户中30天内升级为Pro的比例

### 关键指标

#### 1. 用户增长指标

| 指标 | 当前 | 1个月目标 | 3个月目标 |
|------|------|-----------|-----------|
| 日新增注册用户 | 待统计 | 10 | 30 |
| 免费用户占比 | 待统计 | 50% | 40% |
| 试用用户占比 | 待统计 | 40% | 45% |
| Pro用户数量 | 待统计 | 15 | 50 |

#### 2. 转化漏斗指标

| 漏斗阶段 | 目标转化率 |
|---------|-----------|
| 访问 → 注册 | 5% |
| 注册 → 试用选择 | 60% |
| 试用 → Pro付费 | 30% |
| 免费 → Pro付费 | 10% |

#### 3. 用户活跃指标

| 指标 | 目标 |
|------|------|
| 日活跃用户（DAU） | > 100 |
| 周活跃用户（WAU） | > 200 |
| 月活跃用户（MAU） | > 500 |
| 用户留存率（D7） | > 40% |

#### 4. 收入指标

| 指标 | 1个月目标 | 3个月目标 |
|------|-----------|-----------|
| 月度经常性收入（MRR） | ¥10,000 | ¥50,000 |
| 用户平均收入（ARPU） | ¥100 | ¥150 |
| 客户终身价值（LTV） | 待统计 | > ¥1,000 |
| 获客成本（CAC） | 待统计 | < ¥300 |

### 数据分析计划

#### 事件追踪

```javascript
// 前端事件追踪
analytics.track('user_registered', {
  plan_choice: 'trial' | 'free',
  source: 'organic' | 'referral' | 'direct'
});

analytics.track('trial_started', {
  user_id: '...',
  trial_ends_at: '...'
});

analytics.track('trial_expired', {
  user_id: '...',
  days_in_trial: 14
});

analytics.track('upgraded_to_pro', {
  user_id: '...',
  previous_tier: 'trial' | 'free',
  billing_cycle: 'monthly' | 'yearly'
});
```

#### SQL分析查询

```sql
-- 注册用户计划选择分布
SELECT
  registration_plan_choice,
  COUNT(*) as user_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM users
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY registration_plan_choice;

-- 试用用户付费转化率
WITH trial_users AS (
  SELECT
    id,
    trial_ends_at,
    plan_tier
  FROM users
  WHERE registration_plan_choice = 'trial'
    AND trial_ends_at IS NOT NULL
    AND trial_ends_at >= NOW() - INTERVAL '60 days'
)
SELECT
  COUNT(CASE WHEN plan_tier = 'pro' THEN 1 END) as converted_users,
  COUNT(*) as total_trial_users,
  ROUND(COUNT(CASE WHEN plan_tier = 'pro' THEN 1 END) * 100.0 / COUNT(*), 2) as conversion_rate
FROM trial_users;

-- 用户留存率（D7, D30）
WITH user_cohorts AS (
  SELECT
    DATE(created_at) as cohort_date,
    COUNT(*) as cohort_size
  FROM users
  WHERE created_at >= NOW() - INTERVAL '90 days'
  GROUP BY DATE(created_at)
),
retention AS (
  SELECT
    DATE(u.created_at) as cohort_date,
    COUNT(DISTINCT CASE WHEN l.last_login_at >= u.created_at + INTERVAL '7 days' THEN u.id END) as d7_retained,
    COUNT(DISTINCT CASE WHEN l.last_login_at >= u.created_at + INTERVAL '30 days' THEN u.id END) as d30_retained,
    COUNT(*) as cohort_size
  FROM users u
  LEFT JOIN user_login_stats l ON u.id = l.user_id
  WHERE u.created_at >= NOW() - INTERVAL '90 days'
  GROUP BY DATE(u.created_at)
)
SELECT
  c.cohort_date,
  c.cohort_size,
  ROUND(r.d7_retained * 100.0 / c.cohort_size, 2) as d7_retention_rate,
  ROUND(r.d30_retained * 100.0 / c.cohort_size, 2) as d30_retention_rate
FROM user_cohorts c
LEFT JOIN retention r ON c.cohort_date = r.cohort_date
ORDER BY c.cohort_date DESC
LIMIT 10;
```

---

## 附录

### A. 相关文档

- [FREEMIUM-MONETIZATION-STRATEGY.md](../FREEMIUM-MONETIZATION-STRATEGY.md) - 免费增值 monetization策略
- [USER-JOURNEY-MAP.md](../USER-JOURNEY-MAP.md) - 用户旅程地图
- [BUSINESS-MODEL-STRATEGY.md](../BUSINESS-MODEL-STRATEGY.md) - 商业模式策略

### B. API文档

详见 `backend/docs/api/membership.md`

### C. 数据库Schema

详见 `backend/docs/database/schema.md`

### D. 前端组件库

详见 `frontend/docs/components.md`

---

**文档版本**: 1.0
**最后更新**: 2026-03-14
**维护者**: Development Team
