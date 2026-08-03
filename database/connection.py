import sqlite3
from typing import Optional

class DatabaseConnection:
    """Gestiona la conexión única a la base de datos local SQLite."""
    
    def __init__(self, db_path: str = "tierra_fertil_local.db"):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn