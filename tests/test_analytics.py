import pytest
from spendlens.queries import AnalyticsQueries


class TestAnalyticsQueries:
    """Test analytics queries."""

    def test_total_by_category_month(self, populated_conn):
        """Test total spending by category and month."""
        queries = AnalyticsQueries(populated_conn)
        result = queries.total_by_category_month()

        assert len(result) > 0
        assert all(
            "month" in row and "category" in row and "total" in row for row in result
        )

        may_data = [r for r in result if r["month"] == "2025-05"]
        assert len(may_data) > 0

    def test_moving_average_3months(self, populated_conn):
        """Test 3-month moving average."""
        queries = AnalyticsQueries(populated_conn)
        result = queries.moving_average_3months()

        assert len(result) > 0
        assert all(
            "month" in row
            and "category" in row
            and "total" in row
            and "moving_avg_3m" in row
            for row in result
        )
        assert any(r["moving_avg_3m"] is not None for r in result)

    def test_top5_largest_expenses(self, populated_conn):
        """Test top 5 largest expenses."""
        queries = AnalyticsQueries(populated_conn)
        result = queries.top5_largest_expenses()

        assert len(result) == 5
        assert all(
            "date" in row
            and "description" in row
            and "category" in row
            and "value" in row
            for row in result
        )

        values = [r["value"] for r in result]
        assert values == sorted(values, reverse=True)

        # Highest single expense in fixture is HOSPITAL (450.0)
        assert result[0]["value"] == 450.0

    def test_month_largest_balance_variation(self, populated_conn):
        """Test months ranked by absolute balance variation."""
        queries = AnalyticsQueries(populated_conn)
        result = queries.month_largest_balance_variation()

        assert len(result) == 3  # 3 months of data
        assert all(
            "month" in row
            and "income" in row
            and "expenses" in row
            and "balance" in row
            and "abs_variation" in row
            for row in result
        )

        variations = [r["abs_variation"] for r in result]
        assert variations == sorted(variations, reverse=True)

    def test_queries_return_dicts(self, populated_conn):
        """Test that all queries return list of dicts."""
        queries = AnalyticsQueries(populated_conn)

        for method_name in [
            "total_by_category_month",
            "moving_average_3months",
            "top5_largest_expenses",
            "month_largest_balance_variation",
        ]:
            result = getattr(queries, method_name)()
            assert isinstance(result, list)
            if result:
                assert isinstance(result[0], dict)

    def test_queries_with_empty_db(self, initialized_conn):
        """Test queries on empty database."""
        queries = AnalyticsQueries(initialized_conn)

        assert queries.total_by_category_month() == []
        assert queries.moving_average_3months() == []
        assert queries.top5_largest_expenses() == []
        assert queries.month_largest_balance_variation() == []
