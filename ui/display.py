"""Terminal layout for the Kakina CLI. Uses only standard Python."""
import os
import shutil
import sys
import textwrap


def clear_screen():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def screen_width():
    return shutil.get_terminal_size((90, 24)).columns


def divider():
    print("  " + "-" * max(20, screen_width() - 4))


def border(title, rows=None, symbol="-"):
    """Print a heading and optional rows without enclosing borders."""
    width = max(20, min(screen_width() - 4, 100))
    print("  " + str(title).upper())
    print("  " + symbol * width)
    if rows:
        for row in rows:
            for line in textwrap.wrap(str(row), width) or [""]:
                print("  " + line)
    print()


def heading(title, subtitle=""):
    clear_screen()
    border(title, [subtitle] if subtitle else None, "=")


def main_menu(title, dashboard, groups):
    """Render the header, dashboard, and menu as separate text sections."""
    clear_screen()
    width = max(20, min(screen_width() - 4, 100))
    separator = "  " + "-" * width

    def lines(text):
        return textwrap.wrap(str(text), width) or [""]

    print("  " + "=" * width)
    for line in lines(title.upper()):
        print(line.center(width + 2))
    print("  " + "=" * width)
    print()

    print("  DASHBOARD")
    print(separator)
    for line in lines(dashboard):
        print("  " + line)
    print()

    print("  MENU OPTIONS")
    print(separator)
    for group, options in groups:
        print()
        print("  " + group)
        for option in options:
            for line in lines(option):
                print("    " + line)
    print()


def section(title, description=""):
    border(title, [description] if description else None)


def step(number, title, description="", new_page=False, context=""):
    if new_page:
        clear_screen()
        if context:
            border(context, symbol="=")
    section(f"STEP {number} - {title}", description)


def message(label, text):
    print(f"  [{label}] {text}")


def notice(text):
    message("INFO", text)


def success(text):
    message("SAVED", text)


def warn(text):
    message("NOTICE", text)


def error(text):
    message("ERROR", text)


def qty_text(value):
    return f"{float(value):g}"


def pesos(value):
    amount = float(value)
    return f"-₱{abs(amount):,.2f}" if amount < 0 else f"₱{amount:,.2f}"


def wrap_name(text, width):
    """Split long names into lines that fit a table column."""
    words = str(text).split()
    lines = []
    line = ""
    for word in words:
        while len(word) > width:
            if line:
                lines.append(line)
                line = ""
            lines.append(word[:width])
            word = word[width:]
        if not word:
            continue
        if not line:
            line = word
        elif len(line) + len(word) + 1 <= width:
            line += " " + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines or [""]


def shorten(text, width):
    text = str(text)
    if len(text) <= width:
        return text
    return text[:max(0, width - 3)] + "..." if width >= 4 else text[:width]


def show_table(headers, rows, title=""):
    """Show aligned data columns without vertical or enclosing borders."""
    headers = [str(name) for name in headers]
    rows = [[str(value) for value in row] for row in rows]
    if title:
        print("  " + title.upper())
    if not rows:
        print("  No records found.\n")
        return

    count = len(headers)
    room = max(10, screen_width() - 4 - 2 * (count - 1))
    name_columns = {i for i, header in enumerate(headers)
                    if any(word in header.lower() for word in ("product", "ingredient", "customer", "location", "name"))}
    widths = []
    minimum = []
    for index, header in enumerate(headers):
        lengths = [len(header)] + [len(row[index]) for row in rows]
        widths.append(min(38 if index in name_columns else 25, max(lengths)))
        minimum.append(min(12 if index in name_columns else 8, max(4, len(header))))

    while sum(widths) > room:
        candidates = [i for i in range(count) if widths[i] > minimum[i]]
        if not candidates:
            break
        largest = max(candidates, key=lambda i: widths[i] - minimum[i])
        widths[largest] -= 1

    if sum(widths) > room:
        for row in rows:
            lines = []
            for header, value in zip(headers, row):
                label = header + ": "
                if any(word in header.lower() for word in
                       ("product", "ingredient", "customer", "location", "name")):
                    pieces = wrap_name(value, max(1, screen_width() - 4 - len(label)))
                    lines.append(label + pieces[0])
                    lines.extend(" " * len(label) + part for part in pieces[1:])
                else:
                    lines.append(label + value)
            border("RECORD", lines)
        return

    separator = "  " + "  ".join("-" * width for width in widths)
    print("  " + "  ".join(shorten(header, width).ljust(width)
                           for header, width in zip(headers, widths)))
    print(separator)

    for row in rows:
        cells = []
        for index, value in enumerate(row):
            if index in name_columns:
                cells.append(wrap_name(value, widths[index]))
            else:
                cells.append([shorten(value, widths[index])])
        for number in range(max(len(cell) for cell in cells)):
            values = [cell[number] if number < len(cell) else "" for cell in cells]
            print("  " + "  ".join(value.ljust(width)
                                    for value, width in zip(values, widths)))
    print()


def show_summary(title, rows):
    """Display a transaction review without enclosing borders."""
    width = max(20, min(screen_width() - 4, 100))
    print("  " + title.upper())
    print("  " + "-" * width)
    for label, value in rows:
        label = str(label)
        value = str(value)
        prefix = label + ": "
        if any(word in label.lower() for word in ("product", "ingredient", "customer", "name")):
            pieces = wrap_name(value, max(1, width - len(prefix)))
            for index, piece in enumerate(pieces):
                text = (prefix if index == 0 else " " * len(prefix)) + piece
                print("  " + text)
        else:
            print("  " + shorten(prefix + value, width))
    print()
