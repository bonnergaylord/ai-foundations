# Test report: rent roll count

Tested 2026-10-05 against `level-2/scope.md`, which was committed in `391e104` before the
script existed. The coding agent built `rent-roll-count/rent_roll_count.py` from the
scope page. It did not run the tests, and it did not edit the scope, the test files or
the test script.

## The scope's test, run as written

`bash level-2/rent-roll-count/run_tests.sh`

```
PASS  T1 Cedar Ridge matches expected output
PASS  T2 shuffled rows give identical output
PASS  T3 $1,450-style rents give identical output
PASS  T4 duplicate unit 105 is refused
      exit=1 stderr: Error: unit 105 appears more than once
PASS  T5 blank rent on unit 107 is refused
      exit=1 stderr: Error: unit 107 has a blank monthly rent
PASS  T6 status 'Notice' on unit 104 is refused
      exit=1 stderr: Error: unit 104 has status 'Notice'; only Occupied or Vacant is accepted
PASS  T7 missing file gives a one-line error
      exit=1 stderr: Error: file not found: fixtures/no-such-file.csv

7 passed, 0 failed
```

**By the definition I wrote, it is finished.** All seven pass on the first run, with no
changes to the script.

## What did not work

Seven passes means the seven cases I thought of beforehand work. When the agent handed
over the script, it listed the places where it had to choose behavior the scope didn't
settle. I tested those too. The files are in `fixtures/probes/`.

### 1. A blank row inside the unit table gives a confident wrong answer (FAIL)

`probes/mid-blank.csv` is Cedar Ridge with one empty row inserted after unit 106. The
script prints this and exits 0:

```
Units: 6
Occupied: 6
Vacant: 0
Monthly rent, all units: 8700
Annual gross potential rent: 104400
```

The right answer is 12 units and 208,200. **The script treats the blank row as the end of
the table, silently drops units 107 to 112, and reports half the building with a success
exit code.** The vacant unit disappears, so "Vacant: 0" is wrong too. It is the same
failure I watched a model make in Module 1.3: a figure delivered with confidence and
nothing to tell you it's wrong.

Hand-kept rent rolls get blank rows, so this is a realistic input, not a contrived one.
The agent warned about it in its handoff note, and my seven tests did not cover it. The
fix belongs in both places:
- **Script:** after the first blank row, keep looking for unit rows up to the notes row,
  and refuse if any turn up.
- **Scope:** a T8 with this file, required to fail with an `Error:` naming the problem.

### 2. My scope left a case undefined, and the agent filled it in (scope defect)

`probes/no-notes.csv` has no broker notes section. The script refuses it:
`Error: no 'Notes from the broker' row was found below the table`.

The scope never says whether a rent roll without notes should be refused or should print
`Broker notes: 0`. The agent picked "refuse". I think it should print zero, because many
rent rolls carry no notes. Either way, the decision was mine to make in the scope, and I
left it to the builder. That is the Module 1.4 kind of defect, an unowned decision, in my
own page.

### 3. My test is weaker than my scope says (test defect)

The scope says T1 passes when the output is "byte-for-byte" the expected file. The test
script compares the output after the shell has stripped trailing newlines, so it would
not catch a missing or extra final newline. I checked bytes directly with
`python rent_roll_count.py fixtures/cedar-ridge.csv | cmp - fixtures/expected-cedar-ridge.txt`,
and it is identical. That means T1 is right this time, but the test doesn't prove what
the scope claims it proves. Next version: compare with `cmp`.

### Probes that behaved acceptably

- **`probes/lower-status.csv`** (`occupied` in lowercase) is refused, naming unit 101.
  That's strict, but it's within the scope's wording, and refusing is safer than
  guessing.
- **`probes/crlf.csv`** (Windows line endings, as Excel saves them) gives the correct
  output.

## Summary

| | Result |
| --- | --- |
| The scope's seven tests | 7 pass |
| Blank row inside the table | **Fail.** Wrong totals with exit code 0. |
| No notes section | Refused. The scope never decided this case. |
| T1 "byte-for-byte" | The test doesn't check bytes. The output is byte-identical when checked directly. |

The script meets the definition I wrote, but the definition was incomplete. I would not
hand this to someone else until the blank-row case refuses instead of under-counting. The
seven passing tests are real, and so is the failure. Both belong in the report.
