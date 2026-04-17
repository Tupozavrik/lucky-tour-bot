# Работа с базой пользователей

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import User

logger = logging.getLogger(__name__)


class UserRepository:
    # тут все запросы к БД по юзерам

    @staticmethod
    async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
        # ищем юзера по ТГ айди
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_user(session: AsyncSession, telegram_id: int) -> User:
        # берем юзера или создаем нового если нет
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
        # записываем U-ON айдишник юзеру
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
        # ставим статус автодобавления
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.auto_add_enabled = enabled

    @staticmethod
    async def toggle_auto_add(session: AsyncSession, telegram_id: int) -> bool | None:
        # переключаем автодобавление (вкл/выкл)
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.auto_add_enabled = not user.auto_add_enabled
            return user.auto_add_enabled
        return None
