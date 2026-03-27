"""Менеджер тематических чатов: генерация безопасных (одноразовых) invite-ссылок."""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import THEMATIC_CHATS

logger = logging.getLogger(__name__)


class ChatManager:

    @staticmethod
    async def generate_invite_links(bot: Bot, destination: str) -> list[dict]:
        """Возвращает новые одноразовые пригласительные ссылки для чатов нужного направления."""
        dest_chats = THEMATIC_CHATS.get(destination)
        if not dest_chats:
            logger.warning("Чаты для направления '%s' не настроены", destination)
            return []

        links = []
        for chat_type, chat_id in dest_chats.items():
            url = await _create_invite_link(bot, chat_id, destination)
            if url:
                chat_name = _get_chat_display_name(chat_type, destination)
                links.append({"name": chat_name, "url": url})

        return links


# --- Вспомогательные функции ---

async def _create_invite_link(bot: Bot, chat_id: int, destination: str) -> str | None:
    """Создаёт динамическую invite-ссылку только на 1 вступление (member_limit=1)."""
    try:
        # Для приватных комьюнити нельзя выдавать многоразовые ссылки.
        # Генерируем ссылку, по которой может пройти только 1 человек.
        invite = await bot.create_chat_invite_link(
            chat_id=chat_id,
            name=f"Lucky Tour — {destination} (1 user)",
            member_limit=1,
        )
        return invite.invite_link

    except TelegramForbiddenError:
        logger.error(
            "Бот не является администратором чата %d. "
            "Выдайте боту права администратора.",
            chat_id,
        )
    except TelegramBadRequest as e:
        logger.error("Telegram отклонил запрос для чата %d: %s", chat_id, e)
    except Exception:
        logger.exception("Неожиданная ошибка при создании ссылки для чата %d", chat_id)

    return None


def _get_chat_display_name(chat_type: str, destination: str) -> str:
    """Возвращает читаемое название чата для отображения пользователю."""
    names = {
        "main":   "Туристы Lucky Tour",
        "secret": "Секретные места и экскурсии",
    }
    base_name = names.get(chat_type, chat_type.capitalize())
    return f"{base_name} ({destination})"
