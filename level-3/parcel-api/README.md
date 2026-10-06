# Wake County parcel API (Module 3.2)

The 250-record Wake County parcel sample is in a hosted Cloudflare D1 database, served by
a Cloudflare Worker at **https://wake-parcel-api.bonner-e05.workers.dev**.

| Endpoint | Query |
| --- | --- |
| `/parcels?address=977 Hillsborough St` | Look up one address |
| `/parcels/over-acreage?min=1` | Every parcel over an acre, largest first |
| `/parcels/last-sale?pin=0743949082` (or `?address=`) | Last sale for one parcel |

The Module 3.1 connector (`../parcel-connector/server.py`) now calls these endpoints
instead of reading the CSV. It has one tool per endpoint: `lookup_parcel`,
`find_parcels_over_acreage` and `get_last_sale`.

## Where the code runs

When my laptop is closed, a request to that address goes to Cloudflare. Cloudflare runs
the Worker (`src/index.js`) on whichever of its machines is nearest the person asking.
The Worker queries the D1 database, which Cloudflare also hosts and keeps running. My
laptop only matters when I change the code or reload the data.

## Decisions about the data

- **Types.**
  - `acreage` is `REAL`, so 0.241 stays 0.241.
  - `pin` and `zip` are `TEXT`, because they are labels with leading zeros, not
    quantities.
  - Dollar amounts, square feet and year built are `INTEGER`.
  - `last_sale_date` is `TEXT` with a check that it is `YYYY-MM-DD`.
  - CHECK constraints refuse a negative acreage, a 9-digit PIN, an impossible year, or
    a sale date without a price (and the reverse).
- **Blank fields** become `NULL`, never 0. Year built is blank on 43 rows, heated sq ft
  on 34, and last sale on 23. The API returns them as null and does not guess why
  they're blank.
- **Address matching.** People type `1400 CEDAR RIDGE ROAD`, but the county file says
  `9696  BUCK JONES RD`, with mixed case, doubled spaces and Rd/RD. Each address is
  stored twice: `site_address` exactly as the county spells it, and `address_key`
  normalized (upper case, punctuation removed, spaces collapsed, Road→RD and so on).
  A typed address matches when a stored key is the whole of it or the start of it, so a
  trailing city or ZIP doesn't block the match. No two keys may collide (`UNIQUE`). If a
  query ever matched two parcels, the API returns `ambiguous` with both rather than
  picking one.
- **City** is title-cased on load, because the source mixes `raleigh`, `Raleigh` and
  `RALEIGH`.
- **`tax_district`** is stored as given. It disagrees with `city` on 221 of 250 rows, and
  nothing in the data defines it, so the API passes it through without interpreting it.
- **Owner.** The sample has no owner column, so neither does the table. The API returns
  `owner: null` with a note saying so.

## Rebuild from scratch

    wrangler d1 create wake-parcels                  # put the id in wrangler.toml
    python load.py parcel-sample-wake.csv > seed.sql
    wrangler d1 execute wake-parcels --remote --file=schema.sql
    wrangler d1 execute wake-parcels --remote --file=seed.sql
    wrangler deploy

## Test

    python test_e2e.py https://wake-parcel-api.bonner-e05.workers.dev parcel-sample-wake.csv

This fetches all 250 records back through the live API and compares every field with the
CSV. It also checks the over-an-acre set and order, every last sale, typed-address
variants, a missing address, and bad input. Last run on 2026-10-05: 13 checks, 0
failed.

The first run, seconds after the first deploy, failed 2 checks: the root and the first
few lookups returned 404. The later checks in that same run passed, and a rerun a
minute later passed all 13. A new workers.dev address takes a short while to spread
across Cloudflare's network, so test a fresh deploy twice before you trust or blame it.
