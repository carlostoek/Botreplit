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
from keyboards.subscription_kb import get_free_main_menu_kb
from keyboards.setup_kb import (
    get_setup_main_kb,
    get_setup_channels_kb,
    get_setup_complete_kb,
    get_setup_gamification_kb,
    get_setup_tariffs_kb,
    get_setup_confirmation_kb,
)
from database.models import User
import logging

from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.menu_creators import (
    create_profile_menu,
    create_missions_menu,
    create_rewards_menu,
    create_auction_menu,
    create_ranking_menu
)
from utils.text_utils import sanitize_text

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
            role = await get_user_role(bot, user_id, session=session)

            if menu_state.startswith("setup_") or menu_state == "admin_setup_choice":
                return await self._create_setup_menu(menu_state, user_id, session)

            if menu_state in ["main", "admin_main", "vip_main", "free_main"]:
                return self._create_main_menu(role)

            return await self._create_specific_menu(menu_state, user_id, session, role)

        except Exception as e:
            logger.error(f"Error creating menu for state {menu_state}, user {user_id}: {e}")
            return self._create_fallback_menu(role)

    def _create_main_menu(self, role: str) -> Tuple[str, InlineKeyboardMarkup]:
        """Create the main menu based on user role."""
        if role == "admin":
            return (
                "🛠️ **Centro de Mando**\n\n"
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
                get_free_main_menu_kb()
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
                "🚀 **Bienvenido a la Configuración Inicial**\n\n"
                "¡Hola! Vamos a configurar tu bot paso a paso para que esté listo "
                "para tus usuarios. Este proceso es rápido y fácil.\n\n"
                "**¿Qué vamos a configurar?**\n"
                "• 📢 Canales (VIP y/o Gratuito)\n"
                "• 💳 Tarifas de suscripción\n"
                "• 🎮 Sistema de gamificación\n\n"
                "¡Empecemos!",
                get_setup_main_kb()
            )
        elif menu_state == "setup_channels":
            return (
                "📢 **Configuración de Canales**\n\n"
                "Los canales son el corazón de tu bot. Puedes configurar:\n\n"
                "🔐 **Canal VIP**: Para suscriptores premium\n"
                "🆓 **Canal Gratuito**: Para usuarios sin suscripción\n\n"
                "**Recomendación**: Configura al menos un canal para empezar. "
                "Puedes agregar más canales después desde el panel de administración.",
                get_setup_channels_kb()
            )
        elif menu_state == "setup_complete":
            return (
                "✅ **Configuración Completada**\n\n"
                "¡Perfecto! Tu bot está listo para usar. Puedes acceder al panel de "
                "administración en cualquier momento.",
                get_setup_complete_kb()
            )
        elif menu_state == "admin_setup_choice":
            return self.create_setup_choice_menu()
        elif menu_state == "setup_vip_channel_prompt":
            return (
                "🔐 **Configurar Canal VIP**\n\n"
                "Para configurar tu canal VIP, reenvía cualquier mensaje de tu canal aquí. "
                "El bot detectará automáticamente el ID del canal.\n\n"
                "**Importante**: Asegúrate de que el bot sea administrador del canal "
                "con permisos para invitar usuarios.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_free_channel_prompt":
            return (
                "🆓 **Configurar Canal Gratuito**\n\n"
                "Para configurar tu canal gratuito, reenvía cualquier mensaje de tu canal aquí. "
                "El bot detectará automáticamente el ID del canal.\n\n"
                "**Importante**: Asegúrate de que el bot sea administrador del canal "
                "con permisos para aprobar solicitudes de unión.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_manual_channel_id_prompt":
            return (
                "📝 **Ingresa el ID del Canal Manualmente**\n\n"
                "Por favor, ingresa el ID numérico de tu canal. Normalmente empieza con `-100`.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_gamification":
            return (
                "🎮 **Configuración de Gamificación**\n\n"
                "El sistema de gamificación mantiene a tus usuarios comprometidos con:\n\n"
                "🎯 **Misiones**: Tareas que los usuarios pueden completar\n"
                "🏅 **Insignias**: Reconocimientos por logros\n"
                "🎁 **Recompensas**: Premios por acumular puntos\n"
                "📊 **Niveles**: Sistema de progresión\n\n"
                "**Recomendación**: Usa la configuración por defecto para empezar rápido.",
                get_setup_gamification_kb()
            )
        elif menu_state == "setup_tariffs":
            return (
                "💳 **Configuración de Tarifas VIP**\n\n"
                "Las tarifas determinan los precios y duración de las suscripciones VIP.\n\n"
                "**Opciones disponibles**:\n"
                "💎 **Básica**: Tarifa estándar de 30 días\n"
                "👑 **Premium**: Tarifa de 90 días con descuento\n"
                "🎯 **Personalizada**: Crea tus propias tarifas\n\n"
                "**Recomendación**: Empieza con las tarifas básica y premium.",
                get_setup_tariffs_kb()
            )
        elif menu_state in ["setup_missions_info", "setup_badges_info", "setup_rewards_info", "setup_levels_info"]:
            feature_name = menu_state.replace('_info', '').replace('setup_', '').replace('_', ' ').capitalize()
            return (
                f"ℹ️ **Información sobre {feature_name}**\n\n"
                "Aquí puedes configurar los aspectos clave del sistema de gamificación. "
                "Cada elemento tiene un impacto directo en la experiencia del usuario.",
                get_setup_confirmation_kb("back_to_gamification_setup")
            )
        else:
            return (
                "⚙️ **Configuración No Reconocida**\n\n"
                "El estado de configuración solicitado no es válido.",
                get_setup_confirmation_kb("cancel_setup")
            )


# MyBot no es módulo, es la raíz del proyecto
menu_factory = MenuFactory()
