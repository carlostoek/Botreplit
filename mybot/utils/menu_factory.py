"""
Menu factory for creating consistent menus based on user role and state.
Centralizes menu creation logic for better maintainability.
"""
from typing import Tuple, Optional
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from utils.user_roles import get_user_role
from keyboards.admin_main_kb import get_admin_main_kb
from keyboards.vip_main_kb import get_vip_main_kb
from keyboards.subscription_kb import get_subscription_kb
from keyboards.setup_kb import get_setup_main_kb, get_setup_channels_kb, get_setup_complete_kb
from database.models import User
import logging

logger = logging.getLogger(__name__)

class MenuFactory:
    """
    Factory class for creating menus based on user state and role.
    Centralizes menu logic and ensures consistency.
    """
    
    async def create_menu(
        self, 
        menu_state: str, 
        user_id: int, 
        session: AsyncSession,
        bot=None
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create a menu based on the current state and user role.
        
        Returns:
            Tuple[str, InlineKeyboardMarkup]: (text, keyboard)
        """
        try:
            # Get user role if bot is available
            if bot:
                role = await get_user_role(bot, user_id, session=session)
            else:
                # Fallback to database role check
                user = await session.get(User, user_id)
                role = user.role if user else "free"
            
            # Handle setup flow for new installations
            if menu_state.startswith("setup_"):
                return await self._create_setup_menu(menu_state, user_id, session)
            
            # Handle role-based main menus
            if menu_state in ["main", "admin_main", "vip_main", "free_main"]:
                return self._create_main_menu(role)
            
            # Handle specific menu states
            return await self._create_specific_menu(menu_state, user_id, session, role)
            
        except Exception as e:
            logger.error(f"Error creating menu for state {menu_state}, user {user_id}: {e}")
            # Fallback to basic menu
            return self._create_fallback_menu()
    
    def _create_main_menu(self, role: str) -> Tuple[str, InlineKeyboardMarkup]:
        """Create the main menu based on user role."""
        if role == "admin":
            return (
                "🛠️ **Panel de Administración**\n\n"
                "Bienvenido al centro de control del bot. Desde aquí puedes gestionar "
                "todos los aspectos del sistema.",
                get_admin_main_kb()
            )
        elif role == "vip":
            return (
                "✨ **Bienvenido al Diván de Diana**\n\n"
                "Tu suscripción VIP te da acceso completo a todas las funciones. "
                "¡Disfruta de la experiencia premium!",
                get_vip_main_kb()
            )
        else:
            return (
                "🌟 **Bienvenido a los Kinkys**\n\n"
                "Explora nuestro contenido gratuito y descubre todo lo que tenemos para ti. "
                "¿Listo para una experiencia única?",
                get_subscription_kb()
            )
    
    async def _create_setup_menu(
        self, 
        menu_state: str, 
        user_id: int, 
        session: AsyncSession
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """Create setup menus for initial bot configuration."""
        if menu_state == "setup_main":
            return (
                "🚀 **Configuración Inicial**\n\n"
                "¡Bienvenido! Vamos a configurar tu bot paso a paso.\n"
                "Este proceso te ayudará a establecer los canales y configuraciones básicas.",
                get_setup_main_kb()
            )
        elif menu_state == "setup_channels":
            return (
                "📢 **Configurar Canales**\n\n"
                "Configura tus canales VIP y gratuito. Puedes hacerlo ahora o más tarde "
                "desde el panel de administración.",
                get_setup_channels_kb()
            )
        elif menu_state == "setup_complete":
            return (
                "✅ **Configuración Completada**\n\n"
                "¡Perfecto! Tu bot está listo para usar. Puedes acceder al panel de "
                "administración en cualquier momento.",
                get_setup_complete_kb()
            )
        else:
            return self._create_fallback_menu()
    
    async def _create_specific_menu(
        self, 
        menu_state: str, 
        user_id: int, 
        session: AsyncSession, 
        role: str
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """Create specific menus based on state."""
        # Import specific menu creators here to avoid circular imports
        from utils.menu_creators import (
            create_profile_menu,
            create_missions_menu,
            create_rewards_menu,
            create_auction_menu,
            create_ranking_menu
        )
        
        if menu_state == "profile":
            return await create_profile_menu(user_id, session)
        elif menu_state == "missions":
            return await create_missions_menu(user_id, session)
        elif menu_state == "rewards":
            return await create_rewards_menu(user_id, session)
        elif menu_state == "auctions":
            return await create_auction_menu(user_id, session)
        elif menu_state == "ranking":
            return await create_ranking_menu(user_id, session)
        else:
            # Fallback to main menu for unknown states
            return self._create_main_menu(role)
    
    def _create_fallback_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Create a fallback menu when something goes wrong."""
        return (
            "⚠️ **Error de Navegación**\n\n"
            "Hubo un problema al cargar el menú. Por favor, intenta nuevamente.",
            get_subscription_kb()  # Safe fallback
        )

# Global factory instance
menu_factory = MenuFactory()