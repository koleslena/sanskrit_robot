import psycopg2
import os
import csv

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"), 
        database=os.getenv("DB_NAME", "feedback_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=os.getenv("DB_PORT", "5432")
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS errors (
            id SERIAL PRIMARY KEY,
            user_query TEXT,
            api_response TEXT,
            dharmamitra_response TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def save_error(query, response):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # В Postgres используем %s вместо ?
            cursor.execute(
                "INSERT INTO errors (user_query, api_response) VALUES (%s, %s)",
                (query, response)
            )
        conn.commit()
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
    finally:
        conn.close()

def get_db_file():
    csv_path = "errors_report.csv"
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM errors")
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Получаем названия колонок через описание курсора
            column_names = [desc[0] for desc in cursor.description]

        # Записываем в CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(column_names) # Заголовок
            writer.writerows(rows)        # Данные
            
        return csv_path

    except Exception as e:
        print(f"Ошибка при генерации отчета: {e}")
        return None
    finally:
        conn.close()