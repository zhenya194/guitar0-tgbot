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

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    added_at TEXT
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

    # --- Admin management ---

    def add_admin(self, user_id: int, full_name: str) -> bool:
        """Add an admin. Returns True if added, False if already exists."""
        added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO admins (user_id, full_name, added_at) VALUES (?, ?, ?)",
                    (user_id, full_name, added_at)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_admin(self, user_id: int) -> bool:
        """Remove an admin. Returns True if removed, False if not found."""
        with self.conn:
            cursor = self.conn.execute(
                "DELETE FROM admins WHERE user_id = ?", (user_id,)
            )
        return cursor.rowcount > 0

    def is_admin(self, user_id: int) -> bool:
        """Check if user_id is in the admins table."""
        cursor = self.conn.execute(
            "SELECT 1 FROM admins WHERE user_id = ?", (user_id,)
        )
        return cursor.fetchone() is not None

    def get_all_admins(self) -> list[dict]:
        """Return list of all admins from DB."""
        cursor = self.conn.execute(
            "SELECT user_id, full_name, added_at FROM admins ORDER BY added_at"
        )
        return [
            {"user_id": row[0], "full_name": row[1], "added_at": row[2]}
            for row in cursor.fetchall()
        ]

db = Database()
