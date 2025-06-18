"""
Setup handlers for multi-tenant bot configuration.
Guides new admins through the initial setup process.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from services.tenant_service import TenantService
from keyboards.setup_kb import (
    get_setup_main_kb,
    get_setup_channels_kb,
    get_setup_gamification_kb,
    get_setup_tariffs_kb,
    get_setup_complete_kb,
    get_channel_detection_kb,
    get_setup_confirmation_kb
)
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)
router = Router()

class SetupStates(StatesGroup):
    """States for the setup flow."""
    waiting_for_vip_channel = State()
    waiting_for_free_channel = State()
    waiting_for_channel_confirmation = State()
    waiting_for_manual_channel_id = State()
    configuring_tariffs = State()
    configuring_gamification = State()

@router.message(Command("setup"))
async def start_setup(message: Message, session: AsyncSession):
    """Start the initial setup process for new admins."""
    if not is_admin(message.from_user.id):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden acceder a la configuración inicial.",
            auto_delete_seconds=5
        )
        return
    
    tenant_service = TenantService(session)
    init_result = await tenant_service.initialize_tenant(message.from_user.id)
    
    if not init_result["success"]:
        await menu_manager.send_temporary_message(
            message,
            f"❌ **Error de Inicialización**\n\n{init_result['error']}",
            auto_delete_seconds=10
        )
        return
    
    status = init_result["status"]
    
    if status["basic_setup_complete"]:
        await menu_manager.show_menu(
            message,
            "✅ **Configuración Completada**\n\n"
            "Tu bot ya está configurado y listo para usar. Puedes acceder al "
            "panel de administración o realizar configuraciones adicionales.",
            get_setup_complete_kb(),
            session,
            "setup_complete"
        )
    else:
        await menu_manager.show_menu(
            message,
            "🚀 **Bienvenido a la Configuración Inicial**\n\n"
            "¡Hola! Vamos a configurar tu bot paso a paso para que esté listo "
            "para tus usuarios. Este proceso es rápido y fácil.\n\n"
            "**¿Qué vamos a configurar?**\n"
            "• 📢 Canales (VIP y/o Gratuito)\n"
            "• 💳 Tarifas de suscripción\n"
            "• 🎮 Sistema de gamificación\n\n"
            "¡Empecemos!",
            get_setup_main_kb(),
            session,
            "setup_main"
        )

@router.callback_query(F.data == "setup_channels")
async def setup_channels_menu(callback: CallbackQuery, session: AsyncSession):
    """Show channel configuration options."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "📢 **Configuración de Canales**\n\n"
        "Los canales son el corazón de tu bot. Puedes configurar:\n\n"
        "🔐 **Canal VIP**: Para suscriptores premium\n"
        "🆓 **Canal Gratuito**: Para usuarios sin suscripción\n\n"
        "**Recomendación**: Configura al menos un canal para empezar. "
        "Puedes agregar más canales después desde el panel de administración.",
        get_setup_channels_kb(),
        session,
        "setup_channels"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_vip_channel")
async def setup_vip_channel(callback: CallbackQuery, state: FSMContext):
    """Start VIP channel configuration."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await callback.message.edit_text(
        "🔐 **Configurar Canal VIP**\n\n"
        "Para configurar tu canal VIP, reenvía cualquier mensaje de tu canal aquí. "
        "El bot detectará automáticamente el ID del canal.\n\n"
        "**Importante**: Asegúrate de que el bot sea administrador del canal "
        "con permisos para invitar usuarios.",
        reply_markup=get_setup_confirmation_kb("cancel_channel_setup")
    )
    
    await state.set_state(SetupStates.waiting_for_vip_channel)
    await callback.answer()

@router.callback_query(F.data == "setup_free_channel")
async def setup_free_channel(callback: CallbackQuery, state: FSMContext):
    """Start free channel configuration."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await callback.message.edit_text(
        "🆓 **Configurar Canal Gratuito**\n\n"
        "Para configurar tu canal gratuito, reenvía cualquier mensaje de tu canal aquí. "
        "El bot detectará automáticamente el ID del canal.\n\n"
        "**Importante**: Asegúrate de que el bot sea administrador del canal "
        "con permisos para aprobar solicitudes de unión.",
        reply_markup=get_setup_confirmation_kb("cancel_channel_setup")
    )
    
    await state.set_state(SetupStates.waiting_for_free_channel)
    await callback.answer()

