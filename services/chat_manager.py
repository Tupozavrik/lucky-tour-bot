# Управление чатами и ссылками

import logging

from telethon import TelegramClient
from telethon.errors import ChatAdminRequiredError, ChatForbiddenError, RPCError
from telethon.tl.functions.messages import ExportChatInviteRequest

from config import THEMATIC_CHATS

logger = logging.getLogger(__name__)


class ChatManager:

    @staticmethod
    async def generate_invite_links(client: TelegramClient, destination: str) -> list[dict]:
        # создаем ссылки под нужное направление
        dest_chats = THEMATIC_CHATS.get(destination)
        if not dest_chats:
            logger.warning("Чаты для направления '%s' не настроены", destination)
            return []

        links = []
        for chat_type, chat_id in dest_chats.items():
            url = await _create_invite_link(client, chat_id, destination)
            if url:
                chat_name = _get_chat_display_name(chat_type, destination)
                links.append({"name": chat_name, "url": url})

        return links


# --- Вспомогательные функции ---

async def _create_invite_link(client: TelegramClient, chat_id: int, destination: str) -> str | None:
    # делаем одноразовую ссылку в телеге
    try:
        invite = await client(ExportChatInviteRequest(
            peer=chat_id,
            usage_limit=1,
            title=f"Lucky Tour — {destination} (1 user)",
        ))
        return invite.link

    except ChatAdminRequiredError:
        logger.error(
            "Бот не является администратором чата %d. "
            "Выдайте боту права администратора.",
            chat_id,
        )
    except ChatForbiddenError:
        logger.error("Нет доступа к чату %d. Проверьте, добавлен ли бот.", chat_id)
    except RPCError as e:
        logger.error("Telegram отклонил запрос для чата %d: %s", chat_id, e)
    except Exception:
        logger.exception("Неожиданная ошибка при создании ссылки для чата %d", chat_id)

    return None


def _get_chat_display_name(chat_type: str, destination: str) -> str:
    # красивое имя для чата
    names = {
        "main":   "Туристы Lucky Tour",
        "secret": "Секретные места и экскурсии",
    }
    base_name = names.get(chat_type, chat_type.capitalize())
    return f"{base_name} ({destination})"
