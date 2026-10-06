// Wake County parcel API: a Cloudflare Worker over a D1 database.
//
//   GET /                                   what this is, with example links
//   GET /parcels?address=977 Hillsborough St   one parcel by street address
//   GET /parcels/over-acreage?min=1         every parcel larger than min acres, largest first
//   GET /parcels/last-sale?pin=0743949082   last sale for one parcel (or ?address=...)
//   GET /parcels/sales?from=2020-01-01&to=2020-12-31   parcels whose last sale falls in the range

// Must match normalize() in load.py, or typed addresses stop matching stored ones.
const SUFFIXES = {
  ROAD: "RD", AVENUE: "AVE", AV: "AVE", STREET: "ST", BOULEVARD: "BLVD",
  BLV: "BLVD", DRIVE: "DR", LANE: "LN", COURT: "CT", PLACE: "PL",
  PARKWAY: "PKWY", HIGHWAY: "HWY", CIRCLE: "CIR", TRAIL: "TRL",
};

function normalize(address) {
  return address
    .toUpperCase()
    .replace(/[^A-Z0-9 ]/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => SUFFIXES[w] ?? w)
    .join(" ");
}

const RECORD_COLUMNS = `pin, site_address, city, zip, zoning, land_use, acreage,
  heated_sqft, year_built, assessed_value, last_sale_date, last_sale_price, tax_district`;

const NOTES = {
  owner: "Not in this dataset. The parcel sample carries no owner fields.",
  nulls: "A null field is blank in the county file. The file does not say why.",
  tax_district: "Stored as the file gives it. It disagrees with city on 221 of 250 rows; its meaning is not defined.",
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": "*",
    },
  });
}

const DIRECTIONALS = new Set(["N", "S", "E", "W", "NE", "NW", "SE", "SW", "NORTH", "SOUTH", "EAST", "WEST"]);

// Each strategy is tried in order; the first that finds rows wins, and its label is
// returned as "match" so the person (or the model) can see what was assumed.
//   1. exact: the stored address is the whole query, or the start of it, so a trailing
//      city, state, ZIP or unit ("977 Hillsborough St Apt 4, Raleigh") still matches.
//   2. without directional: the county file has none, so "977 W Hillsborough St" drops the W.
//   3. street type assumed: "977 Hillsborough" matches "977 HILLSBOROUGH ST" if only one does.
const STRATEGIES = [
  { label: "exact", sql: "?1 = address_key OR ?1 LIKE address_key || ' %'" },
  { label: "without directional", sql: "?1 = address_key OR ?1 LIKE address_key || ' %'", drop: true },
  { label: "street type assumed", sql: "address_key LIKE ?1 || ' %'" },
];

