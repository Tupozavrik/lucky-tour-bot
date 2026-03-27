"""Тесты для UserRepository: создание, обновление и toggle пользователей."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from database import Base, User
from services.user_repository import UserRepository


# Используем in-memory SQLite для тестов — быстро и изолированно
TEST_ENGINE = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSession = async_sessionmaker(
    bind=TEST_ENGINE,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture
async def session():
    """Создаёт таблицы, отдаёт сессию для тестов, и удаляет таблицы после."""
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as sess:
        yield sess

    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestGetOrCreateUser:
    """Тесты создания и получения пользователя."""

    @pytest.mark.asyncio
    async def test_creates_new_user(self, session: AsyncSession):
        """Пользователь создаётся, если его не было."""
        user = await UserRepository.get_or_create_user(session, telegram_id=100)
        assert user is not None
        assert user.telegram_id == 100
        assert user.uon_id is None
        assert user.auto_add_enabled is True

    @pytest.mark.asyncio
    async def test_returns_existing_user(self, session: AsyncSession):
        """Повторный вызов возвращает того же пользователя."""
        user1 = await UserRepository.get_or_create_user(session, telegram_id=200)
        user2 = await UserRepository.get_or_create_user(session, telegram_id=200)
        assert user1.telegram_id == user2.telegram_id

    @pytest.mark.asyncio
    async def test_get_user_returns_none_for_unknown(self, session: AsyncSession):
        """get_user возвращает None для несуществующего пользователя."""
        user = await UserRepository.get_user(session, telegram_id=999)
        assert user is None


class TestUpdateUonId:
    """Тесты привязки U-ON ID."""

    @pytest.mark.asyncio
    async def test_updates_uon_id(self, session: AsyncSession):
        """uon_id корректно сохраняется."""
        await UserRepository.get_or_create_user(session, telegram_id=300)
        await UserRepository.update_uon_id(session, telegram_id=300, uon_id="42")

        user = await UserRepository.get_user(session, telegram_id=300)
        assert user.uon_id == "42"

    @pytest.mark.asyncio
    async def test_update_for_nonexistent_user_does_not_raise(self, session: AsyncSession):
        """Обновление несуществующего пользователя не бросает исключение."""
        await UserRepository.update_uon_id(session, telegram_id=404, uon_id="99")


class TestToggleAutoAdd:
    """Тесты переключения флага auto_add_enabled."""

    @pytest.mark.asyncio
    async def test_toggle_switches_flag(self, session: AsyncSession):
        """Флаг переключается с True → False и обратно."""
        await UserRepository.get_or_create_user(session, telegram_id=400)

        new_val = await UserRepository.toggle_auto_add(session, telegram_id=400)
        assert new_val is False

        new_val = await UserRepository.toggle_auto_add(session, telegram_id=400)
        assert new_val is True

    @pytest.mark.asyncio
    async def test_toggle_returns_none_for_unknown_user(self, session: AsyncSession):
        """toggle для несуществующего пользователя возвращает None."""
        result = await UserRepository.toggle_auto_add(session, telegram_id=999)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_auto_add_false(self, session: AsyncSession):
        """set_auto_add корректно устанавливает False."""
        await UserRepository.get_or_create_user(session, telegram_id=500)
        await UserRepository.set_auto_add(session, telegram_id=500, enabled=False)

        user = await UserRepository.get_user(session, telegram_id=500)
        assert user.auto_add_enabled is False
