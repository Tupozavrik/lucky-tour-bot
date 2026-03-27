"""Обработчики команды /start, поддержки и DeepLink-привязки."""

import logging

from aiogram import Router, types, Bot, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from config import SUPPORT_CHAT_URL
from services.user_repository import UserRepository
from services.invite_service import InviteService

from .profile import ProfileStates

logger = logging.getLogger(__name__)

router = Router(name="start_router")


def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    """Главное Reply-меню бота."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Профиль")
    builder.button(text="⚙️ Настройки")
    builder.button(text="💬 Поддержка")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext, bot: Bot) -> None:
    """Обработка /start с опциональным DeepLink (t.me/bot?start=id84756)."""
    user_id = message.from_user.id
    user = await UserRepository.get_or_create_user(user_id)

    # DeepLink: t.me/LuckyTourBot?start=id84756
    args = command.args
    if args and args.startswith("id"):
        uon_id_from_link = args[2:]
        if uon_id_from_link.isdigit():
            await UserRepository.update_uon_id(user_id, uon_id_from_link)

            welcome_text = (
                f"🙋 Привет, {message.from_user.first_name}!\n\n"
                f"Мы успешно распознали вас! Ваш U-ON ID: `{uon_id_from_link}` привязан."
            )
            await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Да, добавить меня в чаты", callback_data=f"enable_autoadd_{uon_id_from_link}")
            builder.button(text="❌ Нет, спасибо", callback_data="disable_autoadd")
            builder.adjust(1)

            await message.answer(
                "Мы создали специальные закрытые чаты для туристов вашего направления (поиск попутчиков, секретные места).\n\n"
                "Желаете получить пригласительные ссылки?",
                reply_markup=builder.as_markup()
            )
            return

    welcome_text = (
        f"🙋 Привет, {message.from_user.first_name}!\n\n"
        "Я ваш тур-ассистент. Чтобы я мог добавлять вас в тематические путешественные чаты и помогать с туром, "
        "пожалуйста, *привяжите ваш аккаунт к системе U-ON*.\n\n"
        "Для этого просто отправьте мне ваш уникальный идентификатор U-ON в ответном сообщении."
    )

    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    await state.set_state(ProfileStates.waiting_for_uon_id)


@router.message(F.text == "💬 Поддержка")
async def support_handler(message: types.Message) -> None:
    """Отправляет кнопку-ссылку на чат поддержки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Перейти в чат поддержки", url=SUPPORT_CHAT_URL)
    await message.answer("Возникли вопросы? Наша служба поддержки всегда на связи!", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("enable_autoadd_"))
async def process_enable_autoadd(callback: types.CallbackQuery, bot: Bot) -> None:
    """Пользователь согласился на добавление в тематические чаты."""
    uon_id = callback.data.removeprefix("enable_autoadd_")
    user_id = callback.from_user.id

    await UserRepository.set_auto_add(user_id, True)
    await callback.message.edit_text("Вы согласились на добавление в чаты! Генерируем ссылки ⏳...")

    result = await InviteService.check_and_invite(bot, uon_id, auto_add_enabled=True)

    if result.links:
        links_text = "\n".join([f"👉 {link['name']}: {link['url']}" for link in result.links])
        await callback.message.answer(
            f"Пригласительные ссылки для направления {result.destination}:\n\n{links_text}"
        )
    elif result.destination:
        await callback.message.answer(
            "К сожалению, тематические чаты для этого направления еще не настроены или я не могу создать ссылку."
        )

    await callback.answer()


@router.callback_query(F.data == "disable_autoadd")
async def process_disable_autoadd(callback: types.CallbackQuery) -> None:
    """Пользователь отказался от приглашений в чаты."""
    await UserRepository.set_auto_add(callback.from_user.id, False)
    await callback.message.edit_text("Вы отказались от приглашений. Включить эту функцию можно позже в настройках.")
    await callback.answer()
