"""Декоратор-ограничитель частоты сообщений (throttling) для Telethon-хэндлеров."""

import functools
import time

_RATE_LIMIT: float = 1.5  # минимальный интервал между сообщениями (секунды)
_cache: dict[int, float] = {}


def throttled(func):
    """Декоратор throttling: пропускает сообщение, если прошло >= RATE_LIMIT секунд."""
    @functools.wraps(func)
    async def wrapper(event):
        user_id = getattr(event, 'sender_id', None)
        if user_id:
            now = time.monotonic()
            if now - _cache.get(user_id, 0.0) < _RATE_LIMIT:
                return
            _cache[user_id] = now
        return await func(event)
    return wrapper
