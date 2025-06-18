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
from utils.user_roles import is_admin, is_vip_member, get_user_role
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
    
    # Check if user has access to rewards (VIP or admin)
    role = await get_user_role(message.bot, user_id, session=session)
    if role not in ["vip", "admin"]:
        await message.answer("Esta función está disponible solo para miembros VIP.")
        return
    
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
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role == "admin":
        await update_menu(
            callback,
            "Menú de administración",
            get_admin_main_kb(),
            session,
            "admin_main",
        )
    elif role == "vip":
        await set_user_menu_state(session, user_id, "root")
        await callback.message.edit_text(
            BOT_MESSAGES["start_welcome_returning_user"],
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await callback.message.edit_text(
            "Bienvenido a los kinkys",
            reply_markup=get_subscription_kb(),
        )
    await callback.answer()


# Handler genérico para callbacks de menú (profile, missions, rewards, ranking, back)
@router.callback_query(F.data.startswith("menu:"))
async def menu_callback_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    # Check access for VIP-only features
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    data = callback.data.split(":")
    menu_type = data[1]

    current_state = await get_user_menu_state(session, user_id)
    new_state = current_state

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
        top_users = await point_service.get_top_users(limit=10)
        message_text = await get_ranking_message(top_users)
        keyboard = get_ranking_keyboard()
        new_state = "ranking"
    elif menu_type == "back":
        if current_state in [
            "profile",
            "missions",
            "rewards",
            "ranking",
            "mission_details",
            "reward_details",
        ]:
            keyboard = get_main_menu_keyboard()
            message_text = BOT_MESSAGES["start_welcome_returning_user"]
            new_state = "root"
        else:
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
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
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
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
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
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    mission_id = callback.data[len("mission_") :]

    mission_service = MissionService(session)
    mission = await mission_service.get_mission_by_id(mission_id)

    if not mission:
        await callback.answer("Misión no encontrada.", show_alert=True)
        return

    mission_details_message = await get_mission_details_message(mission)

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
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Menú Principal", callback_data="menu_principal"
                )
            ],
        ]
    )

    await callback.message.edit_text(mission_details_message, reply_markup=keyboard)
    await set_user_menu_state(session, user_id, "mission_details")
    await callback.answer()


