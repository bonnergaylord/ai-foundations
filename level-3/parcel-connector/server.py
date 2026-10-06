"""Parcel lookup connector: a minimal MCP server over the Wake County parcel sample.

Speaks the Model Context Protocol (JSON-RPC 2.0, one message per line on stdin/stdout)
with the standard library only. It offers one tool, lookup_parcel, which reads the CSV
directly. Usage:

    python server.py [path/to/parcel-sample-wake.csv]
"""

import csv
import json
import re
import sys
from pathlib import Path

DEFAULT_CSV = Path(__file__).parent / "data" / "parcel-sample-wake.csv"
PROTOCOL_VERSION = "2025-06-18"

# Street-type words people type, mapped to the abbreviation the county file uses.
SUFFIXES = {
    "ROAD": "RD", "AVENUE": "AVE", "AV": "AVE", "STREET": "ST", "BOULEVARD": "BLVD",
    "BLV": "BLVD", "DRIVE": "DR", "LANE": "LN", "COURT": "CT", "PLACE": "PL",
    "PARKWAY": "PKWY", "HIGHWAY": "HWY", "CIRCLE": "CIR", "TRAIL": "TRL",
}

TOOL = {
    "name": "lookup_parcel",
    "description": (
        "Look up one property in the Wake County parcel sample (250 records) by its "
        "street address, and return that parcel's record exactly as the file has it. "
        "Use this whenever someone asks about a specific address: its acreage, zoning, "
        "land use, heated square feet, year built, assessed value, last sale date or "
        "price, PIN, or tax district. Do not use it to search, filter or rank many "
        "parcels; it finds one address at a time. "
        "The dataset has NO owner names. If asked who owns a property, call this tool, "
        "report what the record does contain, and say plainly that ownership is not in "
        "the data. Never supply an owner name. "
        "Fields that are blank in the record come back as null. Say the record leaves "
        "them blank; do not estimate them or explain why they are blank. If the "
        "address is not found, say so. Do not "
        "describe a parcel that the tool did not return."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": (
                    "The street address: house number and street name, e.g. "
                    "'977 Hillsborough Street'. City, state and ZIP may be included "
                    "and are ignored for matching. Case, extra spaces and spelled-out "
                    "street types (Road/Rd, Avenue/Ave) do not matter."
                ),
            }
        },
        "required": ["address"],
    },
}

FIELD_NOTES = {
    "owner": "Not in this dataset. The parcel sample carries no owner fields.",
    "tax_district": (
        "A code as the file gives it. It disagrees with the city column on 221 of 250 "
        "rows and the file does not define it, so do not say what it means."
    ),
    "nulls": (
        "A null field is blank in the source file. The file does not say why it is "
        "blank, so do not say whether a sale or a building exists."
    ),
    "city": "As recorded; casing in the source file is inconsistent.",
}


def normalize(address):
    """Upper-case, drop punctuation, collapse spaces, and abbreviate street types."""
    text = re.sub(r"[^A-Z0-9 ]", " ", address.upper())
    return [SUFFIXES.get(word, word) for word in text.split()]


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for i, row in enumerate(rows, start=2):  # row 1 is the header
        row["_line"] = i
        row["_key"] = normalize(row["site_address"])
    return rows


def as_record(row, source):
    def num(value, kind):
        value = value.strip()
        return kind(value) if value else None

    return {
        "pin": row["pin"],
        "site_address": row["site_address"],
        "city": row["city"],
        "zip": row["zip"],
        "zoning": row["zoning"] or None,
        "land_use": row["land_use"] or None,
        "acreage": num(row["acreage"], float),
        "heated_sqft": num(row["heated_sqft"], int),
        "year_built": num(row["year_built"], int),
        "assessed_value": num(row["assessed_value"], int),
        "last_sale_date": row["last_sale_date"].strip() or None,
        "last_sale_price": num(row["last_sale_price"], int),
        "tax_district": row["tax_district"] or None,
        "owner": None,
        "source": f"{source.name}, line {row['_line']}",
    }


def lookup(rows, address, source):
    query = normalize(address)
    if not query:
        return {"status": "error", "message": "No address was given."}
    # A record matches when its normalized address is the start of the query, so
    # trailing city, state or ZIP in the question do not block the match.
    hits = [r for r in rows if r["_key"] and query[: len(r["_key"])] == r["_key"]]
    if not hits:
        return {
            "status": "not_found",
            "searched_for": " ".join(query),
            "message": (
                f"No parcel at '{address}' in the {len(rows)}-record Wake County "
                "sample. Do not describe one."
            ),
        }
    if len(hits) > 1:
        return {
            "status": "ambiguous",
            "message": "More than one parcel matches; ask which one.",
            "candidates": [h["site_address"] + ", " + h["city"] for h in hits],
        }
    return {
        "status": "found",
        "record": as_record(hits[0], source),
        "field_notes": FIELD_NOTES,
    }


def reply(msg_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": msg_id}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    rows = load(source)
    for line in sys.stdin:
        if not line.strip():
            continue
        msg = json.loads(line)
        method, msg_id = msg.get("method"), msg.get("id")
        if msg_id is None:  # a notification, such as notifications/initialized
            continue
        if method == "initialize":
            reply(msg_id, {
                "protocolVersion": msg.get("params", {}).get(
                    "protocolVersion", PROTOCOL_VERSION),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "wake-parcels", "version": "0.1.0"},
            })
        elif method == "tools/list":
            reply(msg_id, {"tools": [TOOL]})
        elif method == "tools/call":
            params = msg.get("params", {})
            if params.get("name") != TOOL["name"]:
                reply(msg_id, error={"code": -32602, "message": "Unknown tool"})
                continue
            address = params.get("arguments", {}).get("address", "")
            result = lookup(rows, address, source)
            reply(msg_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=1)}],
                "isError": result["status"] == "error",
            })
        elif method == "ping":
            reply(msg_id, {})
        else:
            reply(msg_id, error={"code": -32601, "message": f"Unknown method {method}"})


if __name__ == "__main__":
    main()
