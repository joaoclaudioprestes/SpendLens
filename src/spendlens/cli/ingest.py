from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..extractors import NubankExtractor, ItauExtractor
from ..transformers import NubankTransformer, ItauTransformer
from ..classifiers import RuleClassifier
from ..loaders import TransactionLoader
from .interactive import checkbox

console = Console()

_SAMPLES_DIR = Path("data/samples")


def _infer_bank(path: Path) -> str | None:
    name = path.stem.lower()
    if "nubank" in name:
        return "nubank"
    if "itau" in name:
        return "itau"
    return None


def _pick_files() -> list[tuple[Path, str]]:
    """Shadcn-style checkbox menu over data/samples/*.csv, bank inferred from filename."""
    candidates = sorted(_SAMPLES_DIR.glob("*.csv"))
    if not candidates:
        console.print(f"[yellow]No CSV files found in {_SAMPLES_DIR}/.[/yellow]")
        return []

    choices = []
    for path in candidates:
        bank = _infer_bank(path)
        label = f"{path.name}  [dim]({bank or 'unknown bank'})[/dim]"
        choices.append((label, (path, bank)))

    picked = checkbox(console, "Select statements to ingest", choices)

    valid = [(path, bank) for path, bank in picked if bank is not None]
    for path, bank in picked:
        if bank is None:
            console.print(
                f"[yellow]Skipping {path.name}: cannot infer --bank, "
                f"run `spendlens ingest {path} --bank <nubank|itau>` manually.[/yellow]"
            )
    return valid


def _ingest_one(conn, filepath: Path, bank: str) -> None:
    if bank == "nubank":
        extractor = NubankExtractor()
        transformer = NubankTransformer()
    else:  # itau
        extractor = ItauExtractor()
        transformer = ItauTransformer()

    rules_path = Path("data") / "rules.yaml"
    if not rules_path.exists():
        console.print(f"[red]Error: Rules file not found: {rules_path}[/red]")
        raise click.Exit(1)

    try:
        classifier = RuleClassifier(str(rules_path))
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error loading rules: {e}[/red]")
        raise click.Exit(1)

    loader = TransactionLoader(conn)

    console.print(f"[cyan]Extracting from {bank.upper()} ({filepath.name})...[/cyan]")
    try:
        extraction = extractor.extract(str(filepath))
    except Exception as e:
        console.print(f"[red]Extraction error: {e}[/red]")
        raise click.Exit(1)

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

    console.print()


@click.command()
@click.argument("filepath", required=False, type=click.Path(exists=True))
@click.option(
    "--bank",
    type=click.Choice(["nubank", "itau"]),
    required=False,
    help="Bank source: nubank or itau. Omit FILEPATH to pick interactively instead.",
)
@click.pass_context
def ingest(ctx: click.Context, filepath: str | None, bank: str | None):
    """Ingest transactions from a CSV file. Without FILEPATH, opens a picker."""
    if filepath is None:
        targets = _pick_files()
        if not targets:
            console.print("[yellow]No files selected.[/yellow]")
            return
    else:
        path = Path(filepath)
        resolved_bank = bank or _infer_bank(path)
        if resolved_bank is None:
            console.print(
                "[red]Error: --bank is required (could not infer bank from filename).[/red]"
            )
            raise click.Exit(1)
        targets = [(path, resolved_bank)]

    for path, resolved_bank in targets:
        _ingest_one(ctx.obj["conn"], path, resolved_bank)

    console.print(f"[green]Database: {ctx.obj['db_path']}[/green]")
