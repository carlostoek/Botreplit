from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from utils.user_roles import is_admin
from utils.pagination import get_paginated_list
from utils.keyboard_utils import get_admin_lore_piece_list_keyboard, get_back_keyboard
from utils.message_utils import safe_edit_message
from states.gamification_states import LorePieceAdminStates
from services.lore_piece_service import LorePieceService
from database.models import LorePiece

router = Router()

async def show_lore_pieces_page(message: Message, session: AsyncSession, page: int) -> None:
    stmt = select(LorePiece).order_by(LorePiece.id)
    pieces, has_prev, has_next, _ = await get_paginated_list(session, stmt, page)
    lines = [
        "🧩 Pistas",
    ]
    for p in pieces:
        lines.append(
            f"Pista ID: {p.code_name} | Título: {p.title} | Tipo: {p.content_type} | Categoría: {p.category or '-'} | Historia Principal: {'Sí' if p.is_main_story else 'No'}"
        )
    kb = get_admin_lore_piece_list_keyboard(pieces, page, has_prev, has_next)
    await safe_edit_message(message, "\n".join(lines), kb)


@router.callback_query(F.data.in_({"admin_manage_lorepieces", "admin_content_lore_pieces"}))
async def list_lore_pieces(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_lore_pieces_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("lore_piece_page:"))
async def lore_pieces_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    page = int(callback.data.split(":")[1])
    await show_lore_pieces_page(callback.message, session, page)
    await callback.answer()


@router.callback_query(F.data.startswith("lore_piece_view_details:"))
async def lore_piece_view_details(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    code = callback.data.split(":")[1]
    piece = await LorePieceService(session).get_lore_piece_by_code(code)
    if not piece:
        return await callback.answer("Pista no encontrada", show_alert=True)
    lines = [
        f"Código: {piece.code_name}",
        f"Título: {piece.title}",
        f"Descripción: {piece.description or '-'}",
        f"Tipo: {piece.content_type}",
        f"Categoría: {piece.category or '-'}",
        f"Historia Principal: {'Sí' if piece.is_main_story else 'No'}",
    ]
    if piece.content_type == "text":
        lines.append(f"Contenido: {piece.content}")
    else:
        lines.append("Contenido: [Ver archivo adjunto]")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Editar Pista", callback_data=f"lore_piece_edit:{piece.code_name}")],
            [InlineKeyboardButton(text="Eliminar Pista", callback_data=f"lore_piece_delete:{piece.code_name}")],
            [InlineKeyboardButton(text="🔙 Volver a Pistas", callback_data="admin_manage_lorepieces")],
        ]
    )
    await safe_edit_message(callback.message, "\n".join(lines), kb)
    if piece.content_type in {"image", "video", "audio"}:
        try:
            if piece.content_type == "image":
                await callback.message.answer_photo(piece.content)
            elif piece.content_type == "video":
                await callback.message.answer_video(piece.content)
            elif piece.content_type == "audio":
                await callback.message.answer_audio(piece.content)
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data == "lore_piece_create")
async def lore_piece_create(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await safe_edit_message(
        callback.message,
        "Ingresa el code_name único para la pista:",
        get_back_keyboard("admin_manage_lorepieces"),
    )
    await state.set_state(LorePieceAdminStates.creating_code_name)
    await callback.answer()


@router.message(LorePieceAdminStates.creating_code_name)
async def lore_piece_process_code(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    code = message.text.strip()
    exists = await LorePieceService(session).get_lore_piece_by_code(code)
    if exists:
        await message.answer("Ese code_name ya existe, ingresa uno diferente:")
        return
    await state.update_data(code_name=code)
    await message.answer("Título de la pista:")
    await state.set_state(LorePieceAdminStates.creating_title)


@router.message(LorePieceAdminStates.creating_title)
async def lore_piece_process_title(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(title=message.text.strip())
    await message.answer("Descripción de la pista:")
    await state.set_state(LorePieceAdminStates.creating_description)


@router.message(LorePieceAdminStates.creating_description)
async def lore_piece_process_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text.strip())
    await message.answer("Categoría de la pista (opcional):")
    await state.set_state(LorePieceAdminStates.creating_category)


@router.message(LorePieceAdminStates.creating_category)
async def lore_piece_process_category(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(category=message.text.strip())
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sí", callback_data="lore_piece_main_story:yes"),
             InlineKeyboardButton(text="No", callback_data="lore_piece_main_story:no")],
        ]
    )
    await message.answer("¿Pertenece a la historia principal?", reply_markup=kb)
    await state.set_state(LorePieceAdminStates.creating_is_main_story)


