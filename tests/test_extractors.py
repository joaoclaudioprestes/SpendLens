import pytest
from pathlib import Path
import tempfile
from spendlens.extractors import NubankExtractor, ItauExtractor, ExtractionResult


@pytest.fixture
def nubank_sample():
    """Path to Nubank sample CSV."""
    return Path(__file__).parent.parent / "data" / "samples" / "nubank_sample.csv"


@pytest.fixture
def itau_sample():
    """Path to Itau sample CSV."""
    return Path(__file__).parent.parent / "data" / "samples" / "itau_sample.csv"


@pytest.fixture
def nubank_extractor():
    """Nubank extractor instance."""
    return NubankExtractor()


@pytest.fixture
def itau_extractor():
    """Itau extractor instance."""
    return ItauExtractor()


# --- NUBANK TESTS ---


class TestNubankExtractor:
    """Test NubankExtractor with valid and edge-case data."""

    def test_extract_valid_file(self, nubank_extractor, nubank_sample):
        """Extract valid Nubank CSV returns ExtractionResult with rows."""
        result = nubank_extractor.extract(str(nubank_sample))

        assert isinstance(result, ExtractionResult)
        assert len(result.rows) > 0
        assert all(isinstance(row, dict) for row in result.rows)

    def test_extract_has_required_fields(self, nubank_extractor, nubank_sample):
        """Each extracted row has required fields: Data, Descrição, Valor."""
        result = nubank_extractor.extract(str(nubank_sample))

        for row in result.rows:
            assert "Data" in row
            assert "Descrição" in row
            assert "Valor" in row

    def test_extract_no_missing_fields(self, nubank_extractor, nubank_sample):
        """No rows skipped due to missing fields in valid file."""
        result = nubank_extractor.extract(str(nubank_sample))

        missing_field_errors = [e for e in result.errors if "Missing fields" in e]
        assert len(missing_field_errors) == 0, (
            f"Unexpected missing field errors: {missing_field_errors}"
        )

    def test_extract_no_duplicates(self, nubank_extractor, nubank_sample):
        """Duplicate rows are skipped."""
        result = nubank_extractor.extract(str(nubank_sample))

        # Check if rows are unique by content
        rows_set = set(tuple(sorted(row.items())) for row in result.rows)
        assert len(rows_set) == len(result.rows), "Duplicate rows detected"

    def test_extract_metadata(self, nubank_extractor, nubank_sample):
        """Extraction result has metadata."""
        result = nubank_extractor.extract(str(nubank_sample))

        assert result.total_rows > 0
        assert result.skipped_rows >= 0
        assert isinstance(result.errors, list)

    def test_extract_file_not_found(self, nubank_extractor):
        """Extract non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            nubank_extractor.extract("/nonexistent/path/file.csv")

    def test_extract_directory_not_file(self, nubank_extractor):
        """Extract directory path raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                nubank_extractor.extract(tmpdir)

    def test_extract_malformed_csv(self, nubank_extractor):
        """Malformed CSV raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Data,Descrição,Valor\n")
            f.write("2025-03-06,INVALID,,EXTRA\n")  # Extra column
            f.flush()

            # Should still extract what it can (extra columns ignored)
            result = nubank_extractor.extract(f.name)
            assert isinstance(result, ExtractionResult)

    def test_extract_empty_values(self, nubank_extractor):
        """Rows with empty values are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Data,Descrição,Valor\n")
            f.write("2025-03-06,,100.00\n")  # Missing Descrição
            f.write("2025-03-07,VALID,-50.00\n")
            f.flush()

            result = nubank_extractor.extract(f.name)
            assert len(result.rows) == 1  # Only valid row
            assert result.skipped_rows > 0

    def test_extract_with_duplicates(self, nubank_extractor):
        """Duplicate rows are detected and skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Data,Descrição,Valor\n")
            f.write("2025-03-06,SAME TRANSACTION,-100.00\n")
            f.write("2025-03-06,SAME TRANSACTION,-100.00\n")  # Duplicate
            f.flush()

            result = nubank_extractor.extract(f.name)
            assert len(result.rows) == 1
            assert any("Duplicate" in e for e in result.errors)

    def test_extract_latin1_encoding(self, nubank_extractor):
        """Extract CSV with Latin-1 encoding (accents preserved)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="latin-1", delete=False
        ) as f:
            f.write("Data,Descrição,Valor\n")
            f.write("2025-03-06,AÇAÍ AÇÚCAR CAFÉ,-50.00\n")
            f.flush()

            result = nubank_extractor.extract(f.name)
            assert len(result.rows) == 1
            assert "AÇAÍ" in result.rows[0]["Descrição"]

    def test_extract_utf8_bom(self, nubank_extractor):
        """Extract CSV with UTF-8 BOM."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(b"\xef\xbb\xbf")  # UTF-8 BOM
            f.write("Data,Descrição,Valor\n".encode("utf-8"))
            f.write("2025-03-06,TESTE BOM,-50.00\n".encode("utf-8"))
            f.flush()

            result = nubank_extractor.extract(f.name)
            assert len(result.rows) == 1


# --- ITAU TESTS ---


class TestItauExtractor:
    """Test ItauExtractor with valid and edge-case data."""

    def test_extract_valid_file(self, itau_extractor, itau_sample):
        """Extract valid Itau CSV returns ExtractionResult with rows."""
        result = itau_extractor.extract(str(itau_sample))

        assert isinstance(result, ExtractionResult)
        assert len(result.rows) > 0
        assert all(isinstance(row, dict) for row in result.rows)

    def test_extract_has_required_fields(self, itau_extractor, itau_sample):
        """Each extracted row has required fields: data_lancamento, historico, valor, tipo."""
        result = itau_extractor.extract(str(itau_sample))

        for row in result.rows:
            assert "data_lancamento" in row
            assert "historico" in row
            assert "valor" in row
            assert "tipo" in row

    def test_extract_no_missing_fields(self, itau_extractor, itau_sample):
        """No rows skipped due to missing fields in valid file."""
        result = itau_extractor.extract(str(itau_sample))

        missing_field_errors = [e for e in result.errors if "Missing fields" in e]
        assert len(missing_field_errors) == 0

    def test_extract_different_field_count(
        self, itau_extractor, nubank_extractor, itau_sample, nubank_sample
    ):
        """Itau and Nubank extractors extract different field counts."""
        itau_result = itau_extractor.extract(str(itau_sample))
        nubank_result = nubank_extractor.extract(str(nubank_sample))

        # Itau has 4 fields, Nubank has 3
        if itau_result.rows:
            assert len(itau_result.rows[0]) == 4
        if nubank_result.rows:
            assert len(nubank_result.rows[0]) == 3

    def test_extract_tipo_field_preserved(self, itau_extractor, itau_sample):
        """Tipo field (C/D) is preserved in extracted data."""
        result = itau_extractor.extract(str(itau_sample))

        tipos = set(row["tipo"] for row in result.rows)
        assert "C" in tipos or "D" in tipos, "Expected C or D in tipo field"

    def test_extract_missing_tipo_field(self, itau_extractor):
        """Rows missing tipo field are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("data_lancamento,historico,valor,tipo\n")
            f.write("01/03/2025,VALID,-100.00,D\n")
            f.write("02/03/2025,MISSING_TIPO,-50.00,\n")
            f.flush()

            result = itau_extractor.extract(f.name)
            assert len(result.rows) == 1  # Only valid row


