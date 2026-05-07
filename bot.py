import os
import asyncio
import httpx
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
from responces import get_db_file, init_db, save_error

load_dotenv()

# Настройки
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
# Используем прямой URL API вашего Space
API_URL = "https://koleslena-sanskrit-nlp-app.hf.space/gradio_api/call/predict"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Клавиатура ---
def get_error_keyboard():
    builder = InlineKeyboardBuilder()
    # Мы передаем callback_data, чтобы бот понял, что нажата именно кнопка ошибки
    builder.row(types.InlineKeyboardButton(
        text="❌ Ошибка в ответе", 
        callback_data="report_error")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("नमस्ते! Я готов к анализу. Пришли текст.")

@dp.message(Command("export"))
async def export_to_csv(message: types.Message):
    # Замени на свой Telegram ID для безопасности!
    if message.from_user.id == ADMIN_ID: 
        csv_path = get_db_file()

        if not csv_path:
            await message.answer("База пока пуста, экспортировать нечего.")
            return None
        
        csv_file = FSInputFile(csv_path)
        await message.answer_document(csv_file, caption="Актуальная база ошибок")
    else:
        await message.answer("У вас нет прав для этой команды.")

@dp.callback_query(F.data == "report_error")
async def process_error_report(callback: types.CallbackQuery):
    # Достаем текст запроса и ответа прямо из сообщения, над которым кнопка
    # В ответе у нас текст формата "Segmentation: ... POS Tagging: ..."
    original_text = callback.message.text
    # Находим цитату пользователя (Reply), если есть, или берем контекст
    # Для простоты сохраним текущее состояние сообщения
    
    # Чтобы вытащить изначальный запрос пользователя, 
    # лучше всего использовать reply_to_message
    user_query = callback.message.reply_to_message.text if callback.message.reply_to_message else "Unknown"
    api_response = original_text

    save_error(user_query, api_response)
    
    await callback.answer("Ошибка записана. Агент скоро её проверит!")
    await callback.message.edit_reply_markup(reply_markup=None) 

@dp.message(F.text)
async def handle_sanskrit(message: types.Message):
    wait_msg = await message.answer("⏳ Анализирую...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Формируем запрос в формате, который ожидает Gradio 6.0+
            payload = {
                "data": [message.text],
                "api_name": "/predict"
            }
            
            response = await client.post(API_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                # В режиме /call/ ответ часто содержит event_id
                event_id = data.get("event_id")
                
                if event_id:
                    # Если получили ID события, нужно "дозабрать" результат
                    result_url = f"{API_URL}/{event_id}"
                    
                    # Ждем секунду, пока модель думает
                    await asyncio.sleep(1) 
                    
                    res_get = await client.get(result_url)
                    # Gradio присылает результат в формате Server-Sent Events (строками)
                    # Нам нужно вытащить данные из строки, начинающейся с 'data: '
                    for line in res_get.text.split('\n'):
                        if line.startswith('data: '):
                            import json
                            clean_data = json.loads(line[6:])
                            segmented, tagged = clean_data[0], clean_data[1]
                            
                            res_text = (
                                f"<b>Segmentation:</b>\n<code>{segmented}</code>\n\n"
                                f"<b>POS Tagging:</b>\n<code>{tagged}</code>"
                            )
                            await wait_msg.edit_text(res_text, parse_mode="HTML")
                            return
                else:
                    await wait_msg.edit_text("⚠️ Ошибка: не удалось получить ID события.")
            else:
                await wait_msg.edit_text(f"❌ Ошибка сервера HF: {response.status_code}")
                
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка подключения: {str(e)}")

async def main():
    init_db()
    print("Bot started with direct HTTPX client...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())