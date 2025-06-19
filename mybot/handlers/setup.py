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

# Importar menu_factory para crear menús específicos si es necesario
from utils.menu_factory import menu_factory 

logger = logging.getLogger(__name__)
router = Router()

class SetupStates(StatesGroup):
    """States for the setup flow."""
    waiting_for_vip_channel = State()
    waiting_for_free_channel = State()
    waiting_for_channel_confirmation = State()
    waiting_for_manual_channel_id = State()
    # Más estados si necesitas pasos interactivos para configurar cada elemento
    # Por ahora, estos se manejarán con callbacks directos al menú de setup
    # configuring_tariffs = State() 
    # configuring_gamification = State()
    # waiting_for_tariff_details = State()
    # waiting_for_mission_details = State()


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
        text, keyboard = await menu_factory.create_menu("setup_complete", message.from_user.id, session, message.bot)
        await menu_manager.show_menu(
            message,
            text,
            keyboard,
            session,
            "setup_complete",
            delete_origin_message=True # Añadido: borrar el comando /setup
        )
    else:
        text, keyboard = await menu_factory.create_menu("setup_main", message.from_user.id, session, message.bot)
        await menu_manager.show_menu(
            message,
            text,
            keyboard,
            session,
            "setup_main",
            delete_origin_message=True # Añadido: borrar el comando /setup
        )

# -- Canal handlers --
@router.callback_query(F.data == "setup_channels")
async def setup_channels_menu(callback: CallbackQuery, session: AsyncSession):
    """Show channel configuration options."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Usar menu_factory para obtener el texto y teclado, si lo tienes definido allí
    # O seguir usando el texto fijo y get_setup_channels_kb()
    text, keyboard = await menu_factory.create_menu("setup_channels", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_channels"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_vip_channel")
async def setup_vip_channel(callback: CallbackQuery, state: FSMContext):
    """Start VIP channel configuration."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Es mejor usar menu_manager.update_menu aquí para mantener el historial
    await menu_manager.update_menu(
        callback,
        "🔐 **Configurar Canal VIP**\n\n"
        "Para configurar tu canal VIP, reenvía cualquier mensaje de tu canal aquí. "
        "El bot detectará automáticamente el ID del canal.\n\n"
        "**Importante**: Asegúrate de que el bot sea administrador del canal "
        "con permisos para invitar usuarios.",
        get_setup_confirmation_kb("cancel_channel_setup"), # Puedes cambiar este a un teclado específico para cancelar el canal
        session=None, # No necesitas session aquí, solo para la vista
        menu_state="setup_vip_channel_prompt" # Nuevo estado para el historial
    )
    
    await state.set_state(SetupStates.waiting_for_vip_channel)
    await callback.answer()

@router.callback_query(F.data == "setup_free_channel")
async def setup_free_channel(callback: CallbackQuery, state: FSMContext):
    """Start free channel configuration."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "🆓 **Configurar Canal Gratuito**\n\n"
        "Para configurar tu canal gratuito, reenvía cualquier mensaje de tu canal aquí. "
        "El bot detectará automáticamente el ID del canal.\n\n"
        "**Importante**: Asegúrate de que el bot sea administrador del canal "
        "con permisos para aprobar solicitudes de unión.",
        get_setup_confirmation_kb("cancel_channel_setup"), # Puedes cambiar este a un teclado específico para cancelar el canal
        session=None,
        menu_state="setup_free_channel_prompt" # Nuevo estado para el historial
    )
    
    await state.set_state(SetupStates.waiting_for_free_channel)
    await callback.answer()

@router.callback_query(F.data == "setup_both_channels")
async def setup_both_channels(callback: CallbackQuery, session: AsyncSession):
    """Placeholder for configuring both channels."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Podrías iniciar un flujo de FSM para ambos, o simplemente redirigir
    # Por simplicidad, volvemos al menú de canales y mostramos un mensaje
    await menu_manager.update_menu(
        callback,
        "🛠️ **Configuración de Ambos Canales (Próximamente)**\n\n"
        "Esta opción te guiará para configurar ambos canales simultáneamente. "
        "Por ahora, por favor, configúralos individualmente. Gracias.",
        get_setup_channels_kb(),
        session,
        "setup_channels"
    )
    await callback.answer()

