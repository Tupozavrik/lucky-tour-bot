"""Обработчики команды /start и DeepLink-привязки (Telethon)."""

import logging

from telethon import TelegramClient, events, Button
from telethon.tl.types import (
    ReplyKeyboardMarkup, KeyboardButtonRow,
    KeyboardButtonWebView, KeyboardButton,
)

from config import WEB_APP_URL
from database import AsyncSessionLocal
from services.user_repository import UserRepository
from services.invite_service import InviteService
from services.uon_service import UonApiError
from utils.state_machine import set_state, WAITING_FOR_UON_ID
from utils.throttle import throttled

logger = logging.getLogger(__name__)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное Reply-меню бота."""
    return ReplyKeyboardMarkup(
        rows=[
            KeyboardButtonRow(buttons=[
                KeyboardButtonWebView(text="🌐 Веб-приложение", url=WEB_APP_URL),
                KeyboardButton(text="👤 Профиль"),
            ]),
            KeyboardButtonRow(buttons=[
                KeyboardButton(text="⚙️ Настройки"),
                KeyboardButton(text="💬 Поддержка"),
            ]),
        ],
        resize=True,
    )


def register_start_handlers(client: TelegramClient) -> None:
    """Регистрирует хэндлеры /start и связанных callback-запросов."""

    @client.on(events.NewMessage(
        pattern=r'^/start(?:@\w+)?(?:\s(.+))?$',
        func=lambda e: e.is_private,
    ))
    @throttled
    async def cmd_start(event) -> None:
        """Обработка /start с опциональным DeepLink (t.me/bot?start=id84756)."""
        user_id = event.sender_id
        sender = await event.get_sender()
        first_name = (getattr(sender, "first_name", None) or "друг")
        args = event.pattern_match.group(1)
        uon_id_from_link = None

        async with AsyncSessionLocal() as session:
            await UserRepository.get_or_create_user(session, user_id)
            if args and args.startswith("id") and args[2:].isdigit():
                uon_id_from_link = args[2:]
                await UserRepository.update_uon_id(session, user_id, uon_id_from_link)
            await session.commit()

        if uon_id_from_link:
            await event.respond(
                f"🙋 Привет, {first_name}!\n\n"
                f"Мы успешно распознали вас! Ваш U-ON ID: <code>{uon_id_from_link}</code> привязан.",
                buttons=get_main_keyboard(),
                parse_mode="html",
            )
            await event.respond(
                "Мы создали специальные закрытые чаты для туристов вашего направления "
                "(поиск попутчиков, секретные места).\n\nЖелаете получить пригласительные ссылки?",
                buttons=[
                    [Button.inline("✅ Да, добавить меня в чаты",
                                   f"enable_autoadd_{uon_id_from_link}".encode())],
                    [Button.inline("❌ Нет, спасибо", b"disable_autoadd")],
                ],
            )
            return

        await event.respond(
            f"🙋 Привет, {first_name}!\n\n"
            "Я ваш тур-ассистент. Чтобы добавлять вас в тематические чаты и помогать с туром, "
            "пожалуйста, <b>привяжите ваш аккаунт к системе U-ON</b>.\n\n"
            "Для этого отправьте мне ваш уникальный идентификатор U-ON в следующем сообщении.",
            buttons=get_main_keyboard(),
            parse_mode="html",
        )
        set_state(user_id, WAITING_FOR_UON_ID)

    @client.on(events.CallbackQuery(pattern=rb"^enable_autoadd_(.+)$"))
    async def process_enable_autoadd(event) -> None:
        """Пользователь согласился на добавление в тематические чаты."""
        uon_id = event.pattern_match.group(1).decode()
        user_id = event.sender_id

        async with AsyncSessionLocal() as session:
            await UserRepository.set_auto_add(session, user_id, True)
            await session.commit()

        await event.edit("Вы согласились на добавление в чаты! Генерируем ссылки ⏳...")

        try:
            result = await InviteService.check_and_invite(event.client, uon_id, auto_add_enabled=True)
        except UonApiError as e:
            await event.respond(f"⚠️ {e}")
            await event.answer()
            return

        if result.links:
            links_text = "\n".join(f"👉 {link['name']}: {link['url']}" for link in result.links)
            await event.respond(
                f"Пригласительные ссылки для направления {result.destination}:\n\n{links_text}"
            )
        elif result.destination:
            await event.respond(
                "К сожалению, тематические чаты для этого направления ещё не настроены. "
                "Обратитесь в службу поддержки."
            )
        await event.answer()

    @client.on(events.CallbackQuery(data=b"disable_autoadd"))
    async def process_disable_autoadd(event) -> None:
        """Пользователь отказался от приглашений в чаты."""
        async with AsyncSessionLocal() as session:
            await UserRepository.set_auto_add(session, event.sender_id, False)
            await session.commit()

        await event.edit("Вы отказались от приглашений. Включить эту функцию можно позже в настройках.")
        await event.answer()
