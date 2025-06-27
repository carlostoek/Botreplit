import asyncio
import sys
import os

# Ensure project modules can be imported when running this script directly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "mybot"))

from database.setup import init_db, get_session
from services.achievement_service import AchievementService
from services.level_service import LevelService
from services.mission_service import MissionService

DEFAULT_MISSIONS = [
    {
        "name": "Daily Check-in",
        "description": "Registra tu actividad diaria con /checkin",
        "reward_points": 10,
        "mission_type": "login_streak",
        "target_value": 1,
        "duration_days": 0,
    },
    {
        "name": "Primer Mensaje",
        "description": "Envía tu primer mensaje en el chat",
        "reward_points": 5,
        "mission_type": "messages",
        "target_value": 1,
        "duration_days": 0,
    },
]

async def main() -> None:
    await init_db()
    Session = await get_session()
    async with Session() as session:
        await AchievementService(session).ensure_achievements_exist()
        level_service = LevelService(session)
        await level_service._init_levels()

        mission_service = MissionService(session)
        existing = await mission_service.get_active_missions()
        if not existing:
            for m in DEFAULT_MISSIONS:
                await mission_service.create_mission(
                    m["name"],
                    m["description"],
                    m["mission_type"],
                    m.get("target_value", 1),
                    m["reward_points"],
                    m.get("duration_days", 0),
                )
    print("Database initialised")

if __name__ == "__main__":
    asyncio.run(main())
