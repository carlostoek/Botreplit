from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.text_utils import sanitize_text
from utils.menu_utils import send_role_menu
from utils.user_roles import clear_role_cache

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    user_id = message.from_user.id

    # Clear any cached role for this user to ensure fresh check
    clear_role_cache(user_id)

    # Ensure the user exists in the database so profile related features work
    user = await session.get(User, user_id)
    if not user:
        user = User(
            id=user_id,
            username=sanitize_text(message.from_user.username),
            first_name=sanitize_text(message.from_user.first_name),
            last_name=sanitize_text(message.from_user.last_name),
        )
        session.add(user)
        await session.commit()
        print(f"Created new user: {user_id}")
    else:
        print(f"Existing user: {user_id}, role: {user.role}")

    await send_role_menu(message, session)