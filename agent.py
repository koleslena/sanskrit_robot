import os
import time
import json
import httpx
import psycopg2
import logging
from dotenv import load_dotenv
from responces import get_db_connection

load_dotenv()

DM_API_URL = "https://dharmamitra.org/bff/api/translation"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wait_for_table():
    """Ожидание появления таблицы в базе данных."""
    logging.info("Проверка готовности таблицы 'errors'...")
    while True:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Проверяем, существует ли таблица
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'errors'
                );
            """)
            exists = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            if exists:
                logging.info("Таблица 'errors' найдена! Агент приступает к работе.")
                break
            else:
                logging.info("Таблица 'errors' еще не создана. Ждем 10 секунд...")
        except Exception as e:
            logging.error(f"База данных еще недоступна: {e}. Ждем...")
        
        time.sleep(10)

def get_dm_response(query):
    """Отправляет запрос к новому API Dharmamitra и собирает текстовые дельты."""
    payload = {
        "input_sentence": query,
        "input_encoding": "auto",
        "target_lang": "english",
        "do_grammar": False,
        "mode": "explain-grammar",
        "messages": [
            {
                "parts": [{"type": "text", "text": query}],
                "role": "user"
            }
        ]
    }
    
    full_text = []
    try:
        # Используем тайм-аут побольше, так как генерация текста может занять время
        with httpx.Client(timeout=60.0) as client:
            with client.stream("POST", DM_API_URL, json=payload) as response:
                if response.status_code != 200:
                    return f"Error DM API: {response.status_code}"

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        content = line[6:]
                        if content == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(content)
                            # Нас интересуют только кусочки текста (delta)
                            if data.get("type") == "text-delta":
                                full_text.append(data.get("delta", ""))
                        except json.JSONDecodeError:
                            continue
                            
        return "".join(full_text) if full_text else "No explanation generated"
    except Exception as e:
        return f"Connection error: {str(e)}"

def process_pending_errors():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ищем записи, где еще нет ответа от Дхармамитры
        cursor.execute("SELECT id, user_query FROM errors WHERE dharmamitra_response IS NULL")
        rows = cursor.fetchall()

        if not rows:
            logging.info("Новых ошибок нет.")
            return

        for row_id, query in rows:
            logging.info(f"Анализируем запрос {row_id}: {query}")
            
            # Получаем ответ от нового API
            dm_explanation = get_dm_response(query)
            
            # Сохраняем результат
            cursor.execute(
                "UPDATE errors SET dharmamitra_response = %s WHERE id = %s",
                (dm_explanation, row_id)
            )
            conn.commit()
            logging.info(f"ID {row_id} обновлен.")

        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка в работе агента: {e}")

if __name__ == "__main__":
    logging.info("Агент запущен (Postgres Mode)...")

    # Сначала ждем, пока таблица появится в базе
    wait_for_table()

    while True:
        process_pending_errors()
        time.sleep(300)