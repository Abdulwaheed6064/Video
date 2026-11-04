# Free rank-map audit for a prospect (sales tool)

ARGS: $ARGUMENTS   (format: `"<business name>" <town> "<keyword>"`)

Public data only: we have no access to and no relationship with this business. Do not contact it.
Work only inside `prospects/<slug>/` (docs/13 §11). Layout allowed by `tools/validate.py`:
`client.yaml` (required), `facts.yaml`, `keywords.json`, `competitors.json`, `gap-analysis.md`,
`questions.md`, `log.md`, and the folders `scans/`, `reports/`, `reviews/`, `approvals/`.

1. **Folder.** slug = business-town, lowercase-hyphenated (e.g. `kings-barbers-bradford`). Copy the shape of
   `prospects/_demo-prospect/client.yaml` and change: `slug`, `display_name` (exactly as on the listing or
   signage), `mode: pilot-audit`, `niche`, `business_type`, `location` (step 2), `target.keywords` = the
   one keyword, `budget_cad_month: 1.40`, `created`. Remove `synthetic`. `budget.py` caps any pilot-audit
   prospect at US$1 regardless.
2. **Location.** Ask the operator for the address or coordinates if not given, then
   `uv run python tools/geocode.py --address "<address>"` (or `--lat --lng`). Copy `lat`, `lng` and
   `geocode_source` into client.yaml. Validate: `uv run python tools/validate.py prospects/<slug>`.
3. **Scan (rank-tracker)** — one 7×7 scan, one keyword:
   `uv run python tools/rank_scan.py --client <slug> --label baseline` (it runs the budget check itself and
   refuses over US$1). If it reports `client_match: unconfirmed`, ask the operator to confirm the listing
   before going on.
   Then `uv run python tools/metrics.py --client <slug> --label baseline` and
   `uv run python tools/heatmap.py --client <slug> --label baseline`.
4. **keyword-competitor**:
   `uv run python tools/competitors.py --scan prospects/<slug>/scans/baseline/grid.json --client <slug>`,
   then write `gap-analysis.md` with `## Top 3 gaps` (exactly 3 numbered items, each citing its file),
   "Not checked (needs profile access)" and "Competitor flags" (agents/keyword-competitor.md).
5. **Page (reporter)**: `uv run python tools/prospect_audit.py --prospect <slug> --label baseline`.
   This makes a one-page heatmap, competitor table and the 3 gaps, with no promises.
6. **compliance-reviewer** on `gap-analysis.md` and the page. Never claim problems not shown by the data.
7. Append to `prospects/<slug>/log.md` and `SESSION_LOG.md`. Print the page path.

On signing: `uv run python tools/promote_prospect.py <slug>` moves it to `clients/<slug>/` (mode pilot).
The audit scan becomes a candidate baseline only; re-scan on day 1 with the full keyword set.

Demo (fixture, no paid calls): steps 3–5 with `tools/fixture_scan.py --client _demo-prospect --label baseline`
in place of rank_scan.
