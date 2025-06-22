# mybot/keyboards/suscripcion_kb.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_free_main_menu_kb() -> InlineKeyboardMarkup:
    """Return the main menu keyboard for free users."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📌 Sobre mí", callback_data="free_about")
    builder.button(text="🪞 Qué puedes encontrar aquí", callback_data="free_find")
    builder.button(text="🎁 Lo que sí puedes ver gratis", callback_data="free_free")
    builder.button(text="🔒 Lo que te estás perdiendo (contenido VIP)", callback_data="free_vip")
    builder.button(text="🔥 Sesiones privadas y contenido personalizado", callback_data="free_private")
    builder.button(text="🎮 Probar el Juego Kinky (versión gratuita)", callback_data="free_game")
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
