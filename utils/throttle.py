import functools
import time

_RATE_LIMIT: float = 1.5
_cache: dict[int, tuple[float, int]] = {}


def throttled(func):
    # чтоб не спамили
    @functools.wraps(func)
    async def wrapper(event):
        user_id = getattr(event, 'sender_id', None)
        event_id = getattr(event, 'id', None)
        
        if user_id:
            now = time.monotonic()
            last_time, last_id = _cache.get(user_id, (0.0, 0))
            
            # Если это то же самое сообщение, пропускаем без проверки времени
            if event_id and event_id == last_id:
                return await func(event)
            
            # Проверка интервала
            if now - last_time < _RATE_LIMIT:
                return
            
            _cache[user_id] = (now, event_id or 0)
            
        return await func(event)
    return wrapper
