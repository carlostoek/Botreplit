
"""
Handler para la funcionalidad de mochila en El Diván
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from mybot.services.backpack_service import BackpackService
from mybot.utils.user_roles import get_user_role

router = Router()

@router.callback_query(F.data == "view_backpack")
async def show_backpack(callback: CallbackQuery, session: AsyncSession):
    """Display user's backpack contents."""
    user_id = callback.from_user.id
    
    backpack_service = BackpackService(session)
    contents = await backpack_service.get_user_backpack_contents(user_id)
    
    if not contents:
        text = (
            "🎒 **Tu Mochila está vacía**\n\n"
            "Completa misiones en Los Kinkys o El Diván para obtener pistas, "
            "visiones y fragmentos especiales."
        )
    else:
        text = "🎒 **Contenido de tu Mochila**\n\n"
        
        # Agrupar por tipo
        by_type = {}
        for item in contents:
            item_type = item['type']
            if item_type not in by_type:
                by_type[item_type] = []
            by_type[item_type].append(item)
        
        # Mostrar por categorías
        for item_type, items in by_type.items():
            type_emoji = {
                'texto': '📜',
                'vision': '✨', 
                'fragmento_premium': '💎',
                'mapa': '🗺️',
                'simbolo': '🔮',
                'objeto': '🗝️',
                'acertijo': '🧩'
            }.get(item_type, '📋')
            
            text += f"\n{type_emoji} **{item_type.title()}**:\n"
            for item in items:
                qty_text = f" x{item['quantity']}" if item['quantity'] > 1 else ""
                text += f"• *{item['title']}*{qty_text}\n"
                text += f"  {item['description']}\n"
    
    # Keyboard para regresar
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Volver", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("view_pista_"))
async def view_pista_details(callback: CallbackQuery, session: AsyncSession):
    """Show detailed view of a specific pista."""
    pista_id = callback.data.split("_")[2]
    
    backpack_service = BackpackService(session)
    # This would need a method to get pista details
    # For now, just acknowledge
    await callback.answer("Funcionalidad en desarrollo", show_alert=True)
