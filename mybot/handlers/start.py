"""
Enhanced start handler with improved user experience and multi-tenant support.
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.text_utils import sanitize_text
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory # Asegúrate de que esta sea la instancia global
from utils.user_roles import clear_role_cache, is_admin
from services.tenant_service import TenantService
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """
    Enhanced start command with intelligent routing based on user status.
    Provides seamless experience for new and returning users.
    """
    user_id = message.from_user.id
    
    # Clear any cached role for fresh check
    clear_role_cache(user_id)
    
    # Get or create user
    user = await session.get(User, user_id)
    is_new_user = user is None
    
    if not user:
        user = User(
            id=user_id,
            username=sanitize_text(message.from_user.username),
            first_name=sanitize_text(message.from_user.first_name),
            last_name=sanitize_text(message.from_user.last_name),
        )
        session.add(user)
        await session.commit()
        logger.info(f"Created new user: {user_id}")
    else:
        # Update user info if changed
        updated = False
        new_username = sanitize_text(message.from_user.username)
        new_first_name = sanitize_text(message.from_user.first_name)
        new_last_name = sanitize_text(message.from_user.last_name)
        
        if user.username != new_username:
            user.username = new_username
            updated = True
        if user.first_name != new_first_name:
            user.first_name = new_first_name
            updated = True
        if user.last_name != new_last_name:
            user.last_name = new_last_name
            updated = True
            
        if updated:
            await session.commit()
            logger.info(f"Updated user info: {user_id}")
    
    # Check if this is an admin and if setup is needed
    if is_admin(user_id):
        tenant_service = TenantService(session)
        tenant_status = await tenant_service.get_tenant_status(user_id)
        
        # If admin hasn't completed basic setup, guide them to setup
        if not tenant_status["basic_setup_complete"]:
            text_setup, keyboard_setup = menu_factory.create_setup_choice_menu() 
            await menu_manager.show_menu(
                message,
                text_setup,
                keyboard_setup,
                session,
                "admin_setup_choice", # <-- Este estado es reconocido por menu_factory
                delete_origin_message=True # ¡Importante para eliminar el /start!
            )
            return # Terminar aquí para el flujo de setup
    
    # Create appropriate menu based on user role and status
    try:
        # Obtener el texto y teclado del menú principal
        text, keyboard = await menu_factory.create_menu("main", user_id, session, message.bot)
        
        # Customize welcome message for new vs returning users
        # Solo personaliza si es el menú principal, no si es un sub-menú ya generado
        # (La lógica de `_get_current_menu_state_from_text` se encarga de esto)
        if "main" in menu_factory._get_current_menu_state_from_text(text): 
            if is_new_user:
                welcome_prefix = "🌟 **¡Bienvenido!**\n\n"
                if "panel de administración" in text.lower():
                    welcome_prefix = "👑 **¡Bienvenido, Administrador!**\n\n"
                elif "suscripción vip" in text.lower() or "experiencia premium" in text.lower():
                    welcome_prefix = "✨ **¡Bienvenido, Miembro VIP!**\n\n"
                
                text = welcome_prefix + text
            else:
                # Returning user - more concise welcome
                if "panel de administración" in text.lower():
                    text = "👑 **Panel de Administración**\n\n" + text.split('\n\n', 1)[-1]
                elif "suscripción vip" in text.lower() or "experiencia premium" in text.lower():
                    text = "✨ **Bienvenido de vuelta**\n\n" + text.split('\n\n', 1)[-1]
                else:
                    text = "🌟 **¡Hola de nuevo!**\n\n" + text.split('\n\n', 1)[-1]
        
        await menu_manager.show_menu(
            message, 
            text, 
            keyboard, 
            session, 
            "main",
            delete_origin_message=True # ¡Importante para eliminar el /start!
        )
        
    except Exception as e:
        logger.error(f"Error in start command for user {user_id}: {e}")
        # Fallback to basic menu
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\n"
            "Hubo un problema al cargar el menú. Por favor, intenta nuevamente en unos segundos.",
            auto_delete_seconds=5
        )

# NOTA: La función _create_setup_choice_kb y su asignación
# ya se MOVIERON completamente a menu_factory.py.txt
# Asegúrate de que no existan duplicados aquí.
