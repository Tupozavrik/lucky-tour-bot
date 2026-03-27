"""Репозиторий для работы с моделью User — единая точка входа для всех DB-операций."""

import logging
from sqlalchemy import select
from database import AsyncSessionLocal, User

logger = logging.getLogger(__name__)


class UserRepository:
    """Централизованный доступ к данным пользователей."""

    @staticmethod
    async def get_user(telegram_id: int) -> User | None:
        """Получить пользователя по Telegram ID."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_user(telegram_id: int) -> User:
        """Получить пользователя или создать нового."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                user = User(telegram_id=telegram_id)
                session.add(user)
                await session.commit()
                # Перечитываем, чтобы получить дефолтные значения
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = result.scalar_one()

            return user

    @staticmethod
    async def update_uon_id(telegram_id: int, uon_id: str) -> None:
        """Привязать U-ON ID к пользователю."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.uon_id = uon_id
                await session.commit()
            else:
                logger.warning("update_uon_id: user %d not found", telegram_id)

    @staticmethod
    async def set_auto_add(telegram_id: int, enabled: bool) -> None:
        """Установить значение auto_add_enabled."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.auto_add_enabled = enabled
                await session.commit()

    @staticmethod
    async def toggle_auto_add(telegram_id: int) -> bool | None:
        """Переключить auto_add_enabled. Возвращает новое значение или None если пользователь не найден."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.auto_add_enabled = not user.auto_add_enabled
                await session.commit()
                return user.auto_add_enabled
            return None
