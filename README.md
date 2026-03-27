# Lucky Tour Bot 🌴

Telegram-бот для автоматического добавления туристов в закрытые тематические чаты на основе данных из **U-ON Travel CRM**.

## 🚀 Возможности
- Распознавание направлений туристов по U-ON ID.
- Автоматическая генерация пригласительных ссылок.
- Deep-linking (`t.me/bot?start=id...`).
- Защита от спама (Throttling) и стабильное хранение состояний в **Redis**.
- Асинхронная архитектура (aiogram 3.x + aiosqlite + SQLAlchemy 2.0).

---

## 🛠 Установка и запуск

### 1. Требования
- Python 3.10 или выше.
- [Redis](https://redis.io/docs/install/) (рекомендуется для сохранения сессий и защиты от спама).

### 2. Клонирование и зависимости
Создайте виртуальное окружение и установите пакеты:
```bash
python -m venv venv

# Активация окружения (Windows)
venv\Scripts\activate

# Активация окружения (Linux/macOS)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Конфигурация (.env)
Скопируйте файл `.env.example` в `.env`:
```bash
cp .env.example .env
```
И заполните его вашими данными. Обратите внимание на переменную `REDIS_URL`. Если вы не хотите использовать Redis для локальной разработки, просто оставьте ее закомментированной (бот откатится на MemoryStorage).

### 4. Запуск (локально)
```bash
python main.py
```

## 🏗 Архитектура

- `main.py` — Точка входа в приложение (Bot & Dispatcher), внедрение Middleware.
- `database.py` — Конфигурация SQLAlchemy и модели.
- `handlers/` — Роутеры и обработчики команд/кнопок Telegram (MVC-контроллеры).
- `services/` — Бизнес-логика изоляции (CRM интеграция, генерация ссылок, репозитории).
- `middlewares/` — Промежуточное ПО (`ThrottlingMiddleware` и `DbSessionMiddleware`).
- `config.py` — Вводные конфигурации и парсинг `.env`.

## 🛡 Тестирование

Для запуска тестов используйте `pytest`:
```bash
pytest tests/
```
