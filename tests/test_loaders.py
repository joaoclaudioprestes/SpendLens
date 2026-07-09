import sqlite3
from datetime import date

import pytest

from spendlens.loaders import SchemaManager, TransactionLoader
from spendlens.transformers import Transaction
from spendlens.extractors import NubankExtractor
from spendlens.transformers import NubankTransformer
from spendlens.classifiers import RuleClassifier
from pathlib import Path


@pytest.fixture
def memory_conn():
    """In-memory SQLite connection."""
    return sqlite3.connect(":memory:")


@pytest.fixture
def schema_manager(memory_conn):
    """SchemaManager with empty in-memory DB."""
    return SchemaManager(memory_conn)


@pytest.fixture
def initialized_conn(memory_conn, schema_manager):
    """Connection with tables already created."""
    schema_manager.create_tables()
    return memory_conn


@pytest.fixture
def transaction_loader(initialized_conn):
    """TransactionLoader with initialized schema."""
    return TransactionLoader(initialized_conn)


@pytest.fixture
def sample_transaction():
    """A sample Transaction for testing."""
    return Transaction(
        date=date(2025, 1, 15),
        description="IFOOD RESTAURANTE",
        value=45.50,
        type="expense",
        source="nubank",
    )


@pytest.fixture
def rules_path():
    """Path to rules.yaml."""
    return Path(__file__).parent.parent / "data" / "rules.yaml"


@pytest.fixture
def classifier(rules_path):
    """RuleClassifier instance."""
    return RuleClassifier(str(rules_path))


@pytest.fixture
def nubank_sample():
    """Path to Nubank sample CSV."""
    return Path(__file__).parent.parent / "data" / "samples" / "nubank_sample.csv"


# --- SCHEMA MANAGER TESTS ---


class TestSchemaManager:
    """Test schema creation and idempotency."""

    def test_create_tables_succeeds(self, schema_manager, memory_conn):
        """create_tables() creates all three tables."""
        schema_manager.create_tables()

        tables = memory_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [row[0] for row in tables]

        assert "origins" in table_names
        assert "categories" in table_names
        assert "transactions" in table_names

    def test_create_tables_idempotent(self, schema_manager):
        """Calling create_tables() multiple times doesn't error."""
        schema_manager.create_tables()
        schema_manager.create_tables()
        schema_manager.create_tables()
        # If we get here, no exception was raised.

    def test_origins_table_structure(self, schema_manager, memory_conn):
        """origins table has correct schema."""
        schema_manager.create_tables()

        # Check columns
        columns = memory_conn.execute("PRAGMA table_info(origins)").fetchall()
        col_names = [row[1] for row in columns]

        assert "id" in col_names
        assert "name" in col_names

    def test_categories_table_structure(self, schema_manager, memory_conn):
        """categories table has correct schema."""
        schema_manager.create_tables()

        columns = memory_conn.execute("PRAGMA table_info(categories)").fetchall()
        col_names = [row[1] for row in columns]

        assert "id" in col_names
        assert "name" in col_names

    def test_transactions_table_structure(self, schema_manager, memory_conn):
        """transactions table has correct schema with FKs."""
        schema_manager.create_tables()

        columns = memory_conn.execute("PRAGMA table_info(transactions)").fetchall()
        col_names = [row[1] for row in columns]

        assert "id" in col_names
        assert "date" in col_names
        assert "description" in col_names
        assert "value" in col_names
        assert "type" in col_names
        assert "origin_id" in col_names
        assert "category_id" in col_names
        assert "hash" in col_names


# --- TRANSACTION LOADER TESTS ---


