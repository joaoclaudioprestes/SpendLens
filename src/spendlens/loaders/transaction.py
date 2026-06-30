import hashlib
import sqlite3

from ..transformers import Transaction


class TransactionLoader:
    """Load normalized transactions into SQLite with idempotent deduplication."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def load(self, transaction: Transaction, category: str) -> bool:
        """
        Insert a transaction into the database.

        Returns True if inserted, False if duplicate (hash already exists).
        """
        hash_ = self._compute_hash(transaction)
        origin_id = self._get_or_create("origins", transaction.source)
        category_id = self._get_or_create("categories", category)

        cur = self.conn.execute(
            "INSERT OR IGNORE INTO transactions "
            "(date, description, value, type, origin_id, category_id, hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(transaction.date),
                transaction.description,
                transaction.value,
                transaction.type,
                origin_id,
                category_id,
                hash_,
            ),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def _compute_hash(self, transaction: Transaction) -> str:
        """Compute SHA-256 hash of (date, description, value, source)."""
        key = f"{transaction.date}{transaction.description}{transaction.value}{transaction.source}"
        return hashlib.sha256(key.encode()).hexdigest()

    def _get_or_create(self, table: str, name: str) -> int:
        """Insert name into table if not exists, return its id."""
        self.conn.execute(f"INSERT OR IGNORE INTO {table} (name) VALUES (?)", (name,))
        row = self.conn.execute(
            f"SELECT id FROM {table} WHERE name = ?", (name,)
        ).fetchone()
        return row[0]
