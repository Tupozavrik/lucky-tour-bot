"""Обработчики настроек: тоггл автоматического добавления в чаты (Telethon)."""

import logging

from telethon import TelegramClient, events, Button

from database import AsyncSessionLocal
from services.user_repository import UserRepository
from utils.throttle import throttled

logger = logging.getLogger(__name__)

SETTINGS_TEXT = (
    "Настройки бота:\n\n"
    "Вы можете включить или отключить автоматическое добавление вас "
    "в тематические чаты путешествий (по пригласительным ссылкам)."
)


def get_settings_keyboard(auto_add_enabled: bool) -> list:
    """Inline-клавиатура настроек с текущим статусом auto_add."""
    status = "✅ Включено" if auto_add_enabled else "❌ Выключено"
    return [[Button.inline(f"Добавление в чаты: {status}", b"toggle_auto_add")]]


async def show_settings_page(event) -> None:
    """Показывает меню настроек. Вызывается из text_router и /settings."""
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_user(session, event.sender_id)

    if not user:
        await event.respond("Сначала напишите /start.")
        return

    await event.respond(SETTINGS_TEXT, buttons=get_settings_keyboard(user.auto_add_enabled))


def register_settings_handlers(client: TelegramClient) -> None:
    """Регистрирует хэндлеры настроек."""

    @client.on(events.NewMessage(pattern=r"^/settings(?:@\w+)?$", func=lambda e: e.is_private))
    @throttled
    async def cmd_settings(event) -> None:
        """Показывает меню настроек по команде."""
        await show_settings_page(event)

    @client.on(events.CallbackQuery(data=b"toggle_auto_add"))
    async def process_toggle_auto_add(event) -> None:
        """Переключает настройку автоматического добавления в чаты."""
        async with AsyncSessionLocal() as session:
            new_value = await UserRepository.toggle_auto_add(session, event.sender_id)
            await session.commit()

        if new_value is None:
            await event.answer("Пользователь не найден. Напишите /start.", alert=True)
            return

        try:
            await event.edit(SETTINGS_TEXT, buttons=get_settings_keyboard(new_value))
        except Exception:
            logger.debug("Не удалось обновить сообщение настроек — контент не изменился")

        status = "включена" if new_value else "выключена"
        await event.answer(f"Функция добавления в чаты теперь {status}")
