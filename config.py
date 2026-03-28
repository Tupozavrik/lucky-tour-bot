import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
UON_API_KEY = os.getenv("UON_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "lucky_tour.db")
PROXY_URL = os.getenv("PROXY_URL", "")
SUPPORT_CHAT_URL = os.getenv("SUPPORT_CHAT_URL", "https://t.me/zxcwed")
REDIS_URL = os.getenv("REDIS_URL", "")

UON_BASE_URL = "https://api.u-on.ru/"


# Конфигурация направлений загружается из destinations.json
DESTINATIONS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "destinations.json")

def load_destinations():
    if not os.path.exists(DESTINATIONS_CONFIG_PATH):
        return {}
    with open(DESTINATIONS_CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

DESTINATIONS_CONFIG = load_destinations()

# Функция хелпер для старого стиля использования, 
# возвращает только чаты для совместимости в chat_manager
THEMATIC_CHATS = {
    dest: config.get("chats", {})
    for dest, config in DESTINATIONS_CONFIG.items()
}
