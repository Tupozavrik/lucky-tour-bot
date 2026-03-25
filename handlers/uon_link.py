from aiogram import Router, types, Bot, F
from database import AsyncSessionLocal, User
from sqlalchemy import select
from services.uon_service import UonMockService
from services.chat_manager import ChatManager

router = Router(name="uon_link_router")

@router.message(F.text)
async def process_uon_id(message: types.Message, bot: Bot):
    # Это действует как универсальный обработчик для текстовых сообщений, которые не являются командами.
    # Мы предполагаем, что текст может быть идентификатором UON.
    text = message.text.strip()
    user_id = message.from_user.id
    
    # Очень базовая проверка: обрабатывать только если это похоже на ID U-ON
    # В реальности это зависит от формата ID U-ON. Предположим, что он числовой.
    if not text.isdigit():
        return # Игнорировать обычный текст, который не похож на ID

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("Пожалуйста, сначала запустите бота командой /start.")
            return
            
        # Привязка ID
        user.uon_id = text
        await session.commit()
        
        await message.answer(f"✅ Ваш уникальный идентификатор `{text}` успешно привязан!", parse_mode="Markdown")
        
        # Теперь проверяем направление
        destination = await UonMockService.get_user_destination(text)
        
        if destination:
            await message.answer(f"По данным U-ON вы летите в: **{destination}**", parse_mode="Markdown")
            
            if user.auto_add_enabled:
                invite_link = await ChatManager.generate_invite_link(bot, destination)
                if invite_link:
                    await message.answer(
                        f"Так как у вас включено добавление в чаты, мы сгенерировали для вас пригласительную ссылку в чат направления {destination}:\n\n"
                        f"👉 {invite_link}"
                    )
                else:
                    await message.answer("К сожалению, тематический чат для этого направления еще не настроен или я не могу создать ссылку.")
            else:
                await message.answer("Функция автоматического добавления в тематические чаты отключена. Вы можете включить её в /settings.")
        else:
            await message.answer("Для данного идентификатора пока не найдено актуальных туров.")