# Handlers para procesamiento de canales reenviados/manuales
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
        # Check if it's a manual ID input
        if message.text and message.text.strip().startswith("-100"): # Los IDs de canal empiezan con -100
             try:
                channel_id = int(message.text.strip())
             except ValueError:
                pass # Se manejará como ID inválido
        
        if not channel_id:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nPor favor, reenvía un mensaje del canal o ingresa un ID válido.",
                auto_delete_seconds=5
            )
            return await state.set_state(SetupStates.waiting_for_vip_channel) # Volver a esperar
    
    # Store channel info for confirmation
    await state.update_data(
        channel_type="vip",
        channel_id=channel_id,
        channel_title=channel_title,
        message_to_edit_id=message.message_id # Guarda el ID del mensaje del usuario para posible borrado
    )
    
    title_text = f" ({sanitize_text(channel_title)})" if channel_title else ""
    
    # Enviar un nuevo mensaje con la confirmación
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
        # Check if it's a manual ID input
        if message.text and message.text.strip().startswith("-100"):
            try:
                channel_id = int(message.text.strip())
            except ValueError:
                pass
        
        if not channel_id:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nPor favor, reenvía un mensaje del canal o ingresa un ID válido.",
                auto_delete_seconds=5
            )
            return await state.set_state(SetupStates.waiting_for_free_channel) # Volver a esperar
    
    # Store channel info for confirmation
    await state.update_data(
        channel_type="free",
        channel_id=channel_id,
        channel_title=channel_title,
        message_to_edit_id=message.message_id
    )
    
    title_text = f" ({sanitize_text(channel_title)})" if channel_title else ""
    
    await message.answer(
        f"✅ **Canal Gratuito Detectado**\n\n"
        f"**ID del Canal**: `{channel_id}`{title_text}\n\n"
        f"¿Es este el canal correcto?",
        reply_markup=get_channel_detection_kb()
    )
    
    await state.set_state(SetupStates.waiting_for_channel_confirmation)

# Handlers para botones de confirmación de canal
@router.callback_query(F.data == "confirm_channel", SetupStates.waiting_for_channel_confirmation)
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
        # Volver al menú principal de setup
        text, keyboard = await menu_factory.create_menu("setup_main", callback.from_user.id, session, callback.bot)
        await menu_manager.update_menu(
            callback,
            f"✅ **Canal {channel_name} Configurado**\n\n"
            f"El canal ha sido configurado exitosamente.\n\n"
            f"**Siguiente paso**: {text}", # Añade el texto del menú principal
            keyboard,
            session,
            "setup_main"
        )
    else:
        await menu_manager.update_menu( # Usar update_menu en lugar de message.edit_text
            callback,
            f"❌ **Error de Configuración**\n\n{result['error']}",
            get_setup_channels_kb(),
            session,
            "setup_channels"
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "detect_another", SetupStates.waiting_for_channel_confirmation)
async def detect_another_channel(callback: CallbackQuery, state: FSMContext):
    """Allow user to try detecting another channel."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    data = await state.get_data()
    channel_type = data.get("channel_type")
    
    if channel_type == "vip":
        await menu_manager.update_menu(
            callback,
            "🔐 **Reintentar Canal VIP**\n\n"
            "Por favor, reenvía un mensaje de tu canal VIP o ingresa el ID manualmente.",
            get_setup_confirmation_kb("cancel_channel_setup"), # Puedes mejorar este teclado
            session=None,
            menu_state="setup_vip_channel_prompt"
        )
        await state.set_state(SetupStates.waiting_for_vip_channel)
    else:
        await menu_manager.update_menu(
            callback,
            "🆓 **Reintentar Canal Gratuito**\n\n"
            "Por favor, reenvía un mensaje de tu canal Gratuito o ingresa el ID manualmente.",
            get_setup_confirmation_kb("cancel_channel_setup"),
            session=None,
            menu_state="setup_free_channel_prompt"
        )
        await state.set_state(SetupStates.waiting_for_free_channel)
    await callback.answer()

@router.callback_query(F.data == "manual_channel_id", SetupStates.waiting_for_channel_confirmation)
async def manual_channel_id_prompt(callback: CallbackQuery, state: FSMContext):
    """Prompt for manual channel ID input."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    data = await state.get_data()
    channel_type = data.get("channel_type")
    
    await menu_manager.update_menu(
        callback,
        f"📝 **Ingresa el ID del Canal {channel_type.upper()}**\n\n"
        f"Por favor, ingresa el ID numérico de tu canal {channel_type}. "
        f"Normalmente empieza con `-100`.",
        get_setup_confirmation_kb("cancel_channel_setup"),
        session=None,
        menu_state="setup_manual_channel_id_prompt"
    )
    await state.set_state(SetupStates.waiting_for_manual_channel_id)
    await callback.answer()

