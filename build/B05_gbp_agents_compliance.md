# B05 — Google Business Profile agents + compliance lint

Read first: `build/README.md`, `docs/02`, `knowledge/ranking-rules.md`, `agents/gbp-auditor.md`,
`agents/gbp-optimizer.md`, `agents/compliance-reviewer.md`, `docs/06` §7.
Where: local or cloud. Paid calls: none.

## Do

1. **`templates/gbp/current.yaml`** — every field the operator copies from the GBP dashboard (name,
   primary/secondary categories, address shown?, service areas, hours, holiday hours, phone, website URL,
   appointment URL, description, services, products, attributes, photo counts by type, last post date,
   Q&A count, reviews count/rating/reply rate, verification status) with a comment saying where each is
   in the GBP UI.
2. **`knowledge/gbp-categories/barber.md`, `pest-control.md`** — candidate primary/secondary categories,
   each marked `unverified` until checked in the GBP UI; what not to add.
3. **`tools/lint_claims.py <file> --client <slug>`** — flags (with line numbers):
   business-name changes vs the verified `name` fact; town/service words appended to the name;
   superlatives/claims (`best`, `#1`, `top-rated`, `guaranteed`, `award`, `certified`, `licensed`, years)
   without a matching verified fact; review incentive phrases (`% off`, `discount`, `free`, `draw`,
   `chance to win` near "review"); gating phrases ("if you're happy", "if not, contact us first");
   addresses not in facts; phone numbers not in facts; ranking promises ("guarantee", "#1 on Google",
   "top of Google"). Exit non-zero on any flag. Output JSON + human text.
4. `templates/gbp/change-batch.yaml` (example batch in docs/06 shape: field, current, proposed, reason,
   fact_refs, ui_path, risk).
5. **Demo run:** fill `gbp/current.yaml` (fictional, with deliberate gaps), run gbp-auditor →
   gbp-optimizer → compliance-reviewer → `approvals.py request`. Show the operator the batch and the report.

## Tests

lint flags "Demo Fade Co. – Best Barber Bradford" · flags "leave a review for 10% off" · flags gating text ·
flags "Award-winning" (proposed, not verified) · flags "we guarantee #1 on Google Maps" ·
passes a clean natural description · flags a phone number not in facts.

## Verify

```bash
uv run pytest -q
uv run python tools/lint_claims.py clients/_demo-barber/gbp/description-options.md --client _demo-barber
uv run python tools/validate.py clients/_demo-barber
```

## Done when

Demo has audit, change batch, compliance PASS report, approval in `requested`; tests pass; commit.
