from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from utils.user_roles import is_admin

router = Router()


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Gestionar Misiones", callback_data="admin_manage_missions")],
        [InlineKeyboardButton(text="Gestionar Niveles", callback_data="admin_manage_levels")],
        [InlineKeyboardButton(text="Gestionar Pistas", callback_data="admin_manage_lore_pieces")],
        [InlineKeyboardButton(text="Volver al Menú Principal del Bot", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Handle both /admin and /panel_admin commands
@router.message(Command(commands=["admin", "panel_admin"]))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Bienvenido al Panel de Administración. Seleccione una opción:",
        reply_markup=get_admin_main_keyboard(),
    )
