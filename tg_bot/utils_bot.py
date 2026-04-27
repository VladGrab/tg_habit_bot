import os
import sqlite3


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, 'tg_bot.db')
SCHEMA_PATH = os.path.join(CURRENT_DIR, 'schema.sql')


def init_db():
    if not os.path.exists(SCHEMA_PATH):
        print("Файл schema.sql не найден!")
        return
    try:
        with sqlite3.connect(DB_PATH) as conn:
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            conn.executescript(sql_script)
            conn.commit()
            print("База данных успешно инициализирована.")
    except sqlite3.Error as e:
        print(f"Ошибка при работе с SQLite: {e}")


def add_token_to_db(user_id, token):
    with sqlite3.connect(DB_PATH) as conn:
        conn.cursor()
        conn.execute("""INSERT INTO tokens (user_id, token_string) VALUES (?, ?) 
                     ON CONFLICT(user_id) DO UPDATE SET token_string = excluded.token_string""",
                     (user_id, token))
        conn.commit()


def get_token_jwt(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.cursor()
        raw = conn.execute(f"SELECT token_string FROM tokens WHERE user_id = {user_id}")
        result = raw.fetchone()
        try:
            return result[0]
        except TypeError:
            return None
