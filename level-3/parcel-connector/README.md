# Parcel connector (Module 3.1)

An MCP server with one tool, `lookup_parcel(address)`. It reads the Wake County parcel
sample CSV on this laptop and returns that parcel's record. Standard library Python only.

The dataset is not committed. Put `parcel-sample-wake.csv` in `data/`, or pass its path
as the first argument.

Connect it to Claude Code:

    claude mcp add wake-parcels -- python /full/path/to/server.py

Then ask, for example, "What's the acreage on 977 Hillsborough Street?"

What it handles: address casing, doubled spaces, and spelled-out street types; a city,
state or ZIP on the end of the address; blank fields (returned as null, never 0); PINs
kept as text. The dataset has no owner column. The tool says so and returns
`"owner": null`, so the assistant has no gap to fill with an invented name.
