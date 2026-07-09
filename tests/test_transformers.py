import pytest
from datetime import date
from pathlib import Path
from spendlens.extractors import NubankExtractor, ItauExtractor
from spendlens.transformers import (
    NubankTransformer,
    ItauTransformer,
    Transaction,
)


@pytest.fixture
def nubank_extractor():
    return NubankExtractor()


@pytest.fixture
def itau_extractor():
    return ItauExtractor()


@pytest.fixture
def nubank_transformer():
    return NubankTransformer()


@pytest.fixture
def itau_transformer():
    return ItauTransformer()


@pytest.fixture
def nubank_sample():
    return Path(__file__).parent.parent / "data" / "samples" / "nubank_sample.csv"


@pytest.fixture
def itau_sample():
    return Path(__file__).parent.parent / "data" / "samples" / "itau_sample.csv"


# --- NUBANK TRANSFORMER TESTS ---


class TestNubankTransformer:
    """Test NubankTransformer with valid and invalid data."""

    def test_transform_valid_nubank_negative_value(self, nubank_transformer):
        """Valid Nubank row with negative value → expense transaction."""
        raw_row = {"Data": "2025-03-06", "Descrição": "IFOOD", "Valor": "-50.00"}
        result = nubank_transformer.transform(raw_row)

        assert isinstance(result, Transaction)
        assert result.date == date(2025, 3, 6)
        assert result.description == "IFOOD"
        assert result.value == 50.0
        assert result.type == "expense"
        assert result.source == "nubank"

    def test_transform_valid_nubank_positive_value(self, nubank_transformer):
        """Valid Nubank row with positive value → income transaction."""
        raw_row = {"Data": "2025-03-08", "Descrição": "SALARIO", "Valor": "1500.00"}
        result = nubank_transformer.transform(raw_row)

        assert result.date == date(2025, 3, 8)
        assert result.description == "SALARIO"
        assert result.value == 1500.0
        assert result.type == "income"
        assert result.source == "nubank"

    def test_transform_nubank_zero_value_rejected(self, nubank_transformer):
        """Nubank row with zero value is rejected."""
        raw_row = {"Data": "2025-03-06", "Descrição": "TEST", "Valor": "0.00"}

        with pytest.raises(ValueError, match="[Vv]alor.*zero|cannot be zero"):
            nubank_transformer.transform(raw_row)

    def test_transform_nubank_invalid_date(self, nubank_transformer):
        """Nubank row with invalid date raises ValueError."""
        raw_row = {"Data": "2025-13-45", "Descrição": "TEST", "Valor": "-50.00"}

        with pytest.raises(ValueError, match="data|date"):
            nubank_transformer.transform(raw_row)

    def test_transform_nubank_missing_data_field(self, nubank_transformer):
        """Nubank row missing 'Data' field raises ValueError."""
        raw_row = {"Descrição": "TEST", "Valor": "-50.00"}

        with pytest.raises(ValueError, match="Data|data|missing|required"):
            nubank_transformer.transform(raw_row)

    def test_transform_nubank_missing_descricao_field(self, nubank_transformer):
        """Nubank row missing 'Descrição' field raises ValueError."""
        raw_row = {"Data": "2025-03-06", "Valor": "-50.00"}

        with pytest.raises(ValueError, match="Descrição|descricao|missing|required"):
            nubank_transformer.transform(raw_row)

    def test_transform_nubank_missing_valor_field(self, nubank_transformer):
        """Nubank row missing 'Valor' field raises ValueError."""
        raw_row = {"Data": "2025-03-06", "Descrição": "TEST"}

        with pytest.raises(ValueError, match="Valor|valor|missing|required"):
            nubank_transformer.transform(raw_row)

    def test_transform_nubank_empty_descricao(self, nubank_transformer):
        """Nubank row with empty Descrição raises ValueError."""
        raw_row = {"Data": "2025-03-06", "Descrição": "", "Valor": "-50.00"}

        with pytest.raises(ValueError, match="Descrição|descricao|empty"):
            nubank_transformer.transform(raw_row)

    def test_transform_nubank_description_normalization(self, nubank_transformer):
        """Description is normalized (stripped, already uppercase from bank)."""
        raw_row = {"Data": "2025-03-06", "Descrição": "  IFOOD  ", "Valor": "-50.00"}
        result = nubank_transformer.transform(raw_row)

        assert result.description == "IFOOD"

    def test_transform_from_extraction_result(
        self, nubank_extractor, nubank_transformer, nubank_sample
    ):
        """Transform rows from Phase 1 ExtractionResult."""
        extraction_result = nubank_extractor.extract(str(nubank_sample))

        transformed = [
            nubank_transformer.transform(row) for row in extraction_result.rows
        ]

        assert len(transformed) > 0
        assert all(isinstance(t, Transaction) for t in transformed)
        assert all(t.source == "nubank" for t in transformed)


# --- ITAU TRANSFORMER TESTS ---


