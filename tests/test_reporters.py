import csv
from pathlib import Path

import pytest

from spendlens.reporters import CsvReporter, MarkdownReporter, ReportService


@pytest.fixture
def results(populated_conn):
    return ReportService(populated_conn).run()


class TestReportService:
    def test_run_returns_all_keys(self, results):
        assert set(results) == {
            "total_by_category_month",
            "moving_average_3months",
            "top5_largest_expenses",
            "month_largest_balance_variation",
        }

    def test_run_returns_lists_of_dicts(self, results):
        for rows in results.values():
            assert isinstance(rows, list)
            assert isinstance(rows[0], dict)


class TestCsvReporter:
    def test_writes_one_csv_per_query(self, results, tmp_path):
        CsvReporter().write(results, tmp_path)
        files = {f.stem for f in tmp_path.glob("*.csv")}
        assert files == set(results)

    def test_csv_has_correct_headers(self, results, tmp_path):
        CsvReporter().write(results, tmp_path)
        path = tmp_path / "top5_largest_expenses.csv"
        rows = list(csv.DictReader(path.open()))
        assert "value" in rows[0] and "description" in rows[0]


class TestMarkdownReporter:
    def test_file_is_not_empty(self, results, tmp_path):
        out = tmp_path / "report.md"
        MarkdownReporter().write(results, out)
        assert out.stat().st_size > 0

    def test_contains_section_headers(self, results, tmp_path):
        out = tmp_path / "report.md"
        MarkdownReporter().write(results, out)
        content = out.read_text()
        assert "## Total By Category Month" in content
        assert "## Top5 Largest Expenses" in content

    def test_contains_markdown_table(self, results, tmp_path):
        out = tmp_path / "report.md"
        MarkdownReporter().write(results, out)
        content = out.read_text()
        assert "| ---" in content

    def test_empty_db_writes_no_data_placeholder(self, initialized_conn, tmp_path):
        results = ReportService(initialized_conn).run()
        out = tmp_path / "report.md"
        MarkdownReporter().write(results, out)
        assert "_No data._" in out.read_text()
