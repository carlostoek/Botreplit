# utils/keyboard_utils.py
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from database.models import User
from utils.messages import BOT_MESSAGES


def get_main_menu_keyboard():
    """Returns the main inline menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(text="🧾 Mi Suscripción", callback_data="vip_subscription")],
        [InlineKeyboardButton(text="👤 Perfil", callback_data="menu:profile")],
        [InlineKeyboardButton(text="🗺 Misiones", callback_data="menu:missions")],
        [InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards")],
        [InlineKeyboardButton(text="🏛️ Subastas", callback_data="auction_main")],
        [InlineKeyboardButton(text="🏆 Ranking", callback_data="menu:ranking")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_keyboard():
    """Returns the keyboard for the profile section."""
    keyboard = [
        [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_missions_keyboard(missions: list, offset: int = 0):
    """Returns the keyboard for missions, with pagination."""
    keyboard = []
    # Display up to 5 missions per page
    for mission in missions[offset : offset + 5]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{mission.name} ({mission.reward_points} Pts)",
                    callback_data=f"mission_{mission.id}",
                )
            ]
        )

    # Add navigation buttons if there are more missions
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="← Anterior", callback_data=f"missions_page_{offset - 5}"
            )
        )
    if offset + 5 < len(missions):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Siguiente →", callback_data=f"missions_page_{offset + 5}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append(
        [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reward_keyboard(
    rewards: list, claimed_ids: set[int], offset: int = 0
) -> InlineKeyboardMarkup:
    """Return reward keyboard with pagination and claim status."""

    keyboard = []
    for reward in rewards[offset : offset + 5]:
        if reward.id in claimed_ids:
            text = f"{reward.title} ✅"
            callback = f"claimed_{reward.id}"
        else:
            text = f"{reward.title} ({reward.required_points} Pts)"
            callback = f"claim_reward_{reward.id}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="← Anterior", callback_data=f"rewards_page_{offset - 5}"
            )
        )
    if offset + 5 < len(rewards):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Siguiente →", callback_data=f"rewards_page_{offset + 5}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append(
        [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ranking_keyboard():
    """Returns the keyboard for the ranking section."""
    keyboard = [
        [InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reaction_keyboard(
    message_id: int,
    like_text: str = "👍 Me gusta",
    dislike_text: str = "👎 No me gusta",
):
    """Return an inline keyboard with like/dislike buttons for channel posts."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=like_text, callback_data=f"reaction_like_{message_id}"
            ),
            InlineKeyboardButton(
                text=dislike_text, callback_data=f"reaction_dislike_{message_id}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_custom_reaction_keyboard(
    message_id: int, buttons: list[str]
) -> InlineKeyboardMarkup:
    """Return an inline keyboard using custom button texts for reactions."""
    if len(buttons) >= 2:
        like, dislike = buttons[0], buttons[1]
    else:
        like, dislike = "👍", "👎"
    return get_reaction_keyboard(message_id, like, dislike)


