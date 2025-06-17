from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import (
    User,
    Mission,
    Reward,
    get_user_menu_state,
    set_user_menu_state,
)
from utils.text_utils import sanitize_text
from services.point_service import PointService
from services.achievement_service import AchievementService, ACHIEVEMENTS
from services.mission_service import MissionService
from services.reward_service import RewardService
from utils.keyboard_utils import (
    get_main_menu_keyboard,
    get_profile_keyboard,
    get_missions_keyboard,
    get_reward_keyboard,
    get_ranking_keyboard,
    get_reaction_keyboard,
    get_root_menu,
    get_parent_menu,
    get_child_menu,
    get_main_reply_keyboard,
    get_back_keyboard,
)
from utils.message_utils import (
    get_profile_message,
    get_mission_details_message,
    get_reward_details_message,
    get_ranking_message,
)
from utils.messages import BOT_MESSAGES, NIVEL_TEMPLATE
from services.level_service import get_next_level_info
from utils.user_roles import is_admin, is_vip_member
from keyboards.admin_main_kb import get_admin_main_kb
from keyboards.subscription_kb import get_subscription_kb
from utils.menu_utils import update_menu
import logging

logger = logging.getLogger(__name__)

router = Router()


# /rewards command
@router.message(Command("rewards"))
async def rewards_command(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    reward_service = RewardService(session)
    user = await session.get(User, user_id)
    user_points = int(user.points) if user else 0
    available_rewards = await reward_service.get_available_rewards(user_points)
    claimed = await reward_service.get_claimed_reward_ids(user_id)
    await set_user_menu_state(session, user_id, "rewards")
    await message.answer(
        BOT_MESSAGES["menu_rewards_text"],
        reply_markup=get_reward_keyboard(available_rewards, set(claimed)),
    )


# Handler para el botón de "Menú Principal" (callback_data)
@router.callback_query(F.data == "menu_principal")
async def go_to_main_menu_from_inline(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    if is_admin(user_id):
        await update_menu(
            callback,
            "Menú de administración",
            get_admin_main_kb(),
            session,
            "admin_main",
        )
    else:
        await set_user_menu_state(session, user_id, "root")
        await callback.message.edit_text(
            BOT_MESSAGES["start_welcome_returning_user"],
            reply_markup=get_main_menu_keyboard(),
        )
    await callback.answer()


# Handler genérico para callbacks de menú (profile, missions, rewards, ranking, back)
@router.callback_query(F.data.startswith("menu:"))
async def menu_callback_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    data = callback.data.split(":")
    menu_type = data[1]

    current_state = await get_user_menu_state(session, user_id)
    new_state = (
        current_state  # Por defecto, no cambia el estado si no hay una navegación clara
    )

    keyboard = None
    message_text = ""

    if menu_type == "profile":
        user = await session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                username=sanitize_text(callback.from_user.username),
                first_name=sanitize_text(callback.from_user.first_name),
                last_name=sanitize_text(callback.from_user.last_name),
            )
            session.add(user)
            await session.commit()

        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user_id)

        message_text = await get_profile_message(user, active_missions, session)
        keyboard = get_profile_keyboard()
        new_state = "profile"
    elif menu_type == "missions":
        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user_id)
        message_text = BOT_MESSAGES["menu_missions_text"]
        keyboard = get_missions_keyboard(active_missions)
        new_state = "missions"
    elif menu_type == "rewards":
        reward_service = RewardService(session)
        user = await session.get(User, user_id)
        user_points = int(user.points) if user else 0
        available_rewards = await reward_service.get_available_rewards(user_points)
        claimed = await reward_service.get_claimed_reward_ids(user_id)
        message_text = BOT_MESSAGES["menu_rewards_text"]
        keyboard = get_reward_keyboard(available_rewards, set(claimed))
        new_state = "rewards"
    elif menu_type == "ranking":
        point_service = PointService(session)
        top_users = await point_service.get_top_users(
            limit=10
        )  # Asegúrate de que get_top_users exista
        message_text = await get_ranking_message(
            top_users
        )  # Asegúrate de que get_ranking_message exista
        keyboard = get_ranking_keyboard()
        new_state = "ranking"
    elif menu_type == "back":
        # Lógica de "volver"
        # Simplificamos para siempre volver al menú raíz si estamos en un submenú
        # O si get_parent_menu devuelve algo específico.
        # En este caso, si estamos en un submenú (profile, missions, etc.),
        # queremos volver al menú principal (root).
        if current_state in [
            "profile",
            "missions",
            "rewards",
            "ranking",
            "mission_details",
            "reward_details",
        ]:
            keyboard = get_main_menu_keyboard()
            message_text = BOT_MESSAGES[
                "start_welcome_returning_user"
            ]  # Mensaje consistente
            new_state = "root"
        else:
            # Si no estamos en un submenú claro para "volver", ir al menú raíz
            keyboard = get_main_menu_keyboard()
            message_text = BOT_MESSAGES["start_welcome_returning_user"]
            new_state = "root"

    if keyboard:
        await callback.message.edit_text(message_text, reply_markup=keyboard)
        await set_user_menu_state(session, user_id, new_state)
    await callback.answer()


