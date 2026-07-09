import shlex
import sqlite3
import sys
import termios
import tty
from pathlib import Path

import click
from rich.console import Console
from rich.text import Text

from ..loaders import SchemaManager
from .ingest import ingest
from .report import report

_DEFAULT_DB = "data/transactions.db"

_BANNER = """\
███████╗██████╗ ███████╗███╗   ██╗██████╗ ██╗     ███████╗███╗   ██╗███████╗
██╔════╝██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝████╗  ██║██╔════╝
███████╗██████╔╝█████╗  ██╔██╗ ██║██║  ██║██║     █████╗  ██╔██╗ ██║███████╗
╚════██║██╔═══╝ ██╔══╝  ██║╚██╗██║██║  ██║██║     ██╔══╝  ██║╚██╗██║╚════██║
███████║██║     ███████╗██║ ╚████║██████╔╝███████╗███████╗██║ ╚████║███████║
╚══════╝╚═╝     ╚══════╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝\
"""

_COMMANDS = [
    ("ingest", "ingest a bank statement  FILEPATH  --bank"),
    ("report", "monthly report  --month  [--csv]  [--output]"),
    ("clear", "clear the terminal"),
    ("exit", "exit the application"),
]


def _print_welcome(console: Console) -> None:
    console.print(Text(_BANNER, style="bold green"))
    console.print()
    console.print("  [dim]personal spending analyzer · SQLite · Python 3.12+[/dim]")
    console.print()
    console.print("  [bold]commands[/bold]")
    console.print()
    for cmd, desc in _COMMANDS:
        console.print(f"    [green]spendlens {cmd:<8}[/green]  [dim]{desc}[/dim]")
    console.print()
    console.print("  [dim]ESC to quit · <command> --help for details[/dim]")
    console.print()


def _read_line(prompt: str) -> str | None:
    """Reads a line of input. Returns None if ESC is pressed."""
    sys.stdout.write(prompt)
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    chars: list[str] = []

    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x1b":  # ESC
                sys.stdout.write("\n")
                return None
            elif ch in ("\r", "\n"):  # Enter
                sys.stdout.write("\n")
                return "".join(chars)
            elif ch == "\x7f":  # Backspace
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b")
            elif ch == "\x03":  # Ctrl+C
                sys.stdout.write("\n")
                raise KeyboardInterrupt
            elif ch >= " ":
                chars.append(ch)
                sys.stdout.write(ch)
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _run_repl(db: str) -> None:
    console = Console()
    _print_welcome(console)

    while True:
        try:
            line = _read_line("\033[32mspendlens\033[0m \033[2m›\033[0m ")
        except KeyboardInterrupt:
            break

        if line is None:
            break

        line = line.strip()
        if not line or line in ("exit", "quit"):
            break

        if line == "clear":
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
            _print_welcome(console)
            continue

        args = shlex.split(line)
        if args and args[0] == "spendlens":
            args = args[1:]

        if not args:
            continue

        try:
            cli.main(
                ["--db", db] + args,
                standalone_mode=True,
                obj={},
                prog_name="spendlens",
            )
        except SystemExit:
            pass
        except Exception as e:
            console.print(f"[red]error: {e}[/red]")

        console.print()


@click.group(invoke_without_command=True)
@click.option(
    "--db",
    default=_DEFAULT_DB,
    envvar="SPENDLENS_DB",
    help="Path to the SQLite database.",
)
@click.pass_context
def cli(ctx: click.Context, db: str) -> None:
    """SpendLens — personal spending analyzer."""
    db_path = Path(db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    SchemaManager(conn).create_tables()
    ctx.call_on_close(conn.close)

    ctx.ensure_object(dict)
    ctx.obj["conn"] = conn
    ctx.obj["db_path"] = db_path

    if ctx.invoked_subcommand is None:
        _run_repl(db)


cli.add_command(ingest)
cli.add_command(report)
