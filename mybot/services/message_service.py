from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from .config_service import ConfigService
from database.models import ButtonReaction
from keyboards.common import get_interactive_post_kb
from utils.config import VIP_CHANNEL_ID, FREE_CHANNEL_ID


class MessageService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot

    async def send_interactive_post(
        self,
        text: str,
        channel_type: str = "vip",
    ) -> Message | bool | None:
        """Send a message with interactive buttons to the configured channel.

        Returns the ``Message`` object on success, ``None`` when the channel
        isn't configured and ``False`` if sending fails due to Telegram
        errors.
        """
        config = ConfigService(self.session)
        channel_type = channel_type.lower()
        if channel_type == "vip":
            channel_id = await config.get_vip_channel_id()
            if channel_id is None:
                channel_id = VIP_CHANNEL_ID or None
        elif channel_type == "free":
            channel_id = await config.get_free_channel_id()
            if channel_id is None:
                channel_id = FREE_CHANNEL_ID or None
        else:
            channel_id = None
        if not channel_id:
            return None

        try:
            buttons = await config.get_reaction_buttons()
            sent = await self.bot.send_message(
                channel_id, text, reply_markup=get_interactive_post_kb(0, buttons)
            )
            await self.bot.edit_message_reply_markup(
                channel_id,
                sent.message_id,
                reply_markup=get_interactive_post_kb(sent.message_id, buttons),
            )
            if channel_type == "vip":
                vip_reactions = await config.get_vip_reactions()
                if vip_reactions:
                    await self.bot.set_message_reaction(
                        channel_id,
                        sent.message_id,
                        [ReactionTypeEmoji(emoji=r) for r in vip_reactions],
                    )
            return sent
        except (TelegramBadRequest, TelegramForbiddenError, TelegramAPIError):
            return False

    async def register_reaction(
        self, user_id: int, message_id: int, reaction_type: str
    ) -> ButtonReaction:
        reaction = ButtonReaction(
            message_id=message_id,
            user_id=user_id,
            reaction_type=reaction_type,
        )
        self.session.add(reaction)
        await self.session.commit()
        await self.session.refresh(reaction)
        return reaction
