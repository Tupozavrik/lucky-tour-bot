"""Репозиторий для работы с моделью User — единая точка входа для всех DB-операций."""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Централизованный доступ к данным пользователей."""

    @staticmethod
    async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
        """Получить пользователя по Telegram ID."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_user(session: AsyncSession, telegram_id: int) -> User:
        """Получить пользователя или создать нового."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.flush()

        return user

    @staticmethod
    async def update_uon_id(session: AsyncSession, telegram_id: int, uon_id: str) -> None:
        """Привязать U-ON ID к пользователю."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.uon_id = uon_id
        else:
            logger.warning("update_uon_id: user %d not found", telegram_id)

    @staticmethod
    async def set_auto_add(session: AsyncSession, telegram_id: int, enabled: bool) -> None:
        """Установить значение auto_add_enabled."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.auto_add_enabled = enabled

    @staticmethod
    async def toggle_auto_add(session: AsyncSession, telegram_id: int) -> bool | None:
        """Переключить auto_add_enabled. Возвращает новое значение или None если пользователь не найден."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.auto_add_enabled = not user.auto_add_enabled
            return user.auto_add_enabled
        return None
