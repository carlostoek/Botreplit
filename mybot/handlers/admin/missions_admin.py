from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.pagination import paginate
from utils.admin_state import MissionAdminStates
from services.mission_service import MissionService
from database.models import Mission, LorePiece

router = Router()


def build_mission_actions_keyboard(mission: Mission) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(text="Editar", callback_data=f"edit_mission:{mission.id}"),
        InlineKeyboardButton(text="Eliminar", callback_data=f"delete_mission:{mission.id}"),
        InlineKeyboardButton(text="Ver Detalles", callback_data=f"view_mission_details:{mission.id}"),
        InlineKeyboardButton(
            text="Desactivar" if mission.is_active else "Activar",
            callback_data=f"toggle_mission_active:{mission.id}",
        ),
    ]


def build_missions_list_keyboard(missions: list[Mission], page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for m in missions:
        rows.append(build_mission_actions_keyboard(m))
    nav: list[InlineKeyboardButton] = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"missions_page:{page-1}"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"missions_page:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="Crear Nueva Misión", callback_data="create_mission")])
    rows.append([InlineKeyboardButton(text="Volver al Menú Admin", callback_data="admin_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def safe_edit(message: Message, text: str, reply_markup: InlineKeyboardMarkup | None = None):
    if message.text != text or str(message.reply_markup) != str(reply_markup):
        await message.edit_text(text, reply_markup=reply_markup)


async def show_missions_page(message: Message, session: AsyncSession, page: int) -> None:
    stmt = select(Mission).order_by(Mission.created_at)
    missions, _, has_prev, has_next = await paginate(session, stmt, page)
    lines = [f"📌 Misiones (página {page + 1})"]
    for m in missions:
        lines.append(f"ID: {m.id} | Título: {m.name} | Tipo: {m.type}")
    markup = build_missions_list_keyboard(missions, page, has_prev, has_next)
    await safe_edit(message, "\n".join(lines), reply_markup=markup)


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


@router.callback_query(F.data.startswith("view_mission_details:"))
async def view_mission_details(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[-1]
    mission = await MissionService(session).get_mission_by_id(mission_id)
    if not mission:
        return await callback.answer("Misión no encontrada", show_alert=True)
    lore_title = "Ninguna"
    if mission.unlocks_lore_piece_code:
        stmt = select(LorePiece).where(LorePiece.code_name == mission.unlocks_lore_piece_code)
        lore_piece = (await session.execute(stmt)).scalar_one_or_none()
        lore_title = lore_piece.title if lore_piece else "Ninguna"
    text = (
        f"<b>{mission.name}</b> (ID: {mission.id})\n\n"
        f"Tipo: {mission.type}\n"
        f"Puntos: {mission.reward_points}\n"
        f"Descripción: {mission.description or 'Sin descripción'}\n"
        f"Recompensa de Pista: {lore_title}\n"
        f"Estado: {'Activa' if mission.is_active else 'Inactiva'}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Editar Misión", callback_data=f"edit_mission:{mission.id}")],
            [InlineKeyboardButton(text="Eliminar Misión", callback_data=f"delete_mission:{mission.id}")],
            [InlineKeyboardButton(text="Volver a Misiones", callback_data="admin_manage_missions")],
        ]
    )
    await safe_edit(callback.message, text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "create_mission")
async def create_mission(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Cancelar", callback_data="admin_manage_missions")]])
    await callback.message.answer("Ingrese el título de la misión:", reply_markup=kb)
    await state.set_state(MissionAdminStates.waiting_for_name)
    await callback.answer()


@router.message(MissionAdminStates.waiting_for_name)
async def mission_set_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer("Tipo de misión (reaction, daily, weekly, one_time):")
    await state.set_state(MissionAdminStates.waiting_for_type)


@router.message(MissionAdminStates.waiting_for_type)
async def mission_set_type(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(mission_type=message.text)
    await message.answer("Puntos de recompensa:")
    await state.set_state(MissionAdminStates.waiting_for_points)


@router.message(MissionAdminStates.waiting_for_points)
async def mission_set_points(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        points = int(message.text)
    except ValueError:
        await message.answer("Ingrese un número válido de puntos:")
        return
    await state.update_data(points=points)
    await message.answer("Descripción de la misión:")
    await state.set_state(MissionAdminStates.waiting_for_description)


@router.message(MissionAdminStates.waiting_for_description)
async def mission_set_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text)
    await message.answer("Código de la pista de recompensa (o '-' para ninguna):")
    await state.set_state(MissionAdminStates.waiting_for_lore_piece_code)


@router.message(MissionAdminStates.waiting_for_lore_piece_code)
async def mission_finish_creation(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    lore_code = message.text.strip()
    lore_code = lore_code if lore_code != "-" else None
    try:
        mission = await MissionService(session).create_mission(
            name=data["name"],
            description=data["description"],
            mission_type=data["mission_type"],
            target_value=1,
            reward_points=data["points"],
            duration_days=0,
            requires_action=False,
            action_data=None,
        )
        if lore_code:
            await MissionService(session).update_mission(mission.id, unlocks_lore_piece_code=lore_code)
        await message.answer(f"¡Misión '{mission.name}' creada exitosamente!")
    except Exception as e:
        await message.answer(f"Error al crear misión: {e}")
    await state.clear()


@router.callback_query(F.data.startswith("edit_mission:"))
async def edit_mission(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[-1]
    await state.update_data(mission_id=mission_id)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Título", callback_data=f"edit_mission_field:name:{mission_id}")],
            [InlineKeyboardButton(text="Tipo", callback_data=f"edit_mission_field:type:{mission_id}")],
            [InlineKeyboardButton(text="Puntos", callback_data=f"edit_mission_field:points:{mission_id}")],
            [InlineKeyboardButton(text="Descripción", callback_data=f"edit_mission_field:description:{mission_id}")],
            [InlineKeyboardButton(text="Pista", callback_data=f"edit_mission_field:lore:{mission_id}")],
            [InlineKeyboardButton(text="Volver", callback_data="admin_manage_missions")],
        ]
    )
    await callback.message.edit_text("Seleccione el campo a editar:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_mission_field:"))
async def edit_mission_field(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    parts = callback.data.split(":")
    field = parts[1]
    mission_id = parts[2]
    await state.update_data(mission_id=mission_id, field=field)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Cancelar", callback_data="admin_manage_missions")]])
    await callback.message.edit_text("Ingrese el nuevo valor:", reply_markup=kb)
    await state.set_state(MissionAdminStates.editing_field)
    await callback.answer()


@router.message(MissionAdminStates.editing_field)
async def save_field_value(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    mission_id = data["mission_id"]
    field = data["field"]
    value = message.text
    update_kwargs = {}
    if field == "points":
        try:
            value = int(value)
        except ValueError:
            await message.answer("Ingrese un número válido:")
            return
        update_kwargs["reward_points"] = value
    elif field == "name":
        update_kwargs["name"] = value
    elif field == "type":
        update_kwargs["type"] = value
    elif field == "description":
        update_kwargs["description"] = value
    elif field == "lore":
        update_kwargs["unlocks_lore_piece_code"] = value if value != "-" else None
    await MissionService(session).update_mission(mission_id, **update_kwargs)
    await message.answer("Campo actualizado.")
    await state.clear()


@router.callback_query(F.data.startswith("delete_mission:"))
async def delete_mission(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[-1]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sí, Eliminar", callback_data=f"confirm_delete_mission:{mission_id}")],
            [InlineKeyboardButton(text="Cancelar", callback_data="admin_manage_missions")],
        ]
    )
    await callback.message.edit_text("¿Estás seguro de que quieres eliminar esta misión?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_mission:"))
async def confirm_delete_mission(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[-1]
    svc = MissionService(session)
    mission = await svc.get_mission_by_id(mission_id)
    if mission:
        await svc.delete_mission(mission_id)
        await callback.message.edit_text(f"Misión '{mission.name}' eliminada.")
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_mission_active:"))
async def toggle_mission_active(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split(":")[-1]
    service = MissionService(session)
    mission = await service.get_mission_by_id(mission_id)
    if not mission:
        return await callback.answer("Misión no encontrada", show_alert=True)
    await service.toggle_mission_status(mission_id, not mission.is_active)
    await callback.answer(f"Misión '{mission.name}' ahora está {'Activa' if not mission.is_active else 'Inactiva'}.")
