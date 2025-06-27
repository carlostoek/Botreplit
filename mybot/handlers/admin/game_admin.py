from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import datetime

from utils.user_roles import is_admin
from utils.menu_utils import update_menu, send_temporary_reply
from utils.keyboard_utils import (
    get_admin_manage_users_keyboard,
    get_admin_users_list_keyboard,
    get_back_keyboard,
    get_admin_manage_content_keyboard,
    get_admin_content_missions_keyboard,
    get_admin_content_badges_keyboard,
    get_admin_content_levels_keyboard,
    get_admin_content_rewards_keyboard,
    get_admin_content_auctions_keyboard,
    get_admin_content_daily_gifts_keyboard,
    get_admin_content_minigames_keyboard,
    get_badge_selection_keyboard,
    get_reward_type_keyboard,
)
from .missions_admin import show_missions_page
from .levels_admin import show_levels_page
from utils.admin_state import (
    AdminUserStates,
    AdminMissionStates,
    AdminBadgeStates,
    AdminDailyGiftStates,
    AdminRewardStates,
    AdminLevelStates,
)
from services.mission_service import MissionService
from services.reward_service import RewardService
from services.level_service import LevelService
from database.models import User, Mission, Level
from services.point_service import PointService
from services.config_service import ConfigService
from services.badge_service import BadgeService
from utils.messages import BOT_MESSAGES
import logging

logger = logging.getLogger(__name__)

router = Router()


