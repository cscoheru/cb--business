#!/usr/bin/env python3
"""
API Key Generator Utility

Generate API keys for third-party developers.

Usage:
    python scripts/generate_api_key.py --user-id <uuid> --tier developer --name "My App"

    # Or interactive mode
    python scripts/generate_api_key.py
"""

import argparse
import hashlib
import secrets
import uuid
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from config.database import async_session_factory
from models.user import User
from models.api_key import APIKey, APIUsage, APITier, TIER_LIMITS


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        (full_key, key_hash, key_prefix)
    """
    # Generate random hex string
    key_hex = secrets.token_hex(24)  # 48 hex chars
    full_key = f"cb_live_{key_hex}"

    # Hash for storage (SHA256)
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    # Prefix for display (first 12 chars)
    key_prefix = full_key[:12]

    return full_key, key_hash, key_prefix


async def create_api_key(
    user_id: uuid.UUID,
    name: str,
    tier: str = "developer"
) -> tuple[str, APIKey]:
    """
    Create an API key for a user.

    Args:
        user_id: User UUID
        name: Key name (e.g., "Production Key")
        tier: Subscription tier (developer, business, enterprise)

    Returns:
        (full_key, APIKey object)
    """
    full_key, key_hash, key_prefix = generate_api_key()

    # Get tier limits - handle both string key and class attribute key
    tier_limits = TIER_LIMITS.get(tier) or TIER_LIMITS.get(APITier.DEVELOPER)
    if tier_limits is None:
        tier_limits = TIER_LIMITS[APITier.DEVELOPER]

    async with async_session_factory() as db:
        # Verify user exists
        user = await db.get(User, user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Create API key
        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            tier=tier,
            is_active=True,
            rate_limit_per_minute=tier_limits["rate_limit_per_minute"],
            rate_limit_per_day=tier_limits["rate_limit_per_day"]
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        return full_key, api_key


async def list_user_api_keys(user_id: uuid.UUID) -> list[dict]:
    """List all API keys for a user."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(APIKey).where(APIKey.user_id == user_id)
        )
        keys = result.scalars().all()
        return [k.to_dict() for k in keys]


async def interactive_mode():
    """Interactive key generation."""
    print("=" * 60)
    print("API Key Generator")
    print("=" * 60)

    async with async_session_factory() as db:
        # List users
        result = await db.execute(select(User.id, User.email, User.name))
        users = result.all()

        if not users:
            print("No users found in database.")
            return

        print("\nAvailable users:")
        for i, (uid, email, name) in enumerate(users, 1):
            print(f"  {i}. {email} ({name}) - {uid}")

        # Select user
        choice = input("\nSelect user (number): ")
        try:
            idx = int(choice) - 1
            user_id = users[idx][0]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

        # Get key name
        name = input("Key name (e.g., 'Production Key'): ").strip()
        if not name:
            name = "API Key"

        # Select tier
        print("\nAvailable tiers:")
        tiers = [
            ("developer", 1, 299, 1000),
            ("business", 2, 999, 10000),
            ("enterprise", 3, 2999, 100000),
        ]
        for tier, num, price, limit in tiers:
            print(f"  {num}. {tier}: ¥{price}/mo - {limit} requests/day")

        tier_choice = input("Select tier (1-3, default=1): ").strip()
        tier_map = {"1": "developer", "2": "business", "3": "enterprise"}
        tier = tier_map.get(tier_choice, "developer")

        # Generate key
        print(f"\nGenerating {tier} tier key for {users[idx][1]}...")

        full_key, api_key = await create_api_key(user_id, name, tier)

        print("\n" + "=" * 60)
        print("✅ API Key Created Successfully!")
        print("=" * 60)
        print(f"\n  Key ID: {api_key.id}")
        print(f"  Name: {api_key.name}")
        print(f"  Tier: {api_key.tier}")
        print(f"  Rate Limits: {api_key.rate_limit_per_minute}/min, {api_key.rate_limit_per_day}/day")
        print("\n  🔑 API Key (save this - won't be shown again):")
        print(f"  {full_key}")
        print("\n" + "=" * 60)
        print("\nUsage:")
        print(f'  curl -H "X-API-Key: {full_key}" https://api.zenconsult.top/api/v1/public/cpi/weights')
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generate API Keys")
    parser.add_argument("--user-id", type=str, help="User UUID")
    parser.add_argument("--email", type=str, help="User email (alternative to user-id)")
    parser.add_argument("--tier", choices=["developer", "business", "enterprise"],
                        default="developer", help="Subscription tier")
    parser.add_argument("--name", type=str, default="API Key", help="Key name")
    parser.add_argument("--list", action="store_true", help="List user's API keys")

    args = parser.parse_args()

    if args.list and (args.user_id or args.email):
        # List mode
        async def list_keys():
            async with async_session_factory() as db:
                if args.email:
                    result = await db.execute(
                        select(User).where(User.email == args.email)
                    )
                    user = result.scalar_one_or_none()
                    if not user:
                        print(f"User not found: {args.email}")
                        return
                    user_id = user.id
                else:
                    user_id = uuid.UUID(args.user_id)

            keys = await list_user_api_keys(user_id)
            print(f"\nAPI Keys for {user_id}:")
            for k in keys:
                status = "✅ Active" if k["is_active"] else "❌ Inactive"
                print(f"  {k['key_prefix']}... - {k['name']} ({k['tier']}) {status}")

        asyncio.run(list_keys())

    elif args.user_id or args.email:
        # Generate mode
        async def generate():
            async with async_session_factory() as db:
                if args.email:
                    result = await db.execute(
                        select(User).where(User.email == args.email)
                    )
                    user = result.scalar_one_or_none()
                    if not user:
                        print(f"User not found: {args.email}")
                        return
                    user_id = user.id
                else:
                    user_id = uuid.UUID(args.user_id)

            full_key, api_key = await create_api_key(user_id, args.name, args.tier)

            print(f"\n✅ API Key Created")
            print(f"  ID: {api_key.id}")
            print(f"  Key: {full_key}")
            print(f"  Tier: {api_key.tier}")
            print(f"  Limits: {api_key.rate_limit_per_minute}/min, {api_key.rate_limit_per_day}/day")

        asyncio.run(generate())

    else:
        # Interactive mode
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
