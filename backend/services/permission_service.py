"""Permission service for membership system

Manages access control for different user tiers:
- Unregistered: View-only first stage (potential)
- Free: View-only first stage, rate limited
- Trial: Full access for 14 days
- Pro: Unlimited access
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.business_opportunity import BusinessOpportunity


class AccessLevel(str, Enum):
    """Access permission levels"""
    FULL = "full"           # Complete access (read/write)
    VIEW_ONLY = "view_only" # Read-only access
    LOCKED = "locked"       # Previously accessible, now locked
    DENIED = "denied"       # No access


class PermissionService:
    """
    Unified permission checking service

    Handles all access control decisions for the membership system.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_opportunity_access(
        self,
        user: Optional[User],
        opportunity: BusinessOpportunity
    ) -> Dict[str, Any]:
        """
        Get opportunity access permissions

        Returns:
            {
                'access_level': 'full' | 'view_only' | 'locked' | 'denied',
                'can_view': bool,
                'can_manage': bool,
                'reason': str | None,
                'upgrade_required': bool
            }
        """
        # Unauthenticated users
        if not user:
            return self._get_unauth_opportunity_access(opportunity)

        # Free users
        if user.plan_tier == 'free':
            return await self._get_free_opportunity_access(user, opportunity)

        # Trial users
        if user.plan_tier == 'trial':
            return await self._get_trial_opportunity_access(user, opportunity)

        # Pro users
        if user.plan_tier == 'pro':
            return self._get_pro_opportunity_access()

        # Default: deny access
        return {
            'access_level': AccessLevel.DENIED,
            'can_view': False,
            'can_manage': False,
            'reason': 'unknown_plan_tier',
            'upgrade_required': True
        }

    def _get_unauth_opportunity_access(
        self,
        opportunity: BusinessOpportunity
    ) -> Dict[str, Any]:
        """Unauthenticated user can only view potential stage"""
        # Only show first stage (potential)
        if opportunity.status == 'potential':
            return {
                'access_level': AccessLevel.VIEW_ONLY,
                'can_view': True,
                'can_manage': False,
                'reason': 'auth_required_for_full_access',
                'upgrade_required': True
            }

        # Other stages denied
        return {
            'access_level': AccessLevel.DENIED,
            'can_view': False,
            'can_manage': False,
            'reason': 'auth_required',
            'upgrade_required': True
        }

    async def _get_free_opportunity_access(
        self,
        user: User,
        opportunity: BusinessOpportunity
    ) -> Dict[str, Any]:
        """Free users can view first stage, but not manage"""
        # Only show first stage
        if opportunity.status == 'potential':
            return {
                'access_level': AccessLevel.VIEW_ONLY,
                'can_view': True,
                'can_manage': False,
                'reason': 'upgrade_required_for_management',
                'upgrade_required': True
            }

        # Other stages denied
        return {
            'access_level': AccessLevel.DENIED,
            'can_view': False,
            'can_manage': False,
            'reason': 'upgrade_required',
            'upgrade_required': True
        }

    async def _get_trial_opportunity_access(
        self,
        user: User,
        opportunity: BusinessOpportunity
    ) -> Dict[str, Any]:
        """Trial users get full access if trial is active"""
        # Check if trial is expired
        if await self._is_trial_expired(user):
            # Check if this specific opportunity is locked
            if opportunity.is_locked:
                return {
                    'access_level': AccessLevel.LOCKED,
                    'can_view': True,
                    'can_manage': False,
                    'reason': 'trial_expired',
                    'upgrade_required': True,
                    'locked_at': opportunity.locked_at.isoformat() if opportunity.locked_at else None
                }

            # Trial expired but opportunity not yet locked
            return {
                'access_level': AccessLevel.DENIED,
                'can_view': False,
                'can_manage': False,
                'reason': 'trial_expired',
                'upgrade_required': True
            }

        # Active trial: full access
        return {
            'access_level': AccessLevel.FULL,
            'can_view': True,
            'can_manage': True,
            'upgrade_required': False
        }

    def _get_pro_opportunity_access(self) -> Dict[str, Any]:
        """Pro users get full access"""
        return {
            'access_level': AccessLevel.FULL,
            'can_view': True,
            'can_manage': True,
            'upgrade_required': False
        }

    async def _is_trial_expired(self, user: User) -> bool:
        """Check if user's trial has expired"""
        if user.plan_tier != 'trial' or not user.trial_ends_at:
            return False
        return datetime.now(timezone.utc) > user.trial_ends_at

    async def check_card_detail_access(
        self,
        user: Optional[User],
        card_id: str
    ) -> Dict[str, Any]:
        """
        Check card detail access permissions

        Returns:
            {
                'can_view': bool,
                'can_save': bool,
                'reason': str | None,
                'daily_limit': int | None,
                'views_remaining': int | None
            }
        """
        # Unauthenticated users: can view but cannot save
        if not user:
            return {
                'can_view': True,
                'can_save': False,
                'reason': 'auth_required_to_save',
                'daily_limit': None,
                'views_remaining': None
            }

        # Trial and Pro users: unlimited access
        if user.plan_tier in ('trial', 'pro'):
            # Check if trial is expired
            if user.plan_tier == 'trial' and await self._is_trial_expired(user):
                return {
                    'can_view': True,
                    'can_save': False,
                    'reason': 'trial_expired',
                    'daily_limit': None,
                    'views_remaining': None
                }

            return {
                'can_view': True,
                'can_save': True,
                'daily_limit': None,
                'views_remaining': None
            }

        # Free users: limited daily views (3 per day)
        if user.plan_tier == 'free':
            return await self._check_free_user_card_limit(user)

        # Default: deny
        return {
            'can_view': False,
            'can_save': False,
            'reason': 'unknown_plan_tier',
            'daily_limit': None,
            'views_remaining': None
        }

    async def _check_free_user_card_limit(
        self,
        user: User
    ) -> Dict[str, Any]:
        """Check free user's daily card view limit"""
        from datetime import date
        from models.daily_card_views import DailyCardView
        from models.card import Card

        DAILY_LIMIT = 3

        # Query today's views
        today = date.today()
        result = await self.db.execute(
            select(Card)
            .select_from(DailyCardView)
            .join(Card, DailyCardView.card_id == Card.id)
            .where(
                DailyCardView.user_id == user.id,
                DailyCardView.view_date == today
            )
        )

        # Count views
        views_today = len(result.all())
        views_remaining = max(0, DAILY_LIMIT - views_today)

        return {
            'can_view': views_remaining > 0,
            'can_save': True,
            'daily_limit': DAILY_LIMIT,
            'views_remaining': views_remaining,
            'reason': None if views_remaining > 0 else 'daily_limit_exceeded'
        }

    async def check_api_rate_limit(
        self,
        user: Optional[User],
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Check API call rate limit

        Returns:
            {
                'can_call': bool,
                'limit': int | None,
                'remaining': int | None,
                'resets_at': str | None
            }
        """
        # Unauthenticated: no API access
        if not user:
            return {
                'can_call': False,
                'limit': None,
                'remaining': None,
                'reason': 'auth_required'
            }

        # Trial and Pro: unlimited
        if user.plan_tier in ('trial', 'pro'):
            # Check trial expiry
            if user.plan_tier == 'trial' and await self._is_trial_expired(user):
                return {
                    'can_call': False,
                    'limit': None,
                    'remaining': None,
                    'reason': 'trial_expired'
                }

            return {
                'can_call': True,
                'limit': None,
                'remaining': None
            }

        # Free users: 10 calls per day
        if user.plan_tier == 'free':
            return await self._check_free_user_api_limit(user, endpoint)

        return {
            'can_call': False,
            'limit': None,
            'remaining': None,
            'reason': 'unknown_plan_tier'
        }

    async def _check_free_user_api_limit(
        self,
        user: User,
        endpoint: str
    ) -> Dict[str, Any]:
        """Check free user's daily API call limit"""
        from datetime import date, timedelta, datetime
        from models.daily_api_usage import DailyApiUsage

        DAILY_LIMIT = 10

        today = date.today()

        # Get or create usage record
        result = await self.db.execute(
            select(DailyApiUsage).where(
                DailyApiUsage.user_id == user.id,
                DailyApiUsage.usage_date == today,
                DailyApiUsage.endpoint == endpoint
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            # Create new usage record
            usage = DailyApiUsage(
                user_id=user.id,
                usage_date=today,
                endpoint=endpoint,
                call_count=0
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)

        calls_remaining = max(0, DAILY_LIMIT - usage.call_count)

        # Calculate reset time (midnight tomorrow)
        tomorrow = today + timedelta(days=1)
        resets_at = datetime.combine(tomorrow, datetime.min.time()).isoformat()

        return {
            'can_call': calls_remaining > 0,
            'limit': DAILY_LIMIT,
            'remaining': calls_remaining,
            'resets_at': resets_at
        }

    async def record_api_call(
        self,
        user: User,
        endpoint: str
    ):
        """Record an API call for rate limiting"""
        from datetime import date
        from sqlalchemy import select
        from models.daily_api_usage import DailyApiUsage

        today = date.today()

        result = await self.db.execute(
            select(DailyApiUsage).where(
                DailyApiUsage.user_id == user.id,
                DailyApiUsage.usage_date == today,
                DailyApiUsage.endpoint == endpoint
            )
        )
        usage = result.scalar_one_or_none()

        if usage:
            usage.call_count += 1
        else:
            usage = DailyApiUsage(
                user_id=user.id,
                usage_date=today,
                endpoint=endpoint,
                call_count=1
            )
            self.db.add(usage)

        await self.db.commit()

    async def record_card_view(
        self,
        user: User,
        card_id: str
    ):
        """Record a card view for rate limiting"""
        from datetime import date
        from sqlalchemy import select
        from models.daily_card_views import DailyCardView

        today = date.today()

        result = await self.db.execute(
            select(DailyCardView).where(
                DailyCardView.user_id == user.id,
                DailyCardView.view_date == today,
                DailyCardView.card_id == card_id
            )
        )
        view = result.scalar_one_or_none()

        if view:
            view.view_count += 1
        else:
            view = DailyCardView(
                user_id=user.id,
                view_date=today,
                card_id=card_id,
                view_count=1
            )
            self.db.add(view)

        await self.db.commit()
