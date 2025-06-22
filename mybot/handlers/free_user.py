import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import get_user_role
from utils.menu_manager import menu_manager
from keyboards.subscription_kb import get_subscription_kb
from utils.messages import BOT_MESSAGES
from utils.keyboard_utils import get_back_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("subscribe"))
async def show_free_menu(message: Message, session: AsyncSession):
    """Display the menu for free users."""
    if await get_user_role(message.bot, message.from_user.id, session=session) != "free":
        return

    await menu_manager.show_menu(
        message,
        BOT_MESSAGES.get("FREE_MENU_TEXT", "Menú gratuito"),
        get_subscription_kb(),
        session,
        "free_main",
        delete_origin_message=True,
    )


@router.callback_query(F.data == "free_main_menu")
async def cb_free_main_menu(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_MENU_TEXT", "Menú gratuito"),
        get_subscription_kb(),
        session,
        "free_main",
    )
    await callback.answer()


@router.callback_query(F.data == "free_benefits")
async def cb_free_benefits(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_BENEFITS_TEXT", "Beneficios"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_benefits",
    )
    await callback.answer()


@router.callback_query(F.data == "free_limits")
async def cb_free_limits(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_LIMITS_TEXT", "Límites"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_limits",
    )
    await callback.answer()


@router.callback_query(F.data == "free_content")
async def cb_free_content(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_CONTENT_TEXT", "Contenido"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_content",
    )
    await callback.answer()


@router.callback_query(F.data == "free_upgrade")
async def cb_free_upgrade(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_UPGRADE_TEXT", "Sube a VIP"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_upgrade",
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
