from aiogram import Router, Bot
from aiogram.types import ChatJoinRequest, ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database.models import PendingChannelRequest, BotConfig
from services.config_service import ConfigService

router = Router()

@router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest, bot: Bot, session: AsyncSession):
    free_id = await ConfigService(session).get_free_channel_id()
    if event.chat.id != free_id:
        return
    req = PendingChannelRequest(
        user_id=event.from_user.id,
        chat_id=event.chat.id,
        request_timestamp=datetime.utcnow(),
    )
    session.add(req)
    await session.commit()

    config = await session.get(BotConfig, 1)
    wait_minutes = config.free_channel_wait_time_minutes if config else 0
    await bot.send_message(
        event.from_user.id,
        f"Solicitud recibida. Ser\u00e1 aprobada en aproximadamente {wait_minutes} minutos."
    )


@router.chat_member()
async def handle_chat_member(update: ChatMemberUpdated, bot: Bot, session: AsyncSession):
    free_id = await ConfigService(session).get_free_channel_id()
    if update.chat.id != free_id:
        return

    user_id = update.from_user.id
    status = update.new_chat_member.status
    if status in {"member", "administrator", "creator"}:
        await bot.send_message(user_id, "Tu acceso al canal ha sido confirmado.")
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.user_id == user_id,
            PendingChannelRequest.chat_id == update.chat.id,
        )
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()
        if req:
            await session.delete(req)
            await session.commit()
    elif status in {"kicked", "left"}:
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.user_id == user_id,
            PendingChannelRequest.chat_id == update.chat.id,
        )
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()
        if req:
            await session.delete(req)
            await session.commit()
