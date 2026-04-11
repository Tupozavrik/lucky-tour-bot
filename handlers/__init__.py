from telethon import TelegramClient

from .start import register_start_handlers
from .settings import register_settings_handlers
from .profile import register_profile_handlers


def setup_handlers(client: TelegramClient) -> None:
    """Регистрирует все хэндлеры в приложении Telethon.

    Порядок регистрации важен:
    - profile — первым, содержит text_router (FSM + кнопки меню)
    - start, settings — командные и callback хэндлеры
    """
    register_profile_handlers(client)
    register_start_handlers(client)
    register_settings_handlers(client)
