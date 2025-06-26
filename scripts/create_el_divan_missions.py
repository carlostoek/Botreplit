
#!/usr/bin/env python3
"""
Script para crear misiones específicas de la narrativa "El Diván"
"""

import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from mybot.services.mission_service import MissionService
from mybot.utils.config import Config

async def create_el_divan_missions():
    """Create narrative-specific missions for El Diván game."""
    
    # Database setup
    engine = create_async_engine(Config.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        mission_service = MissionService(session)
        
        try:
            print("🎮 Creando misiones para Los Kinkys (Canal Gratuito)...")
            
            # Misión Diaria: Primer contacto
            await mission_service.create_mission(
                name="Primer Contacto en Los Kinkys",
                description="Reacciona al último mensaje publicado para comenzar tu aventura",
                mission_type="daily",
                target_value=1,
                reward_points=10,
                channel_restriction="los_kinkys",
                unlocks_pista="Primer Fragmento del Diván"
            )
            
            # Misión Semanal: Cacería de símbolos
            await mission_service.create_mission(
                name="Cacería Semanal de Símbolos",
                description="Busca y reacciona a publicaciones con símbolos secretos",
                mission_type="weekly", 
                target_value=5,
                reward_points=50,
                channel_restriction="los_kinkys",
                unlocks_pista="Fragmento de Cacería"
            )
            
            # Misión de Acumulación
            await mission_service.create_mission(
                name="Acumulación de Reacciones",
                description="Reacciona múltiples veces para desbloquear el mapa del umbral",
                mission_type="one_time",
                target_value=10,
                reward_points=100,
                channel_restriction="los_kinkys",
                unlocks_pista="Mapa del Umbral"
            )
            
            # Misión de Transición a VIP
            await mission_service.create_mission(
                name="El Umbral hacia El Diván",
                description="Completa 3 misiones en Los Kinkys para obtener la llave de transición",
                mission_type="one_time",
                target_value=3,
                reward_points=200,
                channel_restriction="los_kinkys",
                unlocks_pista="Llave de Transición"
            )
            
            print("\n🌟 Creando misiones para El Diván (Canal VIP)...")
            
            # Trivia de acceso VIP
            await mission_service.create_mission(
                name="Trivia del Diván: Primer Encuentro",
                description="Responde correctamente la trivia sobre Diana para acceder",
                mission_type="one_time",
                target_value=7,  # 7/10 respuestas correctas
                reward_points=150,
                channel_restriction="el_divan",
                unlocks_pista="Visión: Primer Encuentro"
            )
            
            # Misión de Constancia VIP
            await mission_service.create_mission(
                name="Constancia en El Diván",
                description="Reacciona consistentemente durante varios días",
                mission_type="weekly",
                target_value=5,
                reward_points=75,
                channel_restriction="el_divan",
                unlocks_pista="Visión: Los Susurros Profundos"
            )
            
            # Misión de Acertijos
            await mission_service.create_mission(
                name="Acertijo del Diván Supremo",
                description="Resuelve combinaciones de pistas para revelar secretos",
                mission_type="one_time",
                target_value=1,
                reward_points=300,
                channel_restriction="el_divan",
                unlocks_pista="Visión: El Círculo Completo"
            )
            
            print("\n🎉 ¡Misiones de El Diván creadas correctamente!")
            
        except Exception as e:
            print(f"❌ Error al crear las misiones: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_el_divan_missions())
