import sqlite3

from spendlens.queries import AnalyticsQueries


class ReportService:
    """Responsible for generating reports based on analytics queries."""

    def __init__(self, conn: sqlite3.Connection):
        self._q = AnalyticsQueries(conn)

    def run(self) -> dict:
        """Run the analytics queries and return the results as a dictionary."""
        return {
            "total_by_category_month": self._q.total_by_category_month(),
            "moving_average_3months": self._q.moving_average_3months(),
            "top5_largest_expenses": self._q.top5_largest_expenses(),
            "month_largest_balance_variation": self._q.month_largest_balance_variation(),
        }
