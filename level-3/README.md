# Wake County parcel lookup

Type a street address and see that parcel's record, drawn from a 250-record Wake County
parcel sample in a hosted database. The same data can be reached three ways:

| Who | Where |
| --- | --- |
| A person, in a browser | **https://bonnergaylord.github.io/ai-foundations/** |
| Any program, over the API | **https://wake-parcel-api.bonner-e05.workers.dev** (the root lists the endpoints) |
| Claude, through the MCP connector | `parcel-connector/server.py`, with tools `lookup_parcel`, `find_parcels_over_acreage`, `get_last_sale` |

Built for the AI Foundations certificate, Level 3 (Modules 3.1 to 3.3).

## What is in this folder

```
level-3/
  site/index.html        the web page: an address box that calls the API (no build step)
  parcel-api/            the API: a Cloudflare Worker over a D1 database
    schema.sql             table definition, with types and checks
    load.py                CSV to seed.sql, refusing values that don't fit their column
    src/index.js           the three endpoints and the address matching
    test_e2e.py            checks all 250 records through the live API against the CSV
  parcel-connector/      the MCP server that lets Claude query the API
  commercial-use-note.md what would make this commercial rather than coursework
```

## How it is deployed

- **The page:** GitHub Pages. The workflow `.github/workflows/pages.yml` runs on every
  push to `main` that touches `level-3/site/`, uploads the folder and publishes it. There
  is no build step, so the files you see are the files served. Merging a pull request is
  how a change ships. PR #2 (clickable example addresses) went out this way.
- **The API and database:** Cloudflare Workers and D1, on my own Cloudflare account,
  free plan. They are deployed with `wrangler deploy` from `parcel-api/`, not from
  GitHub. That is a known gap; see "Not done" below.

## Run it on a laptop

You need Python 3, Node.js and the parcel CSV (not committed; it is course material).

```bash
cd level-3/parcel-api
npm install -g wrangler                     # once
python load.py path/to/parcel-sample-wake.csv > seed.sql
wrangler d1 execute wake-parcels --local --file=schema.sql
wrangler d1 execute wake-parcels --local --file=seed.sql
wrangler dev --local --port 8787            # API at http://127.0.0.1:8787
```

Check it end to end:

```bash
python test_e2e.py http://127.0.0.1:8787 path/to/parcel-sample-wake.csv
```

For the page, open `site/index.html` in a browser. It calls the live API by default. To
point it at your laptop, change the `API` constant near the bottom of the file to
`http://127.0.0.1:8787`.

To use the connector with Claude Code:

```bash
claude mcp add wake-parcels -e PARCEL_API_URL=http://127.0.0.1:8787 -- python /full/path/to/parcel-connector/server.py
```

## Credentials

The repository holds no secret, and none is needed at run time:
- The Worker reaches the database through a Cloudflare binding (`DB` in `wrangler.toml`),
  not a connection string.
- The `database_id` in `wrangler.toml` identifies the database but grants nothing without
  my Cloudflare login.
- That login (an OAuth token from `wrangler login`) lives in my user profile, outside the
  repository.
- The API is deliberately public and read-only. The page and the connector call it
  without a key.

If the API ever gains a write endpoint, or the data gains owner names, it needs a key.
That key would go in a Worker secret (`wrangler secret put`), never in a file.

## Not done

- **Automatic deploy for the API.** The API deploys from my laptop. Moving it into the
  workflow needs a scoped Cloudflare API token stored as a GitHub Actions secret.
- **Workflow warnings.** The deploy log warns that the pinned actions run on Node 20,
  which GitHub is retiring, and that `ubuntu-latest` moves to Ubuntu 26 from
  2026-10-19. Neither has broken a deploy yet; both need a version bump.
- **Owner names.** The sample has no owner column, so the page says "not in this
  dataset" instead of showing one.
