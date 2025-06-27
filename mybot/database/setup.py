# database/setup.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool # NullPool es adecuado para Railway, para SQLite local puedes mantenerlo o quitarlo
from .models import Base
from utils.config import Config

# Hacemos que el motor sea una variable global o pasada, no creada repetidamente
_engine = None # Variable para almacenar el motor una vez inicializado

async def init_db():
    global _engine
    if _engine is None: # Solo crear el motor si no existe
        _engine = create_async_engine(Config.DATABASE_URL, echo=False, poolclass=NullPool)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    return _engine

async def get_session() -> async_sessionmaker[AsyncSession]:
    # get_session ya no llamará a init_db directamente
    # Asume que init_db ya fue llamado en el inicio de la app y _engine está disponible
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db() first.")
    async_session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
    return async_session

# Simple session factory returning AsyncSession directly

def get_async_session() -> AsyncSession:
    """Return a new AsyncSession using the current engine."""
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_db() first.")
    session_factory = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
    return session_factory()


async def test_connection() -> bool:
    """Check database connectivity."""
    try:
        engine = create_async_engine(Config.DATABASE_URL, echo=False, poolclass=NullPool)
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        await engine.dispose()
        return True
    except Exception:
        return False

