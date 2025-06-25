from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.pagination import get_paginated_list
from utils.keyboard_utils import get_admin_level_list_keyboard, get_back_keyboard
from utils.message_utils import safe_edit_message
from services.level_service import LevelService
from database.models import Level, LorePiece

router = Router()

async def show_levels_page(message: Message, session: AsyncSession, page: int) -> None:
    stmt = select(Level).order_by(Level.level_id)
    levels, has_prev, has_next, _ = await get_paginated_list(session, stmt, page)
    text = "📈 Niveles"
    kb = get_admin_level_list_keyboard(levels, page, has_prev, has_next)
    await safe_edit_message(message, text, kb)


@router.callback_query(F.data == "admin_content_levels")
async def list_levels(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_levels_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("levels_page:"))
async def levels_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    page = int(callback.data.split(":")[1])
    await show_levels_page(callback.message, session, page)
    await callback.answer()


@router.callback_query(F.data.startswith("level_view_details:"))
async def level_view_details(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    level_id = int(callback.data.split(":")[1])
    level = await session.get(Level, level_id)
    if not level:
        return await callback.answer("Nivel no encontrado", show_alert=True)
    lines = [
        f"**Nivel {level.level_id} - {level.name}**",
        f"Pts Mínimos: {level.min_points}",
        f"Recompensa: {level.reward or '-'}",
    ]
    if level.unlocks_lore_piece_code:
        stmt = select(LorePiece).where(LorePiece.code_name == level.unlocks_lore_piece_code)
        lore = (await session.execute(stmt)).scalar_one_or_none()
        if lore:
            lines.append(f"Pista: {lore.title}")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Editar Nivel", callback_data=f"level_edit:{level.level_id}")],
            [InlineKeyboardButton(text="Eliminar Nivel", callback_data=f"level_delete:{level.level_id}")],
            [InlineKeyboardButton(text="🔙 Volver a Niveles", callback_data="admin_content_levels")],
        ]
    )
    await safe_edit_message(callback.message, "\n".join(lines), kb)
    await callback.answer()


@router.callback_query(F.data == "level_create")
async def level_create(callback: CallbackQuery, state: FSMContext):
    from .game_admin import admin_level_add
    await admin_level_add(callback, state)


@router.callback_query(F.data.startswith("level_edit:"))
async def level_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    from .game_admin import start_edit_level
    level_id = callback.data.split(":")[1]
    callback.data = f"edit_level_{level_id}"
    await start_edit_level(callback, state, session)


@router.callback_query(F.data.startswith("level_delete:"))
async def level_delete(callback: CallbackQuery, session: AsyncSession):
    from .game_admin import confirm_del_level
    level_id = callback.data.split(":")[1]
    callback.data = f"del_level_{level_id}"
    await confirm_del_level(callback, session)


@router.callback_query(F.data.startswith("confirm_del_level_"))
async def level_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    from .game_admin import delete_level
    await delete_level(callback, session)