async def show_users_page(message: Message, session: AsyncSession, offset: int) -> None:
    """Display a paginated list of users with action buttons."""
    limit = 5
    if offset < 0:
        offset = 0

    total_stmt = select(func.count()).select_from(User)
    total_result = await session.execute(total_stmt)
    total_users = total_result.scalar_one()

    stmt = (
        select(User)
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    users = result.scalars().all()

    text_lines = [
        "👥 Gestión de Usuarios",
        f"Mostrando {offset + 1}-{min(offset + limit, total_users)} de {total_users}",
        "",
    ]

    for user in users:
        display = user.username or (user.first_name or "Sin nombre")
        text_lines.append(f"- {display} (ID: {user.id}) - {user.points} pts")

    keyboard = get_admin_users_list_keyboard(users, offset, total_users, limit)

    await message.edit_text("\n".join(text_lines), reply_markup=keyboard)


@router.callback_query(F.data == "admin_manage_users")
async def admin_manage_users(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_users_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_users_page_"))
async def admin_users_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    try:
        offset = int(callback.data.split("_")[-1])
    except ValueError:
        offset = 0
    await show_users_page(callback.message, session, offset)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_add_"))
async def admin_user_add(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    await state.update_data(points_operation="add", target_user=user_id)
    await callback.message.answer(
        f"Ingresa la cantidad de puntos a sumar a {user_id}:",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminUserStates.assigning_points_amount)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_deduct_"))
async def admin_user_deduct(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    await state.update_data(points_operation="deduct", target_user=user_id)
    await callback.message.answer(
        f"Ingresa la cantidad de puntos a restar a {user_id}:",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminUserStates.assigning_points_amount)
    await callback.answer()


@router.message(AdminUserStates.assigning_points_amount)
async def process_points_amount(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    try:
        amount = int(message.text)
    except ValueError:
        await send_temporary_reply(message, "Cantidad inválida. Ingresa un número.")
        return
    user_id = data.get("target_user")
    op = data.get("points_operation")
    service = PointService(session)
    if op == "add":
        await service.add_points(user_id, amount)
        await message.answer(f"Se han sumado {amount} puntos a {user_id}.")
    else:
        await service.deduct_points(user_id, amount)
        await message.answer(f"Se han restado {amount} puntos a {user_id}.")
    await state.clear()


@router.callback_query(F.data.startswith("admin_user_view_"))
async def admin_view_user(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Usuario no encontrado", show_alert=True)
        return
    display = user.username or (user.first_name or "Sin nombre")
    await callback.message.answer(f"Perfil de {display}\nPuntos: {user.points}")
    await callback.answer()


@router.callback_query(F.data == "admin_search_user")
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa un ID o nombre de usuario:",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminUserStates.search_user_query)
    await callback.answer()


@router.message(AdminUserStates.search_user_query)
async def process_search_user(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    query = message.text.strip()
    users = []
    if query.isdigit():
        user = await session.get(User, int(query))
        if user:
            users = [user]
    else:
        stmt = select(User).where(
            (User.username.ilike(f"%{query}%")) |
            (User.first_name.ilike(f"%{query}%")) |
            (User.last_name.ilike(f"%{query}%"))
        ).limit(10)
        result = await session.execute(stmt)
        users = result.scalars().all()

    if not users:
        await send_temporary_reply(message, "No se encontraron usuarios.")
    else:
        response = "Resultados:\n" + "\n".join(
            f"- {(u.username or u.first_name or 'Sin nombre')} (ID: {u.id})" for u in users
        )
        await message.answer(response)
    await state.clear()


@router.callback_query(F.data == "admin_content_missions")
async def admin_content_missions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_missions_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data == "toggle_daily_gift")
async def toggle_daily_gift(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    service = ConfigService(session)
    current = await service.get_value("daily_gift_enabled")
    new_value = "false" if current == "true" else "true"
    await service.set_value("daily_gift_enabled", new_value)
    await callback.answer("Configuración actualizada", show_alert=True)
    await admin_content_daily_gifts(callback, session)


@router.callback_query(F.data == "admin_create_mission")
async def admin_start_create_mission(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa el nombre de la misión:",
        reply_markup=get_back_keyboard("admin_content_missions"),
    )
    await state.set_state(AdminMissionStates.creating_mission_name)
    await callback.answer()


@router.message(AdminMissionStates.creating_mission_name)
async def admin_process_mission_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer("Ingresa la descripción de la misión:")
    await state.set_state(AdminMissionStates.creating_mission_description)


@router.message(AdminMissionStates.creating_mission_description)
async def admin_process_mission_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Reaccionar a publicaciones", callback_data="mission_type_reaction")],
            [InlineKeyboardButton(text="📝 Enviar mensajes", callback_data="mission_type_messages")],
            [InlineKeyboardButton(text="📅 Conectarse X días seguidos", callback_data="mission_type_login")],
            [InlineKeyboardButton(text="🎯 Personalizada", callback_data="mission_type_custom")],
        ]
    )
    await message.answer("🎯 Tipo de misión", reply_markup=kb)
    await state.set_state(AdminMissionStates.creating_mission_type)


@router.callback_query(F.data.startswith("mission_type_"))
async def admin_select_mission_type(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    m_type = callback.data.split("mission_type_")[-1]
    mapping = {
        "reaction": "reaction",
        "messages": "messages",
        "login": "login_streak",
        "custom": "custom",
    }
    await state.update_data(type=mapping.get(m_type, m_type))
    await callback.message.edit_text("📊 Cantidad requerida")
    await state.set_state(AdminMissionStates.creating_mission_target)
    await callback.answer()


@router.message(AdminMissionStates.creating_mission_target)
async def admin_process_target(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        value = int(message.text)
    except ValueError:
        await message.answer("Ingresa un número válido:")
        return
    await state.update_data(target=value)
    await message.answer("🏆 Recompensa en puntos")
    await state.set_state(AdminMissionStates.creating_mission_reward)


@router.message(AdminMissionStates.creating_mission_reward)
async def admin_process_reward(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        points = int(message.text)
    except ValueError:
        await message.answer("Ingresa un número válido de puntos:")
        return
    await state.update_data(reward=points)
    await message.answer("⏳ Duración (en días, 0 para permanente)")
    await state.set_state(AdminMissionStates.creating_mission_duration)

@router.message(AdminMissionStates.creating_mission_duration)
async def admin_process_duration(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        days = int(message.text)
        if days < 0:
            await message.answer("❌ La duración debe ser un número positivo")
            return
    except ValueError:
        await message.answer("❌ Ingresa un número válido de días:")
        return

    data = await state.get_data()

    try:
        from mybot.database import get_async_session
        from mybot.services.mission_service import MissionService

        mission_service = MissionService(get_async_session)

        mission = await mission_service.create_mission(
            name=data["name"],
            description=data["description"],
            mission_type=data["type"],
            target_value=int(data["target"]),
            reward_points=int(data["reward"]),
            duration_days=days,
        )

        await message.answer(
            f"✅ Misión '{mission.name}' creada correctamente!\n" f"🆔 ID: {mission.id}",
            reply_markup=get_admin_content_missions_keyboard(),
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Error creating mission: {e}")
        await message.answer(
            "❌ Error al crear la misión. Inténtalo de nuevo.",
            reply_markup=get_admin_content_missions_keyboard(),
        )
        await state.clear()



@router.callback_query(F.data == "admin_toggle_mission")
async def admin_toggle_mission_menu(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    result = await session.execute(select(Mission))
    missions = result.scalars().all()
    keyboard = []
    for m in missions:
        status = "✅" if m.is_active else "❌"
        keyboard.append(
            [InlineKeyboardButton(text=f"{status} {m.name}", callback_data=f"toggle_mission_{m.id}")]
        )
    keyboard.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_missions")])
    await callback.message.edit_text(
        "Activar o desactivar misiones:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_mission_"))
async def toggle_mission_status(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split("toggle_mission_")[-1]
    mission_service = MissionService(session)
    mission = await mission_service.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("Misión no encontrada", show_alert=True)
        return
    await mission_service.toggle_mission_status(mission_id, not mission.is_active)
    status = "activada" if not mission.is_active else "desactivada"
    await callback.answer(f"Misión {status}", show_alert=True)
    # Refresh list
    result = await session.execute(select(Mission))
    missions = result.scalars().all()
    keyboard = []
    for m in missions:
        status_icon = "✅" if m.is_active else "❌"
        keyboard.append(
            [InlineKeyboardButton(text=f"{status_icon} {m.name}", callback_data=f"toggle_mission_{m.id}")]
        )
    keyboard.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_missions")])
    await callback.message.edit_text(
        "Activar o desactivar misiones:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


@router.callback_query(F.data == "admin_view_missions")
async def admin_view_active_missions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    stmt = select(Mission).where(Mission.is_active == True)
    result = await session.execute(stmt)
    missions = result.scalars().all()
    now = datetime.datetime.utcnow()
    lines = []
    for m in missions:
        remaining = "∞"
        if m.duration_days:
            end = m.created_at + datetime.timedelta(days=m.duration_days)
            remaining = str((end - now).days)
        lines.append(f"🗒️ {m.name} | 📊 {m.target_value} | 🎁 {m.reward_points} | ⏳ {remaining}d")
    text = "Misiones activas:" if lines else "No hay misiones activas."
    if lines:
        text += "\n" + "\n".join(lines)
    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard("admin_content_missions"),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_delete_mission")
async def admin_delete_mission_menu(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    result = await session.execute(select(Mission))
    missions = result.scalars().all()
    keyboard = [[InlineKeyboardButton(text=m.name, callback_data=f"delete_mission_{m.id}")] for m in missions]
    keyboard.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_missions")])
    await callback.message.edit_text(
        "Selecciona la misión a eliminar:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_mission_"))
async def admin_confirm_delete_mission(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split("delete_mission_")[-1]
    mission = await session.get(Mission, mission_id)
    if not mission:
        await callback.answer("Misión no encontrada", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm_delete_{mission_id}")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="admin_delete_mission")],
        ]
    )
    await callback.message.edit_text(
        f"¿Eliminar misión {mission.name}?",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def admin_delete_mission(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = callback.data.split("confirm_delete_")[-1]
    service = MissionService(session)
    await service.delete_mission(mission_id)
    await callback.message.edit_text(
        "❌ Misión eliminada",
        reply_markup=get_admin_content_missions_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_badges")
async def admin_content_badges(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await update_menu(
        callback,
        "🏅 Insignias - Selecciona una opción:",
        get_admin_content_badges_keyboard(),
        session,
        "admin_content_badges",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_badge")
async def admin_create_badge(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "📛 Nombre de la insignia:",
        reply_markup=get_back_keyboard("admin_content_badges"),
    )
    await state.set_state(AdminBadgeStates.creating_badge_name)
    await callback.answer()


@router.message(AdminBadgeStates.creating_badge_name)
async def badge_name_step(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await message.answer("📝 Descripción (corta):")
    await state.set_state(AdminBadgeStates.creating_badge_description)


@router.message(AdminBadgeStates.creating_badge_description)
async def badge_description_step(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text.strip())
    await message.answer("🎯 Requisito (ej. 'Alcanzar nivel 5'):")
    await state.set_state(AdminBadgeStates.creating_badge_requirement)


@router.message(AdminBadgeStates.creating_badge_requirement)
async def badge_requirement_step(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(requirement=message.text.strip())
    await message.answer("🖼️ Emoji o símbolo (opcional, escribe 'no' para omitir):")
    await state.set_state(AdminBadgeStates.creating_badge_emoji)


@router.message(AdminBadgeStates.creating_badge_emoji)
async def badge_emoji_step(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    emoji = message.text.strip()
    if emoji.lower() in {"no", "none", "-"}:
        emoji = None
    data = await state.get_data()
    service = BadgeService(session)
    await service.create_badge(
        data.get("name", ""),
        data.get("description", ""),
        data.get("requirement", ""),
        emoji,
    )
    await message.answer(
        "Insignia creada correctamente", reply_markup=get_admin_content_badges_keyboard()
    )
    await state.clear()


@router.callback_query(F.data == "admin_view_badges")
async def admin_view_badges(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    service = BadgeService(session)
    badges = await service.list_badges()
    if badges:
        lines = [f"{b.id}. {b.emoji or ''} {b.name} | {b.requirement}" for b in badges]
        text = "\n".join(lines)
    else:
        text = "No hay insignias definidas."
    await callback.message.edit_text(text, reply_markup=get_back_keyboard("admin_content_badges"))
    await callback.answer()


@router.callback_query(F.data == "admin_delete_badge")
async def admin_delete_badge(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    service = BadgeService(session)
    badges = await service.list_badges()
    if not badges:
        await callback.answer("No hay insignias para eliminar", show_alert=True)
        return
    await callback.message.edit_text(
        "Selecciona la insignia a eliminar:",
        reply_markup=get_badge_selection_keyboard(badges),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_badge_"))
async def select_badge(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    badge_id = int(callback.data.split("select_badge_")[-1])
    badge = await session.get(Badge, badge_id)
    if not badge:
        await callback.answer("Insignia no encontrada", show_alert=True)
        return
    await state.update_data(delete_badge_id=badge_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Sí", callback_data="confirm_delete_badge")],
            [InlineKeyboardButton(text="❌ No", callback_data="admin_content_badges")],
        ]
    )
    await callback.message.edit_text(
        f"¿Eliminar '{badge.name}'?", reply_markup=keyboard
    )
    await state.set_state(AdminBadgeStates.deleting_badge)
    await callback.answer()


@router.callback_query(F.data == "confirm_delete_badge")
async def confirm_delete_badge(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    data = await state.get_data()
    badge_id = data.get("delete_badge_id")
    service = BadgeService(session)
    await service.delete_badge(badge_id)
    await callback.message.edit_text(
        "Insignia eliminada", reply_markup=get_admin_content_badges_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "admin_content_levels")
async def admin_content_levels(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await update_menu(
        callback,
        "📈 Niveles - Selecciona una opción:",
        get_admin_content_levels_keyboard(),
        session,
        "admin_content_levels",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_rewards")
async def admin_content_rewards(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await update_menu(
        callback,
        "🎁 Recompensas (Catálogo VIP) - Selecciona una opción:",
        get_admin_content_rewards_keyboard(),
        session,
        "admin_content_rewards",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_auctions")
async def admin_content_auctions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await update_menu(
        callback,
        "📦 Subastas - Selecciona una opción:",
        get_admin_content_auctions_keyboard(),
        session,
        "admin_content_auctions",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_daily_gifts")
async def admin_content_daily_gifts(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    config = ConfigService(session)
    enabled = (await config.get_value("daily_gift_enabled")) != "false"
    toggle_text = "❌ Desactivar" if enabled else "✅ Activar"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data="toggle_daily_gift")],
            [InlineKeyboardButton(text="🎯 Configurar Regalo del Día", callback_data="admin_configure_daily_gift")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")],
        ]
    )
    await update_menu(
        callback,
        "🎁 Regalos Diarios - Selecciona una opción:",
        keyboard,
        session,
        "admin_content_daily_gifts",
    )


@router.callback_query(F.data == "admin_content_minigames")
async def admin_content_minigames(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    config = ConfigService(session)
    enabled = (await config.get_value("minigames_enabled")) != "false"
    toggle_text = "❌ Desactivar" if enabled else "✅ Activar"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data="toggle_minigames")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")],
        ]
    )
    await update_menu(
        callback,
        "🕹 Minijuegos - Configuración:",
        keyboard,
        session,
        "admin_content_minigames",
    )


@router.callback_query(F.data == "toggle_minigames")
async def toggle_minigames(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    service = ConfigService(session)
    current = await service.get_value("minigames_enabled")
    new_value = "false" if current == "true" else "true"
    await service.set_value("minigames_enabled", new_value)
    await callback.answer("Configuración actualizada", show_alert=True)
    await admin_content_minigames(callback, session)


@router.callback_query(F.data == "admin_configure_daily_gift")
async def configure_daily_gift(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa la cantidad de puntos para el regalo diario:",
        reply_markup=get_back_keyboard("admin_content_daily_gifts"),
    )
    await state.set_state(AdminDailyGiftStates.waiting_for_amount)
    await callback.answer()


@router.message(AdminDailyGiftStates.waiting_for_amount)
async def save_daily_gift_amount(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("Ingresa un número válido.")
        return
    service = ConfigService(session)
    await service.set_value("daily_gift_points", str(amount))
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_daily_gifts")]
        ]
    )
    await message.answer(
        "Regalo diario actualizado.", reply_markup=keyboard
    )
    await state.clear()


# --- Gestión de Recompensas ---

@router.callback_query(F.data == "admin_reward_add")
async def admin_reward_add(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        BOT_MESSAGES["enter_reward_name"],
        reply_markup=get_back_keyboard("admin_content_rewards"),
    )
    await state.set_state(AdminRewardStates.creating_reward_name)
    await callback.answer()


@router.message(AdminRewardStates.creating_reward_name)
async def process_reward_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer(BOT_MESSAGES["enter_reward_points"])
    await state.set_state(AdminRewardStates.creating_reward_points)


@router.message(AdminRewardStates.creating_reward_points)
async def process_reward_points(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        points = int(message.text)
    except ValueError:
        await message.answer(BOT_MESSAGES["invalid_number"])
        return
    await state.update_data(points=points)
    await message.answer(BOT_MESSAGES["enter_reward_description"])
    await state.set_state(AdminRewardStates.creating_reward_description)


@router.message(AdminRewardStates.creating_reward_description)
async def process_reward_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    desc = message.text
    if desc.lower() in ["skip", "-"]:
        desc = None
    await state.update_data(description=desc)
    await message.answer(
        BOT_MESSAGES["select_reward_type"], reply_markup=get_reward_type_keyboard()
    )
    await state.set_state(AdminRewardStates.creating_reward_type)


@router.callback_query(AdminRewardStates.creating_reward_type, F.data.startswith("reward_type_"))
async def process_reward_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    r_type = callback.data.split("reward_type_")[-1]
    data = await state.get_data()
    service = RewardService(session)
    await service.create_reward(
        data["name"],
        data["points"],
        description=data.get("description"),
        reward_type=r_type,
    )
    await callback.message.edit_text(
        BOT_MESSAGES["reward_created"], reply_markup=get_admin_content_rewards_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "admin_reward_view")
async def admin_reward_view(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    rewards = await RewardService(session).list_rewards()
    lines = [
        f"{r.id}. {r.title} - {r.required_points} pts ({r.reward_type or '-'})"
        for r in rewards
    ]
    keyboard = [
        [
            InlineKeyboardButton(text="✏️", callback_data=f"edit_reward_{r.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"del_reward_{r.id}"),
        ]
        for r in rewards
    ]
    keyboard.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_content_rewards")])
    text = "Lista de recompensas:" if lines else "No hay recompensas."
    if lines:
        text += "\n" + "\n".join(lines)
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_reward_delete")
async def admin_reward_delete(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    rewards = await RewardService(session).list_rewards()
    keyboard = [[InlineKeyboardButton(text=r.title, callback_data=f"del_reward_{r.id}")] for r in rewards]
    keyboard.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_content_rewards")])
    await callback.message.edit_text(
        "Selecciona la recompensa a eliminar:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_reward_"))
async def confirm_delete_reward(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    reward_id = int(callback.data.split("del_reward_")[-1])
    reward = await RewardService(session).get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("Recompensa no encontrada", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm_del_reward_{reward_id}")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="admin_reward_delete")],
        ]
    )
    await callback.message.edit_text(
        f"¿Eliminar recompensa {reward.title}?",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_reward_"))
async def delete_reward(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    reward_id = int(callback.data.split("confirm_del_reward_")[-1])
    service = RewardService(session)
    await service.delete_reward(reward_id)
    await callback.message.edit_text(
        BOT_MESSAGES["reward_deleted"], reply_markup=get_admin_content_rewards_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_reward_edit")
async def admin_reward_edit(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    rewards = await RewardService(session).list_rewards()
    keyboard = [[InlineKeyboardButton(text=r.title, callback_data=f"edit_reward_{r.id}")] for r in rewards]
    keyboard.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_content_rewards")])
    await callback.message.edit_text(
        "Selecciona la recompensa a editar:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_reward_"))
async def start_edit_reward(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    reward_id = int(callback.data.split("edit_reward_")[-1])
    reward = await RewardService(session).get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("Recompensa no encontrada", show_alert=True)
        return
    await state.update_data(reward_id=reward_id)
    await callback.message.edit_text(
        BOT_MESSAGES["enter_reward_name"],
        reply_markup=get_back_keyboard("admin_reward_edit"),
    )
    await state.set_state(AdminRewardStates.editing_reward_name)
    await callback.answer()


@router.message(AdminRewardStates.editing_reward_name)
async def edit_reward_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer(BOT_MESSAGES["enter_reward_points"])
    await state.set_state(AdminRewardStates.editing_reward_points)


@router.message(AdminRewardStates.editing_reward_points)
async def edit_reward_points(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        points = int(message.text)
    except ValueError:
        await message.answer(BOT_MESSAGES["invalid_number"])
        return
    await state.update_data(points=points)
    await message.answer(BOT_MESSAGES["enter_reward_description"])
    await state.set_state(AdminRewardStates.editing_reward_description)


@router.message(AdminRewardStates.editing_reward_description)
async def edit_reward_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    desc = message.text
    if desc.lower() in ["skip", "-"]:
        desc = None
    await state.update_data(description=desc)
    await message.answer(
        BOT_MESSAGES["select_reward_type"], reply_markup=get_reward_type_keyboard()
    )
    await state.set_state(AdminRewardStates.editing_reward_type)


@router.callback_query(AdminRewardStates.editing_reward_type, F.data.startswith("reward_type_"))
async def finish_edit_reward(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    r_type = callback.data.split("reward_type_")[-1]
    data = await state.get_data()
    service = RewardService(session)
    await service.update_reward(
        data["reward_id"],
        title=data.get("name"),
        required_points=data.get("points"),
        description=data.get("description"),
        reward_type=r_type,
    )
    await callback.message.edit_text(
        BOT_MESSAGES["reward_updated"], reply_markup=get_admin_content_rewards_keyboard()
    )
    await state.clear()
    await callback.answer()


# --- Gestión de Niveles ---

@router.callback_query(F.data == "admin_levels_view")
async def admin_levels_view(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_levels_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data == "admin_level_add")
async def admin_level_add(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Número del nivel:", reply_markup=get_back_keyboard("admin_content_levels")
    )
    await state.set_state(AdminLevelStates.creating_level_number)
    await callback.answer()


@router.message(AdminLevelStates.creating_level_number)
async def level_add_number(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        num = int(message.text)
    except ValueError:
        await send_temporary_reply(message, BOT_MESSAGES["invalid_number"])
        return
    await state.update_data(level_number=num)
    await message.answer("Nombre del nivel:")
    await state.set_state(AdminLevelStates.creating_level_name)


@router.message(AdminLevelStates.creating_level_name)
async def level_add_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer("Puntos requeridos:")
    await state.set_state(AdminLevelStates.creating_level_points)


@router.message(AdminLevelStates.creating_level_points)
async def level_add_points(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        pts = int(message.text)
    except ValueError:
        await send_temporary_reply(message, BOT_MESSAGES["invalid_number"])
        return
    await state.update_data(points=pts)
    await message.answer("Recompensa (opcional, '-' para ninguna):")
    await state.set_state(AdminLevelStates.creating_level_reward)


@router.message(AdminLevelStates.creating_level_reward)
async def level_add_reward(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    reward = message.text
    if reward.lower() in {"-", "none", "no", "skip"}:
        reward = None
    await state.update_data(reward=reward)
    data = await state.get_data()
    text = (
        f"Crear nivel {data['level_number']} - {data['name']} con {data['points']} pts"
        f" y recompensa '{data['reward'] or '-'}'?"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Confirmar", callback_data="confirm_create_level")],
            [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_content_levels")],
        ]
    )
    await message.answer(text, reply_markup=kb)
    await state.set_state(AdminLevelStates.confirming_create_level)


@router.callback_query(F.data == "confirm_create_level")
async def confirm_create_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    data = await state.get_data()
    service = LevelService(session)
    await service.create_level(
        data["level_number"], data["name"], data["points"], reward=data.get("reward")
    )
    await callback.message.edit_text(
        BOT_MESSAGES["level_created"], reply_markup=get_admin_content_levels_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "admin_level_edit")
async def admin_level_edit(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    levels = await LevelService(session).list_levels()
    keyboard = [
        [InlineKeyboardButton(text=f"{l.level_id}. {l.name}", callback_data=f"edit_level_{l.level_id}")]
        for l in levels
    ]
    keyboard.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_content_levels")])
    await callback.message.edit_text(
        "Selecciona el nivel a editar:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_level_"))
async def start_edit_level(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    level_id: int | None = None,
):
    """Initiate the level editing conversation."""
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    lvl_id = level_id if level_id is not None else int(callback.data.split("edit_level_")[-1])
    level = await session.get(Level, lvl_id)
    if not level:
        await callback.answer("Nivel no encontrado", show_alert=True)
        return
    await state.update_data(level_id=lvl_id)
    await callback.message.edit_text(
        "Nuevo número de nivel:", reply_markup=get_back_keyboard("admin_level_edit")
    )
    await state.set_state(AdminLevelStates.editing_level_number)
    await callback.answer()


@router.message(AdminLevelStates.editing_level_number)
async def edit_level_number(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        num = int(message.text)
    except ValueError:
        await send_temporary_reply(message, BOT_MESSAGES["invalid_number"])
        return
    await state.update_data(new_number=num)
    await message.answer("Nuevo nombre:")
    await state.set_state(AdminLevelStates.editing_level_name)


@router.message(AdminLevelStates.editing_level_name)
async def edit_level_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(new_name=message.text)
    await message.answer("Nuevos puntos requeridos:")
    await state.set_state(AdminLevelStates.editing_level_points)


@router.message(AdminLevelStates.editing_level_points)
async def edit_level_points(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        pts = int(message.text)
    except ValueError:
        await send_temporary_reply(message, BOT_MESSAGES["invalid_number"])
        return
    await state.update_data(new_points=pts)
    await message.answer("Nueva recompensa (opcional, '-' para ninguna):")
    await state.set_state(AdminLevelStates.editing_level_reward)


@router.message(AdminLevelStates.editing_level_reward)
async def finish_edit_level(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    reward = message.text
    if reward.lower() in {"-", "none", "no", "skip"}:
        reward = None
    data = await state.get_data()
    service = LevelService(session)
    await service.update_level(
        data["level_id"],
        new_level_number=data.get("new_number"),
        name=data.get("new_name"),
        required_points=data.get("new_points"),
        reward=reward,
    )
    await message.answer(
        BOT_MESSAGES["level_updated"], reply_markup=get_admin_content_levels_keyboard()
    )
    await state.clear()


@router.callback_query(F.data == "admin_level_delete")
async def admin_level_delete(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    levels = await LevelService(session).list_levels()
    if len(levels) <= 1:
        await callback.answer("No se puede eliminar el último nivel", show_alert=True)
        return
    keyboard = [
        [InlineKeyboardButton(text=f"{l.level_id}. {l.name}", callback_data=f"del_level_{l.level_id}")]
        for l in levels
    ]
    keyboard.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_content_levels")])
    await callback.message.edit_text(
        "Selecciona el nivel a eliminar:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_level_"))
async def confirm_del_level(
    callback: CallbackQuery,
    session: AsyncSession,
    level_id: int | None = None,
):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    lvl_id = level_id if level_id is not None else int(callback.data.split("del_level_")[-1])
    service = LevelService(session)
    levels = await service.list_levels()
    if len(levels) <= 1:
        await callback.answer("No se puede eliminar el último nivel", show_alert=True)
        return
    level = await session.get(Level, lvl_id)
    if not level:
        await callback.answer("Nivel no encontrado", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm_del_level_{lvl_id}")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="admin_level_delete")],
        ]
    )
    await callback.message.edit_text(
        f"¿Eliminar nivel {level.level_id} - {level.name}?", reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_level_"))
async def delete_level(
    callback: CallbackQuery,
    session: AsyncSession,
    level_id: int | None = None,
):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    lvl_id = level_id if level_id is not None else int(callback.data.split("confirm_del_level_")[-1])
    service = LevelService(session)
    levels = await service.list_levels()
    if len(levels) <= 1:
        await callback.answer("No se puede eliminar el último nivel", show_alert=True)
        return
    await service.delete_level(lvl_id)
    await callback.message.edit_text(
        BOT_MESSAGES["level_deleted"], reply_markup=get_admin_content_levels_keyboard()
    )
    await callback.answer()

