from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums.chat_type import ChatType
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from keyboards.admin_config_kb import (
    get_admin_config_kb,
    get_scheduler_config_kb,
    get_channel_type_kb,
    get_config_done_kb,
)
from utils.keyboard_utils import get_back_keyboard
from services.config_service import ConfigService
from services.channel_service import ChannelService
from services.scheduler import run_channel_request_check, run_vip_subscription_check
from database.setup import get_session
from utils.admin_state import AdminConfigStates
from aiogram.fsm.context import FSMContext

router = Router()


@router.callback_query(F.data == "admin_config")
async def config_menu(callback: CallbackQuery, session: AsyncSession):
    """Placeholder bot configuration menu."""
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await update_menu(
        callback,
        "Configuraci\u00f3n del bot",
        get_admin_config_kb(),
        session,
        "admin_config",
    )
    await callback.answer()


@router.callback_query(F.data == "config_reaction_buttons")
async def prompt_reaction_buttons(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Envía el emoji para la primera reacción:",
        reply_markup=get_back_keyboard("admin_config"),
    )
    await state.update_data(reactions=[], reaction_points=[])
    await state.set_state(AdminConfigStates.waiting_for_reaction_buttons)
    await callback.answer()


@router.callback_query(F.data == "config_vip_reactions")
async def prompt_vip_reactions(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Please send the first emoji to use as a reaction.",
        reply_markup=get_back_keyboard("admin_config"),
    )
    await state.update_data(vip_reactions=[])
    await state.set_state(AdminConfigStates.waiting_for_vip_reactions)
    await callback.answer()