@router.callback_query(LorePieceAdminStates.creating_is_main_story, F.data.startswith("lore_piece_main_story:"))
async def lore_piece_process_main_story(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    choice = callback.data.split(":")[1]
    await state.update_data(is_main_story=choice == "yes")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Texto", callback_data="lore_piece_content_type:text")],
            [InlineKeyboardButton(text="Imagen", callback_data="lore_piece_content_type:image")],
            [InlineKeyboardButton(text="Audio", callback_data="lore_piece_content_type:audio")],
            [InlineKeyboardButton(text="Video", callback_data="lore_piece_content_type:video")],
        ]
    )
    await safe_edit_message(
        callback.message,
        "Selecciona el tipo de contenido:",
        kb,
    )
    await state.set_state(LorePieceAdminStates.creating_content_type)
    await callback.answer()


@router.callback_query(LorePieceAdminStates.creating_content_type, F.data.startswith("lore_piece_content_type:"))
async def lore_piece_select_type(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    ctype = callback.data.split(":")[1]
    await state.update_data(content_type=ctype)
    await safe_edit_message(
        callback.message,
        "Envía el contenido ahora:",
        get_back_keyboard("admin_manage_lorepieces"),
    )
    await state.set_state(LorePieceAdminStates.creating_content)
    await callback.answer()


@router.message(LorePieceAdminStates.creating_content)
async def lore_piece_receive_content(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    ctype = data.get("content_type")
    content = None
    if ctype == "text" and message.text:
        content = message.text
    elif ctype == "image" and message.photo:
        content = message.photo[-1].file_id
    elif ctype == "video" and message.video:
        content = message.video.file_id
    elif ctype == "audio" and message.audio:
        content = message.audio.file_id
    if not content:
        await message.answer("Envía un contenido válido acorde al tipo seleccionado")
        return
    service = LorePieceService(session)
    try:
        await service.create_lore_piece(
            data["code_name"],
            data["title"],
            data.get("description", ""),
            ctype,
            content,
            category=data.get("category"),
            is_main_story=data.get("is_main_story", False),
        )
        await message.answer("✅ Pista creada correctamente")
    except IntegrityError:
        await message.answer("Error: code_name duplicado")
    await state.clear()
    await show_lore_pieces_page(message, session, 0)


@router.callback_query(F.data.startswith("lore_piece_edit:"))
async def lore_piece_edit(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    code = callback.data.split(":")[1]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Título", callback_data=f"lore_piece_edit_field:title:{code}")],
            [InlineKeyboardButton(text="Descripción", callback_data=f"lore_piece_edit_field:description:{code}")],
            [InlineKeyboardButton(text="Categoría", callback_data=f"lore_piece_edit_field:category:{code}")],
            [InlineKeyboardButton(text="Historia Principal", callback_data=f"lore_piece_edit_field:is_main_story:{code}")],
            [InlineKeyboardButton(text="Tipo de Contenido", callback_data=f"lore_piece_edit_field:content_type:{code}")],
            [InlineKeyboardButton(text="Contenido", callback_data=f"lore_piece_edit_field:content:{code}")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data=f"lore_piece_view_details:{code}")],
        ]
    )
    await safe_edit_message(callback.message, "¿Qué campo deseas editar?", kb)
    await callback.answer()


@router.callback_query(F.data.startswith("lore_piece_edit_field:"))
async def lore_piece_edit_field(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    _, field, code = callback.data.split(":")
    await state.update_data(code=code)
    prompts = {
        "title": "Nuevo título:",
        "description": "Nueva descripción:",
        "category": "Nueva categoría:",
    }
    if field in {"title", "description", "category"}:
        await safe_edit_message(
            callback.message,
            prompts[field],
            get_back_keyboard(f"lore_piece_edit:{code}"),
        )
        mapping = {
            "title": LorePieceAdminStates.editing_title,
            "description": LorePieceAdminStates.editing_description,
            "category": LorePieceAdminStates.editing_category,
        }
        await state.set_state(mapping[field])
    elif field == "is_main_story":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Sí", callback_data="lore_piece_edit_main_story:yes"),
                 InlineKeyboardButton(text="No", callback_data="lore_piece_edit_main_story:no")],
            ]
        )
        await safe_edit_message(
            callback.message,
            "¿Pertenece a la historia principal?",
            kb,
        )
        await state.set_state(LorePieceAdminStates.editing_is_main_story)
    elif field == "content_type":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Texto", callback_data="lore_piece_edit_type:text")],
                [InlineKeyboardButton(text="Imagen", callback_data="lore_piece_edit_type:image")],
                [InlineKeyboardButton(text="Audio", callback_data="lore_piece_edit_type:audio")],
                [InlineKeyboardButton(text="Video", callback_data="lore_piece_edit_type:video")],
            ]
        )
        await safe_edit_message(
            callback.message,
            "Selecciona el nuevo tipo de contenido:",
            kb,
        )
        await state.set_state(LorePieceAdminStates.editing_content_type)
    elif field == "content":
        await safe_edit_message(
            callback.message,
            "Envía el nuevo contenido:",
            get_back_keyboard(f"lore_piece_edit:{code}"),
        )
        await state.set_state(LorePieceAdminStates.editing_content)
    await callback.answer()


