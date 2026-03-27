"""Точка входа: инициализация бота и запуск polling."""

import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from config import BOT_TOKEN, PROXY_URL, REDIS_URL, UON_API_KEY
from database import init_db, AsyncSessionLocal
from handlers import setup_routers
from services.uon_service import UonService
from middlewares.db import DbSessionMiddleware
from middlewares.throttling import ThrottlingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан. Укажите его в файле .env")
        return

    if not UON_API_KEY or UON_API_KEY == "YOUR_UON_API_KEY_HERE":
        logger.warning(
            "===========================================================\n"
            "Внимание: Запуск в демонстрационном режиме (Mock).\n"
            "Настоящего API-ключа U-ON нет, будут использоваться заглушки.\n"
            "==========================================================="
        )

    await init_db()
    UonService.init_session()

    session = None
    if PROXY_URL:
        logger.info("Используем прокси: %s", PROXY_URL)
        session = AiohttpSession(proxy=PROXY_URL)

    # Подключение к Redis (FSM + Throttling)
    redis_client = None
    storage = MemoryStorage()
    
    if REDIS_URL:
        try:
            logger.info("Используем Redis (%s)", REDIS_URL)
            redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
            # Принудительный пинг для проверки коннекта на старте (опционально)
            # await redis_client.ping() 
            storage = RedisStorage(redis=redis_client)
        except Exception as e:
            logger.error("Ошибка при подключении к Redis, откатываемся на MemoryStorage: %s", e)
    else:
        logger.warning("REDIS_URL не задан, используем локальную память (MemoryStorage)")

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Внедрение зависимостей: прокидываем сессию БД во все хэндлеры
    dp.update.middleware(DbSessionMiddleware(session_pool=AsyncSessionLocal))
    
    # Защита от спама (ограничение скорости сообщений)
    dp.message.middleware(ThrottlingMiddleware(redis=redis_client, rate_limit=1.5))

    for router in setup_routers():
        dp.include_router(router)

    # Глобальный обработчик ошибок
    @dp.errors()
    async def global_error_handler(event: types.ErrorEvent):
        logger.critical("Критическая ошибка: %s", event.exception, exc_info=True)
        if event.update.message:
            await event.update.message.answer("Ой! Что-то сломалось на нашей стороне. Мы уже чиним 🛠️")
        elif event.update.callback_query:
            await event.update.callback_query.answer("Внутренняя ошибка сервера", show_alert=True)

    logger.info("Бот запущен, начинаем polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await UonService.close_session()
        if redis_client:
            await redis_client.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
