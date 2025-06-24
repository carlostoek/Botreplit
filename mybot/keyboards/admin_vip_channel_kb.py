from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_admin_vip_channel_kb() -> InlineKeyboardMarkup:
    """Returns the keyboard for the VIP Channel admin menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Configurar Reacciones VIP", callback_data="vip_config_reactions")
    # Puedes añadir otras opciones específicas del canal VIP aquí en el futuro si las tienes
    builder.button(text="🔙 Volver al Menú Admin", callback_data="admin_main")
    builder.adjust(1)
    return builder.as_markup()
