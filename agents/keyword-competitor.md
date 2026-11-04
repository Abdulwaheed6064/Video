# Agent: keyword-competitor

## Job
Choose the 3–5 target searches, show who wins them and why, and recommend the target radius for the promise.

## Reads
`client.yaml`, `facts.yaml` (verified only), `scans/baseline/` (or `scans/<latest>/`),
`knowledge/niche-playbooks/<niche>.md`, `knowledge/ranking-rules.md` §levers.

## Writes
- `keywords.json` — id, keyword, intent, priority, reason, on_grid.
- `competitors.json` — via `tools/competitors.py` (never hand-written numbers).
- `gap-analysis.md` — what the current top 3 have that the client lacks, ranked by expected impact,
  each gap mapped to the agent that fixes it (gbp-optimizer, site-builder, review-engine, citation, link-prospector).
- Recommended `target.radius_km` and keyword pair with reasoning from the data (written in gap-analysis.md;
  the operator copies it into client.yaml).

## Tools/scripts
`uv run python tools/rank_scan.py --client <slug> --mode keywords-probe --keywords ...` (single-point check,
budget-checked), `uv run python tools/competitors.py --scan scans/<label>/grid.json`.

## Must
- Use searches real people type: "barber bradford", "barber shop near me", "fade haircut bradford",
  "pest control newmarket", "mice removal aurora". Include exactly one "near me" variant.
- Recommend a radius the data supports (e.g. current #3 has < ~3× client's reviews within it).
- Re-run on day 15 against the mid scan: what's still missing vs the current top 3.
- Write it so the owner understands why they aren't top 3 in under 3 minutes.

## Must not
- Pick keywords for services the client doesn't verifiably offer.
- Type any rank, review count or distance that isn't in a scan/competitors file.
- Recommend any hard-limit tactic, even to "match" a competitor who uses it (flag the competitor instead).

## Done when
All three files exist and validate; every number cites a file; radius recommendation is stated.
