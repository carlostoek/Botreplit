from .admin_menu import router as admin_router
from .vip_menu import router as vip_router
from .free_menu import router as free_router
from .config_menu import router as config_router
from .channel_admin import router as channel_admin_router
from .subscription_plans import router as subscription_plans_router
from .game_admin import router as game_admin_router
from .missions_admin import router as missions_admin_router
from .levels_admin import router as levels_admin_router
from .rewards_admin import router as rewards_admin_router
from .badges_admin import router as badges_admin_router
from .event_admin import router as event_admin_router
from .admin_config import router as admin_config_router

__all__ = [
    "admin_router",
    "vip_router",
    "free_router",
    "config_router",
    "channel_admin_router",
    "subscription_plans_router",
    "game_admin_router",
    "missions_admin_router",
    "levels_admin_router",
    "rewards_admin_router",
    "badges_admin_router",
    "event_admin_router",
    "admin_config_router",
]
