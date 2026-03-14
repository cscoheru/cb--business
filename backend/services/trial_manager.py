"""Trial management service

Handles trial user lifecycle:
- Creating 14-day trials for new users
- Checking trial expiration status
- Expiring trials and locking opportunities
- Getting trial status for UI display
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.user import User
from models.business_opportunity import BusinessOpportunity


class TrialManager:
    """
    Trial subscription lifecycle management

    Manages the complete lifecycle of trial subscriptions from
    creation through expiration.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_trial_subscription(
        self,
        user: User,
        duration_days: int = 14
    ) -> User:
        """
        Create a trial subscription for a user

        Args:
            user: The user to give trial access
            duration_days: Trial length in days (default: 14)

        Returns:
            Updated user with trial settings
        """
        trial_ends_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

        user.plan_tier = 'trial'
        user.plan_status = 'active'
        user.trial_ends_at = trial_ends_at
        user.registration_plan_choice = 'trial'

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def check_trial_expiry(self, user: User) -> bool:
        """
        Check if a user's trial has expired

        Args:
            user: The user to check

        Returns:
            True if trial is expired, False otherwise
        """
        if user.plan_tier != 'trial' or not user.trial_ends_at:
            return False
        return datetime.now(timezone.utc) > user.trial_ends_at

    async def expire_trial(self, user: User) -> User:
        """
        Process trial expiration

        - Downgrades user to free tier
        - Locks all active opportunities
        - Updates plan status

        Args:
            user: The user whose trial is expiring

        Returns:
            Updated user
        """
        # Downgrade user
        user.plan_tier = 'free'
        user.plan_status = 'trial_ended'

        # Lock all active opportunities
        await self._lock_user_opportunities(user.id)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def _lock_user_opportunities(self, user_id: str):
        """
        Lock all non-archived opportunities for a user

        Args:
            user_id: The ID of the user
        """
        # Since business_opportunities is a shared table (no user_id column),
        # we need to check the user_interactions JSONB field for ownership
        # For now, we'll use a simpler approach - check if the opportunity
        # is referenced by the user in some way (e.g., saved, managed)

        # Find opportunities that the user has interacted with
        result = await self.db.execute(
            select(BusinessOpportunity).where(
                BusinessOpportunity.status != 'archived'
            )
        )
        opportunities = result.scalars().all()

        now = datetime.now(timezone.utc())
        locked_count = 0

        for opp in opportunities:
            # Check if this opportunity belongs to the user
            # This is a simplified check - in production, you'd have proper
            # user-opportunity relationship tracking
            user_interactions = opp.user_interactions or {}
            if str(user_id) in str(user_interactions):
                opp.is_locked = True
                opp.locked_at = now
                locked_count += 1

        await self.db.commit()

        return locked_count

    async def get_trial_status(self, user: User) -> Dict[str, Any]:
        """
        Get trial status for display in UI

        Returns:
            {
                'is_trial': bool,
                'days_remaining': int | None,
                'trial_ends_at': str | None,
                'is_expired': bool
            }
        """
        if user.plan_tier != 'trial':
            return {
                'is_trial': False,
                'days_remaining': None,
                'trial_ends_at': None,
                'is_expired': False
            }

        if not user.trial_ends_at:
            return {
                'is_trial': True,
                'days_remaining': 0,
                'trial_ends_at': None,
                'is_expired': True
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

    async def get_expiring_trials(self, days_threshold: int = 3) -> list[User]:
        """
        Get users whose trials will expire soon

        Args:
            days_threshold: Days until expiration threshold (default: 3)

        Returns:
            List of users with expiring trials
        """
        threshold_date = datetime.now(timezone.utc) + timedelta(days=days_threshold)

        result = await self.db.execute(
            select(User).where(
                User.plan_tier == 'trial',
                User.trial_ends_at <= threshold_date,
                User.plan_status == 'active'
            )
        )

        return list(result.scalars().all())

    async def get_expired_trials(self) -> list[User]:
        """
        Get users whose trials have expired but not yet processed

        Returns:
            List of users with expired trials
        """
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(User).where(
                User.plan_tier == 'trial',
                User.trial_ends_at <= now,
                User.plan_status == 'active'
            )
        )

        return list(result.scalars().all())

    async def extend_trial(
        self,
        user: User,
        additional_days: int = 7
    ) -> User:
        """
        Extend a user's trial period

        Args:
            user: The user to extend
            additional_days: Days to add (default: 7)

        Returns:
            Updated user
        """
        if user.plan_tier != 'trial':
            # User is not in trial, convert to trial
            user.plan_tier = 'trial'
            user.plan_status = 'active'
            user.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=additional_days)
        else:
            # Extend existing trial
            if user.trial_ends_at:
                user.trial_ends_at = user.trial_ends_at + timedelta(days=additional_days)
            else:
                user.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=additional_days)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def cancel_trial(self, user: User) -> User:
        """
        Cancel a trial and downgrade to free

        Args:
            user: The user to cancel trial for

        Returns:
            Updated user
        """
        user.plan_tier = 'free'
        user.plan_status = 'canceled'

        # Note: We don't lock opportunities on manual cancellation,
        # only on expiration
        await self.db.commit()
        await self.db.refresh(user)

        return user
