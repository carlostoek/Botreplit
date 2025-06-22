import logging
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


@router.callback_query(F.data == "free_about")
async def cb_free_about(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_ABOUT_TEXT", "Sobre mí"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_about",
    )
    await callback.answer()


@router.callback_query(F.data == "free_find")
async def cb_free_find(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_FIND_TEXT", "Información"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_find",
    )
    await callback.answer()


@router.callback_query(F.data == "free_free")
async def cb_free_free(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_FREE_TEXT", "Contenido gratuito"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_free",
    )
    await callback.answer()


@router.callback_query(F.data == "free_vip")
async def cb_free_vip(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_VIP_TEXT", "Contenido VIP"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_vip",
    )
    await callback.answer()


@router.callback_query(F.data == "free_private")
async def cb_free_private(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_PRIVATE_TEXT", "Sesiones privadas"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_private",
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
