import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN, PROXY_URL
from database import init_db
from handlers import setup_routers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Please set it in .env file.")
        return

    await init_db()

    session = None
    if PROXY_URL:
        logger.info(f"Using proxy: {PROXY_URL}")
        session = AiohttpSession(proxy=PROXY_URL)

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()
    
    routers = setup_routers()
    for router in routers:
        dp.include_router(router)

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
