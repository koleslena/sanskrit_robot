# 🕉️ Sanskrit Bot (API Client)

Telegram-бот для морфологического анализа санскрита. Бот работает как легкий клиент, отправляя запросы к ML-моделям (сегментация и POS-теггинг), развернутым на Hugging Face Spaces.

## 🛠 Архитектура
- **Frontend**: Telegram Bot API (библиотека `aiogram`).
- **Backend (ML)**: Hugging Face Spaces (модели `sanskrit_nlp_models` и сегментатор, теггер `sanskrit_tagger`).
- **Host**: Любой Linux-сервер (VPS/VDS).

## 🚀 Быстрый старт

### Требования
- Python 3.10+
- Токен от @BotFather
- Работающий Space на Hugging Face (Gradio API)

### Установка
1. Клонируйте репозиторий:
   ```bash
   git clone [https://github.com/koleslena/sanskrit_robot.git](https://github.com/koleslena/sanskrit_robot.git)
   cd sanskrit_robot
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
   
### Настройка

Создайте файл .env или экспортируйте переменные окружения:

TELEGRAM_TOKEN: Ваш токен бота.

HF_SPACE_ID: Путь к вашему Space (например, username/space-name).

## ⚙️ Деплой (systemd)

Для работы бота в фоновом режиме на сервере используйте прилагаемый файл `sanskrit-robot.service`.

