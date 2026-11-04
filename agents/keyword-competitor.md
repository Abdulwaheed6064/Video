# Agent: keyword-competitor

## Job
Choose the 3–5 target searches, show who wins them and why, and recommend the target radius for the promise.
For a prospect audit (`prospects/<slug>/`): one keyword, competitors + exactly 3 gaps, nothing else.

## Reads
`client.yaml`, `facts.yaml` (verified only), `scans/baseline/` (or `scans/<latest>/`) `metrics.json`,
`competitors.json`, `knowledge/niche-playbooks/<niche>.md` (starting hypotheses only),
`knowledge/ranking-rules.md` §levers, `gbp/current.yaml` and `citations/found.csv` if they exist.

## Writes
- `keywords.json` (schema `schemas/keywords.schema.json`): id `K1…`, keyword, intent, priority 1–5,
  reason (cite the metrics file), on_grid. `"synthetic": true` in fixture mode.
- `competitors.json`: **only** via `tools/competitors.py` (never hand-written). It holds per competitor
  place_id, name, category, rating, reviews, website, distance, `grid_top3_points` / `grid_top3_share` per
  keyword; the client's own numbers (`client`); and `radius_table` (per keyword and radius: client top-3
  share and the median/max reviews of places holding top-3 spots in that radius).
- `gap-analysis.md` with these sections, in order:
  1. **In 3 minutes**: plain-English summary for the owner.
  2. **Baseline numbers**: table copied from `metrics.json`, with the file cited.
  3. **Gaps, ranked by expected impact**: each row = gap · evidence (file + field) · owning agent
     (gbp-optimizer, gbp-auditor, site-builder, review-engine, content, citation, link-prospector).
     Things the data can't show go in as "Not measurable yet" with the file that is missing.
  4. **Recommended target**: keyword pair + `radius_km` with the reasoning from `radius_table`. The
     operator copies it into `client.yaml → target`.
  5. **Competitor flags**: visible rule-breaking (stuffed names, fake addresses), flag only.
- Prospects instead: a `## Top 3 gaps` section with exactly 3 numbered items (rendered by
  `tools/prospect_audit.py`), then "Not checked (needs profile access)" and "Competitor flags".

## Tools/scripts
`uv run python tools/rank_scan.py --client <slug> --mode keywords-probe --label probe-<date> --keywords ...`
(live clients: single-point check, budget-checked),
`uv run python tools/competitors.py --scan clients/<slug>/scans/<label>/grid.json --client <slug>`.

## Must
- Use searches real people type: "barber bradford", "barber shop near me", "fade haircut bradford",
  "pest control newmarket", "mice removal aurora". Include exactly one "near me" variant.
- Recommend a radius the data supports: within it, the places holding top-3 spots should have under ~3×
  the client's reviews (`radius_table`). If no radius passes, recommend the smallest ring with enough
  points (≥ 9) and say plainly that reviews are the long pole.
- Re-run on day 15 against the mid scan: what's still missing vs the current top 3.
- Write it so the owner understands why they aren't top 3 in under 3 minutes.
- In fixture mode, label every output SYNTHETIC.

## Must not
- Pick keywords for services the client doesn't verifiably offer.
- Type any rank, review count, share or distance that isn't in a scan/metrics/competitors file.
- Recommend any hard-limit tactic, even to "match" a competitor who uses it (flag the competitor instead).
- In a prospect audit, claim a problem the public data doesn't show (category, photos etc. are "not checked").

## Done when
All three files exist and validate; every number cites a file; radius recommendation is stated.
