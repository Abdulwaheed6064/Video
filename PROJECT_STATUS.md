# Project status

Last updated: 2026-11-04 (B02, Claude Code cloud)

## Current phase

**B02 implemented → ready for B03 (code in cloud; live test on your PC).** Next action: `/build B03`.

## Build steps

| Step | Name | Status | Notes |
| --- | --- | --- | --- |
| B00 | Bootstrap (uv, git, demo client, verify tool docs) | implemented | Codex docs not verified (network); see DECISIONS |
| B01 | Schemas, validator, approvals, budget | implemented | USD→CAD rate is a placeholder; link-prospector web-access question open |
| B02 | Grid, fixture scans, metrics, heatmaps | implemented | geocode.py not run live (tests mock Nominatim) |
| B03 | DataForSEO adapter | not started | needs DataForSEO account |
| B04 | Keyword/competitor + prospect audit | not started | |
| B05 | GBP auditor/optimizer + compliance lint | not started | |
| B06 | Website template, schema, site checks, deploy | not started | |
| B07 | Citations + NAP checker | not started | |
| B08 | Reviews, content, links, QR card | not started | |
| B09 | Reporter, orchestrator, `/sprint` | not started | |
| B10 | Fixture dry run + live baseline on pilot | not started | needs pilot business + permission |
| B11 | Independent audit + fixes | not started | run in the other tool |

## What exists now (written in planning, not code)

- Rules: `AGENTS.md`, `CLAUDE.md`, `knowledge/ranking-rules.md`
- 14 canonical agent specs in `agents/` + Claude wrappers in `.claude/agents/`
- Commands in `.claude/commands/` + Codex prompts in `prompts/`
- Design pack `docs/00–14`, build steps `build/B00–B11`
- Empty folders: `tools/ schemas/ templates/ tests/ budget/ clients/`

## Implemented in B00

- `pyproject.toml` + `uv.lock` (Python 3.12, deps per B00), `tools/__init__.py`, `tests/test_smoke.py`
- `.claude/settings.json` installed (no `git push` deny; see DECISIONS 2026-11-04)
- `clients/_demo-barber/` synthetic fixture client; `budget/ledger.csv` (header only)

## Implemented in B01

- `schemas/` (11 schemas), `tools/common.py`, `tools/validate.py`, `tools/approvals.py`, `tools/budget.py`,
  `budget/config.yaml`; tests in `tests/test_validate.py`, `test_approvals.py`, `test_budget.py`

## Implemented in B02

- `tools/grid.py`, `tools/geocode.py`, `tools/fixture_scan.py`, `tools/metrics.py`, `tools/heatmap.py`
- Demo: SYNTHETIC `scans/{baseline,mid,final}/` with grid.json, metrics.json, heatmaps (+ before/after)

## Blocked / needs the operator

- `budget/config.yaml → usd_to_cad` is a placeholder (1.40); confirm and set `rate_confirmed: true`
- `GLOBAL_BUDGET_CAD_MONTH` must be set (env or `.env`) before any paid call, otherwise budget.py refuses
- DECISIONS open question: link-prospector web access (decide before B08)

## Stubbed / not real yet

Every `tools/` script after B02 (rank_scan, competitors, lint_claims, schema_gen, site_check, …) and the site/report/card templates. Heatmaps have no basemap yet (plain grid). Agent specs reference scripts that do not
exist until their build step runs.