@router.message(SetupStates.waiting_for_vip_channel)
async def process_vip_channel(message: Message, state: FSMContext, session: AsyncSession):
    """Process VIP channel configuration."""
    if not is_admin(message.from_user.id):
        return
    
    channel_id = None
    channel_title = None
    
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title
    else:
        try:
            channel_id = int(message.text.strip())
        except ValueError:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nPor favor, reenvía un mensaje del canal o ingresa un ID válido.",
                auto_delete_seconds=5
            )
            return
    
    # Store channel info for confirmation
    await state.update_data(
        channel_type="vip",
        channel_id=channel_id,
        channel_title=channel_title
    )
    
    title_text = f" ({channel_title})" if channel_title else ""
    
    await message.answer(
        f"✅ **Canal VIP Detectado**\n\n"
        f"**ID del Canal**: `{channel_id}`{title_text}\n\n"
        f"¿Es este el canal correcto?",
        reply_markup=get_channel_detection_kb()
    )
    
    await state.set_state(SetupStates.waiting_for_channel_confirmation)

@router.message(SetupStates.waiting_for_free_channel)
async def process_free_channel(message: Message, state: FSMContext, session: AsyncSession):
    """Process free channel configuration."""
    if not is_admin(message.from_user.id):
        return
    
    channel_id = None
    channel_title = None
    
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title
    else:
        try:
            channel_id = int(message.text.strip())
        except ValueError:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nPor favor, reenvía un mensaje del canal o ingresa un ID válido.",
                auto_delete_seconds=5
            )
            return
    
    # Store channel info for confirmation
    await state.update_data(
        channel_type="free",
        channel_id=channel_id,
        channel_title=channel_title
    )
    
    title_text = f" ({channel_title})" if channel_title else ""
    
    await message.answer(
        f"✅ **Canal Gratuito Detectado**\n\n"
        f"**ID del Canal**: `{channel_id}`{title_text}\n\n"
        f"¿Es este el canal correcto?",
        reply_markup=get_channel_detection_kb()
    )
    
    await state.set_state(SetupStates.waiting_for_channel_confirmation)