def get_admin_manage_users_keyboard():
    """Returns the keyboard for user management options in the admin panel."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Sumar Puntos a Usuario", callback_data="admin_add_points"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➖ Restar Puntos a Usuario",
                    callback_data="admin_deduct_points",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Ver Perfil de Usuario", callback_data="admin_view_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Buscar Usuario", callback_data="admin_search_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Notificar a Usuarios", callback_data="admin_notify_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver al Menú Principal de Administrador",
                    callback_data="admin_main_menu",
                )
            ],
        ]
    )
    return keyboard


def get_admin_manage_content_keyboard():
    """Returns the keyboard for content management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Gestionar Usuarios", callback_data="admin_manage_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📌 Misiones", callback_data="admin_content_missions"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏅 Insignias", callback_data="admin_content_badges"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📈 Niveles", callback_data="admin_content_levels"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Recompensas (Catálogo VIP)",
                    callback_data="admin_content_rewards",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏛️ Subastas", callback_data="admin_auction_main"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Regalos Diarios", callback_data="admin_content_daily_gifts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🕹 Minijuegos", callback_data="admin_content_minigames"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎉 Eventos y Sorteos",
                    callback_data="admin_manage_events_sorteos",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver al Menú Principal de Administrador",
                    callback_data="admin_main_menu",
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_missions_keyboard():
    """Keyboard for mission management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Crear Misión", callback_data="admin_create_mission"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅/❌ Activar/Desactivar",
                    callback_data="admin_toggle_mission",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👁 Ver Activas", callback_data="admin_view_missions"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Eliminar", callback_data="admin_delete_mission"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_badges_keyboard():
    """Keyboard for badge management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Crear Insignia", callback_data="admin_create_badge"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👁 Ver Insignias", callback_data="admin_view_badges"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Eliminar Insignia", callback_data="admin_delete_badge"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_levels_keyboard():
    """Keyboard for level management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Añadir Nivel", callback_data="admin_level_add")
            ],
            [
                InlineKeyboardButton(text="📝 Editar Nivel", callback_data="admin_level_edit")
            ],
            [
                InlineKeyboardButton(text="🗑 Eliminar Nivel", callback_data="admin_level_delete")
            ],
            [
                InlineKeyboardButton(text="📋 Ver Niveles", callback_data="admin_levels_view")
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_rewards_keyboard():
    """Keyboard for reward catalogue management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Añadir Recompensa", callback_data="admin_reward_add")
            ],
            [
                InlineKeyboardButton(text="🗑️ Eliminar Recompensa", callback_data="admin_reward_delete")
            ],
            [
                InlineKeyboardButton(text="📝 Editar Recompensa", callback_data="admin_reward_edit")
            ],
            [
                InlineKeyboardButton(text="📋 Ver Recompensas", callback_data="admin_reward_view")
            ],
            [
                InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard


def get_admin_content_auctions_keyboard():
    """Keyboard for auction management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏛️ Gestionar Subastas", callback_data="admin_auction_main"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Estadísticas", callback_data="admin_auction_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_daily_gifts_keyboard():
    """Keyboard for daily gift configuration options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Bot\u00f3n de prueba", callback_data="admin_game_test"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_minigames_keyboard():
    """Keyboard placeholder for minigames options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Bot\u00f3n de prueba", callback_data="admin_game_test"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


# --- Funciones para la navegación de menú ---
# Estas funciones están más orientadas a la lógica de estado que a la creación de teclados per se,
# pero se mantienen aquí para compatibilidad si las usas para generar teclados dinámicos.


def get_root_menu():
    """Returns the inline keyboard for the root menu."""
    keyboard = [
        [InlineKeyboardButton(text="👤 Perfil", callback_data="menu:profile")],
        [InlineKeyboardButton(text="🗺 Misiones", callback_data="menu:missions")],
        [InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards")],
        [InlineKeyboardButton(text="🏛️ Subastas", callback_data="auction_main")],
        [InlineKeyboardButton(text="🏆 Ranking", callback_data="menu:ranking")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_parent_menu(parent_name: str):
    """Returns the keyboard for a parent menu based on its name."""
    if parent_name == "profile":
        return get_profile_keyboard()
    elif parent_name == "missions":
        return get_missions_keyboard(
            []
        )  # Puedes adaptar esto si quieres mostrar misiones
    elif parent_name == "rewards":
        return get_reward_keyboard([], set())
    elif parent_name == "ranking":
        return get_ranking_keyboard()
    else:
        return get_root_menu()


def get_child_menu(menu_name: str):
    """Returns the keyboard for a child menu based on its name."""
    if menu_name == "profile":
        return get_profile_keyboard()
    elif menu_name == "missions":
        return get_missions_keyboard([])
    elif menu_name == "rewards":
        return get_reward_keyboard([], set())
    elif menu_name == "ranking":
        return get_ranking_keyboard()
    else:
        return get_root_menu()


def get_main_reply_keyboard():
    """
    Returns the main ReplyKeyboardMarkup with persistent buttons.
    This replaces the need for menu_principal callback for direct access from text.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Perfil"), KeyboardButton(text="🗺 Misiones")],
            [KeyboardButton(text="🎁 Recompensas"), KeyboardButton(text="🏛️ Subastas")],
            [KeyboardButton(text="🏆 Ranking")],
        ],
        resize_keyboard=True,  # Make the keyboard smaller
        one_time_keyboard=False,  # Keep the keyboard visible
    )
    return keyboard


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Return a simple keyboard with a single back button."""
    keyboard = [[InlineKeyboardButton(text="🔙 Volver", callback_data=callback_data)]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_post_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard used to confirm publishing a channel post."""
    keyboard = [
        [InlineKeyboardButton(text="✅ Publicar", callback_data="confirm_channel_post")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_vip")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reward_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to select reward type."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏅 Insignia", callback_data="reward_type_badge")],
            [InlineKeyboardButton(text="📁 Archivo", callback_data="reward_type_file")],
            [InlineKeyboardButton(text="🔓 Acceso", callback_data="reward_type_access")],
        ]
    )
    return keyboard


