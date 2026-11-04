# B04 — Keyword & competitor analysis + prospect audit

Read first: `build/README.md`, `docs/02`, `docs/07` §6, `docs/13` §11, `agents/keyword-competitor.md`.
Where: local or cloud. Paid calls: none (fixture).

## Do

1. **Niche playbooks** (mark every claim "starting hypothesis — verify per client"):
   - `knowledge/niche-playbooks/barber.md` — keyword patterns (barber / barber shop / men's haircut /
     fade / beard trim + town, near me), likely primary category "Barber shop", typical services, common
     gaps, review-velocity norms, photo ideas, booking platforms (Booksy, Fresha, Square).
   - `knowledge/niche-playbooks/pest-control.md` — service-area setup, keywords (pest control / exterminator /
     mice / rats / bed bugs / wasps + town), licence notes for Ontario, seasonal patterns, lead-gen spam
     competitors to watch.
2. **`tools/competitors.py --scan <grid.json> --client <slug>`** → `competitors.json` (docs/06 §5):
   per competitor place_id, name, category, rating, reviews, website, distance from client, top-3 share
   per keyword. Numbers only from the scan.
3. Finalise `agents/keyword-competitor.md` if anything is missing; its outputs: `keywords.json`,
   `competitors.json`, `gap-analysis.md` (gaps ranked, each mapped to an owning agent), recommended
   `radius_km` with reasoning from data.
4. **Prospect flow** (`docs/13` §11): `prompts/audit-prospect.md` already exists — make it work:
   - `prospects/<slug>/` layout (subset of client layout), `mode: pilot-audit`, budget US$1.
   - `templates/report/prospect-audit.html` one page: heatmap, competitor table, 3 gaps, no promises.
   - `tools/promote_prospect.py <slug>` moves a signed prospect to `clients/<slug>/` (mode pilot).
   - validate.py supports `prospects/`.
5. Run keyword-competitor on the demo in fixture mode; show `gap-analysis.md` to the operator.

## Tests

competitors.py on a fixture grid (shares correct, sorted) · promote_prospect refuses if target exists ·
prospect budget cap enforced.

## Verify

```bash
uv run pytest -q
uv run python tools/competitors.py --scan clients/_demo-barber/scans/baseline/grid.json --client _demo-barber
uv run python tools/validate.py clients/_demo-barber
```

## Done when

Demo has keywords.json, competitors.json, gap-analysis.md; prospect flow works in fixture mode; commit.
