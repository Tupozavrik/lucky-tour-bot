"""Обработчики профиля: просмотр, привязка U-ON ID, обновление направления.

Содержит центральный text_router — единую точку входа для всех текстовых
сообщений пользователя (FSM-состояния и кнопки главного меню).
"""

import logging

from telethon import TelegramClient, events, Button

from config import SUPPORT_CHAT_URL
from database import AsyncSessionLocal
from services.user_repository import UserRepository
from services.uon_service import UonService, UonApiError
from services.invite_service import InviteService, InviteResult
from utils.state_machine import get_state, set_state, clear_state, WAITING_FOR_UON_ID
from utils.throttle import throttled

logger = logging.getLogger(__name__)


def get_profile_keyboard() -> list:
    """Inline-клавиатура профиля."""
    return [
        [Button.inline("✏️ Изменить U-ON ID", b"change_uon_id")],
        [Button.inline("🔄 Обновить направление", b"refresh_destination")],
    ]


def get_cancel_keyboard() -> list:
    """Inline-клавиатура с кнопкой отмены."""
    return [[Button.inline("❌ Отмена", b"cancel_change_uon_id")]]


async def _show_profile(event) -> None:
    """Показывает профиль пользователя с U-ON ID и направлением."""
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_user(session, event.sender_id)

    if not user:
        await event.respond("Сначала напишите /start.")
        return

    if user.uon_id:
        try:
            destination = await UonService.get_user_destination(user.uon_id)
            dest_text = destination if destination else "Не найдено"
        except UonApiError:
            dest_text = "Сервис недоступен"
        text = (
            "<b>👤 Ваш профиль</b>\n\n"
            f"U-ON ID: <code>{user.uon_id}</code>\n"
            f"Направление: <b>{dest_text}</b>"
        )
    else:
        text = (
            "<b>👤 Ваш профиль</b>\n\n"
            "U-ON ID: <i>не привязан</i>\n"
            "Направление: <i>неизвестно</i>"
        )

    await event.respond(text, buttons=get_profile_keyboard(), parse_mode="html")


async def _handle_uon_id_input(event) -> None:
    """Обрабатывает ввод нового U-ON ID от пользователя (FSM-состояние)."""
    text = (event.text or "").strip()
    user_id = event.sender_id

    if not text.isdigit() or len(text) > 50:
        await event.respond(
            "Пожалуйста, отправьте корректный числовой идентификатор.\n"
            "Для отмены нажмите кнопку ниже или введите /profile.",
        )
        return

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_user(session, user_id)
        if not user:
            clear_state(user_id)
            await event.respond("Сначала напишите /start.")
            return

        await UserRepository.update_uon_id(session, user_id, text)
        auto_add_enabled = user.auto_add_enabled
        await session.commit()

    clear_state(user_id)
    await event.respond(
        f"✅ Идентификатор <code>{text}</code> успешно привязан!", parse_mode="html"
    )

    try:
        result = await InviteService.check_and_invite(event.client, text, auto_add_enabled)
        await _send_invite_result(event, result)
    except UonApiError as e:
        await event.respond(f"⚠️ {e}")


async def _send_invite_result(event, result: InviteResult) -> None:
    """Отправляет пользователю результат проверки направления и invite-ссылок."""
    if not result.destination:
        await event.respond("Для данного идентификатора активных туров пока не найдено.")
        return

    await event.respond(
        f"По данным U-ON вы летите в: <b>{result.destination}</b>", parse_mode="html"
    )

    if result.auto_add_disabled:
        await event.respond(
            "Автоматическое добавление в тематические чаты отключено. "
            "Включить можно в /settings."
        )
    elif result.links:
        links_text = "\n".join(f"👉 {link['name']}: {link['url']}" for link in result.links)
        await event.respond(
            f"Пригласительные ссылки для направления {result.destination}:\n\n{links_text}"
        )
    else:
        await event.respond(
            "Тематические чаты для этого направления ещё не настроены. "
            "Обратитесь в службу поддержки."
        )


def register_profile_handlers(client: TelegramClient) -> None:
    """Регистрирует хэндлеры профиля и центральный text_router.

    text_router регистрируется первым и обрабатывает все текстовые сообщения:
    - Команды (начинаются с '/') — пропускаются, у них свои хэндлеры
    - FSM-состояния (ввод U-ON ID) — приоритет выше кнопок
    - Кнопки главного меню — маршрутизируются по тексту
    """

    @client.on(events.NewMessage(func=lambda e: e.is_private and bool(e.text)))
    @throttled
    async def text_router(event) -> None:
        """Центральный маршрутизатор текстовых сообщений."""
        text = event.text or ""

        # Команды обрабатываются отдельными хэндлерами
        if text.startswith("/"):
            return

        user_id = event.sender_id
        state = get_state(user_id)

        # FSM: пользователь вводит U-ON ID
        if state == WAITING_FOR_UON_ID:
            await _handle_uon_id_input(event)
            return

        # Маршрутизация кнопок главного меню
        if text == "👤 Профиль":
            await _show_profile(event)

        elif text == "⚙️ Настройки":
            from .settings import show_settings_page
            await show_settings_page(event)

        elif text == "💬 Поддержка":
            await event.respond(
                "Возникли вопросы? Наша служба поддержки всегда на связи!",
                buttons=[[Button.url("Перейти в чат поддержки", SUPPORT_CHAT_URL)]],
            )

    @client.on(events.NewMessage(pattern=r"^/profile(?:@\w+)?$", func=lambda e: e.is_private))
    @throttled
    async def cmd_profile(event) -> None:
        """Команда /profile — показывает профиль."""
        await _show_profile(event)

    @client.on(events.CallbackQuery(data=b"change_uon_id"))
    async def process_change_uon_id(event) -> None:
        """Начинает процесс изменения U-ON ID."""
        set_state(event.sender_id, WAITING_FOR_UON_ID)
        try:
            # Убираем клавиатуру профиля, чтобы не путать пользователя
            msg = await event.get_message()
            if msg:
                await msg.edit(msg.message or ".", buttons=None, parse_mode="html")
        except Exception:
            logger.debug("Не удалось убрать клавиатуру профиля")

        await event.respond(
            "Пожалуйста, отправьте ваш новый уникальный идентификатор U-ON:",
            buttons=get_cancel_keyboard(),
        )
        await event.answer()

    @client.on(events.CallbackQuery(data=b"cancel_change_uon_id"))
    async def process_cancel_change_uon_id(event) -> None:
        """Отмена изменения U-ON ID."""
        clear_state(event.sender_id)
        await event.edit(
            "Изменение U-ON ID отменено. Профиль можно открыть кнопкой меню или командой /profile."
        )
        await event.answer()

    @client.on(events.CallbackQuery(data=b"refresh_destination"))
    async def process_refresh_destination(event) -> None:
        """Обновляет информацию о направлении и генерирует новые ссылки."""
        async with AsyncSessionLocal() as session:
            user = await UserRepository.get_user(session, event.sender_id)

        if not user or not user.uon_id:
            await event.answer(
                "Сначала привяжите U-ON ID через кнопку «Изменить U-ON ID».",
                alert=True,
            )
            return

        await event.answer("Обновляем информацию...")

        try:
            result = await InviteService.check_and_invite(
                event.client, user.uon_id, user.auto_add_enabled
            )
            await _send_invite_result(event, result)
        except UonApiError as e:
            await event.respond(f"⚠️ {e}")
