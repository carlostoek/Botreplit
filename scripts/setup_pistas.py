import asyncio
from sqlalchemy import select
from mybot.database.setup import init_db, get_session
from models import Pista

INITIAL_PISTA = {
    "title": "Pista Inicial",
    "item_type": "TEXT",
    "content_text": "Bienvenido al Diván, busca el espejo.",
    "description": None,
}

DAILY_PISTA = {
    "title": "Pista Diaria",
    "item_type": "TEXT",
    "content_text": "Sigue reaccionando para descubrir más secretos.",
    "description": None,
}

async def ensure_pista(session, data):
    stmt = select(Pista).where(Pista.title == data["title"])
    result = await session.execute(stmt)
    pista = result.scalar_one_or_none()
    if not pista:
        pista = Pista(**data)
        session.add(pista)
        await session.commit()

async def main():
    await init_db()
    Session = await get_session()
    async with Session() as session:
        await ensure_pista(session, INITIAL_PISTA)
        await ensure_pista(session, DAILY_PISTA)
    print("Pistas setup completed")

if __name__ == "__main__":
    asyncio.run(main())
