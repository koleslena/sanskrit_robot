import os
import asyncio
import httpx  # Используем вместо gradio_client
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F

# Настройки
TOKEN = os.getenv("TELEGRAM_TOKEN")
# Используем прямой URL API вашего Space
API_URL = "https://koleslena-sanskrit-nlp-app.hf.space/run/predict"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("नमस्ते! Я готов к анализу. Пришли текст.")

@dp.message(F.text)
async def handle_sanskrit(message: types.Message):
    wait_msg = await message.answer("⏳ Анализирую...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Формируем запрос в формате, который ожидает Gradio 6.0+
            payload = {
                "data": [message.text]
            }
            
            response = await client.post(API_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                # Извлекаем результат из списка 'data' в ответе
                # Обычно это [segmented, tagged]
                result = data.get("data", [])
                
                if len(result) >= 2:
                    segmented, tagged = result[0], result[1]
                    res_text = (
                        f"<b>Segmentation:</b>\n<code>{segmented}</code>\n\n"
                        f"<b>POS Tagging:</b>\n<code>{tagged}</code>"
                    )
                    await wait_msg.edit_text(res_text, parse_mode="HTML")
                else:
                    await wait_msg.edit_text("⚠️ Неожиданный формат ответа от модели.")
            else:
                await wait_msg.edit_text(f"❌ Ошибка сервера HF: {response.status_code}")
                
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка подключения: {str(e)}")

async def main():
    print("Bot started with direct HTTPX client...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())