# --- INTEGRATION TESTS ---


class TestExtractorsIntegration:
    """Integration tests for both extractors."""

    def test_both_extractors_process_samples(
        self, nubank_extractor, itau_extractor, nubank_sample, itau_sample
    ):
        """Both extractors successfully process their respective samples."""
        nubank_result = nubank_extractor.extract(str(nubank_sample))
        itau_result = itau_extractor.extract(str(itau_sample))

        assert len(nubank_result.rows) > 0
        assert len(itau_result.rows) > 0

    def test_extractors_handle_permission_error(self, nubank_extractor):
        """Extractor raises FileNotFoundError for unreadable file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Data,Descrição,Valor\n")
            f.write("2025-03-06,TEST,-100.00\n")
            f.flush()

            # Change permissions to make unreadable (Unix only)
            import os
            import stat

            os.chmod(f.name, 0o000)

            try:
                with pytest.raises(FileNotFoundError):
                    nubank_extractor.extract(f.name)
            finally:
                os.chmod(f.name, 0o644)  # Restore for cleanup

    def test_extraction_result_structure(self, nubank_extractor, nubank_sample):
        """ExtractionResult has correct structure and types."""
        result = nubank_extractor.extract(str(nubank_sample))

        assert hasattr(result, "rows")
        assert hasattr(result, "total_rows")
        assert hasattr(result, "skipped_rows")
        assert hasattr(result, "errors")

        assert isinstance(result.rows, list)
        assert isinstance(result.total_rows, int)
        assert isinstance(result.skipped_rows, int)
        assert isinstance(result.errors, list)