@router.message(LorePieceAdminStates.editing_title)
async def process_edit_title(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    code = data.get("code")
    await LorePieceService(session).update_lore_piece(code, title=message.text.strip())
    await message.answer("Pista actualizada")
    await state.clear()
    await show_lore_pieces_page(message, session, 0)


@router.message(LorePieceAdminStates.editing_description)
async def process_edit_description(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    code = data.get("code")
    await LorePieceService(session).update_lore_piece(code, description=message.text.strip())
    await message.answer("Pista actualizada")
    await state.clear()
    await show_lore_pieces_page(message, session, 0)


@router.message(LorePieceAdminStates.editing_category)
async def process_edit_category(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    code = data.get("code")
    await LorePieceService(session).update_lore_piece(code, category=message.text.strip())
    await message.answer("Pista actualizada")
    await state.clear()
    await show_lore_pieces_page(message, session, 0)


@router.callback_query(LorePieceAdminStates.editing_is_main_story, F.data.startswith("lore_piece_edit_main_story:"))
async def process_edit_main_story(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    choice = callback.data.split(":")[1]
    data = await state.get_data()
    code = data.get("code")
    await LorePieceService(session).update_lore_piece(code, is_main_story=choice == "yes")
    await callback.answer("Pista actualizada", show_alert=True)
    await state.clear()
    await show_lore_pieces_page(callback.message, session, 0)


@router.callback_query(LorePieceAdminStates.editing_content_type, F.data.startswith("lore_piece_edit_type:"))
async def process_edit_content_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    ctype = callback.data.split(":")[1]
    data = await state.get_data()
    code = data.get("code")
    await LorePieceService(session).update_lore_piece(code, content_type=ctype)
    await callback.answer("Tipo actualizado", show_alert=True)
    await state.clear()
    await show_lore_pieces_page(callback.message, session, 0)


@router.message(LorePieceAdminStates.editing_content)
async def process_edit_content(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    code = data.get("code")
    piece = await LorePieceService(session).get_lore_piece_by_code(code)
    if not piece:
        await message.answer("Pista no encontrada")
        await state.clear()
        return
    ctype = piece.content_type
    content = None
    if ctype == "text" and message.text:
        content = message.text
    elif ctype == "image" and message.photo:
        content = message.photo[-1].file_id
    elif ctype == "video" and message.video:
        content = message.video.file_id
    elif ctype == "audio" and message.audio:
        content = message.audio.file_id
    if not content:
        await message.answer("Envía un contenido válido acorde al tipo actual")
        return
    await LorePieceService(session).update_lore_piece(code, content=content)
    await message.answer("Pista actualizada")
    await state.clear()
    await show_lore_pieces_page(message, session, 0)


@router.callback_query(F.data.startswith("lore_piece_delete:"))
async def lore_piece_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    code = callback.data.split(":")[1]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sí, Eliminar", callback_data=f"lore_piece_delete_confirm:{code}")],
            [InlineKeyboardButton(text="Cancelar", callback_data=f"lore_piece_view_details:{code}")],
        ]
    )
    await safe_edit_message(callback.message, f"¿Eliminar permanentemente '{code}'?", kb)
    await callback.answer()


@router.callback_query(F.data.startswith("lore_piece_delete_confirm:"))
async def lore_piece_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    code = callback.data.split(":")[1]
    await LorePieceService(session).delete_lore_piece(code)
    await callback.answer("Pista eliminada", show_alert=True)
    await show_lore_pieces_page(callback.message, session, 0)
