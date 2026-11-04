# Log — Demo Fade Co. (fictional) — SYNTHETIC

## 2026-11-04 · setup · Claude Code (cloud)
- B00: demo client created in fixture mode; all files synthetic.
- HUMAN NEXT: none (demo client).

## 2026-11-04 · B02 · Claude Code (cloud)
- rank-tracker scripts (fixture): SYNTHETIC scans baseline, mid, final (scans/*/grid.json), metrics (scans/*/metrics.json), heatmaps incl. final-vs-baseline.
- target.radius_km set to 1.5 (fictional) so the target-radius metric differs from the whole grid.
- HUMAN NEXT: none (demo client).

## 2026-11-04 · B04 · Claude Code (cloud)
- keyword-competitor (fixture): keywords.json (K1–K3), competitors.json (tools/competitors.py from scans/baseline), gap-analysis.md; recommended target K1+K2 within 1.0 km (SYNTHETIC).
- Not yet compliance-reviewed (lint_claims arrives in B05).
- HUMAN NEXT: none (demo client).

## 2026-11-07 · day 2 · Claude Code (cloud) [B05 demo run]
- gbp-auditor: 7 pass / 10 fail / 3 unknown (gbp/audit.md, gbp/audit.json)
- gbp-optimizer: batch1 proposed, 4 fields: website, services, hours, description (gbp/changes/2026-11-07-batch.yaml); description-options.md, services.yaml, qa-seed.md, photo-shotlist.md; lint_claims PASS on all
- compliance-reviewer: PASS (reviews/compliance/2026-11-07-batch-2026-11-07.md, description-options-2026-11-07.md). Same tool as author, so re-review in Codex at B11
- approvals.py request: A2026-11-07-gbp-apply-batch (requested, owner approval required, expires 2026-11-10)
- questions.md Q4 added (booking link)
- HUMAN NEXT (demo only): send description-options.md to owner; approve: `uv run python tools/approvals.py approve A2026-11-07-gbp-apply-batch --by A --owner-by "owner via WhatsApp" --owner-at <time>`; apply the 4 fields in the GBP UI in one sitting; `uv run python tools/approvals.py consume A2026-11-07-gbp-apply-batch --by A`
