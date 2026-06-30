import sqlite3


class SchemaManager:
    """Manage SQLite schema creation and versioning."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_tables(self) -> None:
        """Create all required tables if they don't exist."""
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS origins (
                id   INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS categories (
                id   INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY,
                date        TEXT    NOT NULL,
                description TEXT    NOT NULL,
                value       REAL    NOT NULL,
                type        TEXT    NOT NULL,
                origin_id   INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                hash        TEXT    UNIQUE NOT NULL,
                FOREIGN KEY (origin_id)   REFERENCES origins(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );
            """
        )
        self.conn.commit()
