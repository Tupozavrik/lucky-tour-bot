"""Middleware для защиты от спама (Throttling) на базе Redis."""

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message
from redis.asyncio.client import Redis

logger = logging.getLogger(__name__)

# Как часто (в секундах) чистить устаревшие записи из memory-кэша
_CLEANUP_INTERVAL: float = 60.0


class ThrottlingMiddleware(BaseMiddleware):
    """
    Лимитирует количество сообщений от одного пользователя.
    Использует Redis (или fallback-механизм) для хранения состояний.

    Fallback-режим (без Redis): хранит метки времени в словаре.
    Каждые _CLEANUP_INTERVAL секунд автоматически удаляет устаревшие
    записи, чтобы словарь не рос бесконечно.
    """

    def __init__(self, redis: Redis | None, rate_limit: float = 1.0) -> None:
        """
        :param redis: Экземпляр подключения к Redis (может быть None для fallback).
        :param rate_limit: Минимальный интервал (в секундах) между сообщениями.
        """
        super().__init__()
        self.redis = redis
        self.rate_limit = rate_limit
        # Локальный fallback-кэш: {user_id: timestamp последнего разрешённого сообщения}
        self._memory_cache: dict[int, float] = {}
        # Время последней очистки кэша
        self._last_cleanup: float = time.monotonic()

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
                return None

            # Записываем флаг с временем жизни = rate_limit (в миллисекундах)
            await self.redis.set(cache_key, "1", px=int(self.rate_limit * 1000))

        else:
            # Fallback (Memory)
            current_time = time.monotonic()

            last_activity = self._memory_cache.get(user_id)
            if last_activity and current_time - last_activity < self.rate_limit:
                # Пользователь пишет слишком часто — игнорируем
                return None

            self._memory_cache[user_id] = current_time

            # Периодически удаляем устаревшие записи, чтобы не копить память
            if current_time - self._last_cleanup >= _CLEANUP_INTERVAL:
                self._evict_stale(current_time)

        # Даём апдейту пройти дальше
        return await handler(event, data)

    def _evict_stale(self, now: float) -> None:
        """Удаляет из кэша записи, которые уже старше rate_limit.

        Вызывается не чаще одного раза в _CLEANUP_INTERVAL секунд,
        поэтому не создаёт заметной нагрузки даже при большом числе пользователей.
        """
        cutoff = now - self.rate_limit
        stale_keys = [uid for uid, ts in self._memory_cache.items() if ts < cutoff]
        for uid in stale_keys:
            del self._memory_cache[uid]

        if stale_keys:
            logger.debug("ThrottlingMiddleware: удалено %d устаревших записей из memory-кэша", len(stale_keys))

        self._last_cleanup = now
