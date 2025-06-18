"""
Enhanced admin menu with improved navigation and multi-tenant support.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.admin_main_kb import get_admin_main_kb
from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory
from services.tenant_service import TenantService
from services import get_admin_statistics
from database.models import Tariff, Token
from uuid import uuid4
from sqlalchemy import select
from utils.messages import BOT_MESSAGES
import logging

logger = logging.getLogger(__name__)
router = Router()

# Include all sub-routers
from .vip_menu import router as vip_router
from .free_menu import router as free_router
from .config_menu import router as config_router
from .channel_admin import router as channel_admin_router
from .subscription_plans import router as subscription_plans_router
from .game_admin import router as game_admin_router
from .event_admin import router as event_admin_router

router.include_router(vip_router)
router.include_router(free_router)
router.include_router(config_router)
router.include_router(channel_admin_router)
router.include_router(subscription_plans_router)
router.include_router(game_admin_router)
router.include_router(event_admin_router)

@router.message(CommandStart())
async def admin_start(message: Message, session: AsyncSession):
    """Enhanced admin start with setup detection."""
    if not is_admin(message.from_user.id):
        return
    
    # Check if this admin needs setup
    tenant_service = TenantService(session)
    tenant_status = await tenant_service.get_tenant_status(message.from_user.id)
    
    if not tenant_status["basic_setup_complete"]:
        # Redirect to setup
        from handlers.setup import start_setup
        await start_setup(message, session)
        return
    
    # Show admin panel
    text, keyboard = await menu_factory.create_menu("admin_main", message.from_user.id, session, message.bot)
    await menu_manager.show_menu(message, text, keyboard, session, "admin_main")

@router.message(Command("admin_menu"))
async def admin_menu(message: Message, session: AsyncSession):
    """Enhanced admin menu command."""
    if not is_admin(message.from_user.id):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return
    
    try:
        text, keyboard = await menu_factory.create_menu("admin_main", message.from_user.id, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "admin_main")
    except Exception as e:
        logger.error(f"Error showing admin menu for user {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar el panel de administración.",
            auto_delete_seconds=5
        )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, session: AsyncSession):
    """Enhanced admin statistics with better formatting."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        stats = await get_admin_statistics(session)
        
        # Get additional tenant-specific stats
        tenant_service = TenantService(session)
        tenant_summary = await tenant_service.get_tenant_summary(callback.from_user.id)
        
        text_lines = [
            "📊 **Estadísticas del Sistema**",
            "",
            "👥 **Usuarios**",
            f"• Total: {stats['users_total']}",
            f"• Suscripciones totales: {stats['subscriptions_total']}",
            f"• Activas: {stats['subscriptions_active']}",
            f"• Expiradas: {stats['subscriptions_expired']}",
            "",
            "💰 **Ingresos**",
            f"• Total recaudado: ${stats.get('revenue_total', 0)}",
            "",
            "⚙️ **Configuración**"
        ]
        
        if "error" not in tenant_summary:
            channels = tenant_summary.get("channels", {})
            text_lines.extend([
                f"• Canal VIP: {'✅' if channels.get('vip_channel_id') else '❌'}",
                f"• Canal Gratuito: {'✅' if channels.get('free_channel_id') else '❌'}",
                f"• Tarifas configuradas: {tenant_summary.get('tariff_count', 0)}"
            ])
        
        from keyboards.common import get_back_kb
        await menu_manager.update_menu(
            callback,
            "\n".join(text_lines),
            get_back_kb("admin_main_menu"),
            session,
            "admin_stats",
        )
    except Exception as e:
        logger.error(f"Error showing admin stats: {e}")
        await callback.answer("Error al cargar estadísticas", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, session: AsyncSession):
    """Enhanced back navigation for admin."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Use menu manager's back functionality
        success = await menu_manager.go_back(callback, session, "admin_main")
        if not success:
            # Fallback to main admin menu
            text, keyboard = await menu_factory.create_menu("admin_main", callback.from_user.id, session, callback.bot)
            await menu_manager.update_menu(callback, text, keyboard, session, "admin_main")
    except Exception as e:
        logger.error(f"Error in admin back navigation: {e}")
        await callback.answer("Error en la navegación", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_main_menu")
async def back_to_admin_main(callback: CallbackQuery, session: AsyncSession):
    """Return to main admin menu."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        text, keyboard = await menu_factory.create_menu("admin_main", callback.from_user.id, session, callback.bot)
        await menu_manager.update_menu(callback, text, keyboard, session, "admin_main")
    except Exception as e:
        logger.error(f"Error returning to admin main: {e}")
        await callback.answer("Error al cargar el menú principal", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_manage_content")
async def admin_manage_content(callback: CallbackQuery, session: AsyncSession):
    """Enhanced content management menu."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        from utils.keyboard_utils import get_admin_manage_content_keyboard
        
        await menu_manager.update_menu(
            callback,
            "🎮 **Gestión de Contenido y Gamificación**\n\n"
            "Administra todos los aspectos del sistema de juego y engagement:\n\n"
            "• 👥 Gestión de usuarios y puntos\n"
            "• 🎯 Misiones y desafíos\n"
            "• 🏅 Sistema de insignias\n"
            "• 🎁 Catálogo de recompensas\n"
            "• 🏛️ Subastas en tiempo real\n"
            "• 🎉 Eventos especiales",
            get_admin_manage_content_keyboard(),
            session,
            "admin_manage_content",
        )
    except Exception as e:
        logger.error(f"Error showing content management: {e}")
        await callback.answer("Error al cargar la gestión de contenido", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_bot_config")
async def admin_bot_config(callback: CallbackQuery, session: AsyncSession):
    """Enhanced bot configuration menu."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        from keyboards.common import get_back_kb
        
        # Get current configuration status
        tenant_service = TenantService(session)
        tenant_summary = await tenant_service.get_tenant_summary(callback.from_user.id)
        
        config_text = "⚙️ **Configuración del Bot**\n\n"
        
        if "error" not in tenant_summary:
            status = tenant_summary["configuration_status"]
            config_text += "**Estado actual:**\n"
            config_text += f"📢 Canales: {'✅ Configurados' if status['channels_configured'] else '❌ Pendiente'}\n"
            config_text += f"💳 Tarifas: {'✅ Configuradas' if status['tariffs_configured'] else '❌ Pendiente'}\n"
            config_text += f"🎮 Gamificación: {'✅ Configurada' if status['gamification_configured'] else '❌ Pendiente'}\n\n"
            
            if not status["basic_setup_complete"]:
                config_text += "⚠️ **Configuración incompleta**\nAlgunas funciones pueden no estar disponibles."
            else:
                config_text += "✅ **Bot completamente configurado**\nTodas las funciones están disponibles."
        else:
            config_text += "❌ Error al cargar el estado de configuración."
        
        await menu_manager.update_menu(
            callback,
            config_text,
            get_back_kb("admin_main_menu"),
            session,
            "admin_bot_config",
        )
    except Exception as e:
        logger.error(f"Error showing bot config: {e}")
        await callback.answer("Error al cargar la configuración", show_alert=True)
    
    await callback.answer()

# Enhanced token generation with better UX
@router.message(Command("admin_generate_token"))
async def admin_generate_token_cmd(message: Message, session: AsyncSession, bot: Bot):
    """Enhanced token generation command."""
    if not is_admin(message.from_user.id):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return
    
    try:
        result = await session.execute(select(Tariff))
        tariffs = result.scalars().all()
        
        if not tariffs:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Sin Tarifas Configuradas**\n\n"
                "Primero debes configurar las tarifas VIP desde el panel de administración.",
                auto_delete_seconds=8
            )
            return
        
        from keyboards.admin_vip_config_kb import get_tariff_select_kb
        
        await menu_manager.show_menu(
            message,
            "💳 **Generar Token VIP**\n\n"
            "Selecciona la tarifa para la cual quieres generar un token de activación:",
            get_tariff_select_kb(tariffs),
            session,
            "admin_generate_token"
        )
    except Exception as e:
        logger.error(f"Error in token generation command: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar las tarifas.",
            auto_delete_seconds=5
        )

