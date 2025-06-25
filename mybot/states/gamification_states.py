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
