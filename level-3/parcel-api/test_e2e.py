"""End-to-end check of the parcel API against the source CSV.

    python test_e2e.py https://wake-parcel-api.<account>.workers.dev path/to/parcel-sample-wake.csv

Every record in the CSV is fetched back through the live endpoints and compared field
by field. Prints one line per check and a final count; exits 1 if anything failed.
"""

import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE, CSV_PATH = sys.argv[1].rstrip("/"), sys.argv[2]
failures = []


def get(path, **params):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"user-agent": "parcel-e2e/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (f"   [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def num(v, kind):
    return kind(v) if v.strip() else None


rows = list(csv.DictReader(open(CSV_PATH, newline="", encoding="utf-8-sig")))

status, body = get("/")
check("root loads as a page", status == 200 and "<h1>" in body, f"status {status}")

# Every record, looked up by its own address exactly as the county file spells it.
mismatches = []
for r in rows:
    status, body = get("/parcels", address=r["site_address"])
    rec = json.loads(body).get("record", {}) if status == 200 else {}
    expected = {
        "pin": r["pin"], "zip": r["zip"], "zoning": r["zoning"], "land_use": r["land_use"],
        "acreage": float(r["acreage"]), "heated_sqft": num(r["heated_sqft"], int),
        "year_built": num(r["year_built"], int), "assessed_value": int(r["assessed_value"]),
        "last_sale_date": r["last_sale_date"] or None,
        "last_sale_price": num(r["last_sale_price"], int), "tax_district": r["tax_district"],
    }
    bad = [k for k, v in expected.items() if rec.get(k) != v]
    if status != 200 or bad:
        mismatches.append(f"{r['pin']} {status} {bad}")
check(f"all {len(rows)} records found by address, every field matching the CSV",
      not mismatches, "; ".join(mismatches[:5]))

# Typed variations of addresses that are in the file, and one that is not.
for typed, pin in [
    ("977 HILLSBOROUGH STREET, Raleigh NC 27606", "0743949082"),
    ("9696 Buck Jones Road", "0763551410"),
    ("  9696   buck jones rd.  ", "0763551410"),
]:
    status, body = get("/parcels", address=typed)
    got = json.loads(body).get("record", {}).get("pin")
    check(f"typed '{typed.strip()}' finds PIN {pin}", status == 200 and got == pin, f"{status} {got}")
status, body = get("/parcels", address="1400 Cedar Ridge Road")
check("1400 Cedar Ridge Road is not found (404)", status == 404, f"status {status}")

# Every parcel over an acre: same set as the CSV, largest first, none at exactly 1.0.
status, body = get("/parcels/over-acreage", min="1")
data = json.loads(body)
want = {r["pin"] for r in rows if float(r["acreage"]) > 1.0}
got = [p["pin"] for p in data.get("parcels", [])]
acres = [p["acreage"] for p in data.get("parcels", [])]
check(f"over-acreage returns the {len(want)} parcels over 1 acre", set(got) == want and len(got) == len(want),
      f"got {len(got)}")
check("over-acreage is sorted largest first", acres == sorted(acres, reverse=True))

# Last sale for every parcel, by PIN.
bad = []
for r in rows:
    status, body = get("/parcels/last-sale", pin=r["pin"])
    sale = json.loads(body).get("last_sale")
    want_sale = ({"date": r["last_sale_date"], "price": int(r["last_sale_price"])}
                 if r["last_sale_date"] else None)
    if status != 200 or sale != want_sale:
        bad.append(f"{r['pin']} {status} {sale}")
check(f"last sale matches the CSV for all {len(rows)} PINs (null for the blank ones)", not bad,
      "; ".join(bad[:5]))

# Bad input gets a clear error, not a crash.
check("min=abc is refused with 400", get("/parcels/over-acreage", min="abc")[0] == 400)
check("missing address is refused with 400", get("/parcels")[0] == 400)
check("unknown PIN gives 404", get("/parcels/last-sale", pin="0000000000")[0] == 404)
check("unknown path gives 404", get("/nope")[0] == 404)

print(f"\n{BASE}: {len(failures)} failed")
sys.exit(1 if failures else 0)
