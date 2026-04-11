"""Ограничитель частоты сообщений (throttling) в виде Pyrogram-фильтра.

Этот модуль больше не используется как aiogram-middleware.
Используйте фильтр `throttled` из `utils.throttle`:

    from utils.throttle import throttled

    @app.on_message(filters.command("start") & throttled)
    async def handler(client, message): ...
"""

from utils.throttle import throttled

__all__ = ["throttled"]
