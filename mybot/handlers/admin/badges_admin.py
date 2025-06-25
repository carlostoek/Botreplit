from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.pagination import get_paginated_list
from utils.keyboard_utils import get_admin_badge_list_keyboard, get_back_keyboard
from utils.message_utils import safe_edit_message
from services.badge_service import BadgeService
from database.models import Badge

router = Router()

async def show_badges_page(message: Message, session: AsyncSession, page: int) -> None:
    stmt = select(Badge).order_by(Badge.id)
    badges, has_prev, has_next, _ = await get_paginated_list(session, stmt, page)
    text = "🏅 Insignias"
    kb = get_admin_badge_list_keyboard(badges, page, has_prev, has_next)
    await safe_edit_message(message, text, kb)


@router.callback_query(F.data == "admin_content_badges")
async def list_badges(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_badges_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("badges_page:"))
async def badges_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    page = int(callback.data.split(":")[1])
    await show_badges_page(callback.message, session, page)
    await callback.answer()


@router.callback_query(F.data.startswith("badge_view_details:"))
async def badge_view_details(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    badge_id = int(callback.data.split(":")[1])
    badge = await session.get(Badge, badge_id)
    if not badge:
        return await callback.answer("Insignia no encontrada", show_alert=True)
    lines = [
        f"ID: {badge.id}",
        f"Nombre: {badge.name}",
        f"Criterio: {getattr(badge, 'requirement', '')}",
        f"Activa: {'Sí' if badge.is_active else 'No'}",
    ]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Editar Insignia", callback_data=f"badge_edit:{badge.id}")],
            [InlineKeyboardButton(text="Eliminar Insignia", callback_data=f"badge_delete:{badge.id}")],
            [InlineKeyboardButton(text="Activar/Desactivar", callback_data=f"badge_toggle_active:{badge.id}")],
            [InlineKeyboardButton(text="🔙 Volver a Insignias", callback_data="admin_content_badges")],
        ]
    )
    await safe_edit_message(callback.message, "\n".join(lines), kb)
    await callback.answer()


@router.callback_query(F.data == "badge_create")
async def badge_create(callback: CallbackQuery, state: FSMContext):
    from .game_admin import admin_create_badge
    await admin_create_badge(callback, state)


@router.callback_query(F.data.startswith("badge_edit:"))
async def badge_edit(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    from .game_admin import select_badge
    badge_id = callback.data.split(":")[1]
    callback.data = f"select_badge_{badge_id}"
    await select_badge(callback, state, session)


@router.callback_query(F.data.startswith("badge_delete:"))
async def badge_delete(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    from .game_admin import select_badge
    badge_id = callback.data.split(":")[1]
    callback.data = f"select_badge_{badge_id}"
    await select_badge(callback, state, session)


@router.callback_query(F.data == "confirm_delete_badge")
async def badge_delete_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    from .game_admin import confirm_delete_badge
    await confirm_delete_badge(callback, state, session)


@router.callback_query(F.data.startswith("badge_toggle_active:"))
async def badge_toggle_active(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    badge_id = int(callback.data.split(":")[1])
    service = BadgeService(session)
    badge = await session.get(Badge, badge_id)
    if not badge:
        return await callback.answer("Insignia no encontrada", show_alert=True)
    await service.toggle_badge_status(badge_id, not badge.is_active)
    status = "Activa" if not badge.is_active else "Inactiva"
    await callback.answer(f"Insignia ahora está {status}", show_alert=True)
    await show_badges_page(callback.message, session, 0)

