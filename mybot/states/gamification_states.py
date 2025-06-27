from aiogram.fsm.state import StatesGroup, State

class LevelAdminStates(StatesGroup):
    creating_level_number = State()
    creating_level_name = State()
    creating_level_points = State()
    creating_level_reward = State()
    confirming_create_level = State()

    editing_level_number = State()
    editing_level_name = State()
    editing_level_points = State()
    editing_level_reward = State()

    deleting_level = State()

class RewardAdminStates(StatesGroup):
    creating_reward_name = State()
    creating_reward_points = State()
    creating_reward_description = State()
    creating_reward_type = State()

    editing_reward_name = State()
    editing_reward_points = State()
    editing_reward_description = State()
    editing_reward_type = State()

class BadgeAdminStates(StatesGroup):
    creating_badge_name = State()
    creating_badge_description = State()
    creating_badge_requirement = State()
    creating_badge_emoji = State()

    deleting_badge = State()


class LorePieceAdminStates(StatesGroup):
    creating_code_name = State()
    creating_title = State()
    creating_description = State()
    creating_category = State()
    creating_is_main_story = State()
    creating_content_type = State()
    creating_content = State()

    editing_title = State()
    editing_description = State()
    editing_category = State()
    editing_is_main_story = State()
    editing_content_type = State()
    editing_content = State()
