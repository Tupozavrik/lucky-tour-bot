import logging
from aiogram import Bot
from config import THEMATIC_CHATS

logger = logging.getLogger(__name__)

class ChatManager:
    @staticmethod
    async def generate_invite_links(bot: Bot, destination: str) -> list:
        """Генерирует одноразовые пригласительные ссылки для чатов направления."""
        dest_chats = THEMATIC_CHATS.get(destination)
        if not dest_chats:
            logger.warning(f"No thematic chats found for destination: {destination}")
            return []
            
        links = []
        for chat_type, chat_id in dest_chats.items():
            try:
                invite_link = await bot.create_chat_invite_link(
                    chat_id=chat_id,
                    name=f"Invite for {destination}",
                    member_limit=1
                )
                
                chat_name = "Туристы Lucky Tour" if chat_type == "main" else "Секретные места и экскурсии"
                links.append({"name": f"{chat_name} ({destination})", "url": invite_link.invite_link})
            except Exception as e:
                logger.error(f"Error creating invite link for chat {chat_id}: {e}")
                
        return links
