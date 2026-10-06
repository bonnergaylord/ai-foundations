-- Wake County parcel sample, one row per parcel.
-- Types are chosen so the database refuses bad values instead of storing them.

DROP TABLE IF EXISTS parcels;

CREATE TABLE parcels (
  pin             TEXT PRIMARY KEY CHECK (length(pin) = 10),  -- text, not a number: keeps leading zeros
  site_address    TEXT NOT NULL,          -- exactly as the county file spells it
  address_key     TEXT NOT NULL UNIQUE,   -- normalized for matching (see load.py)
  city            TEXT NOT NULL,          -- title case; the source mixes raleigh / Raleigh / RALEIGH
  zip             TEXT NOT NULL CHECK (length(zip) = 5),      -- text: ZIPs are labels, not quantities
  zoning          TEXT,
  land_use        TEXT,
  acreage         REAL NOT NULL CHECK (acreage > 0),          -- decimal: 0.241 must not become 0
  heated_sqft     INTEGER,                -- NULL where the source is blank (mostly vacant land)
  year_built      INTEGER CHECK (year_built IS NULL OR year_built BETWEEN 1700 AND 2100),
  assessed_value  INTEGER NOT NULL,       -- whole dollars
  last_sale_date  TEXT CHECK (last_sale_date IS NULL OR last_sale_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  last_sale_price INTEGER,                -- whole dollars; NULL together with last_sale_date
  tax_district    TEXT NOT NULL,          -- stored as given; its meaning is not defined by the source
  CHECK ((last_sale_date IS NULL) = (last_sale_price IS NULL))
);

CREATE INDEX idx_parcels_acreage ON parcels (acreage);
