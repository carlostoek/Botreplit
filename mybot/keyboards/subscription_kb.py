# mybot/keyboards/suscripcion_kb.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_free_main_menu_kb() -> InlineKeyboardMarkup:
    """Return the main menu keyboard for free users."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Desbloquear regalo", callback_data="free_gift")
    builder.button(text="🎀 Ver mis packs exclusivos", callback_data="free_packs")
    builder.button(text="🔐 Explorar el canal VIP", callback_data="free_vip_explore")
    builder.button(text="💌 Quiero contenido personalizado", callback_data="free_custom")
    builder.button(text="🎮 Modo gratuito del juego Kinky", callback_data="free_game")
    builder.button(text="🌐 ¿Dónde más seguirme?", callback_data="free_follow")
    builder.adjust(1)
    return builder.as_markup()

def get_subscription_kb() -> InlineKeyboardMarkup:
    """Alias for backward compatibility."""
    return get_free_main_menu_kb()

def get_free_info_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the information section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Preguntas Frecuentes", callback_data="free_info_faq") # Ejemplo de nuevo botón
    builder.button(text="📢 Novedades", callback_data="free_info_news") # Ejemplo de nuevo botón
    builder.button(text="🔙 Volver al Menú Principal", callback_data="free_main") # Botón para volver al menú principal gratuito
    builder.adjust(1)
    return builder.as_markup()

def get_free_game_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the free mini game section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Jugar Ahora", callback_data="free_game_play") # Ejemplo de botón para iniciar el juego
    builder.button(text="🏆 Mi Puntuación", callback_data="free_game_score") # Ejemplo de botón para ver puntuación
    builder.button(text="🔙 Volver al Menú Principal", callback_data="free_main") # Botón para volver al menú principal gratuito
    builder.adjust(1)
    return builder.as_markup()
