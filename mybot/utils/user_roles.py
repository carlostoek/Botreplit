from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .config import ADMIN_IDS, VIP_CHANNEL_ID
from database.models import User, VipSubscription
import os
import time
from typing import Dict, Tuple
from datetime import datetime

DEFAULT_VIP_MULTIPLIER = int(os.environ.get("VIP_POINTS_MULTIPLIER", "2"))

# Cache user roles for a short time to avoid repeated API calls
_ROLE_CACHE: Dict[int, Tuple[str, float]] = {}


def is_admin(user_id: int) -> bool:
    """Check if the user is an admin."""
    return user_id in ADMIN_IDS


async def is_vip_member(bot: Bot, user_id: int, session: AsyncSession | None = None) -> bool:
    """Check if the user should be considered a VIP."""
    from services.config_service import ConfigService

    # First check database subscription status
    if session:
        try:
            # Check if user has active VIP subscription in database
            user = await session.get(User, user_id)
            if user and user.role == "vip":
                # Check if subscription is still valid
                if user.vip_expires_at is None or user.vip_expires_at > datetime.utcnow():
                    return True
            
            # Also check VipSubscription table
            stmt = select(VipSubscription).where(VipSubscription.user_id == user_id)
            result = await session.execute(stmt)
            subscription = result.scalar_one_or_none()
            if subscription:
                if subscription.expires_at is None or subscription.expires_at > datetime.utcnow():
                    return True
        except Exception as e:
            print(f"Error checking VIP status in database: {e}")

    # Fallback to channel membership check
    vip_channel_id = VIP_CHANNEL_ID
    if session:
        try:
            config_service = ConfigService(session)
            stored_vip_id = await config_service.get_vip_channel_id()
            if stored_vip_id is not None:
                vip_channel_id = stored_vip_id
        except Exception as e:
            print(f"Error getting VIP channel ID from config: {e}")

    if not vip_channel_id:
        return False

    try:
        member = await bot.get_chat_member(vip_channel_id, user_id)
        return member.status in {"member", "administrator", "creator"}
    except Exception as e:
        print(f"Error checking channel membership for user {user_id}: {e}")
        return False


async def get_points_multiplier(bot: Bot, user_id: int, session: AsyncSession | None = None) -> int:
    """Return VIP multiplier for the user."""
    if await is_vip_member(bot, user_id, session=session):
        return DEFAULT_VIP_MULTIPLIER
    return 1


# Backwards compatibility
is_vip = is_vip_member


async def get_user_role(
    bot: Bot, user_id: int, session: AsyncSession | None = None
) -> str:
    """Return the role for the given user (admin, vip or free)."""
    now = time.time()
    cached = _ROLE_CACHE.get(user_id)
    
    # Use cache only for non-admin users and only for 2 minutes
    if cached and now < cached[1] and not is_admin(user_id):
        return cached[0]

    # Check admin first (highest priority)
    if is_admin(user_id):
        role = "admin"
        _ROLE_CACHE[user_id] = (role, now + 120)  # cache for 2 minutes
        return role
    
    # Check VIP status
    try:
        if await is_vip_member(bot, user_id, session=session):
            role = "vip"
        else:
            role = "free"
    except Exception as e:
        print(f"Error determining user role for {user_id}: {e}")
        role = "free"

    _ROLE_CACHE[user_id] = (role, now + 120)  # cache for 2 minutes
    return role


def clear_role_cache(user_id: int = None):
    """Clear role cache for a specific user or all users."""
    if user_id:
        _ROLE_CACHE.pop(user_id, None)
    else:
        _ROLE_CACHE.clear()