async function findByAddress(db, address) {
  const typed = address.trim();
  if (/^\d{10}$/.test(typed)) {
    const row = await db.prepare(`SELECT ${RECORD_COLUMNS} FROM parcels WHERE pin = ?1`).bind(typed).first();
    if (row) return { status: "found", match: "PIN", record: { ...row, owner: null }, notes: NOTES };
  }
  // A leading unit ("Unit 4, ...", "#4 ...", "Apt B ...") would otherwise be read as the
  // house number. Units after the street need no handling: the prefix match ignores them.
  const unitless = typed.replace(/^(unit|apt|apartment|suite|ste|#)\s*[\w-]+\s*,?\s*/i, "");
  const key = normalize(unitless);
  if (!/^\d+ [A-Z]/.test(key)) {
    return { status: "error", message: "Give a house number and street, e.g. 977 Hillsborough St" };
  }
  const words = key.split(" ");
  const noDirectional = DIRECTIONALS.has(words[1]) ? [words[0], ...words.slice(2)].join(" ") : null;

  for (const s of STRATEGIES) {
    const k = s.drop ? noDirectional : key;
    if (!k) continue;
    const { results } = await db.prepare(`SELECT ${RECORD_COLUMNS} FROM parcels WHERE ${s.sql}`).bind(k).all();
    if (results.length > 1) {
      return { status: "ambiguous", match: s.label, candidates: results.map((r) => `${r.site_address}, ${r.city} (PIN ${r.pin})`) };
    }
    if (results.length === 1) {
      const match = s.label + (unitless !== typed ? ", unit ignored" : "");
      return { status: "found", match, record: { ...results[0], owner: null }, notes: NOTES };
    }
  }
  return {
    status: "not_found",
    searched_for: key,
    message: `No parcel at '${address}' in the 250-record Wake County sample. The sample covers Wake County only.`,
    suggestions_not_matches: await nearMisses(db, words),
  };
}

// Up to three real addresses close to a miss: the same street with the nearest house
// numbers, or the same house number on a similarly spelled street. These are offered
// as suggestions only, never as the answer.
async function nearMisses(db, words) {
  const [num, ...street] = words;
  const { results } = await db.prepare("SELECT site_address, city, address_key FROM parcels").all();
  const target = street.join(" ");
  const scored = results.map((r) => {
    const [n, ...s] = r.address_key.split(" ");
    const streetDist = editDistance(s.join(" "), target);
    const numDist = Math.abs(Number(n) - Number(num));
    const score = streetDist === 0 ? numDist / 1000 : n === num && streetDist <= 4 ? streetDist : Infinity;
    return { r, score };
  });
  return scored
    .filter((x) => x.score < Infinity)
    .sort((a, b) => a.score - b.score)
    .slice(0, 3)
    .map((x) => `${x.r.site_address.replace(/\s+/g, " ")}, ${x.r.city}`);
}

function editDistance(a, b) {
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return d[a.length][b.length];
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

async function sales(db, params) {
  const from = params.get("from") ?? "";
  const to = params.get("to") ?? "";
  if (!ISO_DATE.test(from) || !ISO_DATE.test(to) || from > to) {
    return json({ status: "error", message: "Give from and to as YYYY-MM-DD, with from on or before to." }, 400);
  }
  const { results } = await db
    .prepare(`SELECT pin, site_address, city, land_use, acreage, last_sale_date, last_sale_price
              FROM parcels WHERE last_sale_date BETWEEN ?1 AND ?2 ORDER BY last_sale_date, pin`)
    .bind(from, to)
    .all();
  return json({
    status: "found", from, to, count: results.length, parcels: results,
    note: "Only each parcel's most recent sale is in the data, so an earlier sale of a parcel that sold again later will not appear.",
  });
}

const STATUS_CODE = { found: 200, not_found: 404, ambiguous: 300, error: 400 };

async function lookup(db, params) {
  const result = await findByAddress(db, params.get("address") ?? "");
  return json(result, STATUS_CODE[result.status]);
}

async function overAcreage(db, params) {
  const raw = params.get("min") ?? "1";
  const min = Number(raw);
  if (!Number.isFinite(min) || min < 0) {
    return json({ status: "error", message: `min must be a number of acres, got '${raw}'` }, 400);
  }
  const { results } = await db
    .prepare(`SELECT pin, site_address, city, land_use, zoning, acreage, assessed_value
              FROM parcels WHERE acreage > ?1 ORDER BY acreage DESC`)
    .bind(min)
    .all();
  return json({ status: "found", min_acreage_exclusive: min, count: results.length, parcels: results });
}

async function lastSale(db, params) {
  let row;
  if (params.get("pin")) {
    row = await db
      .prepare("SELECT pin, site_address, city, last_sale_date, last_sale_price FROM parcels WHERE pin = ?1")
      .bind(params.get("pin").trim())
      .first();
    if (!row) return json({ status: "not_found", message: `No parcel with PIN ${params.get("pin")}.` }, 404);
  } else if (params.get("address")) {
    const found = await findByAddress(db, params.get("address"));
    if (found.status !== "found") return json(found, STATUS_CODE[found.status]);
    const r = found.record;
    row = { pin: r.pin, site_address: r.site_address, city: r.city, last_sale_date: r.last_sale_date, last_sale_price: r.last_sale_price };
  } else {
    return json({ status: "error", message: "Give ?pin= or ?address=" }, 400);
  }
  const sale = row.last_sale_date
    ? { date: row.last_sale_date, price: row.last_sale_price }
    : null;
  return json({
    status: "found",
    pin: row.pin,
    site_address: row.site_address,
    city: row.city,
    last_sale: sale,
    note: sale ? undefined : "The county file has no sale date or price for this parcel. It does not say why.",
  });
}

function home(origin) {
  const ex = (path) => `<li><a href="${path}"><code>${origin}${path}</code></a></li>`;
  return new Response(
    `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wake Parcel API</title>
<style>body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;line-height:1.5;color:#1a1a1a;background:#fff}
code{font-size:.9em}li{margin:6px 0}</style></head><body>
<h1>Wake County parcel API</h1>
<p>A 250-record sample of Wake County parcels in a Cloudflare D1 database, built for the AI Foundations certificate, Module 3.2. Every endpoint returns JSON.</p>
<ul>
${ex("/parcels?address=977%20Hillsborough%20St")}
${ex("/parcels?address=9696%20Buck%20Jones%20Road%2C%20Cary")}
${ex("/parcels/over-acreage?min=1")}
${ex("/parcels/last-sale?pin=0743949082")}
${ex("/parcels/sales?from=2020-01-01&to=2020-12-31")}
</ul>
<p>Addresses match regardless of case, extra spaces, or Road/Rd-style spelling, and a trailing city or ZIP is ignored. The dataset has no owner names.</p>
</body></html>`,
    { headers: { "content-type": "text/html; charset=utf-8" } },
  );
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== "GET") return json({ status: "error", message: "GET only" }, 405);
    try {
      switch (url.pathname) {
        case "/": return home(url.origin);
        case "/parcels": return await lookup(env.DB, url.searchParams);
        case "/parcels/over-acreage": return await overAcreage(env.DB, url.searchParams);
        case "/parcels/last-sale": return await lastSale(env.DB, url.searchParams);
        case "/parcels/sales": return await sales(env.DB, url.searchParams);
        default: return json({ status: "error", message: `No endpoint at ${url.pathname}. See / for the list.` }, 404);
      }
    } catch (err) {
      return json({ status: "error", message: "The database query failed. Try again shortly." }, 500);
    }
  },
};
