from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

async def paginate(session: AsyncSession, stmt, page: int = 0, page_size: int = 5):
    """Return items for a page with total count and navigation flags."""
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(total_stmt)).scalar_one()
    result = await session.execute(stmt.offset(page * page_size).limit(page_size))
    items = result.scalars().all()
    has_prev = page > 0
    has_next = (page + 1) * page_size < total
    return items, total, has_prev, has_next
