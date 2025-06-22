import logging
import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import get_user_role
from utils.menu_manager import menu_manager
from keyboards.subscription_kb import get_free_main_menu_kb
from utils.messages import BOT_MESSAGES
from utils.keyboard_utils import get_back_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("subscribe"))
async def show_free_main_menu(message: Message, session: AsyncSession):
    """Display the menu for free users."""
    if await get_user_role(message.bot, message.from_user.id, session=session) != "free":
        return

    await menu_manager.show_menu(
        message,
        BOT_MESSAGES.get("FREE_MENU_TEXT", "Menú gratuito"),
        get_free_main_menu_kb(),
        session,
        "free_main",
        delete_origin_message=True,
    )


@router.callback_query(F.data == "free_main_menu")
async def cb_free_main_menu(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_MENU_TEXT", "Menú gratuito"),
        get_free_main_menu_kb(),
        session,
        "free_main",
    )
    await callback.answer()


@router.callback_query(F.data == "free_gift")
async def cb_free_gift(callback: CallbackQuery, session: AsyncSession):
    message = callback.message
    await message.answer(
        "🎁 Antes de dejarte pasar... ¿puedes completar esta prueba rápida?\n\n📌 Sígueme en mis redes y desbloquea tu regalo."
    )
    await message.answer("📡 Verificando Instagram...")
    await asyncio.sleep(2)
    await message.answer("🔄 Reintentando conexión...")
    await asyncio.sleep(2)
    await message.answer("✅ ¡Perfecto! Instagram verificado.")
    await asyncio.sleep(1)
    await message.answer(
        "✨ ¡Regalo desbloqueado!\nAquí tienes una sorpresa para ti solo: [contenido de muestra o enlace al pack gratuito]",
        reply_markup=get_back_keyboard("free_main_menu"),
    )
    await callback.answer()


@router.callback_query(F.data == "free_packs")
async def cb_free_packs(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_PACKS_TEXT", "Packs exclusivos"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_packs",
    )
    await callback.answer()


@router.callback_query(F.data == "free_vip_explore")
async def cb_free_vip_explore(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_VIP_EXPLORE_TEXT", "Canal VIP"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_vip_explore",
    )
    await callback.answer()


@router.callback_query(F.data == "free_custom")
async def cb_free_custom(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_CUSTOM_TEXT", "Contenido personalizado"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_custom",
    )
    await callback.answer()


@router.callback_query(F.data == "free_game")
async def cb_free_game(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_GAME_TEXT", "Mini juego"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_game",
    )
    await callback.answer()


@router.callback_query(F.data == "free_follow")
async def cb_free_follow(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_FOLLOW_TEXT", "Dónde seguirme"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_follow",
    )
    await callback.answer()
