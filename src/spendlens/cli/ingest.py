import sqlite3
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..extractors import NubankExtractor, ItauExtractor
from ..transformers import NubankTransformer, ItauTransformer
from ..classifiers import RuleClassifier
from ..loaders import SchemaManager, TransactionLoader


def get_db_path() -> Path:
    """Return path to SQLite database (create data/ dir if needed)."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir / "transactions.db"


@click.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--banco",
    type=click.Choice(["nubank", "itau"]),
    required=True,
    help="Bank source: nubank or itau",
)
def ingest(filepath: str, banco: str):
    """Ingest transactions from CSV file."""
    console = Console()

    # Validate input
    filepath = Path(filepath)
    if not filepath.exists():
        console.print(f"[red]Error: File not found: {filepath}[/red]")
        raise click.Exit(1)

    # Select extractor and transformer
    if banco == "nubank":
        extractor = NubankExtractor()
        transformer = NubankTransformer()
    else:  # itau
        extractor = ItauExtractor()
        transformer = ItauTransformer()

    # Initialize classifier and loader
    rules_path = Path("data") / "rules.yaml"
    if not rules_path.exists():
        console.print(f"[red]Error: Rules file not found: {rules_path}[/red]")
        raise click.Exit(1)

    try:
        classifier = RuleClassifier(str(rules_path))
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error loading rules: {e}[/red]")
        raise click.Exit(1)

    # Connect to database
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    schema_manager = SchemaManager(conn)
    schema_manager.create_tables()
    loader = TransactionLoader(conn)

    # Extract
    console.print(f"[cyan]Extracting from {banco.upper()}...[/cyan]")
    try:
        extraction = extractor.extract(str(filepath))
    except Exception as e:
        console.print(f"[red]Extraction error: {e}[/red]")
        conn.close()
        raise click.Exit(1)

    # Transform, classify, and load
    total_processed = 0
    total_inserted = 0
    total_duplicates = 0
    errors = []

    for raw_row in extraction.rows:
        try:
            transaction = transformer.transform(raw_row)
            category = classifier.classify(transaction.description)
            inserted = loader.load(transaction, category)
            total_processed += 1
            if inserted:
                total_inserted += 1
            else:
                total_duplicates += 1
        except Exception as e:
            errors.append(str(e))

    conn.close()

    # Display summary
    console.print("\n[bold cyan]Ingest Summary[/bold cyan]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Total Rows", str(extraction.total_rows))
    table.add_row("Processed", str(total_processed))
    table.add_row("Inserted", str(total_inserted))
    table.add_row("Duplicates", str(total_duplicates))
    table.add_row("Extraction Errors", str(len(extraction.errors)))
    table.add_row("Processing Errors", str(len(errors)))

    console.print(table)

    if extraction.errors:
        console.print("\n[yellow]Extraction Errors:[/yellow]")
        for err in extraction.errors:
            console.print(f"  • {err}")

    if errors:
        console.print("\n[yellow]Processing Errors:[/yellow]")
        for err in errors[:5]:  # Show first 5 errors
            console.print(f"  • {err}")
        if len(errors) > 5:
            console.print(f"  ... and {len(errors) - 5} more")

    console.print(f"\n[green]Database: {db_path}[/green]")
