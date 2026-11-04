# B01 — Contracts, validator, approvals, budget

Read first: `build/README.md`, `docs/06_DATA_CONTRACTS.md`, `docs/13` §4 and §6, `agents/*.md`.
Where: local or cloud. Paid calls: none.

## Do

1. **JSON Schemas** in `schemas/` for every file in docs/06: `client`, `facts`, `keywords`,
   `competitors`, `grid`, `metrics`, `approval`, `tasks` (also used for sprint.json), `ledger_row`,
   `gbp_change_batch`, `compliance_report` (front-matter fields: result, sha256, file, date).
   - `client.yaml` adds `gbp_status: active | pending_verification | suspended` and `sprint_start: date`.
   - Task statuses: `pending, running, needs_compliance, awaiting_approval, applied, done, blocked, skipped`
     (`blocked`/`skipped` require `reason`; `blocked` also `human_action`). See docs/13 §4.
2. **`tools/validate.py <client_dir>`** — validates every present file against its schema, plus rules:
   facts status in {proposed, verified, rejected}; grid.json has `synthetic`; fixture-mode files have
   `synthetic: true`; no file outside the docs/06 layout at top level. Readable errors, non-zero exit.
3. **`tools/approvals.py`** — subcommands `hash <file>`, `request`, `approve`, `reject`, `verify`, `consume`,
   implementing docs/06 §7: SHA-256 binding, expiry, compliance report with `RESULT: PASS` for the same
   digest required, owner approval when `required: true`, consume once only, consume writes the applied
   fields to `gbp/applied.log` or a deploy receipt.
4. **`tools/budget.py`** — `check <client> <est_usd>`, `record ...`, `report [client]` implementing
   docs/06 §9; per-client cap from client.yaml (CAD, converted with a rate stored in `budget/config.yaml`)
   and global cap from env `GLOBAL_BUDGET_CAD_MONTH`; fixture-mode clients always have cap 0.
5. Review `agents/*.md` against docs/04 and docs/13 — fix contradictions only; record changes in DECISIONS.md.

## Tests (pytest, no network)

- approval invalid after artifact edit · expired approval rejected · consume twice rejected ·
  missing compliance PASS rejected · owner approval missing when required → rejected
- budget check fails over client cap, over global cap, and for any fixture client with est > 0
- validator catches: fact with unknown status; grid.json without `synthetic`; blocked task without reason
- demo client validates clean

## Verify

```bash
uv run pytest -q
uv run python tools/validate.py clients/_demo-barber
uv run python tools/approvals.py --help
uv run python tools/budget.py report
```

## Done when

All tests pass, demo validates, commit `B01: ...`.
