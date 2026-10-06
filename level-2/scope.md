# Scope: rent roll count

Written 2026-10-05, before any code exists. The test files and the test script
(`rent-roll-count/fixtures/`, `rent-roll-count/run_tests.sh`) are committed with this
page, so the history shows the definition of done came first.

## What it does

`rent-roll-count/rent_roll_count.py` is a script. You give it the path to one rent roll
CSV laid out like the Cedar Ridge file from Module 1.3:
- a few header rows, then a table whose header row starts with `Unit`, with the columns
  Unit, Beds, Status, Lease start, Lease end and Monthly rent;
- below the table, a row reading `Notes from the broker`, followed by one note per row.

It prints exactly these lines, and nothing else:

```
Units: <count of unit rows>
Occupied: <count with status Occupied>
Vacant: <count with status Vacant>
Monthly rent, all units: <sum of the Monthly rent column>
Annual gross potential rent: <that sum x 12>
Broker notes: <count of notes>
- <each note, word for word, without the trailing empty columns>
```

Rents written as `1450`, `1,450` or `$1,450` are all read as 1450.

It refuses bad input rather than guessing. In each of these cases it prints one line to
the error output starting with `Error:`, prints nothing to the normal output, and exits
with code 1:
- A unit number appears twice. The error names the unit.
- A unit has a blank monthly rent. The error names the unit.
- A unit's status is anything other than Occupied or Vacant. The error names the unit.
- The file does not exist.

## What it does not do

- It does not calculate vacancy loss, concessions or NOI, and it does not take a cap
  rate. That is the `in-place-noi` Skill's job (`level-1/in-place-noi/`).
- It does not interpret the broker notes. It counts and prints them, nothing more.
- It does not read `.xlsx` files, more than one file at a time, or any column layout
  other than the one above.
- It does not round, format or add currency symbols to its output numbers.

## How I will know it works

`bash rent-roll-count/run_tests.sh` runs seven tests. Each one prints PASS or FAIL with
no judgment call. **It is finished when all seven pass.**

| Test | Input | Pass means |
| --- | --- | --- |
| T1 | `cedar-ridge.csv` | Output is byte-for-byte `fixtures/expected-cedar-ridge.txt` (12 units, 11 occupied, 1 vacant, 17350, 208200, 4 notes), and the exit code is 0. I worked those figures by hand in Module 1.3. |
| T2 | `cedar-ridge-shuffled.csv` (the same 12 rows in random order) | Output is identical to T1's. |
| T3 | `dollar-format.csv` (every rent written as `"$1,450"`) | Output is identical to T1's. |
| T4 | `duplicate-unit.csv` (unit 105 twice) | Exit code 1, a one-line `Error:` naming 105, nothing on the normal output, no traceback. |
| T5 | `blank-rent.csv` (unit 107 has no rent) | Same as T4, naming 107. |
| T6 | `odd-status.csv` (unit 104 has the status `Notice`) | Same as T4, naming 104. |
| T7 | A path that does not exist | Exit code 1, a one-line `Error:`, no traceback. |

The coding agent builds it from this page. I run the script as written and record what
comes back in `test-report.md`, including anything that fails.
