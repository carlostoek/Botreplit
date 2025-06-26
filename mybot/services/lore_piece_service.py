from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database.models import LorePiece
from utils.text_utils import sanitize_text
import logging

logger = logging.getLogger(__name__)

class LorePieceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_lore_pieces(self):
        result = await self.session.execute(select(LorePiece).order_by(LorePiece.id))
        return result.scalars().all()

    async def get_lore_piece_by_code(self, code_name: str) -> LorePiece | None:
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_lore_piece(
        self,
        code_name: str,
        title: str,
        description: str,
        content_type: str,
        content: str,
        category: str | None = None,
        is_main_story: bool = False,
    ) -> LorePiece:
        new_piece = LorePiece(
            code_name=sanitize_text(code_name),
            title=sanitize_text(title),
            description=sanitize_text(description),
            content_type=content_type,
            content=content,
            category=sanitize_text(category) if category else None,
            is_main_story=is_main_story,
        )
        self.session.add(new_piece)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(new_piece)
        return new_piece

    async def update_lore_piece(self, code_name: str, **fields) -> LorePiece | None:
        piece = await self.get_lore_piece_by_code(code_name)
        if not piece:
            return None
        for key, value in fields.items():
            if value is None:
                continue
            if hasattr(piece, key):
                if isinstance(value, str) and key in {"code_name", "title", "description", "category"}:
                    setattr(piece, key, sanitize_text(value))
                else:
                    setattr(piece, key, value)
        await self.session.commit()
        await self.session.refresh(piece)
        return piece

    async def delete_lore_piece(self, code_name: str) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if not piece:
            return False
        await self.session.delete(piece)
        await self.session.commit()
        return True
