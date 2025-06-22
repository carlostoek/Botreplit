# mybot/keyboards/suscripcion_kb.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_subscription_kb() -> InlineKeyboardMarkup:
    """Return the menu keyboard for free users (main menu)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Información", callback_data="free_info")
    builder.button(text="🧩 Mini Juego Kinky", callback_data="free_game")
    builder.button(text="👑 Obtener VIP", callback_data="free_get_vip") # Nuevo botón para subir a VIP
    builder.adjust(1)
    return builder.as_markup()


def get_free_info_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the information section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Preguntas Frecuentes (FAQ)", callback_data="free_info_faq") # Callback más descriptivo
    builder.button(text="📢 Novedades y Anuncios", callback_data="free_info_news") # Callback más descriptivo
    builder.button(text="🔙 Volver al Menú Principal", callback_data="free_main_menu") # Callback para volver al menú principal gratuito
    builder.adjust(1)
    return builder.as_markup()


def get_free_game_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the free mini game section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Iniciar Juego", callback_data="free_game_start") # Callback para iniciar el juego
    builder.button(text="🏆 Ver Puntuaciones", callback_data="free_game_scores") # Callback para ver puntuaciones
    builder.button(text="🔙 Volver al Menú Principal", callback_data="free_main_menu") # Callback para volver al menú principal gratuito
    builder.adjust(1)
    return builder.as_markup()
    
