from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from .config import ADMIN_IDS, VIP_CHANNEL_ID
import os
import time
from typing import Dict, Tuple

DEFAULT_VIP_MULTIPLIER = int(os.environ.get("VIP_POINTS_MULTIPLIER", "2"))

# Cache user roles for a short time to avoid repeated API calls
_ROLE_CACHE: Dict[int, Tuple[str, float]] = {}


def is_admin(user_id: int) -> bool:
    """Check if the user is an admin."""
    return user_id in ADMIN_IDS


async def is_vip_member(bot: Bot, user_id: int, session: AsyncSession | None = None) -> bool:
    """Check if the user should be considered a VIP."""
    from services.config_service import ConfigService

    vip_channel_id = VIP_CHANNEL_ID

    if session:
        # Check stored VIP channel configuration
        value = await ConfigService(session).get_vip_channel_id()
        if value is not None:
            vip_channel_id = value



    if not vip_channel_id:
        return False

    try:
        member = await bot.get_chat_member(vip_channel_id, user_id)
        return member.status in {"member", "administrator", "creator"}
    except Exception:
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
    if cached and now < cached[1]:
        return cached[0]

    if is_admin(user_id):
        role = "admin"
    elif await is_vip_member(bot, user_id, session=session):
        role = "vip"
    else:
        role = "free"

    _ROLE_CACHE[user_id] = (role, now + 600)  # cache for 10 minutes
    return role
