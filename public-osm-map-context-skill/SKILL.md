---
name: public-osm-map-context
description: |
  Public OSM map context skill. Use when a property workflow needs zero-API-key map context such as approximate geocoding, nearby amenities, nearest transit stops, road/rail risk signals, or manual map verification links.
  This skill only provides best-effort OpenStreetMap-based context. It must not be treated as Google Maps verification, real-time transit routing, street view, ratings, reviews, or complete POI coverage.
metadata:
  short-description: Public OSM map context
---

# Public OSM Map Context

## Role

Provide best-effort map context for property decisions using public OpenStreetMap services and local lightweight caching.

This skill is a data source. It does not recommend properties by itself. It outputs JSON for decision skills such as `property-advisor`.
Publish or install this skill independently when the runtime only discovers top-level skills. If embedded inside another skill repository, the parent skill should call `scripts/cli.py` directly rather than assuming automatic nested-skill discovery.

## Execution Boundary

All operations must go through:

```bash
python3 scripts/cli.py <command>
```

Do not open Google Maps pages and scrape results. Do not claim Google Maps has verified the output.

## Commands

```bash
python3 scripts/cli.py doctor
python3 scripts/cli.py analyze-batch --input listings.json --destination "Melbourne CBD VIC" --city melbourne --incremental
python3 scripts/cli.py cache-stats
```

Live public OSM calls are intentionally bounded. Defaults:

- `--timeout 8`: per HTTP request timeout in seconds
- `--max-live-seconds 45`: whole live analysis time budget
- `--overpass-retries 1`: one attempt per Overpass endpoint before degrading
- `--geocode-strategy photon-first`: fast batch geocoding first, Nominatim fallback

If the live budget is exhausted, return JSON with `status=partial` or `status=degraded`; do not keep waiting silently.

For deterministic tests or demos:

```bash
python3 scripts/cli.py analyze-batch --input tests/fixtures/melbourne_listings.json --destination "Melbourne CBD VIC" --fixture-dir tests/fixtures/osm
```

## Output Semantics

The CLI always returns JSON. Each listing includes:

- `geo.precision`: `address`, `area`, or `missing`
- `geo.confidence`: `high`, `medium`, or `low`
- `amenities`: OSM POI counts when available
- `transit_access`: nearest OSM transit stop when available
- `risk_signals`: rough road/rail/industrial proximity
- `verification_links`: manual OpenStreetMap and Google Maps links
- `limitations`: explicit limits such as `not_google_maps_verified`

## Mandatory Caveats

- Public OSM is not Google Maps.
- Public OSM may be incomplete or temporarily unavailable.
- Public OSM results are suitable for screening, not final lease or purchase decisions.
- Public transport travel time is not verified.
- If only area-level location is available, do not output listing-level precise distance claims.
- `source=photon` and `confidence=low` should be treated as low-confidence screening signals, not address-level proof.
