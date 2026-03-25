import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "5476095283:AAF_pFihJibLQWvrrX3oKvkIeFza7b6XxLk")
UON_API_KEY = os.getenv("UON_API_KEY", "")
DB_PATH = os.getenv("DB_PATH", "lucky_tour.db")

# Примеры тематических чатов (Замените на ваши актуальные ID чатов или используйте переменные окружения)
# Бот должен быть администратором в этих чатах для генерации пригласительных ссылок.
THEMATIC_CHATS = {
    "Turkey": -1001234567890,
    "Egypt": -1000987654321
}

# Базовый URL для UON API или настройки заглушки (mock).
UON_BASE_URL = "https://api.u-on.ru/"
