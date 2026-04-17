# Работа с API U-ON

import logging
import aiohttp

from config import UON_API_KEY, UON_BASE_URL, DESTINATIONS_CONFIG

logger = logging.getLogger(__name__)


class UonApiError(Exception):
    # если сервак U-ON прилег
    pass


# Словарь нормализации: как U-ON API называет страну → ключ в THEMATIC_CHATS
COUNTRY_MAP = {}
for dest, config_data in DESTINATIONS_CONFIG.items():
    for alias in config_data.get("aliases", []):
        if alias:
            COUNTRY_MAP[alias.lower()] = dest


def normalize_country(raw: str | None) -> str | None:
    # превращаем "Турция" в "Turkey" и т.д.
    if not raw:
        return None
    return COUNTRY_MAP.get(raw.strip().lower())


class UonService:
    # тут сессия, чтоб не плодить подключения
    _session: aiohttp.ClientSession | None = None

    @classmethod
    def init_session(cls) -> None:
        # открываем сессию
        if cls._session is None or cls._session.closed:
            timeout = aiohttp.ClientTimeout(total=15)
            cls._session = aiohttp.ClientSession(timeout=timeout)

    @classmethod
    def get_session(cls) -> aiohttp.ClientSession:
        if cls._session is None or cls._session.closed:
            cls.init_session()
        return cls._session

    @classmethod
    async def close_session(cls) -> None:
        # закрываем всё
        if cls._session and not cls._session.closed:
            await cls._session.close()

    @staticmethod
    async def get_user_destination(uon_id: str) -> str | None:
        # ищем куда летит человек по его ID
        if not UON_API_KEY or UON_API_KEY == "YOUR_UON_API_KEY_HERE":
            return _mock_destination(uon_id)

        session = UonService.get_session()
        raw_country = await _fetch_destination_from_api(session, uon_id)
        return normalize_country(raw_country)


# --- Вспомогательные функции ---

def _mock_destination(uon_id: str) -> str | None:
    # моки для тестов
    logger.warning("Внимание: Запуск в демонстрационном режиме без ключа U-ON (Mock). UON_API_KEY не задан или равен заглушке.")
    if uon_id.strip() == "123":
        return "Egypt"
    if uon_id.strip().isdigit():
        return "Turkey"
    return None


async def _fetch_destination_from_api(
    session: aiohttp.ClientSession,
    uon_id: str,
) -> str | None:
    url_user = f"{UON_BASE_URL.rstrip('/')}/{UON_API_KEY}/user/{uon_id}.json"
    try:
        async with session.get(url_user) as resp:
            if resp.status == 200:
                data = await resp.json()
                country = _extract_country_from_user(data)
                if country:
                    return country
            elif resp.status >= 500:
                logger.error("U-ON API вернул HTTP %d (user)", resp.status)
                raise UonApiError("Сервер U-ON временно недоступен. Попробуйте обновить профиль позже.")
    except aiohttp.ClientError as e:
        logger.error("Сетевая ошибка к U-ON API (user, id=%s): %s", uon_id, e)
        raise UonApiError("Сетевая ошибка при доступе к U-ON") from e

    url_req = f"{UON_BASE_URL.rstrip('/')}/{UON_API_KEY}/request/{uon_id}.json"
    try:
        async with session.get(url_req) as resp:
            if resp.status == 200:
                data = await resp.json()
                country = _extract_country_from_request(data)
                if country:
                    return country
            elif resp.status >= 500:
                logger.error("U-ON API вернул HTTP %d (request)", resp.status)
                raise UonApiError("Сервер U-ON временно недоступен.")
    except aiohttp.ClientError as e:
        logger.error("Сетевая ошибка к U-ON API (request, id=%s): %s", uon_id, e)
        raise UonApiError("Сетевая ошибка при доступе к U-ON") from e

    return None


def _extract_country_from_user(data: dict) -> str | None:
    # вытягиваем страну из инфы о юзере
    users = data.get("user", [])
    if not users:
        return None
    user = users[0]
    # Сначала смотрим в заявках пользователя
    for req in user.get("requests", []):
        country = req.get("country") or req.get("country_name")
        if country:
            return country
    # Потом в самом профиле
    return user.get("country") or user.get("country_name")


def _extract_country_from_request(data: dict) -> str | None:
    # вытягиваем страну из заявки
    requests = data.get("request", data.get("requests", []))
    if not requests:
        return None
    return requests[0].get("country") or requests[0].get("country_name")