@router.message(SetupStates.waiting_for_manual_channel_id)
async def process_manual_channel_id(message: Message, state: FSMContext, session: AsyncSession):
    """Process manually entered channel ID."""
    if not is_admin(message.from_user.id):
        return
    
    try:
        channel_id = int(message.text.strip())
        if not str(channel_id).startswith("-100"):
            raise ValueError("Invalid channel ID format")
            
        data = await state.get_data()
        channel_type = data.get("channel_type")
        
        # Store channel info for confirmation
        await state.update_data(
            channel_id=channel_id,
            channel_title=None, # Manual input usually means no title initially
            message_to_edit_id=message.message_id
        )
        
        await message.answer(
            f"✅ **ID de Canal {channel_type.upper()} Ingresado**\n\n"
            f"**ID del Canal**: `{channel_id}`\n\n"
            f"¿Es este el canal correcto?",
            reply_markup=get_channel_detection_kb()
        )
        await state.set_state(SetupStates.waiting_for_channel_confirmation)
        
    except ValueError:
        await menu_manager.send_temporary_message(
            message,
            "❌ **ID Inválido**\n\nPor favor, ingresa un ID numérico válido para el canal. "
            "Debe empezar con `-100`.",
            auto_delete_seconds=7
        )
        await state.set_state(SetupStates.waiting_for_manual_channel_id) # Volver a esperar
    
# -- Gamification Handlers --
# setup_gamification_menu ya existe

# setup_default_game ya existe

@router.callback_query(F.data == "setup_missions")
async def setup_missions(callback: CallbackQuery, session: AsyncSession):
    """Handle setup missions click."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Lógica para configurar misiones (puede ser un sub-menú, un FSM, o mensaje de info)
    await menu_manager.update_menu(
        callback,
        "🎯 **Configurar Misiones**\n\n"
        "Aquí podrás definir las misiones que tus usuarios pueden completar. "
        "Esto podría implicar crear nuevas misiones o editar existentes.\n\n"
        "*(Implementación futura: Interfaz para crear/editar misiones)*",
        get_setup_gamification_kb(), # Volver al menú de gamificación por ahora
        session,
        "setup_missions_info" # Nuevo estado para el historial si es necesario
    )
    await callback.answer()

@router.callback_query(F.data == "setup_badges")
async def setup_badges(callback: CallbackQuery, session: AsyncSession):
    """Handle setup badges click."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "🏅 **Configurar Insignias**\n\n"
        "Define las insignias que tus usuarios pueden ganar por sus logros. "
        "Las insignias añaden un elemento de prestigio.\n\n"
        "*(Implementación futura: Interfaz para crear/editar insignias)*",
        get_setup_gamification_kb(),
        session,
        "setup_badges_info"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_rewards")
async def setup_rewards(callback: CallbackQuery, session: AsyncSession):
    """Handle setup rewards click."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "🎁 **Configurar Recompensas**\n\n"
        "Establece las recompensas que los usuarios pueden canjear con sus puntos. "
        "Las recompensas motivan la participación.\n\n"
        "*(Implementación futura: Interfaz para crear/editar recompensas)*",
        get_setup_gamification_kb(),
        session,
        "setup_rewards_info"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_levels")
async def setup_levels(callback: CallbackQuery, session: AsyncSession):
    """Handle setup levels click."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "📊 **Configurar Niveles**\n\n"
        "Define los diferentes niveles de progresión para tus usuarios. "
        "Los niveles otorgan una sensación de avance.\n\n"
        "*(Implementación futura: Interfaz para crear/editar niveles)*",
        get_setup_gamification_kb(),
        session,
        "setup_levels_info"
    )
    await callback.answer()

