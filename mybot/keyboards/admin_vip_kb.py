from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_vip_kb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Estadísticas", callback_data="vip_stats")
    builder.button(text="🔑 Generar Token", callback_data="vip_generate_token")
    builder.button(text="👥 Suscriptores", callback_data="vip_manage")
    builder.button(text="🏅 Asignar insignia", callback_data="vip_manual_badge")
    builder.button(text="📝 Publicar en Canal", callback_data="admin_send_channel_post")
    builder.button(text="⚙️ Configuración", callback_data="vip_config")
    builder.button(text="🔙 Volver", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()
