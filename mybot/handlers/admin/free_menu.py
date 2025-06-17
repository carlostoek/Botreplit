from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from keyboards.common import get_back_kb

router = Router()


@router.callback_query(F.data == "admin_free")
async def free_menu(callback: CallbackQuery, session: AsyncSession):
    """Placeholder Free channel admin menu."""
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await update_menu(
        callback,
        "Secci\u00f3n Free en construcci\u00f3n",
        get_back_kb(),
        session,
        "admin_free",
    )
    await callback.answer()
