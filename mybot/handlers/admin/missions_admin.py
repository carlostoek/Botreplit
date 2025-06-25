from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.pagination import paginate
from utils.keyboard_utils import (
    get_game_admin_main_keyboard,
    get_admin_mission_list_keyboard,
    get_back_keyboard,
)
from utils.admin_state import MissionAdminStates
from services.mission_service import MissionService
from database.models import Mission

router = Router()


async def show_missions_page(message: Message, session: AsyncSession, page: int) -> None:
    stmt = select(Mission).order_by(Mission.created_at)
    missions, total, has_prev, has_next = await paginate(session, stmt, page)
    lines = [f"📌 Misiones (página {page + 1})"]
    for m in missions:
        lines.append(f"- {m.name} [{m.id}]")
    kb = get_admin_mission_list_keyboard(missions, page, has_prev, has_next)
    await message.edit_text("\n".join(lines), reply_markup=kb)


@router.callback_query(F.data == "game_admin_main")
async def admin_main_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text("Selecciona una entidad a gestionar:", reply_markup=get_game_admin_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_manage_missions")
async def admin_manage_missions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_missions_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("missions_page:"))
async def missions_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    page = int(callback.data.split(":")[-1])
    await show_missions_page(callback.message, session, page)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_mission:"))
async def edit_mission_start(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[-1]
    mission = await MissionService(session).get_mission_by_id(mission_id)
    if not mission:
        return await callback.answer("Misión no encontrada", show_alert=True)
    await state.update_data(mission_id=mission_id, page=0)
    await callback.message.answer(f"Nuevo nombre para {mission.name}:", reply_markup=get_back_keyboard("admin_manage_missions"))
    await state.set_state(MissionAdminStates.editing_name)
    await callback.answer()


@router.message(MissionAdminStates.editing_name)
async def process_edit_name(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    mission_id = data.get("mission_id")
    page = data.get("page", 0)
    await MissionService(session).update_mission(mission_id, name=message.text)
    await message.answer("Misión actualizada")
    await state.clear()
    await show_missions_page(message, session, page)
