import sqlite3
import csv

DB = "feedback.db"

# --- Работа с базой данных ---
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            api_response TEXT,
            dharmamitra_response TEXT DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_error(query, response):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO errors (user_query, api_response) VALUES (?, ?)",
        (query, response)
    )
    conn.commit()
    conn.close()

def get_db_file():
    csv_path = "errors_report.csv"

    # 1. Читаем данные из базы
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM errors")
    rows = cursor.fetchall()
    
    if not rows:
        return None
    
    # Получаем названия колонок
    column_names = [description[0] for description in cursor.description]
    conn.close()

    # 2. Записываем в CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(column_names) # Заголовок
        writer.writerows(rows)        # Данные