class TestTransactionLoader:
    """Test transaction insertion and deduplication."""

    def test_load_single_transaction(self, transaction_loader, sample_transaction):
        """Load a single transaction returns True."""
        result = transaction_loader.load(sample_transaction, "food")
        assert result is True

    def test_load_transaction_inserted(
        self, transaction_loader, initialized_conn, sample_transaction
    ):
        """Loaded transaction appears in database."""
        transaction_loader.load(sample_transaction, "food")

        row = initialized_conn.execute("SELECT COUNT(*) FROM transactions").fetchone()
        assert row[0] == 1

    def test_load_duplicate_transaction_returns_false(
        self, transaction_loader, sample_transaction
    ):
        """Loading duplicate transaction returns False."""
        transaction_loader.load(sample_transaction, "food")
        result2 = transaction_loader.load(sample_transaction, "food")
        assert result2 is False

    def test_load_duplicate_not_inserted(
        self, transaction_loader, initialized_conn, sample_transaction
    ):
        """Duplicate transaction is not inserted."""
        transaction_loader.load(sample_transaction, "food")
        transaction_loader.load(sample_transaction, "food")

        row = initialized_conn.execute("SELECT COUNT(*) FROM transactions").fetchone()
        assert row[0] == 1

    def test_load_different_transactions(
        self, transaction_loader, initialized_conn, sample_transaction
    ):
        """Different transactions are both inserted."""
        transaction_loader.load(sample_transaction, "food")

        tx2 = Transaction(
            date=date(2025, 1, 16),
            description="UBER TRIP",
            value=25.00,
            type="expense",
            source="nubank",
        )
        transaction_loader.load(tx2, "transport")

        row = initialized_conn.execute("SELECT COUNT(*) FROM transactions").fetchone()
        assert row[0] == 2

    def test_origin_created_on_load(self, transaction_loader, initialized_conn):
        """Loading a transaction creates origin if not exists."""
        tx = Transaction(
            date=date(2025, 1, 15),
            description="TEST",
            value=10.0,
            type="expense",
            source="itau",
        )
        transaction_loader.load(tx, "other")

        origin = initialized_conn.execute(
            "SELECT id, name FROM origins WHERE name = ?", ("itau",)
        ).fetchone()
        assert origin is not None
        assert origin[1] == "itau"

    def test_category_created_on_load(
        self, transaction_loader, initialized_conn, sample_transaction
    ):
        """Loading a transaction creates category if not exists."""
        transaction_loader.load(sample_transaction, "food")

        category = initialized_conn.execute(
            "SELECT id, name FROM categories WHERE name = ?", ("food",)
        ).fetchone()
        assert category is not None
        assert category[1] == "food"

    def test_foreign_keys_integrity(
        self, transaction_loader, initialized_conn, sample_transaction
    ):
        """Loaded transaction has valid FKs to origins and categories."""
        transaction_loader.load(sample_transaction, "food")

        tx_row = initialized_conn.execute(
            "SELECT origin_id, category_id FROM transactions LIMIT 1"
        ).fetchone()
        origin_id, category_id = tx_row

        origin = initialized_conn.execute(
            "SELECT id FROM origins WHERE id = ?", (origin_id,)
        ).fetchone()
        assert origin is not None

        category = initialized_conn.execute(
            "SELECT id FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        assert category is not None


# --- IDEMPOTENCY TESTS ---


class TestIdempotency:
    """Test that ingesting the same data twice is safe."""

    def test_ingest_same_csv_twice_idempotent(
        self, initialized_conn, nubank_sample, classifier
    ):
        """Loading the same CSV twice results in the same row count."""
        loader = TransactionLoader(initialized_conn)

        # First pass
        extractor = NubankExtractor()
        extraction = extractor.extract(str(nubank_sample))
        transformer = NubankTransformer()
        for raw_row in extraction.rows:
            tx = transformer.transform(raw_row)
            category = classifier.classify(tx.description)
            loader.load(tx, category)

        count1 = initialized_conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        # Second pass (same data)
        extraction = extractor.extract(str(nubank_sample))
        for raw_row in extraction.rows:
            tx = transformer.transform(raw_row)
            category = classifier.classify(tx.description)
            loader.load(tx, category)

        count2 = initialized_conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        assert count1 == count2


# --- INTEGRATION TESTS ---


class TestIntegration:
    """Test full pipeline: extractor → transformer → classifier → loader."""

    def test_end_to_end_nubank(self, initialized_conn, nubank_sample, classifier):
        """Full pipeline with Nubank sample."""
        loader = TransactionLoader(initialized_conn)
        extractor = NubankExtractor()
        transformer = NubankTransformer()

        extraction = extractor.extract(str(nubank_sample))
        assert extraction.total_rows > 0

        count = 0
        for raw_row in extraction.rows:
            tx = transformer.transform(raw_row)
            category = classifier.classify(tx.description)
            if loader.load(tx, category):
                count += 1

        # Verify data in DB
        db_count = initialized_conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]
        assert db_count == count
        assert db_count > 0

    def test_origins_populated(self, initialized_conn, nubank_sample, classifier):
        """Origins table is populated during pipeline."""
        loader = TransactionLoader(initialized_conn)
        extractor = NubankExtractor()
        transformer = NubankTransformer()

        extraction = extractor.extract(str(nubank_sample))
        for raw_row in extraction.rows:
            tx = transformer.transform(raw_row)
            category = classifier.classify(tx.description)
            loader.load(tx, category)

        origins = initialized_conn.execute("SELECT COUNT(*) FROM origins").fetchone()[0]
        assert origins > 0

    def test_categories_populated(self, initialized_conn, nubank_sample, classifier):
        """Categories table is populated during pipeline."""
        loader = TransactionLoader(initialized_conn)
        extractor = NubankExtractor()
        transformer = NubankTransformer()

        extraction = extractor.extract(str(nubank_sample))
        for raw_row in extraction.rows:
            tx = transformer.transform(raw_row)
            category = classifier.classify(tx.description)
            loader.load(tx, category)

        categories = initialized_conn.execute(
            "SELECT COUNT(*) FROM categories"
        ).fetchone()[0]
        assert categories > 0
