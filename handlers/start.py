from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database import AsyncSessionLocal, User
from sqlalchemy import select

from .profile import ProfileStates

def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Профиль")
    builder.button(text="⚙️ Настройки")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)
router = Router(name="start_router")

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        # Проверка существования пользователя
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            # Создание нового пользователя
            user = User(telegram_id=user_id)
            session.add(user)
            await session.commit()
            
    welcome_text = (
        f"🙋 Привет, {message.from_user.first_name}!\n\n"
        "Я ваш тур-ассистент. Чтобы я мог добавлять вас в тематические путешественные чаты и помогать с туром, "
        "пожалуйста, *привяжите ваш аккаунт к системе U-ON*.\n\n"
        "Для этого просто отправьте мне ваш уникальный идентификатор U-ON в ответном сообщении."
    )
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    await state.set_state(ProfileStates.waiting_for_uon_id)
