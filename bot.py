import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from gradio_client import Client

# Настройки
TOKEN = os.getenv("TELEGRAM_TOKEN")
# Ссылка на Space
HF_SPACE_ID = "koleslena/sanskrit-nlp-app" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализируем клиент Gradio
# Он сам найдет нужную функцию в app.py
client = Client(HF_SPACE_ID)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("नमस्ते! Я бот-интерфейс для Sanskrit NLP. Пришли текст для анализа.")

@dp.message(F.text)
async def handle_sanskrit(message: types.Message):
    wait_msg = await message.answer("⏳ Анализирую...")
    
    try:
        # Обращаемся к API Space
        # '.predict' вызывает функцию, привязанную к кнопке в Gradio
        # Передаем текст и указываем имя функции или индекс кнопки (обычно 0)
        result = client.predict(
            message.text,	
            api_name="/predict" 
        )
        
        # Результат приходит в виде кортежа (segmented, tagged)
        segmented, tagged = result
        
        response = (
            f"<b>Segmentation:</b>\n<code>{segmented}</code>\n\n"
            f"<b>POS Tagging:</b>\n<code>{tagged}</code>"
        )
        
        await wait_msg.edit_text(response, parse_mode="HTML")
        
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка API: {str(e)}")

async def main():
    print(f"Bot started as API client for {HF_SPACE_ID}...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())