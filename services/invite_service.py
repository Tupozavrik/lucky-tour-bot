"""Сервис для проверки направления и генерации invite-ссылок в тематические чаты."""

import logging
from dataclasses import dataclass

from aiogram import Bot

from services.uon_service import UonService
from services.chat_manager import ChatManager

logger = logging.getLogger(__name__)


@dataclass
class InviteResult:
    """Результат проверки направления и генерации ссылок."""
    destination: str | None = None
    links: list[dict[str, str]] | None = None
    auto_add_disabled: bool = False


class InviteService:
    """Бизнес-логика: проверка направления пользователя и генерация приглашений."""

    @staticmethod
    async def check_and_invite(bot: Bot, uon_id: str, auto_add_enabled: bool) -> InviteResult:
        """
        Проверяет направление по U-ON ID и генерирует invite-ссылки (если auto_add включён).

        Returns:
            InviteResult с заполненными полями в зависимости от результата.
        """
        destination = await UonService.get_user_destination(uon_id)

        if not destination:
            return InviteResult(destination=None)

        if not auto_add_enabled:
            return InviteResult(destination=destination, auto_add_disabled=True)

        links = await ChatManager.generate_invite_links(bot, destination)
        return InviteResult(destination=destination, links=links if links else None)
