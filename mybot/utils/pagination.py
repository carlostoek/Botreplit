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


async def get_paginated_list(session: AsyncSession, stmt, page: int = 0, page_size: int = 5):
    """Return paginated items with navigation info."""
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(total_stmt)).scalar_one()
    result = await session.execute(stmt.offset(page * page_size).limit(page_size))
    items = result.scalars().all()
    total_pages = (total + page_size - 1) // page_size if total else 1
    has_prev = page > 0
    has_next = (page + 1) < total_pages
    return items, has_prev, has_next, total_pages
