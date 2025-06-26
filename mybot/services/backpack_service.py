from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import BackpackItem, Pista

logger = logging.getLogger(__name__)


class BackpackService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_item(self, user_id: int, pista_id: int) -> BackpackItem | None:
        stmt = select(BackpackItem).where(
            BackpackItem.user_id == user_id,
            BackpackItem.pista_id == pista_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_any_item(self, user_id: int) -> bool:
        stmt = select(BackpackItem).where(BackpackItem.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_item(self, user_id: int, pista_id: int, quantity: int = 1) -> BackpackItem:
        item = await self._get_item(user_id, pista_id)
        if item:
            item.quantity += quantity
        else:
            item = BackpackItem(user_id=user_id, pista_id=pista_id, quantity=quantity)
            self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_pista_by_title(self, title: str) -> Pista | None:
        stmt = select(Pista).where(Pista.title == title)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def give_initial_pista(self, user_id: int) -> bool:
        pista = await self.get_pista_by_title("Pista Inicial")
        if not pista:
            logger.warning("Initial pista not found in database")
            return False
        await self.add_item(user_id, pista.id)
        return True

    async def give_daily_pista(self, user_id: int) -> bool:
        pista = await self.get_pista_by_title("Pista Diaria")
        if not pista:
            logger.warning("Daily pista not found in database")
            return False
        await self.add_item(user_id, pista.id)
        return True
