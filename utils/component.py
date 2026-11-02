"""Reusable console formatting and input helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Sequence, overload


def header(text: str, *, clear: bool = True) -> None:
    """Print a centered application heading."""
    width = max(40, shutil.get_terminal_size((80, 20)).columns)
    if clear:
        command = ["cmd", "/c", "cls"] if os.name == "nt" else ["clear"]
        subprocess.run(command, check=False)
    line = "=" * width
    print(f"\n{line}\n{text.center(width)}\n{line}")


def section(title: str) -> None:
    """Print a section title and separator."""
    print(f"\n{title}\n{'-' * max(len(title), 20)}")


def show_menu(options: Sequence[str], *, prompt: str = "Select an option: ") -> int | None:
    """Display menu options and return a numeric choice, or None for invalid input."""
    for option in options:
        print(option)
    try:
        value = input(f"\n{prompt}").strip()
    except EOFError:
        return 0
    return int(value) if value.isdigit() else None


def show_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    """Render a fully bordered, width-adjusted terminal table."""
    if not headers:
        print("(No columns)")
        return
    values = [[_format_cell(value) for value in row] for row in rows]
    widths = [len(str(name)) for name in headers]
    for row in values:
        for index in range(min(len(row), len(widths))):
            widths[index] = max(widths[index], len(row[index]))
    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def print_row(cells: Sequence[str]) -> None:
        padded_cells = list(cells[:len(widths)])
        padded_cells.extend([""] * (len(widths) - len(padded_cells)))
        print("|" + "|".join(
            f" {cell.ljust(widths[index])} "
            for index, cell in enumerate(padded_cells)
        ) + "|")

    print(border)
    print_row([str(name) for name in headers])
    print(border)
    if values:
        for row in values:
            print_row(row)
            print(border)
    else:
        print_row(["No records"])
        print(border)


def display_records(
    title: str,
    records: Sequence[dict[str, Any]],
    fields: Sequence[tuple[str, str]],
) -> None:
    """Print selected fields from API records as a labeled table."""
    section(title)
    keys = [field[1] for field in fields]
    show_table(
        [field[0] for field in fields],
        [[record.get(key, "") for key in keys] for record in records],
    )


def ask_text(prompt: str, *, required: bool = True, max_length: int | None = None) -> str:
    """Read text, retrying until the required constraints are met."""
    while True:
        value = input(prompt).strip()
        if required and not value:
            print("This field is required.")
            continue
        if max_length is not None and len(value) > max_length:
            print(f"Enter no more than {max_length} characters.")
            continue
        return value


@overload
def ask_int(
    prompt: str,
    *,
    minimum: int | None = None,
    allow_blank: Literal[False] = False,
) -> int: ...


@overload
def ask_int(
    prompt: str,
    *,
    minimum: int | None = None,
    allow_blank: Literal[True],
) -> int | None: ...


def ask_int(
    prompt: str,
    *,
    minimum: int | None = None,
    allow_blank: bool = False,
) -> int | None:
    """Read a whole number, validating its minimum."""
    while True:
        raw = input(prompt).strip()
        if allow_blank and not raw:
            return None
        try:
            value = int(raw)
        except ValueError:
            print("Enter a whole number.")
            continue
        if minimum is not None and value < minimum:
            print(f"Enter a value of at least {minimum}.")
            continue
        return value


@overload
def ask_number(
    prompt: str,
    *,
    minimum: Decimal | int | float = Decimal("0"),
    allow_blank: Literal[False] = False,
) -> float: ...


@overload
def ask_number(
    prompt: str,
    *,
    minimum: Decimal | int | float = Decimal("0"),
    allow_blank: Literal[True],
) -> float | None: ...


def ask_number(
    prompt: str,
    *,
    minimum: Decimal | int | float = Decimal("0"),
    allow_blank: bool = False,
) -> float | None:
    """Read a finite decimal value and validate its minimum."""
    while True:
        raw = input(prompt).strip()
        if allow_blank and not raw:
            return None
        try:
            value = Decimal(raw)
        except InvalidOperation:
            print("Enter a valid number.")
            continue
        if not value.is_finite() or value < Decimal(str(minimum)):
            print(f"Enter a value of at least {minimum}.")
            continue
        return float(value)


def ask_choice(prompt: str, choices: Sequence[str]) -> str:
    """Display allowed values and return the selected API enum value."""
    normalized = {choice.casefold(): choice for choice in choices}
    while True:
        print(" / ".join(choices))
        value = input(prompt).strip().casefold()
        if value in normalized:
            return normalized[value]
        print("Choose one of the listed values.")


def ask_yes_no(prompt: str, *, default: bool = False) -> bool:
    """Prompt for a yes/no confirmation."""
    suffix = "[Y/n]" if default else "[y/N]"
    value = input(f"{prompt} {suffix}: ").strip().casefold()
    if not value:
        return default
    return value in {"y", "yes"}


def _format_cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, dict):
        return ", ".join(f"{key}: {item}" for key, item in value.items())
    if isinstance(value, list):
        return "; ".join(_format_cell(item) for item in value)
    return str(value)
