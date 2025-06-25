from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.pagination import get_paginated_list
from utils.keyboard_utils import get_admin_mission_list_keyboard, get_back_keyboard
from utils.admin_state import AdminMissionStates, MissionAdminStates
from utils.message_utils import safe_edit_message
from services.mission_service import MissionService
from database.models import Mission, LorePiece

router = Router()


async def show_missions_page(message: Message, session: AsyncSession, page: int) -> None:
    stmt = select(Mission).order_by(Mission.created_at)
    missions, has_prev, has_next, total_pages = await get_paginated_list(session, stmt, page)
    lines = [f"📌 Misiones (Página {page + 1} de {total_pages})"]
    for m in missions:
        mission_line = (
            f"Misión ID: {str(m.id)[:8]} | Título: {m.name} | Tipo: {m.type} | "
            f"Puntos: {m.reward_points} | Activa: {'Sí' if m.is_active else 'No'}"
        )
        lines.append(mission_line)
        lines.append("---")
    text = "\n".join(lines).strip()
    kb = get_admin_mission_list_keyboard(missions, page, has_prev, has_next)
    await safe_edit_message(message, text, kb)


@router.callback_query(F.data == "admin_content_missions")
async def list_missions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_missions_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("missions_page:"))
async def missions_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    page = int(callback.data.split(":")[1])
    await show_missions_page(callback.message, session, page)
    await callback.answer()


@router.callback_query(F.data.startswith("mission_view_details:"))
async def mission_view_details(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[1]
    mission = await MissionService(session).get_mission_by_id(mission_id)
    if not mission:
        return await callback.answer("Misión no encontrada", show_alert=True)

    lore_text = ""
    if mission.unlocks_lore_piece_code:
        stmt = select(LorePiece).where(LorePiece.code_name == mission.unlocks_lore_piece_code)
        lore = (await session.execute(stmt)).scalar_one_or_none()
        if lore:
            lore_text = f"Recompensa: {lore.title}"

    lines = [
        f"ID: {mission.id}",
        f"Título: {mission.name}",
        f"Descripción: {mission.description or '-'}",
        f"Tipo: {mission.type}",
        f"Puntos: {mission.reward_points}",
        f"Activa: {'Sí' if mission.is_active else 'No'}",
    ]
    if lore_text:
        lines.append(lore_text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Editar Misión", callback_data=f"mission_edit:{mission.id}")],
            [InlineKeyboardButton(text="Eliminar Misión", callback_data=f"mission_delete:{mission.id}")],
            [InlineKeyboardButton(text="Activar/Desactivar", callback_data=f"mission_toggle_active:{mission.id}")],
            [InlineKeyboardButton(text="🔙 Volver a Misiones", callback_data="admin_content_missions")],
        ]
    )
    await safe_edit_message(callback.message, "\n".join(lines), keyboard)
    await callback.answer()


@router.callback_query(F.data == "mission_create")
async def mission_create(callback: CallbackQuery, state: FSMContext):
    from .game_admin import admin_start_create_mission
    await admin_start_create_mission(callback, state)


@router.callback_query(F.data.startswith("mission_edit:"))
async def mission_edit(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[1]
    text = "¿Qué campo deseas editar?"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Título", callback_data=f"mission_edit_field:name:{mission_id}")],
            [InlineKeyboardButton(text="Descripción", callback_data=f"mission_edit_field:description:{mission_id}")],
            [InlineKeyboardButton(text="Puntos", callback_data=f"mission_edit_field:points:{mission_id}")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data=f"mission_view_details:{mission_id}")],
        ]
    )
    await safe_edit_message(callback.message, text, kb)
    await callback.answer()


@router.callback_query(F.data.startswith("mission_edit_field:"))
async def mission_edit_field(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    _, field, mission_id = callback.data.split(":")
    prompts = {
        "name": "Nuevo título de la misión:",
        "description": "Nueva descripción:",
        "points": "Nuevo valor de puntos:",
    }
    states = {
        "name": MissionAdminStates.editing_name,
        "description": MissionAdminStates.editing_description,
        "points": MissionAdminStates.editing_reward,
    }
    await state.update_data(mission_id=mission_id)
    await safe_edit_message(
        callback.message,
        prompts[field],
        get_back_keyboard(f"mission_edit:{mission_id}"),
    )
    await state.set_state(states[field])
    await callback.answer()


@router.message(MissionAdminStates.editing_name)
async def process_edit_name(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    mission_id = data.get("mission_id")
    await MissionService(session).update_mission(mission_id, name=message.text)
    await message.answer("Misión actualizada")
    await state.clear()


@router.message(MissionAdminStates.editing_description)
async def process_edit_description(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    mission_id = data.get("mission_id")
    await MissionService(session).update_mission(mission_id, description=message.text)
    await message.answer("Misión actualizada")
    await state.clear()


@router.message(MissionAdminStates.editing_reward)
async def process_edit_reward(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    mission_id = data.get("mission_id")
    try:
        points = int(message.text)
    except ValueError:
        await message.answer("Ingresa un número válido")
        return
    await MissionService(session).update_mission(mission_id, reward_points=points)
    await message.answer("Misión actualizada")
    await state.clear()


@router.callback_query(F.data.startswith("mission_delete:"))
async def mission_delete(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[1]
    mission = await MissionService(session).get_mission_by_id(mission_id)
    if not mission:
        return await callback.answer("Misión no encontrada", show_alert=True)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sí, Eliminar", callback_data=f"mission_delete_confirm:{mission_id}")],
            [InlineKeyboardButton(text="Cancelar", callback_data=f"mission_view_details:{mission_id}")],
        ]
    )
    await safe_edit_message(callback.message, f"¿Eliminar permanentemente '{mission.name}'?", kb)
    await callback.answer()


@router.callback_query(F.data.startswith("mission_delete_confirm:"))
async def mission_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[1]
    mission = await MissionService(session).get_mission_by_id(mission_id)
    if not mission:
        return await callback.answer("Misión no encontrada", show_alert=True)
    await MissionService(session).delete_mission(mission_id)
    await safe_edit_message(callback.message, f"Misión '{mission.name}' eliminada.")
    await list_missions(callback, session)
    await callback.answer()


@router.callback_query(F.data.startswith("mission_toggle_active:"))
async def mission_toggle_active(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[1]
    service = MissionService(session)
    mission = await service.get_mission_by_id(mission_id)
    if not mission:
        return await callback.answer("Misión no encontrada", show_alert=True)
    await service.toggle_mission_status(mission_id, not mission.is_active)
    status = "Activa" if not mission.is_active else "Inactiva"
    await callback.answer(f"Misión ahora está {status}.", show_alert=True)
    await show_missions_page(callback.message, session, 0)
