import os
import asyncio
import httpx  # Используем вместо gradio_client
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F

# Настройки
TOKEN = os.getenv("TELEGRAM_TOKEN")
# Используем прямой URL API вашего Space
API_URL = "https://koleslena-sanskrit-nlp-app.hf.space/gradio_api/call/predict"

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
                    result_url = f"https://koleslena-sanskrit-nlp-app.hf.space/gradio_api/call/predict/{event_id}"
                    
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
    print("Bot started with direct HTTPX client...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())