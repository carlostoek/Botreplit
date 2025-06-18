from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.admin_state import AdminTariffStates
from keyboards.tarifas_kb import get_duration_kb, get_tarifas_kb
from keyboards.common import get_back_kb
from utils.menu_utils import send_temporary_reply, update_menu
from database.models import Tariff
from utils.text_utils import sanitize_text
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "config_tarifas")
async def config_tarifas(callback: CallbackQuery, session: AsyncSession):
    """Show existing tariffs and menu options."""
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    
    result = await session.execute(select(Tariff).order_by(Tariff.duration_days))
    tariffs = result.scalars().all()
    
    if tariffs:
        lines = [f"• **{t.name}**: {t.duration_days} días - ${t.price}" for t in tariffs]
        text = "💳 **Tarifas VIP configuradas:**\n\n" + "\n".join(lines)
    else:
        text = "💳 **Tarifas VIP**\n\nNo hay tarifas configuradas."
    
    await update_menu(callback, text, get_tarifas_kb(), session, "config_tarifas")
    await callback.answer()


@router.callback_query(F.data == "tarifa_new")
async def start_new_tarifa(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    
    await state.set_state(AdminTariffStates.waiting_for_tariff_duration)
    await callback.message.edit_text(
        "⏱️ **Crear nueva tarifa**\n\nSelecciona la duración:", 
        reply_markup=get_duration_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Command("admin_configure_tariffs"))
async def admin_configure_tariffs(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminTariffStates.waiting_for_tariff_duration)
    await message.answer("⏱️ Selecciona la duración:", reply_markup=get_duration_kb())


@router.callback_query(AdminTariffStates.waiting_for_tariff_duration)
async def tariff_duration_selected(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    
    duration = int(callback.data.split("_")[-1])
    await state.update_data(duration_days=duration)
    await state.set_state(AdminTariffStates.waiting_for_tariff_price)
    
    await callback.message.edit_text(
        f"💰 **Nueva tarifa - {duration} días**\n\nIngresa el precio (solo números):",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AdminTariffStates.waiting_for_tariff_price)
async def tariff_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await send_temporary_reply(message, "❌ Precio inválido. Ingresa un número positivo.")
        return
    
    await state.update_data(price=price)
    await state.set_state(AdminTariffStates.waiting_for_tariff_name)
    
    data = await state.get_data()
    await message.answer(
        f"📝 **Nueva tarifa**\n"
        f"Duración: {data['duration_days']} días\n"
        f"Precio: ${price}\n\n"
        f"Ingresa el nombre de la tarifa:"
    )


@router.message(AdminTariffStates.waiting_for_tariff_name)
async def tariff_name(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    
    name = sanitize_text(message.text.strip())
    if not name:
        await send_temporary_reply(message, "❌ El nombre no puede estar vacío.")
        return
    
    # Check if tariff name already exists
    stmt = select(Tariff).where(Tariff.name.ilike(name))
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        await send_temporary_reply(message, "❌ Ya existe una tarifa con ese nombre.")
        return
    
    data = await state.get_data()
    tariff = Tariff(
        name=name,
        duration_days=data["duration_days"],
        price=data["price"],
    )
    session.add(tariff)
    await session.commit()
    await session.refresh(tariff)
    
    success_msg = (
        f"✅ **Tarifa creada exitosamente**\n\n"
        f"📋 **Nombre:** {tariff.name}\n"
        f"⏱️ **Duración:** {tariff.duration_days} días\n"
        f"💰 **Precio:** ${tariff.price}"
    )
    
    await message.answer(success_msg, reply_markup=get_tarifas_kb(), parse_mode="Markdown")
    await state.clear()
    
    logger.info(f"Admin {message.from_user.id} created tariff: {tariff.name} ({tariff.duration_days}d, ${tariff.price})")


@router.callback_query(F.data.startswith("delete_tariff_"))
async def delete_tariff(callback: CallbackQuery, session: AsyncSession):
    """Delete a tariff (admin only)."""
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    
    tariff_id = int(callback.data.split("_")[-1])
    tariff = await session.get(Tariff, tariff_id)
    
    if not tariff:
        await callback.answer("❌ Tarifa no encontrada", show_alert=True)
        return
    
    # Check if there are active tokens for this tariff
    from database.models import Token
    stmt = select(Token).where(Token.tariff_id == tariff_id, Token.is_used == False)
    result = await session.execute(stmt)
    active_tokens = result.scalars().all()
    
    if active_tokens:
        await callback.answer(
            f"❌ No se puede eliminar. Hay {len(active_tokens)} tokens activos para esta tarifa.", 
            show_alert=True
        )
        return
    
    await session.delete(tariff)
    await session.commit()
    
    await callback.answer("✅ Tarifa eliminada", show_alert=True)
    logger.info(f"Admin {callback.from_user.id} deleted tariff: {tariff.name}")
    
    # Refresh the tariffs list
    await config_tarifas(callback, session)