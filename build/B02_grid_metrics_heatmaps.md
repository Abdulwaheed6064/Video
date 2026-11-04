# B02 — Grid, geocode, fixture scans, metrics, heatmaps

Read first: `build/README.md`, `docs/07_RANK_TRACKING_AND_REPORTING.md`, `docs/06` §6, `agents/rank-tracker.md`.
Where: local or cloud. Paid calls: none.

## Do

1. **`tools/grid.py --client <slug>`** (or `--lat --lng --size --spacing-km`): N×N points around the centre,
   longitude spacing corrected for latitude, stable row/col (row 0 = north, col 0 = west), JSON output,
   also stores each point's distance from centre in km.
2. **`tools/geocode.py`** — `--address` via OpenStreetMap Nominatim (custom User-Agent naming the project,
   ≤ 1 request/s, cache in `.cache/geocode.json`) or `--lat --lng` manual pin. Always prints/records the
   source. Network only when called explicitly; tests mock it.
3. **`tools/fixture_scan.py --client <slug> --label <label> [--seed N]`** — deterministic fake `grid.json`
   for fixture clients only (refuses others): plausible ranks that are worse far from centre, improve
   from `baseline` → `mid` → `final`, include 2 error points and some not-found points, fake competitors
   with stable place_ids, `synthetic: true`, `cost_usd: 0`.
4. **`tools/metrics.py --client <slug> --label <label> [--baseline <label>]`** — every metric in
   docs/07 §3: ARP (found-only and not-found=depth+1), top-3 share, found share, target-radius top-3
   share, organic position if present, review count/rating, deltas; percentage only when baseline > 0,
   else `{"from": 0, "to": N}`; error points excluded and listed. Refuses comparison if scan params differ.
5. **`tools/heatmap.py --client <slug> --label <label> [--compare <label>]`** — PNG per keyword: colour
   bands green 1–3, yellow 4–10, orange 11–20, red 20+, grey error; rank number in each cell; label block
   (keyword, date, grid, spacing, device); **SYNTHETIC** watermark when synthetic; side-by-side before/after
   composite with identical scale. Plain grid (no map tiles) is fine for v1; note OSM tiles as a later option.
6. Run on the demo: baseline, mid, final scans → metrics → heatmaps.

## Tests

grid spacing within 2% at 44°N · metrics on hand-built 3×3 grids (all found / some not found / error
points / zero baseline) · metrics refuses mismatched params · fixture_scan refuses non-fixture clients ·
heatmap PNG created with expected pixel size · same seed → identical output.

## Verify

```bash
uv run pytest -q
uv run python tools/fixture_scan.py --client _demo-barber --label baseline
uv run python tools/metrics.py --client _demo-barber --label baseline
uv run python tools/heatmap.py --client _demo-barber --label final --compare baseline
uv run python tools/validate.py clients/_demo-barber
```

## Done when

Demo has three scans with metrics and a before/after heatmap; tests pass; commit `B02: ...`.