# Mostrar información de nivel actual del usuario
@router.callback_query(F.data == "view_level")
async def show_user_level(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Debes iniciar con /start", show_alert=True)
        return

    info = get_next_level_info(int(user.points))
    text = NIVEL_TEMPLATE.format(
        current_level=info["current_level"],
        points=int(user.points),
        percentage=info["percentage_to_next"],
        points_needed=info["points_needed"],
        next_level=info["next_level"],
    )

    await callback.message.edit_text(text, reply_markup=get_back_keyboard("vip_game"))
    await callback.answer()


# Handler para reclamar una recompensa
@router.callback_query(F.data.startswith("claim_reward_"))
async def handle_claim_reward_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    reward_id = int(callback.data.split("_")[-1])

    reward_service = RewardService(session)
    success, message = await reward_service.claim_reward(user_id, reward_id)

    user = await session.get(User, user_id)
    user_points = int(user.points) if user else 0
    available_rewards = await reward_service.get_available_rewards(user_points)
    claimed = await reward_service.get_claimed_reward_ids(user_id)

    if success:
        await callback.message.edit_text(
            f"✅ {BOT_MESSAGES['reward_claim_success']}\n\n{BOT_MESSAGES['menu_rewards_text']}",
            reply_markup=get_reward_keyboard(available_rewards, set(claimed)),
        )
        await callback.answer()
    else:
        await callback.answer(message, show_alert=True)


# Handler para ver detalles de una misión
@router.callback_query(F.data.startswith("mission_"))
async def handle_mission_details_callback(
    callback: CallbackQuery, session: AsyncSession
):
    user_id = callback.from_user.id
    mission_id = callback.data[len("mission_") :]

    mission_service = MissionService(session)
    mission = await mission_service.get_mission_by_id(mission_id)

    if not mission:
        await callback.answer("Misión no encontrada.", show_alert=True)
        return

    mission_details_message = await get_mission_details_message(mission)

    # Un teclado específico para la misión, con un botón para completarla si es posible
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Completar Misión",
                    callback_data=f"complete_mission_{mission_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Volver a Misiones", callback_data="menu:missions"
                )
            ],  # Volver al menú de misiones
            [
                InlineKeyboardButton(
                    text="🏠 Menú Principal", callback_data="menu_principal"
                )
            ],
        ]
    )

    await callback.message.edit_text(mission_details_message, reply_markup=keyboard)
    await set_user_menu_state(
        session, user_id, "mission_details"
    )  # Establecer el estado para detalles de misión
    await callback.answer()


# Handler para paginación de misiones
@router.callback_query(F.data.startswith("missions_page_"))
async def handle_missions_pagination(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    try:
        offset = int(callback.data.split("_")[-1])
    except ValueError:
        offset = 0

    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user_id)

    await callback.message.edit_text(
        BOT_MESSAGES["menu_missions_text"],
        reply_markup=get_missions_keyboard(active_missions, offset=offset),
    )
    await set_user_menu_state(session, user_id, "missions")
    await callback.answer()


