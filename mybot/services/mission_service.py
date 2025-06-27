from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete
from models.mission import Mission
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

def sanitize_text(text: str) -> str:
    """Función para limpiar texto - implementar según tus necesidades"""
    return text.strip()

class MissionService:
    def __init__(self, session_factory):
        """
        session_factory debe ser una función que retorne AsyncSession
        Ejemplo: lambda: AsyncSession(engine)
        """
        self.session_factory = session_factory
    
    @asynccontextmanager
    async def get_session(self):
        """Context manager para manejar sesiones de forma segura"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database operation failed: {e}")
                raise
            finally:
                await session.close()
    
    async def create_mission(
        self,
        name: str,
        description: str,
        mission_type: str,
        target_value: int,
        reward_points: int,
        duration_days: int = 0,
        *,
        requires_action: bool = False,
        action_data: Optional[Dict[str, Any]] = None,
        channel_restriction: Optional[str] = None,
        unlocks_pista: Optional[str] = None,
    ) -> Mission:
        """Crear una nueva misión de forma asíncrona"""
        
        # Generar ID único
        mission_id = f"{mission_type}_{sanitize_text(name).lower().replace(' ', '_').replace('.', '').replace(',', '')}"
        
        # Preparar action_data
        if action_data is None:
            action_data = {}
        
        if channel_restriction:
            action_data["channel_restriction"] = channel_restriction
        if unlocks_pista:
            action_data["unlocks_pista"] = unlocks_pista

        # Crear objeto Mission
        new_mission = Mission(
            id=mission_id,
            name=sanitize_text(name),
            description=sanitize_text(description),
            reward_points=reward_points,
            type=mission_type,
            target_value=target_value,
            duration_days=duration_days,
            requires_action=requires_action,
            action_data=action_data,
            unlocks_lore_piece_code=unlocks_pista,  # Asegurar que este campo esté mapeado
            is_active=True,
        )
        
        # Guardar usando context manager
        async with self.get_session() as session:
            try:
                session.add(new_mission)
                await session.flush()  # Para obtener el ID generado
                await session.refresh(new_mission)  # Refrescar para obtener created_at
                
                logger.info(f"Mission '{name}' created successfully with ID: {mission_id}")
                return new_mission
                
            except Exception as e:
                logger.error(f"Error creating mission '{name}': {type(e).__name__}: {e}")
                raise
    
    async def get_mission_by_id(self, mission_id: str) -> Optional[Mission]:
        """Obtener misión por ID"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Mission).where(Mission.id == mission_id)
            )
            return result.scalar_one_or_none()
    
    async def get_all_missions(self, active_only: bool = True) -> List[Mission]:
        """Obtener todas las misiones"""
        async with self.get_session() as session:
            query = select(Mission)
            if active_only:
                query = query.where(Mission.is_active == True)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def update_mission(self, mission_id: str, **kwargs) -> Optional[Mission]:
        """Actualizar una misión"""
        async with self.get_session() as session:
            # Buscar la misión
            result = await session.execute(
                select(Mission).where(Mission.id == mission_id)
            )
            mission = result.scalar_one_or_none()
            
            if not mission:
                return None
            
            # Actualizar campos
            for key, value in kwargs.items():
                if hasattr(mission, key):
                    setattr(mission, key, value)
            
            await session.flush()
            await session.refresh(mission)
            return mission
    
    async def delete_mission(self, mission_id: str) -> bool:
        """Eliminar una misión"""
        async with self.get_session() as session:
            result = await session.execute(
                delete(Mission).where(Mission.id == mission_id)
            )
            return result.rowcount > 0

# Clase alternativa si prefieres inyección de dependencias
class MissionServiceDI:
    """Version con dependency injection para casos más complejos"""
    
    def __init__(self, engine):
        self.engine = engine
        self.SessionLocal = sessionmaker(
            engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    async def create_mission(self, **kwargs) -> Mission:
        async with self.SessionLocal() as session:
            async with session.begin():
                # Tu lógica aquí - similar a la anterior
                pass
