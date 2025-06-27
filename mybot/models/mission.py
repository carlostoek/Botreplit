# models/mission.py - Versión corregida para async

from sqlalchemy import String, Integer, Boolean, JSON, DateTime, func, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class Mission(Base):
    __tablename__ = "missions"
    
    # Usar mapped_column para mejor compatibilidad con async
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    reward_points: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_action: Mapped[bool] = mapped_column(Boolean, default=False)
    action_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    unlocks_lore_piece_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Usar server_default para timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self):
        return f"<Mission(id='{self.id}', name='{self.name}', type='{self.type}')>"

# Alternativa si prefieres el estilo clásico
class MissionClassic(Base):
    __tablename__ = "missions"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    reward_points = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    target_value = Column(Integer, nullable=False)
    duration_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    requires_action = Column(Boolean, default=False)
    action_data = Column(JSON, default=dict)
    unlocks_lore_piece_code = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
