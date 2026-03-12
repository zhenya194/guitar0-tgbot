import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT
            )
        """)

        self.conn.commit()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                text TEXT,
                timestamp TEXT
            )
        """)

        self.conn.commit()

    def add_user(self, user_id, full_name):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", 
            (user_id, full_name)
        )
        self.conn.commit()

    def add_feedback(self, user_id, user_name, text):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO feedback (user_id, user_name, text, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, user_name, text, timestamp)
        )
        self.conn.commit()

db = Database()
