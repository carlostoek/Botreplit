import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from database.models import PendingChannelRequest, BotConfig, User
from utils.config import CHANNEL_SCHEDULER_INTERVAL, VIP_SCHEDULER_INTERVAL
from services.config_service import ConfigService
from services.auction_service import AuctionService


async def run_channel_request_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Process pending channel requests once."""
    async with session_factory() as session:
        config = await session.get(BotConfig, 1)
        wait_minutes = config.free_channel_wait_time_minutes if config else 0
        threshold = datetime.utcnow() - timedelta(minutes=wait_minutes)
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.approved == False,
            PendingChannelRequest.request_timestamp <= threshold,
        )
        result = await session.execute(stmt)
        requests = result.scalars().all()
        for req in requests:
            try:
                await bot.approve_chat_join_request(req.chat_id, req.user_id)
                await bot.send_message(req.user_id, "Tu solicitud de acceso ha sido aprobada.")
                await session.delete(req)
                logging.info("Approved join request %s for %s", req.chat_id, req.user_id)
            except Exception as e:
                logging.exception("Failed to approve join request for %s: %s", req.user_id, e)
        await session.commit()


async def channel_request_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task processing channel join requests."""
    logging.info("Channel request scheduler started")
    interval = CHANNEL_SCHEDULER_INTERVAL
    try:
        while True:
            await run_channel_request_check(bot, session_factory)
            async with session_factory() as session:
                config_service = ConfigService(session)
                value = await config_service.get_value("channel_scheduler_interval")
                if value and value.isdigit():
                    interval = int(value)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("Channel request scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in channel request scheduler")


async def run_vip_subscription_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Check VIP expirations and send reminders once."""
    async with session_factory() as session:
        now = datetime.utcnow()
        remind_threshold = now + timedelta(hours=24)
        config_service = ConfigService(session)
        reminder_msg = await config_service.get_value("vip_reminder_message")
        farewell_msg = await config_service.get_value("vip_farewell_message")
        if not reminder_msg:
            reminder_msg = "Tu suscripción VIP expira pronto."
        if not farewell_msg:
            farewell_msg = "Tu suscripción VIP ha expirado."
        stmt = select(User).where(
            User.role == "vip",
            User.vip_expires_at <= remind_threshold,
            User.vip_expires_at > now,
            (User.last_reminder_sent_at.is_(None))
            | (User.last_reminder_sent_at <= now - timedelta(hours=24)),
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        for user in users:
            try:
                await bot.send_message(user.id, reminder_msg)
                user.last_reminder_sent_at = now
                logging.info("Sent VIP expiry reminder to %s", user.id)
            except Exception as e:
                logging.exception("Failed to send reminder to %s: %s", user.id, e)

        stmt = select(User).where(
            User.role == "vip",
            User.vip_expires_at.is_not(None),
            User.vip_expires_at <= now,
        )
        result = await session.execute(stmt)
        expired_users = result.scalars().all()
        vip_channel_id = await ConfigService(session).get_vip_channel_id()
        for user in expired_users:
            try:
                if vip_channel_id:
                    await bot.ban_chat_member(vip_channel_id, user.id)
                    await bot.unban_chat_member(vip_channel_id, user.id)
            except Exception as e:
                logging.exception("Failed to remove %s from VIP channel: %s", user.id, e)
            user.role = "free"
            await bot.send_message(user.id, farewell_msg)
            logging.info("VIP expired for %s", user.id)
        await session.commit()


async def vip_subscription_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task checking VIP subscriptions."""
    logging.info("VIP subscription scheduler started")
    interval = VIP_SCHEDULER_INTERVAL
    try:
        while True:
            await run_vip_subscription_check(bot, session_factory)
            async with session_factory() as session:
                config_service = ConfigService(session)
                value = await config_service.get_value("vip_scheduler_interval")
                if value and value.isdigit():
                    interval = int(value)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("VIP subscription scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in VIP subscription scheduler")


async def run_auction_monitor_check(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Check for expired auctions and end them automatically."""
    async with session_factory() as session:
        auction_service = AuctionService(session)
        try:
            expired_auctions = await auction_service.check_expired_auctions(bot)
            if expired_auctions:
                logging.info(f"Auto-ended {len(expired_auctions)} expired auctions")
        except Exception as e:
            logging.exception("Error in auction monitor check: %s", e)


async def auction_monitor_scheduler(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task monitoring auction expirations."""
    logging.info("Auction monitor scheduler started")
    interval = 60  # Check every minute for auction expirations
    try:
        while True:
            await run_auction_monitor_check(bot, session_factory)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("Auction monitor scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in auction monitor scheduler")