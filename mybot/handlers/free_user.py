# mybot/handlers/free_user.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession # Importar AsyncSession

from keyboards.suscripcion_kb import (
    get_subscription_kb,
    get_free_info_kb,
    get_free_game_kb,
)
from utils.user_roles import is_admin, is_vip # Asegúrate de que is_vip ahora espera 'bot' y 'session'
from utils.menu_manager import menu_manager # Importar menu_manager
from utils.menu_factory import menu_factory # Importar menu_factory

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("subscribe"))
async def subscription_menu(message: Message, session: AsyncSession): # Añadir session aquí
    # Asume que is_admin y is_vip esperan session
    if await is_admin(message.from_user.id, session) or await is_vip(message.bot, message.from_user.id, session):
        return

    # Usar menu_manager para mostrar el menú principal gratuito
    text, keyboard = await menu_factory.create_menu("free_main", message.from_user.id, session, message.bot)
    await menu_manager.show_menu(
        message,
        text,
        keyboard,
        session,
        "free_main", # Estado del menú para el historial
        delete_origin_message=True # Opcional: elimina el mensaje del comando
    )

@router.callback_query(F.data == "free_info")
async def show_info(callback: CallbackQuery, session: AsyncSession): # Añadir session aquí
    """Display the info section for free users."""
    text = "ℹ️ **Información General para Usuarios Gratuitos**\n\n" \
           "Bienvenido a la sección de información. Aquí puedes encontrar " \
           "detalles sobre cómo funciona el bot, sus características, " \
           "y cómo obtener acceso VIP.\n\n" \
           "*(¡Más información próximamente!)*"
    
    keyboard = get_free_info_kb()
    
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "free_info_section" # Nuevo estado para el historial del menú
    )
    await callback.answer()

# --- Nuevos manejadores para los botones dentro de "Información" ---
@router.callback_query(F.data == "free_info_faq")
async def show_faq(callback: CallbackQuery):
    await callback.answer("Cargando Preguntas Frecuentes...", show_alert=False)
    text = "❓ **Preguntas Frecuentes (FAQ)**\n\n" \
           "**P: ¿Cómo funciona este bot?**\n" \
           "R: Es un bot de interacción y comunidad con contenido exclusivo.\n\n" \
           "**P: ¿Cómo consigo acceso VIP?**\n" \
           "R: Puedes obtener acceso VIP en la sección 'Obtener VIP' del menú principal.\n\n" \
           "**P: ¿El mini juego es gratuito?**\n" \
           "R: Sí, el mini juego es para usuarios gratuitos. ¡Diviértete!"
    
    # Podrías crear un nuevo teclado para esta sección o reusar get_free_info_kb() con un botón de volver
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver a Información", callback_data="free_info") # Volver a la sección de info
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "free_info_news")
async def show_news(callback: CallbackQuery):
    await callback.answer("Cargando Novedades...", show_alert=False)
    text = "📢 **Novedades y Anuncios**\n\n" \
           "• **22 de Junio, 2025**: Lanzamiento del nuevo sistema de gamificación (solo VIP).\n" \
           "• **15 de Junio, 2025**: Actualización de contenido en el canal VIP.\n" \
           "• **01 de Junio, 2025**: ¡Hemos alcanzado 1000 usuarios! Gracias por tu apoyo."
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver a Información", callback_data="free_info")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# --- Manejador para el botón "Mini Juego Kinky" ---
@router.callback_query(F.data == "free_game")
async def free_game_menu(callback: CallbackQuery, session: AsyncSession): # Añadir session aquí
    """Display the mini game section for free users."""
    text = "🧩 **Mini Juego Kinky (versión gratuita)**\n\n" \
           "Este es un divertido mini juego para pasar el rato. " \
           "¡Prueba tu suerte y ve qué tan bien te va!\n\n" \
           "*(¡El juego estará disponible pronto!)*"
    
    keyboard = get_free_game_kb()
    
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "free_game_section" # Nuevo estado para el historial del menú
    )
    await callback.answer()

# --- Nuevos manejadores para los botones dentro de "Mini Juego Kinky" ---
@router.callback_query(F.data == "free_game_start")
async def start_free_game(callback: CallbackQuery):
    await callback.answer("Iniciando el juego... (Funcionalidad en desarrollo)", show_alert=True)
    # Aquí iría la lógica para iniciar el juego
    # Por ahora, puedes dejar un mensaje simple o redirigir a un menú de juego real

@router.callback_query(F.data == "free_game_scores")
async def show_free_game_scores(callback: CallbackQuery):
    await callback.answer("Cargando puntuaciones...", show_alert=False)
    text = "🏆 **Mejores Puntuaciones del Mini Juego Kinky**\n\n" \
           "Aquí verás los jugadores con las mejores puntuaciones.\n\n" \
           "1. Anónimo_123: 500 puntos\n" \
           "2. KinkyLover: 450 puntos\n" \
           "3. JugadorX: 400 puntos\n\n" \
           "*(¡Juega para aparecer en el ranking!)*"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver al Juego", callback_data="free_game") # Volver al menú del juego
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# --- Manejador para el botón "Obtener VIP" ---
@router.callback_query(F.data == "free_get_vip")
async def handle_get_vip(callback: CallbackQuery):
    await callback.answer("Redirigiendo a la información VIP...", show_alert=False)
    text = "👑 **Conviértete en Miembro VIP**\n\n" \
           "Obtén acceso exclusivo a:\n" \
           "• Contenido premium y eventos\n" \
           "• Misiones y recompensas avanzadas\n" \
           "• Soporte prioritario\n\n" \
           "¡No te lo pierdas!\n\n" \
           "*(Aquí iría la información sobre cómo comprar la suscripción VIP, por ejemplo, enlaces a tu pasarela de pago o instrucciones.)*"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Comprar Suscripción", url="https://t.me/TuEnlaceDePagoVIP") # Reemplaza con tu enlace de pago
    builder.button(text="🔙 Volver al Menú Principal", callback_data="free_main_menu")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


# --- Manejador para volver al menú principal gratuito (MUY IMPORTANTE) ---
@router.callback_query(F.data == "free_main_menu")
async def navigate_to_free_main_menu(callback: CallbackQuery, session: AsyncSession):
    """Navigates back to the main free user menu."""
    text, keyboard = await menu_factory.create_menu("free_main", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "free_main"
    )
    await callback.answer()

