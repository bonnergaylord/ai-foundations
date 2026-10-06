"""Count a rent roll CSV laid out like the Cedar Ridge file.

Usage: python rent_roll_count.py <rent-roll.csv>

Prints unit, occupancy, rent and broker-note counts. Refuses bad input with a
one-line "Error:" message on stderr and exit code 1. See level-2/scope.md.
"""

import csv
import sys
from decimal import Decimal, InvalidOperation

COLUMNS = ["Unit", "Beds", "Status", "Lease start", "Lease end", "Monthly rent"]
STATUSES = ("Occupied", "Vacant")
NOTES_MARKER = "Notes from the broker"


class InputError(Exception):
    pass


def is_blank(row):
    return all(not cell.strip() for cell in row)


def parse_rent(text, unit):
    cleaned = text.strip().replace("$", "").replace(",", "").strip()
    if not cleaned:
        raise InputError(f"unit {unit} has a blank monthly rent")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise InputError(
            f"unit {unit} has a monthly rent that is not a number: {text.strip()!r}"
        ) from None
    if not value.is_finite():
        raise InputError(
            f"unit {unit} has a monthly rent that is not a number: {text.strip()!r}"
        )
    return value


def read_rows(path):
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.reader(f))
    except FileNotFoundError:
        raise InputError(f"file not found: {path}") from None
    except IsADirectoryError:
        raise InputError(f"not a file: {path}") from None
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise InputError(f"could not read {path}: {exc}") from None


def analyse(rows):
    header_at = next(
        (i for i, r in enumerate(rows) if r and r[0].strip() == "Unit"), None
    )
    if header_at is None:
        raise InputError("no table header row starting with 'Unit' was found")
    header = [c.strip() for c in rows[header_at]]
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        raise InputError(f"table header is missing column(s): {', '.join(missing)}")
    col = {name: header.index(name) for name in COLUMNS}

    units = []
    i = header_at + 1
    while i < len(rows):
        row = rows[i]
        if is_blank(row) or (row and row[0].strip() == NOTES_MARKER):
            break
        units.append(row)
        i += 1

    notes_at = next(
        (j for j in range(i, len(rows)) if rows[j] and rows[j][0].strip() == NOTES_MARKER),
        None,
    )
    if notes_at is None:
        raise InputError(f"no '{NOTES_MARKER}' row was found below the table")

    seen = set()
    occupied = vacant = 0
    total = Decimal(0)
    for row in units:
        cells = row + [""] * (len(header) - len(row))
        unit = cells[col["Unit"]].strip()
        if not unit:
            raise InputError(f"a row in the unit table has no unit number: {row}")
        if unit in seen:
            raise InputError(f"unit {unit} appears more than once")
        seen.add(unit)
        status = cells[col["Status"]].strip()
        if status == "Occupied":
            occupied += 1
        elif status == "Vacant":
            vacant += 1
        else:
            raise InputError(
                f"unit {unit} has status {status!r}; only Occupied or Vacant is accepted"
            )
        total += parse_rent(cells[col["Monthly rent"]], unit)

    notes = []
    for row in rows[notes_at + 1 :]:
        cells = list(row)
        while cells and not cells[-1].strip():
            cells.pop()
        if cells:
            notes.append(",".join(cells))

    return len(units), occupied, vacant, total, notes


def fmt(value):
    # No rounding: whole numbers print without a decimal point, others as written.
    if value == value.to_integral_value():
        return str(value.quantize(Decimal(1)))
    return str(value.normalize())


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(newline="\n")
        except (AttributeError, ValueError):
            pass
    try:
        if len(argv) != 2:
            raise InputError("usage: python rent_roll_count.py <rent-roll.csv>")
        count, occupied, vacant, total, notes = analyse(read_rows(argv[1]))
    except InputError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    lines = [
        f"Units: {count}",
        f"Occupied: {occupied}",
        f"Vacant: {vacant}",
        f"Monthly rent, all units: {fmt(total)}",
        f"Annual gross potential rent: {fmt(total * 12)}",
        f"Broker notes: {len(notes)}",
    ]
    lines += [f"- {note}" for note in notes]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
