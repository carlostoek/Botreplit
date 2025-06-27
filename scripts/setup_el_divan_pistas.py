
#!/usr/bin/env python3
"""
Script para inicializar las pistas específicas de la narrativa "El Diván"
"""

import asyncio
import sys
import os

# Add project root (mybot directory) to path to import modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "mybot"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.pista import Pista
from utils.config import Config

async def setup_el_divan_pistas():
    """Initialize narrative-specific pistas for El Diván game."""
    
    # Database setup
    engine = create_async_engine(Config.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Pistas for Los Kinkys (Free Channel)
    los_kinkys_pistas = [
        {
            "title": "Primer Fragmento del Diván",
            "description": "Un susurro inicial que revela que hay más allá de lo visible.",
            "item_type": "texto",
            "content_text": "🌙 'En el silencio del diván, las verdades danzan con las sombras...' - Fragmento encontrado"
        },
        {
            "title": "Fragmento de Cacería",
            "description": "Pista obtenida durante las cacerías semanales en Los Kinkys.",
            "item_type": "simbolo",
            "content_text": "🔮 Símbolo místico que resuena con energías ocultas"
        },
        {
            "title": "Mapa del Umbral",
            "description": "Fragmento que muestra el camino hacia El Diván.",
            "item_type": "mapa",
            "content_text": "📜 'El umbral se abre solo para quienes han demostrado su dedicación...'"
        },
        {
            "title": "Llave de Transición",
            "description": "Permite el acceso desde Los Kinkys hacia El Diván.",
            "item_type": "objeto",
            "content_text": "🗝️ Una llave etérea que pulsa con energía VIP"
        }
    ]
    
    # Pistas for El Diván (VIP Channel)
    el_divan_pistas = [
        {
            "title": "Visión: Primer Encuentro",
            "description": "La primera visión revelada al acceder a El Diván.",
            "item_type": "vision",
            "content_text": "✨ 'En esta dimensión, cada pensamiento es una revelación y cada silencio una confesión...'"
        },
        {
            "title": "Visión: Los Susurros Profundos",
            "description": "Visión obtenida tras completar misiones de constancia.",
            "item_type": "vision",
            "content_text": "🌊 'Las aguas profundas del diván guardan secretos que solo los persistentes pueden descifrar...'"
        },
        {
            "title": "Fragmento Premium: La Verdad Oculta",
            "description": "Fragmento exclusivo del Diván que revela verdades profundas.",
            "item_type": "fragmento_premium",
            "content_text": "💎 'No todos los tesoros brillan. Los más valiosos susurran en la oscuridad...'"
        },
        {
            "title": "Visión: El Círculo Completo",
            "description": "Visión final que completa el ciclo narrativo.",
            "item_type": "vision",
            "content_text": "🔄 'Lo que comienza en Los Kinkys se completa en El Diván, y lo que se completa regresa transformado...'"
        },
        {
            "title": "Acertijo del Diván Supremo",
            "description": "Acertijo maestro que requiere múltiples pistas para resolverse.",
            "item_type": "acertijo",
            "content_text": "🧩 'Combina tres fragmentos de diferentes mundos para revelar el secreto supremo...'"
        }
    ]
    
    async with async_session() as session:
        try:
            # Create Los Kinkys pistas
            print("🔹 Creando pistas para Los Kinkys...")
            for pista_data in los_kinkys_pistas:
                # Check if already exists
                existing = await session.get(Pista, pista_data["title"])
                if not existing:
                    pista = Pista(
                        title=pista_data["title"],
                        description=pista_data["description"],
                        item_type=pista_data["item_type"],
                        content_text=pista_data["content_text"]
                    )
                    session.add(pista)
                    print(f"  ✅ Creada: {pista_data['title']}")
                else:
                    print(f"  ⚠️  Ya existe: {pista_data['title']}")
            
            # Create El Diván pistas
            print("\n🔸 Creando pistas para El Diván...")
            for pista_data in el_divan_pistas:
                # Check if already exists
                existing = await session.get(Pista, pista_data["title"])
                if not existing:
                    pista = Pista(
                        title=pista_data["title"],
                        description=pista_data["description"],
                        item_type=pista_data["item_type"],
                        content_text=pista_data["content_text"]
                    )
                    session.add(pista)
                    print(f"  ✅ Creada: {pista_data['title']}")
                else:
                    print(f"  ⚠️  Ya existe: {pista_data['title']}")
            
            await session.commit()
            print("\n🎉 ¡Pistas de El Diván inicializadas correctamente!")
            
        except Exception as e:
            print(f"❌ Error al crear las pistas: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_el_divan_pistas())
