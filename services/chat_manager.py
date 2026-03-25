import logging
from aiogram import Bot
from config import THEMATIC_CHATS

logger = logging.getLogger(__name__)

class ChatManager:
    @staticmethod
    async def generate_invite_link(bot: Bot, destination: str) -> str:
        """
        Генерирует одноразовую пригласительную ссылку для тематического чата, если он доступен.
        """
        chat_id = THEMATIC_CHATS.get(destination)
        if not chat_id:
            logger.warning(f"No thematic chat found for destination: {destination}")
            return None
        
        try:
            # Мы создаем пригласительную ссылку, по которой пользователи могут перейти для вступления.
            # creates_join_request=False делает это прямым приглашением.
            invite_link = await bot.create_chat_invite_link(
                chat_id=chat_id,
                name=f"Invite for {destination} trip",
                member_limit=1 # Одноразовое использование на генерацию для безопасности
            )
            return invite_link.invite_link
        except Exception as e:
            logger.error(f"Error creating invite link for chat {chat_id}: {e}")
            return None
