"""Middleware для прокидывания сессии базы данных в хэндлеры."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)

class DbSessionMiddleware(BaseMiddleware):
    """
    Создает новую AsyncSession на каждый апдейт (событие) от Telegram 
    и помещает её в `data["session"]`.
    Автоматически делает commit при успехе и rollback при ошибке.
    """

    def __init__(self, session_pool: async_sessionmaker) -> None:
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Автоматически открываем и закрываем сессию вокруг вызова хэндлера
        async with self.session_pool() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error("Ошибка хендлера (transaction rollback): %s", e, exc_info=True)
                raise