# Handler para paginación de misiones
@router.callback_query(F.data.startswith("missions_page_"))
async def handle_missions_pagination(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
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
    role = await get_user_role(callback.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await callback.answer("Esta función está disponible solo para miembros VIP.", show_alert=True)
        return
    
    mission_id = callback.data[len("complete_mission_") :]

    mission_service = MissionService(session)
    point_service = PointService(session)
    achievement_service = AchievementService(session)

    user = await session.get(User, user_id)
    mission = await mission_service.get_mission_by_id(mission_id)

    if not user or not mission:
        await callback.answer("Error: Usuario o misión no encontrada.", show_alert=True)
        return

    is_completed_for_period, _ = await mission_service.check_mission_completion_status(
        user, mission
    )
    if is_completed_for_period:
        await callback.answer(
            "Ya completaste esta misión. ¡Pronto habrá más!", show_alert=True
        )
        return

    completed, completed_mission_obj = await mission_service.complete_mission(
        user_id,
        mission_id,
        bot=callback.bot,
    )

    if completed:
        if not user.missions_completed:
            await achievement_service.grant_achievement(user_id, "first_mission")
        await callback.answer("Misión completada!", show_alert=True)

        active_missions = await mission_service.get_active_missions(user_id=user_id)
        await callback.message.edit_text(
            BOT_MESSAGES["menu_missions_text"],
            reply_markup=get_missions_keyboard(active_missions),
        )
        await set_user_menu_state(session, user_id, "missions")
    else:
        await callback.answer(
            "No puedes completar esta misión ahora mismo o requiere una acción externa.",
            show_alert=True,
        )


# Handler para reacción (like/dislike)
@router.callback_query(F.data.startswith("reaction_"))
async def handle_reaction_callback(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    reaction_type = parts[1]
    target_message_id = int(parts[2])

    point_service = PointService(session)
    mission_service = MissionService(session)
    achievement_service = AchievementService(session)

    base_points_for_reaction = 10 if reaction_type == "like" else 5

    user = await session.get(User, user_id)
    if not user:
        await callback.answer(
            "Por favor, inicia con /start antes de reaccionar.", show_alert=True
        )
        return

    if user.channel_reactions and user.channel_reactions.get(str(target_message_id)):
        await callback.answer("Ya has reaccionado a este mensaje.", show_alert=True)
        return

    await point_service.add_points(user_id, base_points_for_reaction, bot=callback.bot)

    if user.channel_reactions is None:
        user.channel_reactions = {}
    user.channel_reactions[str(target_message_id)] = True
    await session.commit()

    mission_completed_message = ""
    active_action_missions = await mission_service.get_active_missions(
        user_id=user_id, mission_type="reaction"
    )

    for mission in active_action_missions:
        requires_specific_message = (
            mission.action_data
            and mission.action_data.get("target_message_id") == target_message_id
        )
        requires_specific_reaction = (
            mission.action_data
            and mission.action_data.get("reaction_type") == reaction_type
        )

        if mission.requires_action and (
            not mission.action_data
            or (requires_specific_message and requires_specific_reaction)
        ):
            is_completed_for_period, _ = (
                await mission_service.check_mission_completion_status(
                    user, mission, target_message_id=target_message_id
                )
            )

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

@router.message(F.text == "👤 Perfil")
async def show_profile_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await message.answer("Esta función está disponible solo para miembros VIP.")
        return
    
    user = await session.get(User, user_id)
    if user:
        mission_service = MissionService(session)
        active_missions = await mission_service.get_active_missions(user_id=user_id)
        profile_message = await get_profile_message(user, active_missions, session)
        await set_user_menu_state(session, user_id, "profile")
        await message.answer(profile_message, reply_markup=get_profile_keyboard())
    else:
        await message.answer(BOT_MESSAGES["profile_not_registered"])


@router.message(F.text == "🗺 Misiones")
async def show_missions_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await message.answer("Esta función está disponible solo para miembros VIP.")
        return
    
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
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await message.answer("Esta función está disponible solo para miembros VIP.")
        return
    
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


@router.message(F.text == "🏛️ Subastas")
async def show_auctions_from_reply_keyboard(message: Message, session: AsyncSession):
    """Handle auction access from reply keyboard."""
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await message.answer("Esta función está disponible solo para miembros VIP.")
        return
    
    from keyboards.auction_kb import get_auction_main_kb
    await set_user_menu_state(session, user_id, "auction_main")
    await message.answer(
        "🏛️ **Subastas en Tiempo Real**\n\nParticipa en subastas exclusivas y gana premios únicos.",
        reply_markup=get_auction_main_kb(),
    )


@router.message(F.text == "🏆 Ranking")
async def show_ranking_from_reply_keyboard(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await message.answer("Esta función está disponible solo para miembros VIP.")
        return
    
    point_service = PointService(session)
    top_users = await point_service.get_top_users(limit=10)
    ranking_message = await get_ranking_message(top_users)
    await set_user_menu_state(session, user_id, "ranking")
    await message.answer(ranking_message, reply_markup=get_ranking_keyboard())


@router.message(F.text.regexp("/checkin"))
async def handle_daily_checkin(message: Message, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    role = await get_user_role(bot, user_id, session=session)
    
    if role not in ["vip", "admin"]:
        await message.answer("Esta función está disponible solo para miembros VIP.")
        return
    
    service = PointService(session)
    success, progress = await service.daily_checkin(user_id, bot)
    mission_service = MissionService(session)
    completed_challenges = []
    if success:
        completed_challenges = await mission_service.increment_challenge_progress(
            user_id,
            "checkins",
            bot=bot,
        )
        await mission_service.update_progress(
            user_id,
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


# Handler para mensajes no reconocidos
@router.message(F.text)
async def handle_unrecognized_text(message: Message, session: AsyncSession, bot: Bot):
    """Handle arbitrary text depending on the user's role."""
    user_id = message.from_user.id
    role = await get_user_role(bot, user_id, session=session)

    if role == "admin":
        await message.answer(
            BOT_MESSAGES["unrecognized_command_text"],
            reply_markup=get_admin_main_kb(),
        )
    elif role == "vip":
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