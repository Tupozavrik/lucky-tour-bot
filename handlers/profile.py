"""Обработчики профиля: просмотр, привязка U-ON ID, обновление направления."""

import logging

from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.user_repository import UserRepository
from services.uon_service import UonService, UonApiError
from services.invite_service import InviteService

logger = logging.getLogger(__name__)

router = Router(name="profile_router")


class ProfileStates(StatesGroup):
    waiting_for_uon_id = State()


def get_profile_keyboard() -> types.InlineKeyboardMarkup:
    """Inline-клавиатура профиля."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить U-ON ID", callback_data="change_uon_id")
    builder.button(text="🔄 Обновить направление", callback_data="refresh_destination")
    builder.adjust(1)
    return builder.as_markup()


def get_cancel_keyboard() -> types.InlineKeyboardMarkup:
    """Inline-клавиатура с кнопкой отмены."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_change_uon_id")
    return builder.as_markup()


@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def cmd_profile(message: types.Message, session) -> None:
    """Показывает профиль пользователя с U-ON ID и направлением."""
    user = await UserRepository.get_user(session, message.from_user.id)

    if not user:
        await message.answer("Сначала напишите /start.")
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

    await message.answer(text, reply_markup=get_profile_keyboard())


@router.callback_query(F.data == "change_uon_id")
async def process_change_uon_id(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Начинает процесс изменения U-ON ID (переход в FSM-состояние)."""
    await state.set_state(ProfileStates.waiting_for_uon_id)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        logger.debug("Не удалось убрать reply_markup — сообщение уже изменено")
    await callback.message.answer(
        "Пожалуйста, отправьте ваш новый уникальный идентификатор U-ON:",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_change_uon_id")
async def process_cancel_change_uon_id(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Отмена изменения U-ON ID."""
    await state.clear()
    await callback.message.edit_text(
        "Изменение U-ON ID отменено. Профиль можно открыть кнопкой меню или командой /profile."
    )
    await callback.answer()


@router.message(ProfileStates.waiting_for_uon_id, F.text)
async def process_new_uon_id(message: types.Message, state: FSMContext, bot: Bot, session) -> None:
    """Обрабатывает ввод нового U-ON ID от пользователя."""
    text = message.text.strip()
    user_id = message.from_user.id

    if not text.isdigit():
        await message.answer(
            "Пожалуйста, отправьте корректный числовой идентификатор.\n"
            "Для отмены нажмите кнопку ниже или введите /profile.",
        )
        return

    user = await UserRepository.get_user(session, user_id)
    if not user:
        await state.clear()
        await message.answer("Сначала напишите /start.")
        return

    await UserRepository.update_uon_id(session, user_id, text)
    await state.clear()
    await message.answer(f"✅ Идентификатор <code>{text}</code> успешно привязан!")

    try:
        result = await InviteService.check_and_invite(bot, text, user.auto_add_enabled)
        await _send_invite_result(message, result)
    except UonApiError as e:
        await message.answer(f"⚠️ {e}")


@router.callback_query(F.data == "refresh_destination")
async def process_refresh_destination(callback: types.CallbackQuery, bot: Bot, session) -> None:
    """Обновляет информацию о направлении и генерирует новые ссылки."""
    user = await UserRepository.get_user(session, callback.from_user.id)

    if not user or not user.uon_id:
        await callback.answer(
            "Сначала привяжите U-ON ID через кнопку «Изменить U-ON ID».",
            show_alert=True,
        )
        return

    await callback.answer("Обновляем информацию...")
    
    try:
        result = await InviteService.check_and_invite(bot, user.uon_id, user.auto_add_enabled)
        await _send_invite_result(callback.message, result)
    except UonApiError as e:
        await callback.message.answer(f"⚠️ {e}")


async def _send_invite_result(message: types.Message, result) -> None:
    """Отправляет пользователю результат проверки направления и invite-ссылок."""
    if not result.destination:
        await message.answer("Для данного идентификатора активных туров пока не найдено.")
        return

    await message.answer(f"По данным U-ON вы летите в: <b>{result.destination}</b>")

    if result.auto_add_disabled:
        await message.answer(
            "Автоматическое добавление в тематические чаты отключено. "
            "Включить можно в /settings."
        )
    elif result.links:
        links_text = "\n".join(f"👉 {link['name']}: {link['url']}" for link in result.links)
        await message.answer(
            f"Пригласительные ссылки для направления {result.destination}:\n\n{links_text}"
        )
    else:
        await message.answer(
            "Тематические чаты для этого направления ещё не настроены. "
            "Обратитесь в службу поддержки."
        )
