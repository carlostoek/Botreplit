from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from aiogram.filters import Command

from keyboards.admin_kb import get_admin_kb
from utils.user_roles import is_admin
from services.scheduler import run_channel_request_check, run_vip_subscription_check
from database.setup import get_session

router = Router()


@router.message(Command("admin_menu"))
async def admin_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Menú de administración", reply_markup=get_admin_kb())


@router.callback_query(F.data == "admin_button")
async def admin_placeholder_handler(callback: CallbackQuery):
    await callback.answer("Acción de administración")


@router.message(Command("run_schedulers"))
async def run_schedulers(message: Message, bot: Bot):
    """Allow an admin to trigger scheduler checks manually."""
    if not is_admin(message.from_user.id):
        return
    Session = await get_session()
    await run_channel_request_check(bot, Session)
    await run_vip_subscription_check(bot, Session)
    await message.answer("Schedulers ejecutados")
