from aiogram import Router
from .start import router as start_router
from .settings import router as settings_router
from .profile import router as profile_router

def setup_routers() -> list[Router]:
    """
    Возвращает список всех роутеров для включения в диспетчер.
    """
    return [
        start_router,
        settings_router,
        profile_router
    ]
