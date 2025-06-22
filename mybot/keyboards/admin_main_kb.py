from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_main_kb():
    """Return the main admin inline keyboard with free channel management."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Canal VIP", callback_data="admin_vip")

    builder.button(text="💬 Canal Free", callback_data="admin_free")
    builder.button(text="🎮 Juego Kinky", callback_data="admin_kinky_game")

   
    builder.button(text="🛠 Configuración del Bot", callback_data="admin_config")
    builder.button(text="📈 Estadísticas", callback_data="admin_stats")
    builder.button(text="🔙 Volver", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()
