# Capstone prep (Module 3.4)

What to have ready before the live run. The input in the room is unseen. This sheet is
everything else.

**Open before you start:**
- the page, https://bonnergaylord.github.io/ai-foundations/
- the API root, https://wake-parcel-api.bonner-e05.workers.dev
- the file `parcel-api/src/index.js`
- a terminal in `level-3/parcel-api/`

## Trace the path out loud

For an address typed into the page:

1. **The page** (`site/index.html`, `lookup()` at line 135) sends
   `GET /parcels?address=...` to the API.
2. **The Worker** (`parcel-api/src/index.js`) routes it at line 223 to `lookup()`, which
   calls `findByAddress()` (line 59).
3. **`findByAddress`** normalizes the typed address with `normalize()` (line 16): upper
   case, punctuation dropped, spaces collapsed, Road→RD. It then tries the strategies
   at line 53, in order:
   - **exact:** the stored address is the whole query, or the start of it.
   - **without directional:** if the second word was N, S, E or W, drop it and try again.
   - **street type assumed:** `977 Hillsborough` matches `977 HILLSBOROUGH ST` when
     only one parcel does.

   Before any of that, a 10-digit input is treated as a PIN, and a leading unit
   ("Unit 4,", "#4") is stripped (line 67).
4. **Each strategy is one parameterized `SELECT`** against the D1 `parcels` table, on
   the `address_key` column that `load.py` filled when the data was loaded.
5. **The Worker returns JSON:**
   - `found` comes with the record and `match`, which says what was assumed.
   - `not_found` comes with up to three `suggestions_not_matches` (`nearMisses()`,
     line 98).
   - `ambiguous` comes with the candidates.
6. **The page renders the record.** Blank fields read "blank in the county file".
   Owner reads "not in this dataset".

For a question asked to Claude, steps 2 to 5 are the same:

1. Claude reads the tool descriptions in `parcel-connector/server.py`, picks
   `lookup_parcel`, and emits a call with the address.
2. My connector (`call_api()`, line 119) makes the same HTTP request.
3. Claude receives the JSON and writes its answer from that record. It never touches
   the database.

## What I tested before the room (2026-10-05)

| Input | Before prep | After |
| --- | --- | --- |
| `977 Hillsborough` (no street type) | not found | found; match: street type assumed |
| `Unit 4, 977 Hillsborough St`, `#4 977 Hillsborough St` | not found | found; match: exact, unit ignored |
| `977 W Hillsborough St` | not found | found; match: without directional |
| `0743949082` (a PIN in the address box) | not found | found; match: PIN |
| `977 Hillsboro St` (typo), `978 Hillsborough St` | not found, no help | not found, suggests `977 Hillsborough St` |
| Sales in a date range | no endpoint | `/parcels/sales?from=&to=`; the connector has `find_sales_in_date_range` |
| `977 Hillsborough St., Raleigh, NC`, `977 Hillsborough St Apt 4` | found | found |
| `9696 BUCK JONES RD` (blank year built and sale) | found, blanks shown | same |
| `101 W Main St, Durham NC` | not found | not found; says the sample is Wake County only |

`test_e2e.py` now holds all of these: 23 checks, all passing live.

## What it does not handle (the answer to "what are your limits?")

- **Owner names.** The dataset has none. The tool says so, and never guesses one.
- **Any county but Wake, and any Wake parcel outside the 250-record sample.** It is a
  sample, not the county database.
- **Spelled-out numbers** ("nine seventy-seven") are refused as "give a house number".
  Street aliases such as "US 1" for "Capital Blvd" are not found. "Saint" for "St" is not
  found either, though the suggestion offers the right address.
- **Anything after the street is ignored, silently.** That is how a trailing city, ZIP
  or unit works. But "977 Hillsborough St W" also comes back as an `exact` match with the
  W dropped and not flagged. In a real county, where a West and an East version of a
  street can both exist, that would return the wrong parcel. The fix is to flag
  trailing words that aren't a city, state, ZIP or unit.
- **Sale history.** Only each parcel's most recent sale is stored. A date-range search
  misses any earlier sale of a parcel that sold again later.
- **Units.** The sample has one record per address, so a unit is ignored, not looked up.
- **Fuzzy matching is suggestion-only.** A typo never returns a record as if it were an
  answer.
- **Freshness.** The data is a fixed snapshot. Nothing refreshes it.

## If it breaks in the room

1. **Read what came back, first.** `not_found` means the code ran and the matcher missed.
   A `500` or "didn't respond" means the code or the database failed.
2. **For a miss, look at `searched_for`** in the raw API response (open
   `/parcels?address=...` in a tab). It shows the normalized text that was compared.
   Compare it to how the county spells that street:
   `wrangler d1 execute wake-parcels --remote --command="SELECT site_address FROM parcels WHERE address_key LIKE '%HILLSBOROUGH%'"`.
   The fix almost always belongs in `normalize()` (line 16) or `STRATEGIES` (line 53),
   with the same change in `load.py` line 21 if it alters stored keys.
3. **If every endpoint fails at once,** it is the database, not the matcher. This happened
   in prep. The local database was empty because its ID changed. The fix was to reload
   it with `schema.sql` and `seed.sql`.
4. **If Claude gives a wrong answer but the API is right,** the problem is the tool
   description in `server.py`, because that is all the model chooses from.

## Account for the submission form (fill in after the presentation)

> Input I was given: ________. What happened: ________ (what the tool returned, and
> whether it was right). What broke, and how I diagnosed it: ________. What I changed:
> ________ (file and line), or "nothing broke; I checked ________."
>
> Before the room I ran unseen-style inputs and found five that failed: no street type,
> a unit before the number, a directional, a PIN in the address box, and any
> date-range question. I fixed those, added "did you mean" suggestions, and added a
> sales-by-date endpoint. All 23 end-to-end checks pass on the live API.
