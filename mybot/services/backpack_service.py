from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from models.backpack_item import BackpackItem
from models.pista import Pista

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
        """Give initial pista when user makes first reaction in Los Kinkys."""
        pista = await self.get_pista_by_title("Primer Fragmento del Diván")
        if not pista:
            logger.warning("Initial pista not found in database")
            return False
        await self.add_item(user_id, pista.id)
        return True

    async def give_daily_pista(self, user_id: int) -> bool:
        """Give daily pista for completing missions in Los Kinkys."""
        pista = await self.get_pista_by_title("Fragmento de Cacería")
        if not pista:
            logger.warning("Daily pista not found in database")
            return False
        await self.add_item(user_id, pista.id)
        return True
    
    async def give_vip_vision(self, user_id: int, vision_name: str) -> bool:
        """Give VIP vision when completing El Diván missions."""
        pista = await self.get_pista_by_title(f"Visión: {vision_name}")
        if not pista:
            logger.warning(f"VIP vision '{vision_name}' not found in database")
            return False
        await self.add_item(user_id, pista.id)
        return True
    
    async def get_user_backpack_contents(self, user_id: int) -> list:
        """Get all items in user's backpack for display."""
        stmt = select(BackpackItem).where(BackpackItem.user_id == user_id)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        backpack_contents = []
        for item in items:
            # Get pista details
            pista = await self.session.get(Pista, item.pista_id)
            if pista:
                backpack_contents.append({
                    'title': pista.title,
                    'description': pista.description,
                    'type': pista.item_type,
                    'quantity': item.quantity,
                    'obtained_at': item.obtained_at
                })
        
        return backpack_contents
