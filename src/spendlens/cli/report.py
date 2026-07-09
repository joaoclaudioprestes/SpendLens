from datetime import date
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..reporters import CsvReporter, MarkdownReporter, ReportService

console = Console()

_INCOME_KEYS = {"income"}
_EXPENSE_KEYS = {"total", "moving_avg_3m", "value", "expenses", "abs_variation"}
_SIGNED_KEYS = {"balance"}


def _filter_by_month(results: dict, month: str) -> dict:
    """Keep only rows belonging to `month` (YYYY-MM), matched on 'month' or 'date' keys."""
    filtered = {}
    for name, rows in results.items():
        filtered[name] = [
            row for row in rows if row.get("month", row.get("date", ""))[:7] == month
        ]
    return filtered


def _fmt_cell(key: str, value) -> str:
    if key in _INCOME_KEYS:
        return f"[green]R$ {value:,.2f}[/green]"
    if key in _EXPENSE_KEYS:
        return f"[red]R$ {value:,.2f}[/red]"
    if key in _SIGNED_KEYS:
        color = "green" if value >= 0 else "red"
        return f"[{color}]R$ {value:,.2f}[/{color}]"
    return str(value)


@click.command()
@click.option(
    "--month",
    default=None,
    help="Month to filter (YYYY-MM). Defaults to current month.",
)
@click.option("--csv", "as_csv", is_flag=True, help="Also export each query as CSV.")
@click.option(
    "--output", default="./output", type=click.Path(), help="Output directory."
)
@click.pass_context
def report(ctx: click.Context, month: str, as_csv: bool, output: str):
    """Generate a spending report for a given month."""
    month = month or date.today().strftime("%Y-%m")

    results = _filter_by_month(ReportService(ctx.obj["conn"]).run(), month)

    console.print(f"\n[bold green]SpendLens Report — {month}[/bold green]")
    for name, rows in results.items():
        table = Table(
            title=name.replace("_", " ").title(), show_header=True, header_style="bold"
        )
        if rows:
            for col in rows[0]:
                table.add_column(col)
            for row in rows:
                table.add_row(*(_fmt_cell(k, v) for k, v in row.items()))
        console.print(table)

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    MarkdownReporter().write(results, output_dir / "report.md")
    if as_csv:
        CsvReporter().write(results, output_dir)

    console.print(f"\n[green]Report written to: {output_dir}[/green]")
