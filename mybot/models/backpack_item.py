from __future__ import annotations

from sqlalchemy import Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
import datetime

from database.models import Base, User
from .pista import Pista


class BackpackItem(AsyncAttrs, Base):
    """Mapping of items owned by a user."""

    __tablename__ = "backpack_items"
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(User.id), primary_key=True)
    pista_id: Mapped[int] = mapped_column(Integer, ForeignKey(Pista.id), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    obtained_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    # ORM relationships
    user: Mapped[User] = relationship(User, backref="backpack_items")
    pista: Mapped[Pista] = relationship(Pista, backref="owned_by")


