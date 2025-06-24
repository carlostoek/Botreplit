import datetime
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import UserProgress, MiniGamePlay, ReactionChallenge
from .point_service import PointService

class MiniGameService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)

    async def play_roulette(self, user_id: int, bot: Bot, *, cost: int = 5) -> int:
        """Play roulette. Returns points won."""
        progress = await self.session.get(UserProgress, user_id)
        if not progress:
            progress = UserProgress(user_id=user_id)
            self.session.add(progress)
            await self.session.commit()
        now = datetime.datetime.utcnow()
        free_available = not progress.last_roulette_at or (now - progress.last_roulette_at).total_seconds() >= 86400
        is_free = free_available
        if not free_available:
            await self.point_service.deduct_points(user_id, cost)
        progress.last_roulette_at = now
        score = bot.dice_emoji if hasattr(bot, "dice_emoji") else None
        dice_msg = await bot.send_dice(user_id)
        score = dice_msg.dice.value
        await self.point_service.add_points(user_id, score, bot=bot)
        play = MiniGamePlay(
            user_id=user_id,
            game_type="roulette",
            is_free=is_free,
            cost_points=0 if is_free else cost,
        )
        self.session.add(play)
        await self.session.commit()
        return score

    async def start_reaction_challenge(self, user_id: int, reactions: int, duration_minutes: int = 10, reward: int = 5, penalty: int = 2) -> ReactionChallenge:
        end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=duration_minutes)
        challenge = ReactionChallenge(
            user_id=user_id,
            target_reactions=reactions,
            end_time=end_time,
            reward_points=reward,
            penalty_points=penalty,
        )
        self.session.add(challenge)
        await self.session.commit()
        await self.session.refresh(challenge)
        return challenge

    async def record_reaction(self, user_id: int, bot: Bot):
        now = datetime.datetime.utcnow()
        stmt = select(ReactionChallenge).where(ReactionChallenge.user_id == user_id, ReactionChallenge.active == True)
        result = await self.session.execute(stmt)
        challenges = result.scalars().all()
        for ch in challenges:
            if ch.end_time < now:
                await self._fail_challenge(ch, bot)
                continue
            ch.progress += 1
            if ch.progress >= ch.target_reactions:
                ch.active = False
                await self.point_service.add_points(user_id, ch.reward_points, bot=bot)
        await self.session.commit()

    async def _fail_challenge(self, challenge: ReactionChallenge, bot: Bot):
        if not challenge.active:
            return
        challenge.active = False
        if challenge.penalty_points > 0:
            await self.point_service.deduct_points(challenge.user_id, challenge.penalty_points)
        await self.session.commit()