@router.message(AdminConfigStates.waiting_for_reaction_buttons)
async def set_reaction_buttons(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    reactions = data.get("reactions", [])
    points = data.get("reaction_points", [])
    if len(reactions) >= 10:
        await message.answer(
            "Se alcanzó el número máximo de reacciones (10).",
            reply_markup=get_reaction_confirm_kb(),
        )
        return
    reactions.append(message.text.strip())
    await state.update_data(reactions=reactions, reaction_points=points)
    await message.answer("Ingresa los puntos para esta reacción:")
    await state.set_state(AdminConfigStates.waiting_for_reaction_points)


@router.message(AdminConfigStates.waiting_for_reaction_points)
async def set_reaction_points_value(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    try:
        value = float(message.text.strip())
    except ValueError:
        await message.answer("Ingresa un número válido para los puntos:")
        return
    data = await state.get_data()
    points = data.get("reaction_points", [])
    points.append(value)
    await state.update_data(reaction_points=points)
    reactions = data.get("reactions", [])
    if len(reactions) >= 10:
        text = "Máximo de reacciones alcanzado."
    else:
        text = "Reacción registrada. Envía otro emoji o presiona Aceptar."
    await message.answer(text, reply_markup=get_reaction_confirm_kb())
    await state.set_state(AdminConfigStates.waiting_for_reaction_buttons)


@router.message(AdminConfigStates.waiting_for_vip_reactions)
async def set_vip_reactions(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    reactions = data.get("vip_reactions", [])
    if len(reactions) >= 5:
        await message.answer(
            "❌ Only 5 reactions are allowed. Press Accept to confirm your selection.",
            reply_markup=get_reaction_confirm_kb(),
        )
        return
    reactions.append(message.text.strip())
    await state.update_data(vip_reactions=reactions)
    if len(reactions) >= 5:
        text = f"✅ Reaction received: {message.text.strip()}"
    else:
        text = f"✅ Reaction received: {message.text.strip()}\nSend another emoji or press Accept to confirm."
    await message.answer(text, reply_markup=get_reaction_confirm_kb())


@router.callback_query(
    (AdminConfigStates.waiting_for_reaction_buttons | AdminConfigStates.waiting_for_reaction_points),
    F.data == "save_reactions",
)
async def save_reaction_buttons_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    data = await state.get_data()
    reactions = data.get("reactions", [])
    points = data.get("reaction_points", [])
    if not reactions:
        await callback.answer("Debes ingresar al menos una reacción.", show_alert=True)
        return
    service = ConfigService(session)
    await service.set_value("reaction_buttons", ";".join(reactions))
    if points:
        await service.set_reaction_points(points)
    await callback.message.edit_text(
        "Botones de reacción actualizados.", reply_markup=get_admin_config_kb()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(AdminConfigStates.waiting_for_vip_reactions, F.data == "save_reactions")
async def save_vip_reactions_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    data = await state.get_data()
    reactions = data.get("vip_reactions", [])
    if not reactions:
        await callback.answer("Debes ingresar al menos una reacción.", show_alert=True)
        return
    service = ConfigService(session)
    await service.set_vip_reactions(reactions)
    await callback.message.edit_text(
        "👍 Reactions saved successfully.", reply_markup=get_admin_config_kb()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "config_scheduler")
async def scheduler_menu(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    config = ConfigService(session)
    ch = await config.get_value("channel_scheduler_interval") or "30"
    vip = await config.get_value("vip_scheduler_interval") or "3600"
    text = f"Intervalos actuales:\nCanal: {ch}s\nVIP: {vip}s"
    await update_menu(callback, text, get_scheduler_config_kb(), session, "scheduler_config")
    await callback.answer()


@router.callback_query(F.data == "config_add_channels")
async def prompt_channel_type(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "\u00bfQu\u00e9 tipo de canales deseas configurar?",
        reply_markup=get_channel_type_kb(),
    )
    await state.set_state(AdminConfigStates.waiting_for_channel_choice)
    await callback.answer()


@router.callback_query(AdminConfigStates.waiting_for_channel_choice, F.data == "channel_mode_vip")
async def channel_mode_vip(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await state.update_data(mode="vip_only")
    await callback.message.edit_text(
        "Por favor reenvía un mensaje desde tu canal VIP para detectar el ID.",
        reply_markup=get_back_keyboard("admin_config"),
    )
    await state.set_state(AdminConfigStates.waiting_for_vip_channel_id)
    await callback.answer()


@router.callback_query(AdminConfigStates.waiting_for_channel_choice, F.data == "channel_mode_free")
async def channel_mode_free(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await state.update_data(mode="free_only")
    await callback.message.edit_text(
        "Por favor reenvía un mensaje desde tu canal FREE para detectar el ID.",
        reply_markup=get_back_keyboard("admin_config"),
    )
    await state.set_state(AdminConfigStates.waiting_for_free_channel_id)
    await callback.answer()


@router.callback_query(AdminConfigStates.waiting_for_channel_choice, F.data == "channel_mode_both")
async def channel_mode_both(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await state.update_data(mode="both")
    await callback.message.edit_text(
        "Primero, reenvía un mensaje desde tu canal VIP para detectar el ID.",
        reply_markup=get_back_keyboard("admin_config"),
    )
    await state.set_state(AdminConfigStates.waiting_for_vip_channel_id)
    await callback.answer()


@router.callback_query(F.data == "set_channel_interval")
async def prompt_channel_interval(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa el intervalo en segundos para revisar solicitudes de canal:",
        reply_markup=get_back_keyboard("config_scheduler"),
    )
    await state.set_state(AdminConfigStates.waiting_for_channel_interval)
    await callback.answer()


@router.callback_query(F.data == "set_vip_interval")
async def prompt_vip_interval(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa el intervalo en segundos para revisar suscripciones VIP:",
        reply_markup=get_back_keyboard("config_scheduler"),
    )
    await state.set_state(AdminConfigStates.waiting_for_vip_interval)
    await callback.answer()


@router.callback_query(F.data == "run_schedulers_now")
async def run_schedulers_now(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    Session = await get_session()
    await run_channel_request_check(bot, Session)
    await run_vip_subscription_check(bot, Session)
    await callback.answer("Schedulers ejecutados", show_alert=True)


@router.message(AdminConfigStates.waiting_for_channel_interval)
async def set_channel_interval(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    try:
        seconds = int(message.text.strip())
    except ValueError:
        await message.answer("Ingresa un número válido.")
        return
    await ConfigService(session).set_value("channel_scheduler_interval", str(seconds))
    await message.answer("Intervalo actualizado.", reply_markup=get_admin_config_kb())
    await state.clear()


@router.message(AdminConfigStates.waiting_for_vip_channel_id)
async def receive_vip_channel(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    chat_id = None
    if message.forward_from_chat and message.forward_from_chat.type == ChatType.CHANNEL:
        chat_id = message.forward_from_chat.id
    else:
        try:
            chat_id = int(message.text.strip())
        except (TypeError, ValueError):
            await message.answer("ID inv\u00e1lido. Intenta de nuevo.")
            return
    await state.update_data(vip_channel_id=chat_id)
    await message.answer(f"\u2705 ID del canal detectado: {chat_id}.")
    data = await state.get_data()
    mode = data.get("mode")
    if mode == "vip_only":
        config = ConfigService(session)
        await config.set_vip_channel_id(chat_id)
        await ChannelService(session).add_channel(chat_id)
        await message.answer("\u2705 Configuraci\u00f3n guardada correctamente.", reply_markup=get_config_done_kb())
        await state.clear()
    else:
        await message.answer(
            "Ahora reenv\u00eda un mensaje desde tu canal FREE.",
            reply_markup=get_back_keyboard("admin_config"),
        )
        await state.set_state(AdminConfigStates.waiting_for_free_channel_id)


@router.message(AdminConfigStates.waiting_for_free_channel_id)
async def receive_free_channel(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    chat_id = None
    if message.forward_from_chat and message.forward_from_chat.type == ChatType.CHANNEL:
        chat_id = message.forward_from_chat.id
    else:
        try:
            chat_id = int(message.text.strip())
        except (TypeError, ValueError):
            await message.answer("ID inv\u00e1lido. Intenta de nuevo.")
            return
    data = await state.get_data()
    mode = data.get("mode")
    vip_id = data.get("vip_channel_id")
    if vip_id is not None and int(vip_id) == chat_id:
        await message.answer("Los IDs de los canales VIP y FREE no deben ser iguales.")
        return
    config = ConfigService(session)
    if mode == "free_only":
        await config.set_free_channel_id(chat_id)
        await ChannelService(session).add_channel(chat_id)
    else:
        if vip_id is not None:
            await config.set_vip_channel_id(int(vip_id))
            await ChannelService(session).add_channel(int(vip_id))
        await config.set_free_channel_id(chat_id)
        await ChannelService(session).add_channel(chat_id)
    await message.answer(
        "\u2705 Configuraci\u00f3n guardada correctamente.",
        reply_markup=get_config_done_kb(),
    )
    await state.clear()


@router.message(AdminConfigStates.waiting_for_vip_interval)
async def set_vip_interval(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    try:
        seconds = int(message.text.strip())
    except ValueError:
        await message.answer("Ingresa un número válido.")
        return
    await ConfigService(session).set_value("vip_scheduler_interval", str(seconds))
    await message.answer("Intervalo actualizado.", reply_markup=get_admin_config_kb())
    await state.clear()