@router.callback_query(F.data == "confirm_channel")
async def confirm_channel_setup(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirm and save channel configuration."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    data = await state.get_data()
    channel_type = data.get("channel_type")
    channel_id = data.get("channel_id")
    channel_title = data.get("channel_title")
    
    if not channel_id:
        await callback.answer("Error: No se encontró información del canal", show_alert=True)
        return
    
    tenant_service = TenantService(session)
    
    # Configure the channel
    if channel_type == "vip":
        result = await tenant_service.configure_channels(
            callback.from_user.id,
            vip_channel_id=channel_id,
            channel_titles={"vip": channel_title} if channel_title else None
        )
    else:
        result = await tenant_service.configure_channels(
            callback.from_user.id,
            free_channel_id=channel_id,
            channel_titles={"free": channel_title} if channel_title else None
        )
    
    if result["success"]:
        channel_name = "VIP" if channel_type == "vip" else "Gratuito"
        await menu_manager.update_menu(
            callback,
            f"✅ **Canal {channel_name} Configurado**\n\n"
            f"El canal ha sido configurado exitosamente.\n\n"
            f"**Siguiente paso**: ¿Quieres configurar más elementos?",
            get_setup_main_kb(),
            session,
            "setup_main"
        )
    else:
        await callback.message.edit_text(
            f"❌ **Error de Configuración**\n\n{result['error']}",
            reply_markup=get_setup_channels_kb()
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "setup_gamification")
async def setup_gamification_menu(callback: CallbackQuery, session: AsyncSession):
    """Show gamification setup options."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "🎮 **Configuración de Gamificación**\n\n"
        "El sistema de gamificación mantiene a tus usuarios comprometidos con:\n\n"
        "🎯 **Misiones**: Tareas que los usuarios pueden completar\n"
        "🏅 **Insignias**: Reconocimientos por logros\n"
        "🎁 **Recompensas**: Premios por acumular puntos\n"
        "📊 **Niveles**: Sistema de progresión\n\n"
        "**Recomendación**: Usa la configuración por defecto para empezar rápido.",
        get_setup_gamification_kb(),
        session,
        "setup_gamification"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_default_game")
async def setup_default_gamification(callback: CallbackQuery, session: AsyncSession):
    """Set up default gamification elements."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    tenant_service = TenantService(session)
    result = await tenant_service.setup_default_gamification(callback.from_user.id)
    
    if result["success"]:
        await menu_manager.update_menu(
            callback,
            "✅ **Gamificación Configurada**\n\n"
            "Se ha configurado el sistema de gamificación con:\n\n"
            f"🎯 **Misiones creadas**: {len(result['missions_created'])}\n"
            f"📊 **Niveles inicializados**: {'Sí' if result['levels_initialized'] else 'No'}\n"
            f"🏆 **Logros inicializados**: {'Sí' if result['achievements_initialized'] else 'No'}\n\n"
            "Los usuarios ya pueden empezar a ganar puntos y completar misiones.",
            get_setup_main_kb(),
            session,
            "setup_main"
        )
    else:
        await callback.message.edit_text(
            f"❌ **Error de Configuración**\n\n{result['error']}",
            reply_markup=get_setup_gamification_kb()
        )
    
    await callback.answer()

@router.callback_query(F.data == "setup_tariffs")
async def setup_tariffs_menu(callback: CallbackQuery, session: AsyncSession):
    """Show tariff setup options."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "💳 **Configuración de Tarifas VIP**\n\n"
        "Las tarifas determinan los precios y duración de las suscripciones VIP.\n\n"
        "**Opciones disponibles**:\n"
        "💎 **Básica**: Tarifa estándar de 30 días\n"
        "👑 **Premium**: Tarifa de 90 días con descuento\n"
        "🎯 **Personalizada**: Crea tus propias tarifas\n\n"
        "**Recomendación**: Empieza con las tarifas básica y premium.",
        get_setup_tariffs_kb(),
        session,
        "setup_tariffs"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_basic_tariff")
async def setup_basic_tariff(callback: CallbackQuery, session: AsyncSession):
    """Set up basic tariff."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    tenant_service = TenantService(session)
    result = await tenant_service.create_default_tariffs(callback.from_user.id)
    
    if result["success"]:
        tariffs_text = "\n".join([f"• {name}" for name in result["tariffs_created"]])
        await menu_manager.update_menu(
            callback,
            f"✅ **Tarifas Creadas**\n\n"
            f"Se han creado las siguientes tarifas:\n\n{tariffs_text}\n\n"
            f"Puedes modificar precios y crear tarifas adicionales desde el panel de administración.",
            get_setup_main_kb(),
            session,
            "setup_main"
        )
    else:
        await callback.message.edit_text(
            f"❌ **Error de Configuración**\n\n{result['error']}",
            reply_markup=get_setup_tariffs_kb()
        )
    
    await callback.answer()

@router.callback_query(F.data == "setup_complete")
async def complete_setup(callback: CallbackQuery, session: AsyncSession):
    """Complete the setup process."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    tenant_service = TenantService(session)
    summary = await tenant_service.get_tenant_summary(callback.from_user.id)
    
    if "error" in summary:
        await callback.message.edit_text(
            f"❌ **Error**\n\n{summary['error']}",
            reply_markup=get_setup_main_kb()
        )
        return
    
    status = summary["configuration_status"]
    
    status_text = "✅ **Configuración Completada**\n\n"
    status_text += "**Estado de tu bot**:\n"
    status_text += f"📢 Canales: {'✅' if status['channels_configured'] else '❌'}\n"
    status_text += f"💳 Tarifas: {'✅' if status['tariffs_configured'] else '❌'}\n"
    status_text += f"🎮 Gamificación: {'✅' if status['gamification_configured'] else '❌'}\n\n"
    
    if status["basic_setup_complete"]:
        status_text += "🎉 **¡Tu bot está listo para usar!**\n\n"
        status_text += "Puedes empezar a invitar usuarios y gestionar tu comunidad."
    else:
        status_text += "⚠️ **Configuración incompleta**\n\n"
        status_text += "Algunas funciones pueden no estar disponibles hasta completar la configuración."
    
    await menu_manager.update_menu(
        callback,
        status_text,
        get_setup_complete_kb(),
        session,
        "setup_complete"
    )
    await callback.answer()

@router.callback_query(F.data == "skip_setup")
async def skip_setup(callback: CallbackQuery, session: AsyncSession):
    """Skip setup and go to admin panel."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    from keyboards.admin_main_kb import get_admin_main_kb
    
    await menu_manager.update_menu(
        callback,
        "⏭️ **Configuración Omitida**\n\n"
        "Has omitido la configuración inicial. Puedes configurar tu bot "
        "en cualquier momento desde el panel de administración.\n\n"
        "**Nota**: Algunas funciones pueden no estar disponibles hasta "
        "completar la configuración básica.",
        get_admin_main_kb(),
        session,
        "admin_main"
    )
    await callback.answer()

# Error handlers and cleanup
@router.callback_query(F.data.startswith("cancel_"))
async def cancel_setup_action(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Cancel current setup action."""
    await state.clear()
    await menu_manager.update_menu(
        callback,
        "❌ **Acción Cancelada**\n\n"
        "La configuración ha sido cancelada. Puedes intentar nuevamente cuando quieras.",
        get_setup_main_kb(),
        session,
        "setup_main"
    )
    await callback.answer()