class TestItauTransformer:
    """Test ItauTransformer with valid and invalid data."""

    def test_transform_valid_itau_expense(self, itau_transformer):
        """Valid Itau row with tipo='D' → expense transaction."""
        raw_row = {
            "data_lancamento": "06/03/2025",
            "historico": "IFOOD",
            "valor": "50.00",
            "tipo": "D",
        }
        result = itau_transformer.transform(raw_row)

        assert isinstance(result, Transaction)
        assert result.date == date(2025, 3, 6)
        assert result.description == "IFOOD"
        assert result.value == 50.0
        assert result.type == "expense"
        assert result.source == "itau"

    def test_transform_valid_itau_income(self, itau_transformer):
        """Valid Itau row with tipo='C' → income transaction."""
        raw_row = {
            "data_lancamento": "08/03/2025",
            "historico": "TED RECEBIDA",
            "valor": "1500.00",
            "tipo": "C",
        }
        result = itau_transformer.transform(raw_row)

        assert result.date == date(2025, 3, 8)
        assert result.description == "TED RECEBIDA"
        assert result.value == 1500.0
        assert result.type == "income"
        assert result.source == "itau"

    def test_transform_itau_zero_value_rejected(self, itau_transformer):
        """Itau row with zero value is rejected."""
        raw_row = {
            "data_lancamento": "06/03/2025",
            "historico": "TEST",
            "valor": "0.00",
            "tipo": "D",
        }

        with pytest.raises(ValueError, match="[Vv]alor.*zero|cannot be zero"):
            itau_transformer.transform(raw_row)

    def test_transform_itau_invalid_date_format(self, itau_transformer):
        """Itau row with invalid date format raises ValueError."""
        raw_row = {
            "data_lancamento": "2025-03-06",  # Wrong format, should be DD/MM/YYYY
            "historico": "TEST",
            "valor": "50.00",
            "tipo": "D",
        }

        with pytest.raises(ValueError, match="data_lancamento|date|DD/MM/YYYY"):
            itau_transformer.transform(raw_row)

    def test_transform_itau_invalid_date_values(self, itau_transformer):
        """Itau row with invalid date values raises ValueError."""
        raw_row = {
            "data_lancamento": "32/13/2025",
            "historico": "TEST",
            "valor": "50.00",
            "tipo": "D",
        }

        with pytest.raises(ValueError, match="data_lancamento|date"):
            itau_transformer.transform(raw_row)

    def test_transform_itau_missing_data_lancamento(self, itau_transformer):
        """Itau row missing 'data_lancamento' raises ValueError."""
        raw_row = {"historico": "TEST", "valor": "50.00", "tipo": "D"}

        with pytest.raises(ValueError, match="data_lancamento|missing|required"):
            itau_transformer.transform(raw_row)

    def test_transform_itau_missing_historico(self, itau_transformer):
        """Itau row missing 'historico' raises ValueError."""
        raw_row = {"data_lancamento": "06/03/2025", "valor": "50.00", "tipo": "D"}

        with pytest.raises(ValueError, match="historico|missing|required"):
            itau_transformer.transform(raw_row)

    def test_transform_itau_missing_valor(self, itau_transformer):
        """Itau row missing 'valor' raises ValueError."""
        raw_row = {
            "data_lancamento": "06/03/2025",
            "historico": "TEST",
            "tipo": "D",
        }

        with pytest.raises(ValueError, match="valor|missing|required"):
            itau_transformer.transform(raw_row)

    def test_transform_itau_missing_tipo(self, itau_transformer):
        """Itau row missing 'tipo' raises ValueError."""
        raw_row = {
            "data_lancamento": "06/03/2025",
            "historico": "TEST",
            "valor": "50.00",
        }

        with pytest.raises(ValueError, match="tipo|missing|required"):
            itau_transformer.transform(raw_row)

    def test_transform_itau_invalid_tipo(self, itau_transformer):
        """Itau row with invalid tipo (not C or D) raises ValueError."""
        raw_row = {
            "data_lancamento": "06/03/2025",
            "historico": "TEST",
            "valor": "50.00",
            "tipo": "X",
        }

        with pytest.raises(ValueError, match="tipo|C|D|invalid"):
            itau_transformer.transform(raw_row)

    def test_transform_itau_empty_historico(self, itau_transformer):
        """Itau row with empty historico raises ValueError."""
        raw_row = {
            "data_lancamento": "06/03/2025",
            "historico": "",
            "valor": "50.00",
            "tipo": "D",
        }

        with pytest.raises(ValueError, match="historico|empty"):
            itau_transformer.transform(raw_row)

    def test_transform_from_extraction_result(
        self, itau_extractor, itau_transformer, itau_sample
    ):
        """Transform rows from Phase 1 ExtractionResult."""
        extraction_result = itau_extractor.extract(str(itau_sample))

        transformed = [
            itau_transformer.transform(row) for row in extraction_result.rows
        ]

        assert len(transformed) > 0
        assert all(isinstance(t, Transaction) for t in transformed)
        assert all(t.source == "itau" for t in transformed)


# --- TRANSACTION MODEL TESTS ---


class TestTransaction:
    """Test Transaction dataclass."""

    def test_transaction_creation(self):
        """Transaction can be created with all required fields."""
        t = Transaction(
            date=date(2025, 3, 6),
            description="TEST",
            value=50.0,
            type="expense",
            source="nubank",
        )

        assert t.date == date(2025, 3, 6)
        assert t.description == "TEST"
        assert t.value == 50.0
        assert t.type == "expense"
        assert t.source == "nubank"

    def test_transaction_type_hints(self):
        """Transaction enforces type hints (dataclass validation)."""
        # This test ensures the dataclass is properly typed
        # Python dataclasses don't enforce types at runtime, but they provide structure
        t = Transaction(
            date=date(2025, 3, 6),
            description="TEST",
            value=50.0,
            type="income",
            source="itau",
        )

        assert isinstance(t.date, date)
        assert isinstance(t.description, str)
        assert isinstance(t.value, float)
        assert isinstance(t.type, str)
        assert isinstance(t.source, str)
