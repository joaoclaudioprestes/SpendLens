import os
import select
import sys
import termios
import tty
from typing import TypeVar

from rich.console import Console

T = TypeVar("T")


def _getch(fd: int) -> str:
    """Reads one byte straight from the fd (bypasses sys.stdin's internal
    buffer, which would otherwise desync from the select() calls below)."""
    return os.read(fd, 1).decode(errors="replace")


def _read_key(fd: int) -> str:
    """Reads a single keypress, resolving arrow-key escape sequences.

    Assumes the terminal is already in raw mode for the duration of the
    picker session — toggling raw/cooked mode per keystroke corrupts
    multi-byte sequences like arrow keys.
    """
    ch = _getch(fd)
    if ch == "\x1b":
        # A bare ESC has no follow-up bytes; an arrow key does.
        if select.select([fd], [], [], 0.05)[0]:
            ch2 = _getch(fd)
            if ch2 == "[" and select.select([fd], [], [], 0.05)[0]:
                ch3 = _getch(fd)
                return {"A": "up", "B": "down"}.get(ch3, "")
        return "esc"
    if ch in ("\r", "\n"):
        return "enter"
    if ch == " ":
        return "space"
    if ch == "\x03":
        raise KeyboardInterrupt
    if ch == "j":
        return "down"
    if ch == "k":
        return "up"
    return ch


def _render(title: str, labels: list[str], selected: list[bool], cursor: int) -> list[str]:
    lines = [f"  [bold]{title}[/bold]", ""]
    for i, label in enumerate(labels):
        mark = "[green]●[/green]" if selected[i] else "○"
        pointer = "[cyan]›[/cyan]" if i == cursor else " "
        lines.append(f"  {pointer} {mark} {label}")
    lines.append("")
    lines.append("  [dim]↑/↓ move · space toggle · enter confirm · esc cancel[/dim]")
    return lines


def checkbox(console: Console, title: str, choices: list[tuple[str, T]]) -> list[T]:
    """Interactive multi-select checkbox menu (shadcn-CLI style). Returns selected values."""
    if not choices:
        return []

    labels = [label for label, _ in choices]
    selected = [False] * len(choices)
    cursor = 0

    lines = _render(title, labels, selected, cursor)
    sys.stdout.write("\033[?25l")  # hide cursor
    for line in lines:
        console.print(line)

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            key = _read_key(fd)
            if key == "up":
                cursor = (cursor - 1) % len(choices)
            elif key == "down":
                cursor = (cursor + 1) % len(choices)
            elif key == "space":
                selected[cursor] = not selected[cursor]
            elif key == "enter":
                break
            elif key == "esc":
                selected = [False] * len(choices)
                break

            sys.stdout.write(f"\033[{len(lines)}A")
            lines = _render(title, labels, selected, cursor)
            for line in lines:
                sys.stdout.write("\033[2K")
                console.print(line)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[?25h")  # show cursor
        sys.stdout.flush()

    return [value for (_, value), is_sel in zip(choices, selected) if is_sel]
