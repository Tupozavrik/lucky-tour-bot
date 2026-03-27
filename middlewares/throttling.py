"""Middleware для защиты от спама (Throttling) на базе Redis."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message
from redis.asyncio.client import Redis

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Лимитирует количество сообщений от одного пользователя.
    Использует Redis (или fallback-механизм) для хранения состояний.
    """

    def __init__(self, redis: Redis | None, rate_limit: float = 1.0) -> None:
        """
        :param redis: Экземпляр подключения к Redis (может быть None для fallback).
        :param rate_limit: Разрешенное время (в секундах) между сообщениями.
        """
        super().__init__()
        self.redis = redis
        self.rate_limit = rate_limit
        # Локальный fallback-кэш на случай, если Redis недоступен
        self._memory_cache: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return await handler(event, data)

        # Если Redis доступен — используем его
        if self.redis:
            cache_key = f"throttle_{user_id}"
            
            # Проверяем, есть ли запись в Redis
            is_throttled = await self.redis.get(cache_key)
            if is_throttled:
                # Пользователь пишет слишком часто — игнорируем апдейт
                # (опционально: можно отправить предупреждение один раз)
                return None
            
            # Записываем флаг блока с временем жизни = rate_limit
            # Умножаем на 1000 для перевода в миллисекунды для PEXPIRE/PX
            await self.redis.set(cache_key, "1", px=int(self.rate_limit * 1000))
        
        else:
            # Fallback (Memory) - упрощенная логика
            import time
            current_time = time.time()
            last_activity = self._memory_cache.get(user_id)
            if last_activity and current_time - last_activity < self.rate_limit:
                # Игнорировать спам
                return None
            
            self._memory_cache[user_id] = current_time

        # Даем апдейту пройти дальше
        return await handler(event, data)