def get_mission_completed_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown after completing a mission."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=BOT_MESSAGES["view_all_missions_button_text"],
                callback_data="menu:missions",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_users_list_keyboard(
    users: list[User], offset: int, total_count: int, limit: int = 5
) -> InlineKeyboardMarkup:
    """Return a keyboard for the paginated list of users with action buttons."""
    keyboard: list[list[InlineKeyboardButton]] = []

    for user in users:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="➕", callback_data=f"admin_user_add_{user.id}"
                ),
                InlineKeyboardButton(
                    text="➖", callback_data=f"admin_user_deduct_{user.id}"
                ),
                InlineKeyboardButton(
                    text="👁", callback_data=f"admin_user_view_{user.id}"
                ),
            ]
        )

    nav_buttons: list[InlineKeyboardButton] = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"admin_users_page_{offset - limit}"
            )
        )
    if offset + limit < total_count:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️", callback_data=f"admin_users_page_{offset + limit}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append(
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_main_menu")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_badge_selection_keyboard(badges: list) -> InlineKeyboardMarkup:
    rows = []
    for b in badges:
        label = f"{b.emoji or ''} {b.name}".strip()
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"select_badge_{b.id}")]
        )
    rows.append(
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_badges")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_game_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard for game administration."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📌 Gestionar Misiones", callback_data="admin_manage_missions")],
            [InlineKeyboardButton(text="📈 Gestionar Niveles", callback_data="admin_content_levels")],
            [InlineKeyboardButton(text="🧩 Gestionar Pistas", callback_data="admin_manage_lorepieces")],
            [InlineKeyboardButton(text="🎁 Gestionar Recompensas", callback_data="admin_content_rewards")],
            [InlineKeyboardButton(text="👥 Gestionar Usuarios", callback_data="admin_manage_users")],
            [InlineKeyboardButton(text="🏛️ Gestionar Subastas", callback_data="admin_auction_main")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_main_menu")],
        ]
    )
    return keyboard


def get_admin_mission_list_keyboard(missions: list, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """Keyboard for a paginated list of missions displayed as rows."""
    rows: list[list[InlineKeyboardButton]] = []
    for m in missions:
        # Fila con el nombre de la misión
        rows.append([InlineKeyboardButton(text=m.name, callback_data="noop")])
        # Fila con las acciones de la misión
        rows.append([
            InlineKeyboardButton(text="✏️", callback_data=f"mission_edit:{m.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"mission_delete:{m.id}"),
            InlineKeyboardButton(text="ℹ️", callback_data=f"mission_view_details:{m.id}"),
            InlineKeyboardButton(text="✅" if m.is_active else "❌", callback_data=f"mission_toggle_active:{m.id}"),
        ])

    nav: list[InlineKeyboardButton] = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"missions_page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}", callback_data="noop"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"missions_page:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="➕ Crear Nueva Misión", callback_data="mission_create")])
    rows.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_kinky_game")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
