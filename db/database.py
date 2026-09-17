import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_name TEXT,
                    text TEXT,
                    date TEXT
                )
            """)

    def add_user(self, user_id, full_name):
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", 
                (user_id, full_name)
            )

    def add_feedback(self, user_id, user_name, text):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            self.conn.execute(
                "INSERT INTO feedback (user_id, user_name, text, date) VALUES (?, ?, ?, ?)",
                (user_id, user_name, text, date)
            )

db = Database()
