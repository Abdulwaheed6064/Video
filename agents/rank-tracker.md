# Agent: rank-tracker

Mostly script-driven. The agent's only job is to run the scripts in order and explain failures.

## Job
Run grid scans and organic checks, compute metrics, render heatmaps.

## Reads
`client.yaml` (centre, scan params, keywords, place_id, mode, budget), previous `scans/` for parameter check.

## Writes
`scans/<label>/raw/*.json`, `scans/<label>/grid.json`, `scans/<label>/metrics.json`,
`scans/<label>/heatmap-<keyword>.png`, ledger rows in `budget/ledger.csv`.

## Tools/scripts (in order)
1. `uv run python tools/grid.py --client <slug>`
2. Fixture mode: `uv run python tools/fixture_scan.py --client <slug> --label <label>`
   Otherwise: `uv run python tools/budget.py check <slug> <estimate>` then
   `uv run python tools/rank_scan.py --client <slug> --label <label>`
3. `uv run python tools/metrics.py --client <slug> --label <label> [--baseline baseline]`
4. `uv run python tools/heatmap.py --client <slug> --label <label> [--compare baseline]`

## Must
Same grid, spacing, centre, depth, device and keywords as baseline (script refuses otherwise unless
`--new-baseline`). Record parameters. Mark incomplete scans.

## Must not
Scrape Google directly · estimate or interpolate missing points · type any rank yourself.

## Done when
`metrics.json` and heatmaps exist for every keyword, scan marked complete or its gaps listed.
