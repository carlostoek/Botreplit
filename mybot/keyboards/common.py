from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from utils.config import DEFAULT_REACTION_BUTTONS


def get_back_kb(callback_data: str = "admin_back"):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def get_interactive_post_kb(
    message_id: int,
    raw_reactions: list[str],
    channel_id: int,
    reaction_counts: dict[str, int] | None = None,
) -> InlineKeyboardMarkup:
    """
    Keyboard with reaction buttons for channel posts.
    Always returns a valid InlineKeyboardMarkup.
    """
    builder = InlineKeyboardBuilder()

    if reaction_counts is None:
        reaction_counts = {}

    reactions_to_use = raw_reactions if raw_reactions else DEFAULT_REACTION_BUTTONS

    for emoji in reactions_to_use[:10]:
        count = reaction_counts.get(emoji, 0)
        display = f"{emoji} {count}"
        callback_data = f"ip_{channel_id}_{message_id}_{emoji}"
        builder.button(text=display, callback_data=callback_data)

    if builder.buttons:
        num_buttons = len(builder.buttons)
        if num_buttons <= 4:
            builder.adjust(num_buttons)
        else:
            builder.adjust(4)

    return builder.as_markup()
