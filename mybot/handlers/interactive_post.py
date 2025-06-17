from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.message_service import MessageService

router = Router()


@router.callback_query(F.data.startswith("ip_"))
async def handle_interactive_post_callback(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
):
    parts = callback.data.split("_")
    if len(parts) < 3:
        return await callback.answer()
    reaction_type = parts[1]  # e.g. 'r0'
    try:
        message_id = int(parts[2])
    except ValueError:
        return await callback.answer()

    service = MessageService(session, bot)
    await service.register_reaction(callback.from_user.id, message_id, reaction_type)
    await callback.answer("\u2757 Gracias por reaccionar!")

