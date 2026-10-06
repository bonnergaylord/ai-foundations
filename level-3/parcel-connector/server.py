"""Parcel connector: a minimal MCP server over the Wake County parcel API.

Speaks the Model Context Protocol (JSON-RPC 2.0, one message per line on stdin/stdout)
with the standard library only. Module 3.1 read the CSV on this laptop; since Module 3.2
every tool calls the parcel API, which queries the hosted D1 database. Usage:

    PARCEL_API_URL=https://wake-parcel-api.<account>.workers.dev python server.py
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("PARCEL_API_URL", "http://127.0.0.1:8787").rstrip("/")
PROTOCOL_VERSION = "2025-06-18"

NO_OWNER = (
    "The dataset has NO owner names. If asked who owns a property, report what the "
    "record does contain and say plainly that ownership is not in the data. Never "
    "supply an owner name."
)
NULLS = (
    "Fields that are blank in the county file come back as null. Say the record leaves "
    "them blank; do not estimate them or explain why they are blank."
)

TOOLS = [
    {
        "name": "lookup_parcel",
        "description": (
            "Look up one property in the Wake County parcel sample (250 records) by its "
            "street address and return that parcel's full record: PIN, zoning, land use, "
            "acreage, heated square feet, year built, assessed value, last sale and tax "
            "district. Use this whenever someone asks about a specific address. If the "
            "address is not found, say so and do not describe a parcel the tool did not "
            "return; suggestions_not_matches are other real addresses you may offer as "
            "'did you mean', never as the answer. When a record is found, its 'match' "
            "field says what was assumed (e.g. 'street type assumed', 'without "
            "directional', 'unit ignored'); tell the person. " + NO_OWNER + " " + NULLS
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": (
                        "House number and street, e.g. '977 Hillsborough Street'. A "
                        "trailing city, state or ZIP is ignored. Case, extra spaces and "
                        "Road/Rd-style spelling do not matter."
                    ),
                }
            },
            "required": ["address"],
        },
        "path": "/parcels",
    },
    {
        "name": "find_parcels_over_acreage",
        "description": (
            "List every parcel in the Wake County sample larger than a given number of "
            "acres, largest first, with PIN, address, city, land use, zoning, acreage and "
            "assessed value. Use for questions like 'which parcels are over an acre' or "
            "'the biggest lots'. The count in the result is the complete answer for this "
            "250-record sample, not for the whole county. " + NO_OWNER
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "min_acres": {
                    "type": "number",
                    "description": "Return parcels strictly larger than this. Defaults to 1.",
                }
            },
        },
        "path": "/parcels/over-acreage",
    },
    {
        "name": "get_last_sale",
        "description": (
            "Return the most recent sale date and price for one parcel, given its PIN or "
            "its street address. Use when someone asks when a property last sold or what "
            "it sold for. A null last_sale means the county file has no sale for that "
            "parcel; say so and do not guess a date or price."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pin": {"type": "string", "description": "The 10-digit parcel PIN, e.g. '0743949082'."},
                "address": {"type": "string", "description": "Street address, if there is no PIN."},
            },
        },
        "path": "/parcels/last-sale",
    },
    {
        "name": "find_sales_in_date_range",
        "description": (
            "List every parcel in the Wake County sample whose most recent sale falls "
            "between two dates, oldest first, with sale date and price. Use for questions "
            "like 'what sold in 2020' or 'sales between March and June 2023'. Only each "
            "parcel's latest sale is in the data, so an earlier sale of a parcel that sold "
            "again later will not appear; say so when it matters. " + NO_OWNER
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_date": {"type": "string", "description": "Start date, YYYY-MM-DD, inclusive."},
                "to_date": {"type": "string", "description": "End date, YYYY-MM-DD, inclusive."},
            },
            "required": ["from_date", "to_date"],
        },
        "path": "/parcels/sales",
    },
]


def call_api(tool, args):
    if tool["name"] == "lookup_parcel":
        params = {"address": args.get("address", "")}
    elif tool["name"] == "find_parcels_over_acreage":
        params = {"min": args.get("min_acres", 1)}
    elif tool["name"] == "find_sales_in_date_range":
        params = {"from": args.get("from_date", ""), "to": args.get("to_date", "")}
    else:
        params = {k: args[k] for k in ("pin", "address") if args.get(k)}
    url = API + tool["path"] + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"user-agent": "wake-parcels-mcp/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode(), False
    except urllib.error.HTTPError as e:  # 404 not found and 300 ambiguous carry useful JSON
        return e.read().decode(), e.code >= 500
    except (urllib.error.URLError, TimeoutError) as e:
        return json.dumps({"status": "error", "message": f"The parcel API could not be reached ({e})."}), True


def reply(msg_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": msg_id}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    by_name = {t["name"]: t for t in TOOLS}
    for line in sys.stdin:
        if not line.strip():
            continue
        msg = json.loads(line)
        method, msg_id = msg.get("method"), msg.get("id")
        if msg_id is None:  # a notification, such as notifications/initialized
            continue
        if method == "initialize":
            reply(msg_id, {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL_VERSION),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "wake-parcels", "version": "0.3.0"},
            })
        elif method == "tools/list":
            reply(msg_id, {"tools": [{k: v for k, v in t.items() if k != "path"} for t in TOOLS]})
        elif method == "tools/call":
            params = msg.get("params", {})
            tool = by_name.get(params.get("name"))
            if not tool:
                reply(msg_id, error={"code": -32602, "message": "Unknown tool"})
                continue
            text, failed = call_api(tool, params.get("arguments", {}))
            reply(msg_id, {"content": [{"type": "text", "text": text}], "isError": failed})
        elif method == "ping":
            reply(msg_id, {})
        else:
            reply(msg_id, error={"code": -32601, "message": f"Unknown method {method}"})


if __name__ == "__main__":
    main()
