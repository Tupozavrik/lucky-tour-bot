"""Обработчики настроек: тоггл автоматического добавления в чаты."""

import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = Router(name="settings_router")


def get_settings_keyboard(auto_add_enabled: bool) -> types.InlineKeyboardMarkup:
    """Inline-клавиатура настроек с текущим статусом auto_add."""
    builder = InlineKeyboardBuilder()
    status_emoji = "✅ Включено" if auto_add_enabled else "❌ Выключено"
    builder.button(
        text=f"Добавление в чаты: {status_emoji}",
        callback_data="toggle_auto_add"
    )
    return builder.as_markup()


SETTINGS_TEXT = (
    "Настройки бота:\n\n"
    "Вы можете включить или отключить автоматическое добавление вас "
    "в тематические чаты путешествий (по пригласительным ссылкам)."
)


@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def cmd_settings(message: types.Message, session) -> None:
    """Показывает меню настроек."""
    user = await UserRepository.get_user(session, message.from_user.id)

    if not user:
        await message.answer("Сначала напишите /start.")
        return

    await message.answer(SETTINGS_TEXT, reply_markup=get_settings_keyboard(user.auto_add_enabled))


@router.callback_query(F.data == "toggle_auto_add")
async def process_toggle_auto_add(callback: types.CallbackQuery, session) -> None:
    """Переключает настройку автоматического добавления в чаты."""
    new_value = await UserRepository.toggle_auto_add(session, callback.from_user.id)

    if new_value is None:
        await callback.answer("Пользователь не найден. Напишите /start.", show_alert=True)
        return

    try:
        await callback.message.edit_text(SETTINGS_TEXT, reply_markup=get_settings_keyboard(new_value))
    except Exception:
        logger.debug("Не удалось обновить сообщение настроек — контент не изменился")

    status = "включена" if new_value else "выключена"
    await callback.answer(f"Функция добавления в чаты теперь {status}")