# -- Tariff Handlers --
# setup_tariffs_menu ya existe
# setup_basic_tariff ya existe (que también crea tarifas "premium" por defecto)

@router.callback_query(F.data == "setup_premium_tariff")
async def setup_premium_tariff(callback: CallbackQuery, session: AsyncSession):
    """Handle setup premium tariff click."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Si setup_basic_tariff ya crea tarifas premium, este botón puede ser redundante
    # O podrías tener una lógica para crear una tarifa premium específica aquí.
    # Por ahora, un mensaje informativo.
    await menu_manager.update_menu(
        callback,
        "👑 **Crear Tarifa Premium Específica (Próximamente)**\n\n"
        "Esta opción te permitirá crear una tarifa premium con configuraciones "
        "avanzadas. Por ahora, puedes usar las tarifas básicas y premium por defecto.",
        get_setup_tariffs_kb(),
        session,
        "setup_tariffs"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_custom_tariffs")
async def setup_custom_tariffs(callback: CallbackQuery, session: AsyncSession):
    """Handle setup custom tariffs click."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "🎯 **Configuración de Tarifas Personalizadas (Próximamente)**\n\n"
        "Esta sección te permitirá crear tarifas de suscripción con duración, "
        "precio y beneficios personalizados.\n\n"
        "*(Implementación futura: Interfaz para crear/editar tarifas)*",
        get_setup_tariffs_kb(),
        session,
        "setup_tariffs"
    )
    await callback.answer()

# -- Completion and Navigation Handlers --
# complete_setup ya existe
# skip_setup ya existe

@router.callback_query(F.data == "setup_guide")
async def show_setup_guide(callback: CallbackQuery, session: AsyncSession):
    """Show setup guide for admin."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "📖 **Guía de Uso del Bot**\n\n"
        "Aquí encontrarás información detallada sobre cómo usar y configurar tu bot. "
        "Temas:\n"
        "• Gestión de usuarios\n"
        "• Creación de contenido\n"
        "• Marketing y monetización\n\n"
        "*(Implementación futura: Contenido de la guía)*",
        get_setup_complete_kb(), # Puedes tener un teclado específico para la guía si es necesario
        session,
        "setup_guide_info"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_advanced")
async def setup_advanced(callback: CallbackQuery, session: AsyncSession):
    """Handle advanced setup options."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await menu_manager.update_menu(
        callback,
        "🔧 **Configuración Avanzada (Próximamente)**\n\n"
        "Esta sección contendrá opciones avanzadas para la personalización del bot, "
        "integraciones y herramientas de depuración.\n\n"
        "*(Implementación futura: Opciones avanzadas)*",
        get_setup_complete_kb(),
        session,
        "setup_advanced_info"
    )
    await callback.answer()

# Error handlers and cleanup
# Modificación en cancel_setup_action para manejar 'cancel_channel_setup'
@router.callback_query(F.data.startswith("cancel_"))
async def cancel_setup_action(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Cancel current setup action and return to main setup menu."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.clear() # Limpiar el estado de FSM

    # Usar menu_factory para el menú principal de setup para consistencia
    text, keyboard = await menu_factory.create_menu("setup_main", callback.from_user.id, session, callback.bot)
    
    await menu_manager.update_menu(
        callback,
        "❌ **Acción Cancelada**\n\n"
        "La configuración ha sido cancelada. Puedes intentar nuevamente cuando quieras.\n\n"
        f"**Siguiente paso**: {text}", # Añade el texto del menú principal de setup
        keyboard,
        session,
        "setup_main"
    )
    await callback.answer()

# Handler para el botón "admin_main" en get_setup_complete_kb
@router.callback_query(F.data == "admin_main")
async def navigate_to_admin_main_from_setup(callback: CallbackQuery, session: AsyncSession):
    """Navigate to the main admin panel after setup completion or skip."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Asume que 'admin_main' es un estado de menú reconocido por menu_factory
    text, keyboard = await menu_factory.create_menu("admin_main", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "admin_main"
    )
    await callback.answer()

