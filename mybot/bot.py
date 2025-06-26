import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from .database.setup import init_db, get_session

from .handlers import start, free_user
from .handlers import daily_gift, minigames
from .handlers.channel_access import router as channel_access_router
from .handlers.user import start_token
from .handlers.vip import menu as vip
from .handlers.vip import gamification
from .handlers.vip.auction_user import router as auction_user_router
from .handlers.reaction_callback import router as reaction_callback_router
from .handlers.admin import admin_router
from .handlers.admin.auction_admin import router as auction_admin_router
from .handlers.lore_handlers import router as lore_router

from .handlers import setup as setup_handlers # ¡IMPORTACIÓN CLAVE!

from .handlers.free_channel_admin import router as free_channel_admin_router
from .handlers.publication_test import router as publication_test_router

from .utils.config import BOT_TOKEN, VIP_CHANNEL_ID
from .services import (
    channel_request_scheduler,
    vip_subscription_scheduler,
    vip_membership_scheduler,
)
from .services.scheduler import auction_monitor_scheduler, free_channel_cleanup_scheduler


async def main() -> None:
    await init_db()
    Session = await get_session()

    logging.basicConfig(level=logging.INFO)
    logging.info(f"VIP channel ID: {VIP_CHANNEL_ID}")
    logging.info("Bot starting...")

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    def session_middleware_factory(session_factory, bot_instance):
        async def middleware(handler, event, data):
            async with session_factory() as session:
                data["session"] = session
                data["bot"] = bot_instance
                return await handler(event, data)
        return middleware

    dp.message.outer_middleware(session_middleware_factory(Session, bot))
    dp.callback_query.outer_middleware(session_middleware_factory(Session, bot))
    dp.chat_join_request.outer_middleware(session_middleware_factory(Session, bot))
    dp.chat_member.outer_middleware(session_middleware_factory(Session, bot))
    dp.poll_answer.outer_middleware(session_middleware_factory(Session, bot))
    dp.message_reaction.outer_middleware(session_middleware_factory(Session, bot))

    from .middlewares import PointsMiddleware, UserRegistrationMiddleware
    user_reg_mw = UserRegistrationMiddleware()
    dp.message.outer_middleware(user_reg_mw)
    dp.callback_query.outer_middleware(user_reg_mw)
    dp.chat_join_request.outer_middleware(user_reg_mw)
    dp.chat_member.outer_middleware(user_reg_mw)
    dp.poll_answer.outer_middleware(user_reg_mw)
    dp.message_reaction.outer_middleware(user_reg_mw)

    dp.message.middleware(PointsMiddleware())
    dp.poll_answer.middleware(PointsMiddleware())
    dp.message_reaction.middleware(PointsMiddleware())

    # --- INCLUSIÓN DEL ROUTER DE SETUP ---
    # Es crucial incluirlo para que sus handlers sean reconocidos.
    # Colocarlo aquí, antes de otros routers que puedan tener handlers genéricos,
    # ayuda a asegurar que el comando /setup sea manejado por el handler correcto.
    dp.include_router(setup_handlers.router) 
    # --- FIN INCLUSIÓN ROUTER DE SETUP ---

    dp.include_router(start_token)
    dp.include_router(start.router)
    dp.include_router(admin_router)
    dp.include_router(auction_admin_router)
    dp.include_router(free_channel_admin_router)  # Nuevo router para canal gratuito
    dp.include_router(publication_test_router)
    dp.include_router(vip.router)
    dp.include_router(gamification.router)
    dp.include_router(auction_user_router)
    dp.include_router(reaction_callback_router)
    dp.include_router(daily_gift.router)
    dp.include_router(minigames.router)
    dp.include_router(free_user.router)
    dp.include_router(lore_router)
    dp.include_router(channel_access_router)

    # Tareas programadas
    pending_task = asyncio.create_task(channel_request_scheduler(bot, Session))
    vip_task = asyncio.create_task(vip_subscription_scheduler(bot, Session))
    membership_task = asyncio.create_task(vip_membership_scheduler(bot, Session))
    auction_task = asyncio.create_task(auction_monitor_scheduler(bot, Session))
    cleanup_task = asyncio.create_task(free_channel_cleanup_scheduler(bot, Session))

    try:
        logging.info("Bot is starting polling...")
        await dp.start_polling(bot)
    finally:
        pending_task.cancel()
        vip_task.cancel()
        membership_task.cancel()
        auction_task.cancel()
        cleanup_task.cancel()
        await asyncio.gather(
            pending_task, vip_task, membership_task, auction_task, cleanup_task,
            return_exceptions=True
        )


if __name__ == "__main__":
    asyncio.run(main())

