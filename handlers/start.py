from aiogram import Router, types, Bot, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database import AsyncSessionLocal, User
from sqlalchemy import select

from .profile import ProfileStates

def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Профиль")
    builder.button(text="⚙️ Настройки")
    builder.button(text="💬 Поддержка")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

router = Router(name="start_router")

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    args = command.args
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(telegram_id=user_id)
            session.add(user)
            await session.commit()
            
    # DeepLink: t.me/LuckyTourBot?start=id84756
    uon_id_from_link = None
    if args and args.startswith("id"):
        uon_id_from_link = args[2:]
        if uon_id_from_link.isdigit():
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.telegram_id == user_id))
                user = result.scalar_one()
                user.uon_id = uon_id_from_link
                await session.commit()
            
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
async def support_handler(message: types.Message):
    from config import SUPPORT_CHAT_URL
    builder = InlineKeyboardBuilder()
    builder.button(text="Перейти в чат поддержки", url=SUPPORT_CHAT_URL)
    await message.answer("Возникли вопросы? Наша служба поддержки всегда на связи!", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("enable_autoadd_"))
async def process_enable_autoadd(callback: types.CallbackQuery, bot: Bot):
    uon_id = callback.data.removeprefix("enable_autoadd_")
    user_id = callback.from_user.id
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one()
        user.auto_add_enabled = True
        await session.commit()
        
    await callback.message.edit_text("Вы согласились на добавление в чаты! Генерируем ссылки ⏳...")
    from .profile import check_and_invite_user
    await check_and_invite_user(callback.message, bot, uon_id, True)
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "disable_autoadd")
async def process_disable_autoadd(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one()
        user.auto_add_enabled = False
        await session.commit()
    await callback.message.edit_text("Вы отказались от приглашений. Включить эту функцию можно позже в настройках.")
    await callback.answer()
