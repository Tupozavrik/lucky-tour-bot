"""Утилита для работы с сессией БД в хэндлерах Pyrogram.

Этот модуль больше не используется как aiogram-middleware.
Каждый хэндлер открывает сессию напрямую:

    async with AsyncSessionLocal() as session:
        ...
        await session.commit()

Модуль оставлен для обратной совместимости и тестов.
"""

from database import AsyncSessionLocal

__all__ = ["AsyncSessionLocal"]
