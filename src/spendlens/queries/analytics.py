import sqlite3
from pathlib import Path


class AnalyticsQueries:
    """Runs analytical SQL queries against the transactions database."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.sql_dir = Path(__file__).parent / "sql"

    def _load_sql(self, filename: str) -> str:
        with open(self.sql_dir / filename) as f:
            return f.read()

    def _query(self, filename: str) -> list[dict]:
        cursor = self.conn.execute(self._load_sql(filename))
        if not cursor.description:
            return []
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def total_by_category_month(self) -> list[dict]:
        """Total expenses per category per month."""
        return self._query("total_by_category_month.sql")

    def moving_average_3months(self) -> list[dict]:
        """3-month moving average of expenses per category."""
        return self._query("moving_average_3months.sql")

    def top5_largest_expenses(self) -> list[dict]:
        """Top 5 largest expenses in the period."""
        return self._query("top5_largest_expenses.sql")

    def month_largest_balance_variation(self) -> list[dict]:
        """Months ranked by absolute balance variation (income - expenses)."""
        return self._query("month_largest_balance_variation.sql")
