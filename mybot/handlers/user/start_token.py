from datetime import datetime, timedelta
from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.filters.command import CommandObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.text_utils import sanitize_text
from services.token_service import TokenService
from services.subscription_service import SubscriptionService
from utils.menu_utils import send_temporary_reply
from services.achievement_service import AchievementService
from services.config_service import ConfigService

router = Router()


@router.message(CommandStart(deep_link=True))
async def start_with_token(message: Message, command: CommandObject, session: AsyncSession, bot: Bot):
    token_string = command.args
    if not token_string:
        return


    service = TokenService(session)
    try:
        duration = await service.activate_token(token_string, message.from_user.id)
    except Exception:
        await send_temporary_reply(message, "Token inválido o ya utilizado.")
        return

    user = await session.get(User, message.from_user.id)
    if not user:
        user = User(
            id=message.from_user.id,
            username=sanitize_text(message.from_user.username),
            first_name=sanitize_text(message.from_user.first_name),
            last_name=sanitize_text(message.from_user.last_name),
        )
        session.add(user)

    user.role = "vip"
    expires_at = datetime.utcnow() + timedelta(days=duration)
    user.vip_expires_at = expires_at
    user.last_reminder_sent_at = None

    # Record the subscription for tracking
    sub_service = SubscriptionService(session)
    existing = await sub_service.get_subscription(user.id)
    if existing:
        existing.expires_at = expires_at
    else:
        await sub_service.create_subscription(user.id, expires_at)

    await session.commit()
    ach_service = AchievementService(session)
    await ach_service.check_vip_achievement(user.id, bot=bot)

    invite_link = None
    vip_id = await ConfigService(session).get_vip_channel_id()
    if vip_id:
        try:
            link = await bot.create_chat_invite_link(vip_id, member_limit=1)
            invite_link = link.invite_link
        except Exception:
            invite_link = None

    if invite_link:
        await message.answer(f"¡Bienvenido! Únete a nuestro canal VIP: {invite_link}")
    else:
        await message.answer("Suscripción activada correctamente!")
