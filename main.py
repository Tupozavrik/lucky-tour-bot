# Главный файл запуска бота

import asyncio
import logging
from urllib.parse import urlparse, parse_qs

from telethon import TelegramClient, connection

from config import BOT_TOKEN, API_ID, API_HASH, UON_API_KEY, PROXY_URL
from database import init_db
from services.uon_service import UonService
from handlers import setup_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def _build_proxy_kwargs(proxy_url: str) -> dict:
    # парсим MTProto прокси из конфига
    if not proxy_url:
        return {}

    parsed = urlparse(proxy_url)
    scheme = parsed.scheme.lower()

    if scheme in ("mtproto", "tg"):
        query_params = parse_qs(parsed.query)
        server = query_params.get("server", [parsed.hostname])[0]
        port_str = query_params.get("port", [str(parsed.port)])[0]
        
        try:
            port = int(port_str)
        except ValueError:
            port = 443  # Фолбэк на стандартный порт
            
        secret = query_params.get("secret", [""])[0]

        logger.info("MTProto прокси: %s:%s", server, port)
        return {
            "connection": connection.ConnectionTcpMTProxyRandomizedIntermediate,
            "proxy": (server, port, secret),
        }

    logger.warning("Прокси '%s' проигнорирован. Оставили только MTProto.", scheme)
    return {}

async def main() -> None:
    if not BOT_TOKEN or not API_ID or not API_HASH:
        logger.error("Ключи BOT_TOKEN, API_ID или API_HASH не заданы в .env!")
        return

    if not UON_API_KEY or UON_API_KEY == "YOUR_UON_API_KEY_HERE":
        logger.warning("Внимание: Запуск в демонстрационном режиме (нет ключа U-ON).")

    await init_db()
    UonService.init_session()

    proxy_kwargs = _build_proxy_kwargs(PROXY_URL)

    client = TelegramClient(
        session="lucky_tour_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        **proxy_kwargs,
    )

    setup_handlers(client)

    # поехали!
    logger.info("Запуск бота...")
    
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    logger.info("Бот успешно запущен как @%s", me.username)

    try:
        await client.run_until_disconnected()
    finally:
        await UonService.close_session()
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    asyncio.run(main())