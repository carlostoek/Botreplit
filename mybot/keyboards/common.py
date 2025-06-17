from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from utils.config import DEFAULT_REACTION_BUTTONS


def get_back_kb(callback_data: str = "admin_back"):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def get_interactive_post_kb(
    message_id: int, buttons: list[str] | None = None
) -> InlineKeyboardMarkup:
    """Keyboard with reaction buttons for channel posts."""
    texts = buttons if buttons else DEFAULT_REACTION_BUTTONS
    builder = InlineKeyboardBuilder()
    for idx, text in enumerate(texts[:10]):
        builder.button(text=text, callback_data=f"ip_r{idx}_{message_id}")
    builder.adjust(len(texts[:10]))
    return builder.as_markup()
