import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "data/tennis.db"):
        self.db_path = db_path
        self.init_database()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_database(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    country TEXT,
                    birth_date DATE,
                    hand TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
