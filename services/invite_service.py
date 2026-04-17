# Сервис для ссылок и инвайтов

import logging
from dataclasses import dataclass

from telethon import TelegramClient

from services.uon_service import UonService
from services.chat_manager import ChatManager

logger = logging.getLogger(__name__)


@dataclass
class InviteResult:
    # что в итоге получилось после проверки
    destination: str | None = None
    links: list[dict[str, str]] | None = None
    auto_add_disabled: bool = False


class InviteService:
    # бизнес-логика тут

    @staticmethod
    async def check_and_invite(
        client: TelegramClient, uon_id: str, auto_add_enabled: bool
    ) -> InviteResult:
        # основная функция: чекаем тур и даем ссылки
        destination = await UonService.get_user_destination(uon_id)

        if not destination:
            return InviteResult(destination=None)

        if not auto_add_enabled:
            return InviteResult(destination=destination, auto_add_disabled=True)

        links = await ChatManager.generate_invite_links(client, destination)
        return InviteResult(destination=destination, links=links if links else None)
