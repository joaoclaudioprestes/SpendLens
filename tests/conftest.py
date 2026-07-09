import sqlite3
from datetime import date
import pytest

from spendlens.loaders import SchemaManager, TransactionLoader
from spendlens.transformers import Transaction


@pytest.fixture
def memory_conn():
    """In-memory SQLite connection."""
    return sqlite3.connect(":memory:")


@pytest.fixture
def initialized_conn(memory_conn):
    """Connection with tables already created."""
    schema_manager = SchemaManager(memory_conn)
    schema_manager.create_tables()
    return memory_conn


@pytest.fixture
def populated_conn(initialized_conn):
    """Connection with 100 test transactions across 3 months, 3 origins, 5 categories."""
    loader = TransactionLoader(initialized_conn)

    # Insert origins
    initialized_conn.execute("INSERT INTO origins (name) VALUES (?)", ("nubank",))
    initialized_conn.execute("INSERT INTO origins (name) VALUES (?)", ("itau",))
    initialized_conn.execute("INSERT INTO origins (name) VALUES (?)", ("bradesco",))

    # Insert categories
    categories = [
        "food",
        "transport",
        "entertainment",
        "health",
        "shopping",
    ]
    for cat in categories:
        initialized_conn.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
    initialized_conn.commit()

    # Insert 100 transactions across May, June, July 2025
    transactions = [
        # May - 35 transactions
        Transaction(date(2025, 5, 1), "IFOOD RESTAURANTE", 45.50, "expense", "nubank"),
        Transaction(date(2025, 5, 2), "UBER", 23.00, "expense", "nubank"),
        Transaction(date(2025, 5, 3), "SUPERMERCADO", 156.30, "expense", "itau"),
        Transaction(date(2025, 5, 4), "SALÁRIO", 5000.00, "income", "nubank"),
        Transaction(date(2025, 5, 5), "FARMACIA", 89.90, "expense", "bradesco"),
        Transaction(date(2025, 5, 6), "CINEMA", 60.00, "expense", "nubank"),
        Transaction(date(2025, 5, 7), "PADARIA", 25.00, "expense", "itau"),
        Transaction(date(2025, 5, 8), "TAXI", 34.50, "expense", "nubank"),
        Transaction(date(2025, 5, 9), "AÇAÍ", 18.00, "expense", "bradesco"),
        Transaction(date(2025, 5, 10), "NETFLIX", 29.90, "expense", "nubank"),
        Transaction(date(2025, 5, 11), "RESTAURANTE", 78.00, "expense", "itau"),
        Transaction(date(2025, 5, 12), "COMBUSTIVEL", 200.00, "expense", "nubank"),
        Transaction(date(2025, 5, 13), "HOSPITAL", 450.00, "expense", "bradesco"),
        Transaction(date(2025, 5, 14), "ROUPAS", 150.00, "expense", "nubank"),
        Transaction(date(2025, 5, 15), "SUPERMERCADO", 198.50, "expense", "itau"),
        Transaction(date(2025, 5, 16), "SPOTIFY", 12.99, "expense", "nubank"),
        Transaction(date(2025, 5, 17), "MERCADO", 89.30, "expense", "bradesco"),
        Transaction(date(2025, 5, 18), "IFOOD", 52.00, "expense", "nubank"),
        Transaction(date(2025, 5, 19), "UBER", 41.00, "expense", "itau"),
        Transaction(date(2025, 5, 20), "DENTISTA", 350.00, "expense", "nubank"),
        Transaction(date(2025, 5, 21), "EBOOK", 59.90, "expense", "bradesco"),
        Transaction(date(2025, 5, 22), "RESTAURANTE", 95.00, "expense", "nubank"),
        Transaction(date(2025, 5, 23), "ESTACIONAMENTO", 30.00, "expense", "itau"),
        Transaction(date(2025, 5, 24), "SUPERMERCADO", 201.20, "expense", "nubank"),
        Transaction(date(2025, 5, 25), "PRESENTE", 120.00, "expense", "bradesco"),
        Transaction(date(2025, 5, 26), "AÇAÍ", 22.00, "expense", "nubank"),
        Transaction(date(2025, 5, 27), "BOLO", 45.00, "expense", "itau"),
        Transaction(date(2025, 5, 28), "TAXI", 29.50, "expense", "nubank"),
        Transaction(date(2025, 5, 29), "GAME", 199.90, "expense", "bradesco"),
        Transaction(date(2025, 5, 30), "MEDICO", 200.00, "expense", "nubank"),
        Transaction(date(2025, 5, 31), "SAPATOS", 180.00, "expense", "itau"),
        Transaction(date(2025, 5, 5), "FREELANCE", 1500.00, "income", "bradesco"),
        Transaction(date(2025, 5, 10), "BONUS", 800.00, "income", "nubank"),
        Transaction(date(2025, 5, 15), "VENDA ITEM", 200.00, "income", "itau"),
        Transaction(date(2025, 5, 20), "CONSULTORIA", 600.00, "income", "nubank"),
        # June - 35 transactions
        Transaction(date(2025, 6, 1), "IFOOD", 38.00, "expense", "nubank"),
        Transaction(date(2025, 6, 2), "99", 45.00, "expense", "itau"),
        Transaction(date(2025, 6, 3), "MERCADO", 167.40, "expense", "nubank"),
        Transaction(date(2025, 6, 4), "SALÁRIO", 5000.00, "income", "bradesco"),
        Transaction(date(2025, 6, 5), "FARMACIA", 76.50, "expense", "nubank"),
        Transaction(date(2025, 6, 6), "CINEMA", 60.00, "expense", "itau"),
        Transaction(date(2025, 6, 7), "PADARIA", 31.00, "expense", "nubank"),
        Transaction(date(2025, 6, 8), "UBER", 38.00, "expense", "bradesco"),
        Transaction(date(2025, 6, 9), "AÇAÍ", 20.00, "expense", "nubank"),
        Transaction(date(2025, 6, 10), "HULU", 35.90, "expense", "itau"),
        Transaction(date(2025, 6, 11), "RESTAURANTE", 89.50, "expense", "nubank"),
        Transaction(date(2025, 6, 12), "COMBUSTIVEL", 220.00, "expense", "bradesco"),
        Transaction(date(2025, 6, 13), "CLINICA", 350.00, "expense", "nubank"),
        Transaction(date(2025, 6, 14), "JAQUETA", 200.00, "expense", "itau"),
        Transaction(date(2025, 6, 15), "SUPERMERCADO", 210.30, "expense", "nubank"),
        Transaction(date(2025, 6, 16), "APPLE MUSIC", 10.99, "expense", "bradesco"),
        Transaction(date(2025, 6, 17), "MERCADO", 95.00, "expense", "nubank"),
        Transaction(date(2025, 6, 18), "IFOOD", 61.00, "expense", "itau"),
        Transaction(date(2025, 6, 19), "TAXI", 52.00, "expense", "nubank"),
        Transaction(date(2025, 6, 20), "OCULISTA", 280.00, "expense", "bradesco"),
        Transaction(date(2025, 6, 21), "LIVRO", 89.90, "expense", "nubank"),
        Transaction(date(2025, 6, 22), "RESTAURANTE", 105.00, "expense", "itau"),
        Transaction(date(2025, 6, 23), "ESTACIONAMENTO", 45.00, "expense", "nubank"),
        Transaction(date(2025, 6, 24), "SUPERMERCADO", 189.40, "expense", "bradesco"),
        Transaction(date(2025, 6, 25), "BONECO", 99.90, "expense", "nubank"),
        Transaction(date(2025, 6, 26), "AÇAÍ", 24.00, "expense", "itau"),
        Transaction(date(2025, 6, 27), "BOLO", 50.00, "expense", "nubank"),
        Transaction(date(2025, 6, 28), "UBER", 35.50, "expense", "bradesco"),
        Transaction(date(2025, 6, 29), "GAME", 249.99, "expense", "nubank"),
        Transaction(date(2025, 6, 30), "CLINICA GERAL", 220.00, "expense", "itau"),
        Transaction(date(2025, 6, 5), "FREELANCE", 1200.00, "income", "nubank"),
        Transaction(date(2025, 6, 10), "BONUS", 600.00, "income", "bradesco"),
        Transaction(date(2025, 6, 15), "VENDA", 300.00, "income", "itau"),
        Transaction(date(2025, 6, 20), "CONSULTORIA", 800.00, "income", "nubank"),
        Transaction(
            date(2025, 6, 25), "BOLETO RECEBIDO", 500.00, "income", "bradesco"
        ),
        # July - 30 transactions
        Transaction(date(2025, 7, 1), "IFOOD", 42.00, "expense", "nubank"),
        Transaction(date(2025, 7, 2), "UBER", 48.00, "expense", "itau"),
        Transaction(date(2025, 7, 3), "SUPERMERCADO", 172.10, "expense", "nubank"),
        Transaction(date(2025, 7, 4), "SALÁRIO", 5000.00, "income", "bradesco"),
        Transaction(date(2025, 7, 5), "FARMACIA", 65.00, "expense", "nubank"),
        Transaction(date(2025, 7, 6), "CINEMA", 55.00, "expense", "itau"),
        Transaction(date(2025, 7, 7), "PADARIA", 28.00, "expense", "nubank"),
        Transaction(date(2025, 7, 8), "UBER", 33.00, "expense", "bradesco"),
        Transaction(date(2025, 7, 9), "AÇAÍ", 19.00, "expense", "nubank"),
        Transaction(date(2025, 7, 10), "DISNEY+", 39.90, "expense", "itau"),
        Transaction(date(2025, 7, 11), "RESTAURANTE", 75.00, "expense", "nubank"),
        Transaction(date(2025, 7, 12), "GASOLINA", 210.00, "expense", "bradesco"),
        Transaction(date(2025, 7, 13), "LABORATORIO", 150.00, "expense", "nubank"),
        Transaction(date(2025, 7, 14), "TENIS", 160.00, "expense", "itau"),
        Transaction(date(2025, 7, 15), "MERCADO", 178.50, "expense", "nubank"),
        Transaction(date(2025, 7, 16), "TIDAL", 12.99, "expense", "bradesco"),
        Transaction(date(2025, 7, 17), "MERCADO", 92.00, "expense", "nubank"),
        Transaction(date(2025, 7, 18), "IFOOD", 55.00, "expense", "itau"),
        Transaction(date(2025, 7, 19), "99", 40.00, "expense", "nubank"),
        Transaction(date(2025, 7, 20), "FARMACIA", 180.00, "expense", "bradesco"),
        Transaction(date(2025, 7, 21), "REVISTA", 65.00, "expense", "nubank"),
        Transaction(date(2025, 7, 22), "LANCHERIA", 48.00, "expense", "itau"),
        Transaction(date(2025, 7, 23), "ESTACIONAMENTO", 35.00, "expense", "nubank"),
        Transaction(date(2025, 7, 24), "SUPERMERCADO", 155.80, "expense", "bradesco"),
        Transaction(date(2025, 7, 25), "BONECO", 85.00, "expense", "nubank"),
        Transaction(date(2025, 7, 26), "PICOLÉ", 18.00, "expense", "itau"),
        Transaction(date(2025, 7, 27), "PASTEL", 22.00, "expense", "nubank"),
        Transaction(date(2025, 7, 28), "UBER", 39.00, "expense", "bradesco"),
        Transaction(date(2025, 7, 29), "JOGO", 199.99, "expense", "nubank"),
        Transaction(date(2025, 7, 30), "MEDICO", 250.00, "expense", "itau"),
    ]

    for txn in transactions:
        loader.load(
            txn,
            "food"
            if "restaurante" in txn.description.lower()
            or "ifood" in txn.description.lower()
            or "mercado" in txn.description.lower()
            or "padaria" in txn.description.lower()
            or "açaí" in txn.description.lower()
            or "bolo" in txn.description.lower()
            or "picolé" in txn.description.lower()
            or "pastel" in txn.description.lower()
            else "transport"
            if "uber" in txn.description.lower()
            or "taxi" in txn.description.lower()
            or "99" in txn.description.lower()
            or "combustivel" in txn.description.lower()
            or "gasolina" in txn.description.lower()
            or "estacionamento" in txn.description.lower()
            else "health"
            if "farmacia" in txn.description.lower()
            or "dentista" in txn.description.lower()
            or "hospital" in txn.description.lower()
            or "clinica" in txn.description.lower()
            or "medico" in txn.description.lower()
            or "oculista" in txn.description.lower()
            or "laboratorio" in txn.description.lower()
            else "entertainment"
            if "cinema" in txn.description.lower()
            or "netflix" in txn.description.lower()
            or "spotify" in txn.description.lower()
            or "hulu" in txn.description.lower()
            or "apple music" in txn.description.lower()
            or "disney" in txn.description.lower()
            or "tidal" in txn.description.lower()
            or "game" in txn.description.lower()
            or "jogo" in txn.description.lower()
            or "ebook" in txn.description.lower()
            or "livro" in txn.description.lower()
            or "revista" in txn.description.lower()
            else "shopping"
            if "roupas" in txn.description.lower()
            or "sapatos" in txn.description.lower()
            or "jaqueta" in txn.description.lower()
            or "tenis" in txn.description.lower()
            or "presente" in txn.description.lower()
            or "boneco" in txn.description.lower()
            else "shopping",
        )

    return initialized_conn
