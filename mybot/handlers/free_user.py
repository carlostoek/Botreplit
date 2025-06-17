from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from keyboards.subscription_kb import (
    get_subscription_kb,
    get_free_info_kb,
    get_free_game_kb,
)
from utils.user_roles import is_admin, is_vip

router = Router()


@router.message(Command("subscribe"))
async def subscription_menu(message: Message):
    if is_admin(message.from_user.id) or await is_vip(message.bot, message.from_user.id):
        return
    await message.answer(
        "Bienvenido a los kinkys",
        reply_markup=get_subscription_kb(),
    )


@router.callback_query(F.data == "free_info")
async def show_info(callback: CallbackQuery):
    """Display the info section for free users."""
    await callback.answer()
    await callback.message.edit_text(
        "Información del canal gratuito.",
        reply_markup=get_free_info_kb(),
    )


@router.callback_query(F.data == "free_game")
async def free_game(callback: CallbackQuery):
    """Placeholder mini game for free users."""
    await callback.message.edit_text(
        "Mini Juego Kinky (versión gratuita)",
        reply_markup=get_free_game_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.in_("free_info_test free_game_test".split()))
async def dummy_button(callback: CallbackQuery):
    """Handle placeholder buttons in the free user menu."""
    await callback.answer("Botón de prueba")
