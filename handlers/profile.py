from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import AsyncSessionLocal, User
from sqlalchemy import select
from services.uon_service import UonService
from services.chat_manager import ChatManager

router = Router(name="profile_router")

class ProfileStates(StatesGroup):
    waiting_for_uon_id = State()

def get_profile_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить U-ON ID", callback_data="change_uon_id")
    builder.button(text="Обновить направление", callback_data="refresh_destination")
    builder.adjust(1)
    return builder.as_markup()

@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("Сначала напишите /start.")
            return

        if user.uon_id:
            destination = await UonService.get_user_destination(user.uon_id)
            dest_text = destination if destination else "Не найдено или недействительно"
            text = f"👤 **Ваш Профиль**\n\nТекущий U-ON ID: `{user.uon_id}`\nТекущее направление: **{dest_text}**"
        else:
            text = "👤 **Ваш Профиль**\n\nU-ON ID: `Не привязан`\nТекущее направление: **Неизвестно**"
            
        await message.answer(text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")

def get_cancel_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_change_uon_id")
    return builder.as_markup()

@router.callback_query(F.data == "change_uon_id")
async def process_change_uon_id(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ProfileStates.waiting_for_uon_id)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(
        "Пожалуйста, отправьте мне ваш новый уникальный идентификатор U-ON в ответном сообщении:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_change_uon_id")
async def process_cancel_change_uon_id(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Изменение U-ON ID отменено. Вы можете снова открыть профиль командой /profile или кнопкой меню.")
    await callback.answer()

@router.message(ProfileStates.waiting_for_uon_id, F.text)
async def process_new_uon_id(message: types.Message, state: FSMContext, bot: Bot):
    text = message.text.strip()
    user_id = message.from_user.id
    
    if not text.isdigit():
        await message.answer("Пожалуйста, отправьте корректный числовой идентификатор. Для отмены вы можете использовать любую другую команду, например /profile.")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await state.clear()
            await message.answer("Сначала напишите /start.")
            return

        user.uon_id = text
        await session.commit()
        
    await state.clear()
    await message.answer(f"✅ Ваш уникальный идентификатор `{text}` успешно привязан!", parse_mode="Markdown")
    await check_and_invite_user(message, bot, text, user.auto_add_enabled)

@router.callback_query(F.data == "refresh_destination")
async def process_refresh_destination(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.uon_id:
            await callback.answer("Сначала привяжите U-ON ID через кнопку 'Изменить U-ON ID'!", show_alert=True)
            return
            
    await callback.answer("Обновляем информацию...")
    await check_and_invite_user(callback.message, bot, user.uon_id, user.auto_add_enabled)


async def check_and_invite_user(message: types.Message, bot: Bot, uon_id: str, auto_add_enabled: bool):
    destination = await UonService.get_user_destination(uon_id)
    
    if destination:
        await message.answer(f"По данным U-ON вы летите в: **{destination}**", parse_mode="Markdown")
        
        if auto_add_enabled:
            links = await ChatManager.generate_invite_links(bot, destination)
            if links:
                links_text = "\n".join([f"👉 {link['name']}: {link['url']}" for link in links])
                await message.answer(
                    f"Так как у вас включено добавление в чаты, мы сгенерировали для вас пригласительные ссылки для направления {destination}:\n\n"
                    f"{links_text}"
                )
            else:
                await message.answer("К сожалению, тематические чаты для этого направления еще не настроены или я не могу создать ссылку.")
        else:
            await message.answer("Функция автоматического добавления в тематические чаты отключена. Вы можете включить её в /settings.")
    else:
        await message.answer("Для данного идентификатора пока не найдено актуальных туров.")
