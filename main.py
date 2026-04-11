"""Точка входа: инициализация бота на Telethon (native MTProto) и запуск."""

import asyncio
import logging

from telethon import TelegramClient

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
    """Парсит PROXY_URL и возвращает kwargs для TelegramClient.

    Поддерживаемые форматы:
      mtproto://host:port?secret=dd...  (MTProto proxy, в т.ч. fake-TLS)
      socks5://user:pass@host:port      (SOCKS5)
      socks4://host:port                (SOCKS4)
      http://host:port                  (HTTP proxy)
    """
    if not proxy_url:
        return {}

    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(proxy_url)
    scheme = parsed.scheme.lower()

    if scheme == "mtproto":
        secret = parse_qs(parsed.query).get("secret", [None])[0] or ""
        # Telethon 1.43 сам обрабатывает dd-секреты (fake-TLS):
        # normalize_secret() срезает префикс 'dd'/'ee' и использует
        # оставшиеся 16 байт с RandomizedIntermediate-обфускацией.
        from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
        logger.info("MTProto прокси: %s:%d (секрет: %s...)",
                    parsed.hostname, parsed.port, secret[:6])
        return {
            "connection": ConnectionTcpMTProxyRandomizedIntermediate,
            "proxy": (parsed.hostname, parsed.port, secret),
        }

    # SOCKS5 / SOCKS4 / HTTP — через модуль socks
    import socks  # PySocks, устанавливается с Telethon автоматически

    scheme_map = {
        "socks5": socks.SOCKS5,
        "socks4": socks.SOCKS4,
        "http":   socks.HTTP,
    }
    proxy_type = scheme_map.get(scheme)
    if not proxy_type:
        logger.warning("Неизвестный тип прокси '%s' — игнорируем", scheme)
        return {}

    proxy_tuple: tuple = (proxy_type, parsed.hostname, parsed.port or 1080, True)
    if parsed.username:
        proxy_tuple += (parsed.username, parsed.password or "")

    logger.info("SOCKS/HTTP прокси: %s://%s:%d", scheme, parsed.hostname, parsed.port)
    return {"proxy": proxy_tuple}


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан. Укажите его в файле .env")
        return

    if not API_ID or not API_HASH:
        logger.error("API_ID или API_HASH не заданы. Укажите их в файле .env")
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

    proxy_kwargs = _build_proxy_kwargs(PROXY_URL)

    client = TelegramClient(
        session="lucky_tour_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        **proxy_kwargs,
    )

    setup_handlers(client)

    logger.info("Бот запускается на Telethon (native MTProto)...")
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    logger.info("Бот запущен как @%s", me.username)

    try:
        await client.run_until_disconnected()
    finally:
        await UonService.close_session()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())
