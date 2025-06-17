from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_vip_main_kb():
    """Return the root VIP menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Mi Suscripción", callback_data="vip_subscription")
    builder.button(text="🎮 Juego Kinky", callback_data="vip_game")
    builder.adjust(1)
    return builder.as_markup()
