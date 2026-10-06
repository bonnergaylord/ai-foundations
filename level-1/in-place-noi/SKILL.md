---
name: in-place-noi
description: Use when handed a multifamily rent roll and an operating expense summary and asked for in-place NOI, the going-in cap rate, or "what does this building earn today at the asking price". Reads the files directly, including the notes below the rent roll table, and returns a line-by-line NOI worksheet with the cap rate.
---

# In-place NOI and going-in cap rate

You turn a rent roll and an operating expense summary into in-place NOI and the going-in cap rate at the asking price. Follow the steps in order. Do the arithmetic line by line and show it. Never return a single net-rent figure in place of the worksheet lines.

**In-place** means the leases as they stand on the rent roll date, not the rents the building might earn later.

## The job

| | |
|---|---|
| **Starts when** | Someone hands over a listing's rent roll and expense summary and asks for NOI or the cap rate. |
| **Required inputs** | 1. A rent roll with unit, status, lease start, lease end and monthly rent, plus everything written below the table. 2. An expense summary with annual other income and annual operating expenses. 3. The asking price, from the rent roll header or from the person asking. |
| **Produces** | A broker-note map, the 11-line worksheet, NOI, the cap rate, and a short list of flags for diligence. |
| **Works when** | Every worksheet line is shown, every broker note is assigned to a line, the totals tie out, and the result is the same however the rent roll rows are ordered. |

## Step 1: Read everything before calculating

1. Open each file and read **all** of it. Rent rolls carry notes below the last unit, and those notes change the arithmetic. If you stop at the last unit row, you will get a confident wrong answer.
2. Record the rent roll date and the asking price.
3. Build the unit list **keyed by unit number**. Do not rely on the order of the rows. Count the units, and check that no unit number appears twice.

## Step 2: Map the broker notes

Before any arithmetic, make a table with one row per note: the note, the unit(s) it names, and the worksheet line it changes. If a note changes nothing, write "explains only". Every note must appear in this table.

## Step 3: Rental income

| Line | Rule |
|---|---|
| 1. Gross potential rent | Sum the monthly rent of **every** unit, whatever its status, and multiply by 12. |
| 2. Less vacancy loss | For every unit whose status is vacant, its monthly rent × 12. |
| 3. Less non-revenue units | For every unit that is occupied but pays no rent, its monthly rent × 12. These units are usually identified only in the notes: a manager's or employee's unit given as compensation, a model unit, an office. The status column will say "Occupied". |
| 4. Less concessions (year one) | For every lease still in its first year on the rent roll date (lease start no more than 12 months before that date), deduct the free rent named in the notes. One month free = one month's rent. Deduct it **even if the free month fell before the rent roll date**, because the line measures what the lease's first year collects. |
| 5. Effective rental income | Line 1 − lines 2, 3 and 4. |

A unit belongs on **at most one** of lines 2 and 3. A vacant unit is never also non-revenue.

## Step 4: Other income and operating expenses

| Line | Rule |
|---|---|
| 6. Plus other income | The annual total from the expense summary. Add up the line items and confirm they equal the stated total. |
| 7. Effective gross income | Line 5 + line 6. |
| 8. Less operating expenses | The annual total from the expense summary, **including** replacement reserves. Add up the line items and confirm they equal the stated total. Do not add, remove or re-estimate any expense. |
| 9. In-place NOI | Line 7 − line 8. |
| 10. Asking price | As given. |
| 11. Going-in cap rate | Line 9 ÷ line 10, as a percentage to two decimals. |

## Step 5: Stop and ask, do not guess

If any of these is true, **do not produce NOI**. List the questions and stop.

- No asking price is given anywhere.
- A unit has no monthly rent, or its status is blank or anything other than occupied or vacant (for example notice, eviction or down unit).
- A note names a concession or a non-revenue arrangement without enough detail to price it (for example "reduced rent" with no amount, or free rent with no length).
- A note contradicts the table (for example a note calls a unit vacant that the table marks occupied).
- The other-income or expense line items do not add up to the stated total.
- The expense summary is not annual (a monthly or a partial-year figure), or its period is not stated.
- The number of units in the table disagrees with a unit count stated anywhere else.

## Step 6: Flag and proceed (written conventions, not guesses)

Apply these conventions, and list each case under **Flags** in the output.

- **Expired lease still marked occupied:** count it in place at its listed rent, as month-to-month. Flag the lease end date, because the tenant may be leaving.
- **Rent below the market rent stated in a note:** use the actual rent. List the gap as upside, not as in-place income.
- **Partial-year concession on a lease signed before the rent roll date:** deduct it under the line 4 rule, and also state what the unit collects over the next 12 months.

## Output format

1. **Answer first:** "In-place NOI is $X; going-in cap rate is Y% at the $Z asking price."
2. **Broker-note map** (from Step 2).
3. **Worksheet:** the 11 lines, numbered as above. Each line shows its amount and a short "how" (which units, rent × months).
4. **Self-check:** recompute line 5 from the paying units directly (rent × 12 for each unit that is neither vacant nor non-revenue, minus line 4) and confirm it equals line 5. Confirm that the units on lines 2 and 3 plus the paying units equal the total unit count.
5. **Flags** (from Step 6). Keep them to two lines each.

Round dollars to whole numbers. Show the cap rate to two decimals.
