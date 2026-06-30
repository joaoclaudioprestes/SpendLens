import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.cli import main


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def nubank_sample():
    """Path to Nubank sample CSV."""
    return Path(__file__).parent.parent / "data" / "samples" / "nubank_sample.csv"


@pytest.fixture
def itau_sample():
    """Path to Itau sample CSV."""
    return Path(__file__).parent.parent / "data" / "samples" / "itau_sample.csv"


class TestIngestCommand:
    """Test the 'ingest' CLI command."""

    def test_ingest_nubank_success(self, runner, nubank_sample):
        """ingest command succeeds with Nubank CSV."""
        result = runner.invoke(main, ["ingest", str(nubank_sample), "--banco", "nubank"])
        assert result.exit_code == 0
        assert "Ingest Summary" in result.output
        assert "Inserted" in result.output

    def test_ingest_itau_success(self, runner, itau_sample):
        """ingest command succeeds with Itau CSV."""
        result = runner.invoke(main, ["ingest", str(itau_sample), "--banco", "itau"])
        assert result.exit_code == 0
        assert "Ingest Summary" in result.output
        assert "Inserted" in result.output

    def test_ingest_missing_file(self, runner):
        """ingest fails when file doesn't exist."""
        result = runner.invoke(main, ["ingest", "/nonexistent/file.csv", "--banco", "nubank"])
        assert result.exit_code == 2  # Click error for invalid argument
        assert "does not exist" in result.output

    def test_ingest_missing_banco_option(self, runner, nubank_sample):
        """ingest fails without --banco option."""
        result = runner.invoke(main, ["ingest", str(nubank_sample)])
        assert result.exit_code == 2
        assert "Missing option '--banco'" in result.output

    def test_ingest_invalid_banco_option(self, runner, nubank_sample):
        """ingest fails with invalid --banco value."""
        result = runner.invoke(main, ["ingest", str(nubank_sample), "--banco", "invalid"])
        assert result.exit_code == 2
        assert "Invalid value for '--banco'" in result.output

    def test_ingest_creates_database(self, runner, nubank_sample):
        """ingest creates database file."""
        # Clean up before test
        db_path = Path("data") / "transactions.db"
        if db_path.exists():
            db_path.unlink()

        result = runner.invoke(main, ["ingest", str(nubank_sample), "--banco", "nubank"])
        assert result.exit_code == 0
        assert db_path.exists()

        # Verify database has data
        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        conn.close()
        assert count > 0

        # Clean up
        db_path.unlink()

    def test_ingest_idempotency(self, runner, nubank_sample):
        """Running ingest twice with same file results in same transaction count."""
        db_path = Path("data") / "transactions.db"
        if db_path.exists():
            db_path.unlink()

        # First ingest
        result1 = runner.invoke(main, ["ingest", str(nubank_sample), "--banco", "nubank"])
        assert result1.exit_code == 0

        conn = sqlite3.connect(str(db_path))
        count1 = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        conn.close()

        # Second ingest (same file)
        result2 = runner.invoke(main, ["ingest", str(nubank_sample), "--banco", "nubank"])
        assert result2.exit_code == 0

        conn = sqlite3.connect(str(db_path))
        count2 = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        conn.close()

        assert count1 == count2

        # Clean up
        db_path.unlink()

    def test_ingest_output_format(self, runner, nubank_sample):
        """ingest output contains expected summary table."""
        result = runner.invoke(main, ["ingest", str(nubank_sample), "--banco", "nubank"])
        assert result.exit_code == 0
        assert "Ingest Summary" in result.output
        assert "Total Rows" in result.output
        assert "Processed" in result.output
        assert "Inserted" in result.output
        assert "Duplicates" in result.output
        assert "Database:" in result.output