@router.callback_query(F.data.startswith("generate_token_"))
async def generate_token_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Enhanced token generation with better feedback."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        tariff_id = int(callback.data.split("_")[-1])
        tariff = await session.get(Tariff, tariff_id)
        
        if not tariff:
            await callback.answer("Tarifa no encontrada", show_alert=True)
            return
        
        # Generate token
        token_string = str(uuid4())
        token = Token(token_string=token_string, tariff_id=tariff_id)
        session.add(token)
        await session.commit()
        
        # Create activation link
        bot_username = (await bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={token_string}"
        
        from keyboards.common import get_back_kb
        
        success_text = (
            f"✅ **Token VIP Generado**\n\n"
            f"📋 **Tarifa:** {tariff.name}\n"
            f"⏱️ **Duración:** {tariff.duration_days} días\n"
            f"💰 **Precio:** ${tariff.price}\n\n"
            f"🔗 **Enlace de activación:**\n"
            f"`{link}`\n\n"
            f"⚠️ **Importante:** Este enlace es de un solo uso. "
            f"Compártelo directamente con el cliente."
        )
        
        await menu_manager.update_menu(
            callback,
            success_text,
            get_back_kb("admin_vip"),
            session,
            "token_generated"
        )
        
        logger.info(f"Admin {callback.from_user.id} generated token for tariff {tariff.name}")
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        await callback.answer("Error al generar el token", show_alert=True)
    
    await callback.answer()