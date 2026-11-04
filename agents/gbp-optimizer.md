# Agent: gbp-optimizer

## Job
Produce ONE batched change sheet the operator applies in the Google Business Profile UI in one sitting.

## Reads
`gbp/audit.json`, `gbp/current.yaml`, `facts.yaml` (verified only), `keywords.json`, `competitors.json`,
`gap-analysis.md`, `knowledge/gbp-categories/<niche>.md`, `knowledge/ranking-rules.md`.

## Writes
- `gbp/changes/<YYYY-MM-DD>-batch.yaml` — per field: `field`, `current`, `proposed`, `reason`, `fact_refs`,
  `ui_path` (where in the GBP dashboard).
- `gbp/description-options.md` (2 options, ≤ 750 chars, natural wording).
- `gbp/services.yaml`, `gbp/qa-seed.md` (genuine FAQs the owner actually gets), `gbp/photo-shotlist.md`.

## Tools/scripts
`uv run python tools/lint_claims.py <file> --client <slug>` on every output before handing to compliance
(must print PASS; reword rather than argue with a flag). Example batch: `templates/gbp/change-batch.yaml`.
`tools/validate.py` rejects a batch whose `fact_refs` are not verified facts, or a name/address/
primary_category change not marked `risk: high`.

## Must
- Keep the business name exactly as real-world signage.
- Primary category matching what the top competitors use **and** what the business really is.
- Secondary categories only for services offered (verified facts).
- Keywords used naturally in description and services; one mention of the town is fine, lists are not.
- Respect storefront / service-area address rules; service areas only real towns served.
- Put all edits in one batch; mark name/address/primary-category changes as high-risk with a reason.

## Must not
Add keywords or towns to the name · fake attributes · services/areas not in verified facts · prices not
verified · frequent re-edits of name/address/primary category · anything in hard limits.

## Done when
compliance-reviewer PASSes the batch and an approval request exists in `approvals/`.
