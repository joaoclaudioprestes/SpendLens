import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner

from spendlens.cli import main


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
        result = runner.invoke(
            main, ["ingest", str(nubank_sample), "--bank", "nubank"]
        )
        assert result.exit_code == 0
        assert "Ingest Summary" in result.output
        assert "Inserted" in result.output

    def test_ingest_itau_success(self, runner, itau_sample):
        """ingest command succeeds with Itau CSV."""
        result = runner.invoke(main, ["ingest", str(itau_sample), "--bank", "itau"])
        assert result.exit_code == 0
        assert "Ingest Summary" in result.output
        assert "Inserted" in result.output

    def test_ingest_missing_file(self, runner):
        """ingest fails when file doesn't exist."""
        result = runner.invoke(
            main, ["ingest", "/nonexistent/file.csv", "--bank", "nubank"]
        )
        assert result.exit_code == 2  # Click error for invalid argument
        assert "does not exist" in result.output

    def test_ingest_infers_bank_from_filename(self, runner, nubank_sample):
        """ingest infers --bank from a recognizable filename when omitted."""
        result = runner.invoke(main, ["ingest", str(nubank_sample)])
        assert result.exit_code == 0
        assert "Ingest Summary" in result.output

    def test_ingest_missing_bank_option(self, runner, tmp_path, nubank_sample):
        """ingest fails without --bank when the bank can't be inferred from filename."""
        ambiguous = tmp_path / "statement.csv"
        ambiguous.write_text(nubank_sample.read_text())

        result = runner.invoke(main, ["ingest", str(ambiguous)])
        assert result.exit_code == 1
        assert "--bank is required" in result.output

    def test_ingest_invalid_bank_option(self, runner, nubank_sample):
        """ingest fails with invalid --bank value."""
        result = runner.invoke(
            main, ["ingest", str(nubank_sample), "--bank", "invalid"]
        )
        assert result.exit_code == 2
        assert "Invalid value for '--bank'" in result.output

    def test_ingest_creates_database(self, runner, nubank_sample):
        """ingest creates database file."""
        # Clean up before test
        db_path = Path("data") / "transactions.db"
        if db_path.exists():
            db_path.unlink()

        result = runner.invoke(
            main, ["ingest", str(nubank_sample), "--bank", "nubank"]
        )
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
        result1 = runner.invoke(
            main, ["ingest", str(nubank_sample), "--bank", "nubank"]
        )
        assert result1.exit_code == 0

        conn = sqlite3.connect(str(db_path))
        count1 = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        conn.close()

        # Second ingest (same file)
        result2 = runner.invoke(
            main, ["ingest", str(nubank_sample), "--bank", "nubank"]
        )
        assert result2.exit_code == 0

        conn = sqlite3.connect(str(db_path))
        count2 = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        conn.close()

        assert count1 == count2

        # Clean up
        db_path.unlink()

    def test_ingest_output_format(self, runner, nubank_sample):
        """ingest output contains expected summary table."""
        result = runner.invoke(
            main, ["ingest", str(nubank_sample), "--bank", "nubank"]
        )
        assert result.exit_code == 0
        assert "Ingest Summary" in result.output
        assert "Total Rows" in result.output
        assert "Processed" in result.output
        assert "Inserted" in result.output
        assert "Duplicates" in result.output
        assert "Database:" in result.output


class TestIngestInteractivePicker:
    """Test the shadcn-style checkbox picker used when FILEPATH is omitted."""

    def test_infer_bank_from_filename(self):
        from spendlens.cli.ingest import _infer_bank

        assert _infer_bank(Path("nubank_sample.csv")) == "nubank"
        assert _infer_bank(Path("ITAU_2025.csv")) == "itau"
        assert _infer_bank(Path("statement.csv")) is None

    def test_pick_files_lists_samples_dir(self, monkeypatch):
        from spendlens.cli import ingest as ingest_module

        def fake_checkbox(console, title, choices):
            return [value for _, value in choices]

        monkeypatch.setattr(ingest_module, "checkbox", fake_checkbox)
        result = ingest_module._pick_files()
        names = {path.name for path, _ in result}
        assert names == {"nubank_sample.csv", "itau_sample.csv"}

    def test_pick_files_skips_unrecognized_bank(self, monkeypatch, tmp_path):
        from spendlens.cli import ingest as ingest_module

        monkeypatch.setattr(ingest_module, "_SAMPLES_DIR", tmp_path)
        (tmp_path / "mystery.csv").write_text("data,description,value\n")

        def fake_checkbox(console, title, choices):
            return [value for _, value in choices]

        monkeypatch.setattr(ingest_module, "checkbox", fake_checkbox)
        result = ingest_module._pick_files()
        assert result == []


class TestReportCommand:
    """Test the 'report' CLI command."""

    def test_report_generates_output(self, runner, nubank_sample, tmp_path):
        db_path = Path("data") / "transactions.db"
        if db_path.exists():
            db_path.unlink()

        runner.invoke(main, ["ingest", str(nubank_sample), "--bank", "nubank"])

        output_dir = tmp_path / "output"
        result = runner.invoke(
            main,
            ["report", "--month", "2025-03", "--csv", "--output", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "SpendLens Report" in result.output
        assert (output_dir / "report.md").exists()
        assert (output_dir / "report.md").stat().st_size > 0
        assert list(output_dir.glob("*.csv"))

        db_path.unlink()

    def test_report_creates_database_when_missing(self, runner, tmp_path):
        """report auto-creates an empty database, matching ingest's behavior."""
        db_path = Path("data") / "transactions.db"
        if db_path.exists():
            db_path.unlink()

        result = runner.invoke(main, ["report", "--month", "2025-03"])
        assert result.exit_code == 0
        assert db_path.exists()

        db_path.unlink()

    def test_report_respects_db_option(self, runner, nubank_sample, tmp_path):
        """--db overrides the default database path."""
        db_path = tmp_path / "custom.db"
        runner.invoke(
            main, ["--db", str(db_path), "ingest", str(nubank_sample), "--bank", "nubank"]
        )
        assert db_path.exists()

        result = runner.invoke(
            main, ["--db", str(db_path), "report", "--month", "2025-03"]
        )
        assert result.exit_code == 0
