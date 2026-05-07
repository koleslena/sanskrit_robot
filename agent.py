import sqlite3
import time
import logging
# from dharmamitra_sanskrit_grammar import DharmamitraSanskritProcessor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_pending_errors():
    # 1. Подключаемся к базе
    conn = sqlite3.connect("feedback.db")
    cursor = conn.cursor()

    try:
        # 2. Ищем записи, которые еще не обработаны агентом
        cursor.execute("SELECT id, user_query FROM errors WHERE dharmamitra_response IS NULL")
        rows = cursor.fetchall()

        if not rows:
            logging.info("Нет новых ошибок для обработки.")
            return

        logging.info(f"Найдено {len(rows)} новых записей для анализа.")

        # Инициализируем процессор Дхармамитры
        # processor = DharmamitraSanskritProcessor()

        # for row_id, query in rows:
        #     try:
        #         logging.info(f"Обработка запроса ID {row_id}: {query}")
                
        #         # 3. Запрос к Dharmamitra API
        #         # Используем самый подробный режим, чтобы иметь максимум данных для сравнения
        #         results = processor.process_batch(
        #             [query],
        #             mode="unsandhied-lemma-morphosyntax",
        #             human_readable_tags=True
        #         )

        #         # Преобразуем результат в строку (или JSON), чтобы сохранить в БД
        #         # Берём первый результат, так как мы передавали список из одного предложения
        #         dm_output = str(results[0]) if results else "No result from Dharmamitra"

        #         # 4. Обновляем базу данных
        #         cursor.execute(
        #             "UPDATE errors SET dharmamitra_response = ? WHERE id = ?",
        #             (dm_output, row_id)
        #         )
        #         conn.commit()
        #         logging.info(f"Запись ID {row_id} успешно обновлена.")

        #     except Exception as e:
        #         logging.error(f"Ошибка при обработке ID {row_id}: {e}")
        #         continue

    except Exception as e:
        logging.error(f"Ошибка базы данных: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logging.info("Агент запущен...")
    while True:
        process_pending_errors()
        # Проверяем базу каждые 5 минут (300 секунд)
        logging.info("Ожидание 5 минут перед следующей проверкой...")
        time.sleep(300)