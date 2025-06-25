from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.pagination import get_paginated_list
from utils.keyboard_utils import get_admin_reward_list_keyboard, get_back_keyboard
from utils.message_utils import safe_edit_message
from services.reward_service import RewardService
from database.models import Reward

router = Router()

async def show_rewards_page(message: Message, session: AsyncSession, page: int) -> None:
    stmt = select(Reward).order_by(Reward.id)
    rewards, has_prev, has_next, _ = await get_paginated_list(session, stmt, page)
    text = "🎁 Recompensas"
    kb = get_admin_reward_list_keyboard(rewards, page, has_prev, has_next)
    await safe_edit_message(message, text, kb)


@router.callback_query(F.data == "admin_content_rewards")
async def list_rewards(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_rewards_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("rewards_page:"))
async def rewards_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    page = int(callback.data.split(":")[1])
    await show_rewards_page(callback.message, session, page)
    await callback.answer()


@router.callback_query(F.data.startswith("reward_view_details:"))
async def reward_view_details(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    reward_id = int(callback.data.split(":")[1])
    reward = await session.get(Reward, reward_id)
    if not reward:
        return await callback.answer("Recompensa no encontrada", show_alert=True)
    lines = [
        f"ID: {reward.id}",
        f"Nombre: {reward.title}",
        f"Tipo: {reward.reward_type or '-'}",
        f"Valor: {reward.required_points}",
        f"Descripción: {reward.description or '-'}",
        f"Activa: {'Sí' if reward.is_active else 'No'}",
    ]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Editar Recompensa", callback_data=f"reward_edit:{reward.id}")],
            [InlineKeyboardButton(text="Eliminar Recompensa", callback_data=f"reward_delete:{reward.id}")],
            [InlineKeyboardButton(text="Activar/Desactivar", callback_data=f"reward_toggle_active:{reward.id}")],
            [InlineKeyboardButton(text="🔙 Volver a Recompensas", callback_data="admin_content_rewards")],
        ]
    )
    await safe_edit_message(callback.message, "\n".join(lines), kb)
    await callback.answer()


@router.callback_query(F.data == "reward_create")
async def reward_create(callback: CallbackQuery, state: FSMContext):
    from .game_admin import admin_reward_add
    await admin_reward_add(callback, state)


@router.callback_query(F.data.startswith("reward_edit:"))
async def reward_edit(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    from .game_admin import start_edit_reward
    reward_id = callback.data.split(":")[1]
    callback.data = f"edit_reward_{reward_id}"
    await start_edit_reward(callback, session, state)


@router.callback_query(F.data.startswith("reward_delete:"))
async def reward_delete(callback: CallbackQuery, session: AsyncSession):
    from .game_admin import confirm_delete_reward
    reward_id = callback.data.split(":")[1]
    callback.data = f"del_reward_{reward_id}"
    await confirm_delete_reward(callback, session)


@router.callback_query(F.data.startswith("confirm_del_reward_"))
async def reward_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    from .game_admin import delete_reward
    await delete_reward(callback, session)


@router.callback_query(F.data.startswith("reward_toggle_active:"))
async def reward_toggle_active(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    reward_id = int(callback.data.split(":")[1])
    service = RewardService(session)
    reward = await service.get_reward_by_id(reward_id)
    if not reward:
        return await callback.answer("Recompensa no encontrada", show_alert=True)
    await service.toggle_reward_status(reward_id, not reward.is_active)
    status = "Activa" if not reward.is_active else "Inactiva"
    await callback.answer(f"Recompensa ahora está {status}", show_alert=True)
    await show_rewards_page(callback.message, session, 0)

