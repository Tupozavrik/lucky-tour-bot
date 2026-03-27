import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
UON_API_KEY = os.getenv("UON_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "lucky_tour.db")
PROXY_URL = os.getenv("PROXY_URL", "")

# Бот должен быть администратором в этих чатах
THEMATIC_CHATS = {
    "Turkey": {
        "main": -1003743821562,
        "secret": -1000987654321
    },
    "Egypt": {
        "main": -1003794486597,
        "secret": -1004445556667
    }
}

SUPPORT_CHAT_URL = os.getenv("SUPPORT_CHAT_URL", "https://t.me/zxcwed")
UON_BASE_URL = "https://api.u-on.ru/"
