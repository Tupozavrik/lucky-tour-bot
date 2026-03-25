from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import AsyncSessionLocal, User
from sqlalchemy import select

router = Router(name="settings_router")

def get_settings_keyboard(auto_add_enabled: bool) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    status_emoji = "✅ Включено" if auto_add_enabled else "❌ Выключено"
    builder.button(
        text=f"Добавление в чаты: {status_emoji}", 
        callback_data="toggle_auto_add"
    )
    return builder.as_markup()

@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    user_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("Сначала напишите /start.")
            return
            
        text = "Настройки бота:\n\nВы можете включить или отключить автоматическое добавление вас в тематические чаты путешествий (по пригласительным ссылкам)."
        await message.answer(text, reply_markup=get_settings_keyboard(user.auto_add_enabled))

@router.callback_query(F.data == "toggle_auto_add")
async def process_toggle_auto_add(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            user.auto_add_enabled = not user.auto_add_enabled
            await session.commit()
            
            text = "Настройки бота:\n\nВы можете включить или отключить автоматическое добавление вас в тематические чаты путешествий (по пригласительным ссылкам)."
            try:
                await callback.message.edit_text(text, reply_markup=get_settings_keyboard(user.auto_add_enabled))
            except Exception:
                pass
            
            await callback.answer(f"Функция добавления в чаты теперь {'включена' if user.auto_add_enabled else 'выключена'}")
        else:
            await callback.answer("Пользователь не найден. Напишите /start.", show_alert=True)