# Handler para completar una misión
@router.callback_query(F.data.startswith("complete_mission_"))
async def handle_complete_mission_callback(
    callback: CallbackQuery, session: AsyncSession
):
    user_id = callback.from_user.id
    mission_id = callback.data[len("complete_mission_") :]

    mission_service = MissionService(session)
    point_service = PointService(session)
    achievement_service = AchievementService(session)

    user = await session.get(User, user_id)
    mission = await mission_service.get_mission_by_id(mission_id)

    if not user or not mission:
        await callback.answer("Error: Usuario o misión no encontrada.", show_alert=True)
        return

    # Verificar si la misión ya está completada para el período actual
    is_completed_for_period, _ = await mission_service.check_mission_completion_status(
        user, mission
    )
    if is_completed_for_period:
        await callback.answer(
            "Ya completaste esta misión. ¡Pronto habrá más!", show_alert=True
        )
        return

    # Intentar completar la misión
    completed, completed_mission_obj = await mission_service.complete_mission(
        user_id,
        mission_id,
        bot=callback.bot,
    )

    if completed:
        # Opcional: Otorgar un logro por la primera misión
        if not user.missions_completed:  # Si es la primera misión del usuario
            await achievement_service.grant_achievement(user_id, "first_mission")
        await callback.answer("Misión completada!", show_alert=True)

        # Volver al menú de misiones y actualizarlo
        active_missions = await mission_service.get_active_missions(
            user_id=user_id
        )  # Volver a obtener las misiones activas
        await callback.message.edit_text(
            BOT_MESSAGES["menu_missions_text"],
            reply_markup=get_missions_keyboard(active_missions),
        )
        await set_user_menu_state(
            session, user_id, "missions"
        )  # Volver al estado de misiones
    else:
        # Aquí podrías añadir un mensaje específico si la misión requiere una acción externa
        await callback.answer(
            "No puedes completar esta misión ahora mismo o requiere una acción externa.",
            show_alert=True,
        )


# Handler para reacción (like/dislike)
@router.callback_query(F.data.startswith("reaction_"))
async def handle_reaction_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    reaction_type = parts[1]  # 'like' or 'dislike'
    target_message_id = int(parts[2])  # ID del mensaje al que se reaccionó

    # Asume un servicio para manejar reacciones y puntos
    # Puedes crear un ReactionService o integrar esto en PointService/MissionService
    point_service = PointService(session)
    mission_service = MissionService(session)
    achievement_service = AchievementService(session)

    # Puntos base por reacción
    base_points_for_reaction = 10 if reaction_type == "like" else 5  # Ejemplo

    user = await session.get(User, user_id)
    if not user:
        await callback.answer(
            "Por favor, inicia con /start antes de reaccionar.", show_alert=True
        )
        return

    # Verificar si el usuario ya reaccionó a este mensaje para evitar spam de puntos
    if user.channel_reactions and user.channel_reactions.get(str(target_message_id)):
        await callback.answer("Ya has reaccionado a este mensaje.", show_alert=True)
        return

    # Añadir los puntos base
    await point_service.add_points(user_id, base_points_for_reaction, bot=callback.bot)

    # Marcar el mensaje como reaccionado por el usuario
    if user.channel_reactions is None:
        user.channel_reactions = {}
    user.channel_reactions[str(target_message_id)] = (
        True  # Puedes guardar el timestamp si quieres más detalle
    )
    await session.commit()  # Guardar el estado de reacción

    # Verificar si hay misiones relacionadas con la reacción
    mission_completed_message = ""
    # Obtener misiones activas que requieran acción
    active_action_missions = await mission_service.get_active_missions(
        user_id=user_id, mission_type="reaction"
    )  # Asume un tipo 'reaction'

    for mission in active_action_missions:
        # Aquí la action_data de la misión debería especificar el message_id y/o reaction_type
        # Ejemplo: mission.action_data = {'target_message_id': X, 'reaction_type': 'like'}
        requires_specific_message = (
            mission.action_data
            and mission.action_data.get("target_message_id") == target_message_id
        )
        requires_specific_reaction = (
            mission.action_data
            and mission.action_data.get("reaction_type") == reaction_type
        )

        # Si la misión no requiere una acción específica o si la requiere y coincide
        if mission.requires_action and (
            not mission.action_data
            or (requires_specific_message and requires_specific_reaction)
        ):
            # Check if the user has already completed this mission for the current period
            is_completed_for_period, _ = (
                await mission_service.check_mission_completion_status(
                    user, mission, target_message_id=target_message_id
                )
            )  # Pasa target_message_id

            if not is_completed_for_period:
                completed, mission_obj = await mission_service.complete_mission(
                    user_id,
                    mission.id,
                    target_message_id=target_message_id,
                    bot=callback.bot,
                )
                if completed:
                    mission_completed_message = (
                        f"\n\n🎉 ¡Misión completada: **{mission_obj.name}**!"
                    )

    alert_message = (
        f"¡Reacción registrada! Ganaste `{base_points_for_reaction}` puntos."
    )
    alert_message += mission_completed_message

    await callback.answer(alert_message, show_alert=True)
    logger.info(
        f"User {user_id} reacted with {reaction_type} to message {target_message_id}. Points awarded."
    )


