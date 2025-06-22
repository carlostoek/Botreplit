# mybot/keyboards/suscripcion_kb.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_subscription_kb() -> InlineKeyboardMarkup:
    """Return the menu keyboard for free users (main menu)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Información", callback_data="free_info")
    builder.button(text="🧩 Mini Juego Kinky", callback_data="free_game")
    builder.button(text="🔗 Canal Gratuito", url="https://t.me/TuCanalGratuito") # Considera añadir un enlace real aquí
    builder.adjust(1)
    return builder.as_markup()

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
