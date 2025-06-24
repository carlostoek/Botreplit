"""
Teclados para administración del canal gratuito.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_free_channel_admin_kb(channel_configured: bool = False) -> InlineKeyboardMarkup:
    """Teclado principal para administración del canal gratuito."""
    builder = InlineKeyboardBuilder()
    
    if channel_configured:
        builder.button(text="⏰ Configurar Tiempo de Espera", callback_data="set_wait_time")
        builder.button(text="🔗 Crear Enlace de Invitación", callback_data="create_invite_link")
        builder.button(text="📝 Enviar Contenido al Canal", callback_data="send_to_free_channel")
        builder.button(text="⚡ Procesar Solicitudes Pendientes", callback_data="process_pending_now")
        builder.button(text="🧹 Limpiar Solicitudes Antiguas", callback_data="cleanup_old_requests")
        builder.button(text="📊 Ver Estadísticas", callback_data="free_channel_stats")
        builder.button(text="📝 Configurar Reacciones Free", callback_data="free_config_reactions")
    else:
        builder.button(text="⚙️ Configurar Canal Gratuito", callback_data="configure_free_channel")
    
    builder.button(text="🔙 Volver", callback_data="admin_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_wait_time_selection_kb() -> InlineKeyboardMarkup:
    """Teclado para seleccionar tiempo de espera."""
    builder = InlineKeyboardBuilder()
    
    # Opciones de tiempo en minutos
    times = [
        (0, "Inmediato"),
        (5, "5 minutos"),
        (15, "15 minutos"),
        (30, "30 minutos"),
        (60, "1 hora"),
        (120, "2 horas"),
        (360, "6 horas"),
        (720, "12 horas"),
        (1440, "24 horas")
    ]
    
    for minutes, label in times:
        builder.button(text=label, callback_data=f"wait_time_{minutes}")
    
    builder.button(text="🔙 Volver", callback_data="admin_free_channel")
    builder.adjust(2)
    return builder.as_markup()


def get_channel_post_options_kb() -> InlineKeyboardMarkup:
    """Teclado para opciones de publicación en canal."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📎 Agregar Multimedia", callback_data="add_media")
    builder.button(text="➡️ Continuar sin Multimedia", callback_data="continue_without_media")
    builder.button(text="❌ Cancelar", callback_data="admin_free_channel")
    
    builder.adjust(1)
    return builder.as_markup()


def get_content_protection_kb() -> InlineKeyboardMarkup:
    """Teclado para configurar protección de contenido."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔒 Sí, Proteger Contenido", callback_data="protect_yes")
    builder.button(text="🔓 No, Contenido Libre", callback_data="protect_no")
    builder.button(text="❌ Cancelar", callback_data="admin_free_channel")
    
    builder.adjust(1)
    return builder.as_markup()


def get_invite_link_options_kb() -> InlineKeyboardMarkup:
    """Teclado para opciones de enlace de invitación."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📋 Crear Enlace Estándar", callback_data="create_standard_link")
    builder.button(text="⏰ Crear Enlace Temporal", callback_data="create_temporary_link")
    builder.button(text="👥 Crear Enlace Limitado", callback_data="create_limited_link")
    builder.button(text="🔙 Volver", callback_data="admin_free_channel")
    
    builder.adjust(1)
    return builder.as_markup()