# --- Handlers para los botones del ReplyKeyboardMarkup ---
# Estos handlers se activarán cuando el usuario envíe el texto exacto del botón.


@router.message(F.text == "👤 Perfil")
async def show_profile_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user = await session.get(User, user_id)
    if user:
        point_service = PointService(session)
        achievement_service = AchievementService(session)
        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user_id)
        profile_message = await get_profile_message(user, active_missions, session)
        await set_user_menu_state(session, user_id, "profile")
        # Mostrar el perfil con su teclado INLINE específico (para Volver y Menú Principal)
        await message.answer(profile_message, reply_markup=get_profile_keyboard())
    else:
        await message.answer(BOT_MESSAGES["profile_not_registered"])


@router.message(F.text == "🗺 Misiones")
async def show_missions_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user_id)
    await set_user_menu_state(session, user_id, "missions")
    await message.answer(
        BOT_MESSAGES["menu_missions_text"],
        reply_markup=get_missions_keyboard(active_missions),
    )


@router.message(F.text == "🎁 Recompensas")
async def show_rewards_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    reward_service = RewardService(session)
    user = await session.get(User, user_id)
    user_points = int(user.points) if user else 0
    available_rewards = await reward_service.get_available_rewards(user_points)
    claimed = await reward_service.get_claimed_reward_ids(user_id)
    await set_user_menu_state(session, user_id, "rewards")
    await message.answer(
        BOT_MESSAGES["menu_rewards_text"],
        reply_markup=get_reward_keyboard(available_rewards, set(claimed)),
    )


@router.message(F.text == "🏆 Ranking")
async def show_ranking_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    point_service = PointService(session)
    top_users = await point_service.get_top_users(limit=10)
    ranking_message = await get_ranking_message(top_users)
    await set_user_menu_state(session, user_id, "ranking")
    await message.answer(ranking_message, reply_markup=get_ranking_keyboard())


@router.message(F.text.regexp("/checkin"))
async def handle_daily_checkin(message: Message, session: AsyncSession, bot: Bot):
    service = PointService(session)
    success, progress = await service.daily_checkin(message.from_user.id, bot)
    mission_service = MissionService(session)
    completed_challenges = []
    if success:
        completed_challenges = await mission_service.increment_challenge_progress(
            message.from_user.id,
            "checkins",
            bot=bot,
        )
        await mission_service.update_progress(
            message.from_user.id,
            "login_streak",
            current_value=progress.checkin_streak,
            bot=bot,
        )
    if success:
        await message.answer(BOT_MESSAGES["checkin_success"].format(points=10))
        for ch in completed_challenges:
            await message.answer(f"🎯 ¡Desafío {ch.type} completado! +100 puntos")
    else:
        await message.answer(BOT_MESSAGES["checkin_already_done"])


# IMPORTANTE: Este handler debe ir AL FINAL de todos los otros F.text handlers,
# porque si no, podría capturar otros mensajes antes de que sean procesados por handlers más específicos.
@router.message(F.text)
async def handle_unrecognized_text(message: Message, session: AsyncSession, bot: Bot):
    """Handle arbitrary text depending on the user's role."""
    user_id = message.from_user.id

    if is_admin(user_id):
        await message.answer(
            BOT_MESSAGES["unrecognized_command_text"],
            reply_markup=get_admin_main_kb(),
        )
    elif await is_vip_member(bot, user_id, session=session):
        await message.answer(
            BOT_MESSAGES["unrecognized_command_text"],
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await message.answer(
            "Bienvenido a los kinkys",
            reply_markup=get_subscription_kb(),
        )

    logger.warning(f"Unrecognized message from user {user_id}: {message.text}")
