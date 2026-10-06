# Parcel connector (Module 3.1)

An MCP server for the Wake County parcel sample, in standard library Python only.

In Module 3.1 it read the CSV on this laptop. Since Module 3.2 it calls the hosted parcel
API (`../parcel-api/`), so it works without the file. It has three tools:
`lookup_parcel(address)`, `find_parcels_over_acreage(min_acres)` and
`get_last_sale(pin or address)`.

Connect it to Claude Code:

    claude mcp add wake-parcels -e PARCEL_API_URL=https://wake-parcel-api.bonner-e05.workers.dev -- python /full/path/to/server.py

Then ask, for example, "What's the acreage on 977 Hillsborough Street?"

What it handles: address casing, doubled spaces, and spelled-out street types; a city,
state or ZIP on the end of the address; blank fields (returned as null, never 0); PINs
kept as text. The dataset has no owner column. The tool says so and returns
`"owner": null`, so the assistant has no gap to fill with an invented name.
