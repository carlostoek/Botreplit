from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_admin_vip_channel_kb() -> InlineKeyboardMarkup:
    """Returns the keyboard for the VIP Channel admin menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Estadísticas", callback_data="vip_stats")
    builder.button(text="🔑 Generar Token", callback_data="vip_generate_token")
    builder.button(text="👥 Suscriptores", callback_data="vip_manage")
    builder.button(text="🏅 Asignar insignia", callback_data="vip_manual_badge")
    builder.button(text="📝 Publicar en Canal", callback_data="admin_send_channel_post")
    builder.button(text="⚙️ Configuración", callback_data="vip_config")
    builder.button(text="📝 Configurar Reacciones VIP", callback_data="vip_config_reactions")
    builder.button(text="🔙 Volver al Menú Admin", callback_data="admin_main")
    builder.adjust(1)
    return builder.as_markup()
