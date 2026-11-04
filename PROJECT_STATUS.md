# Project status

Last updated: 2026-11-04 (B05, Claude Code cloud)

## Current phase

**B05 implemented → ready for B06 (suggested tool: Codex).** B03 live smoke test still pending on your PC.

## Build steps

| Step | Name | Status | Notes |
| --- | --- | --- | --- |
| B00 | Bootstrap (uv, git, demo client, verify tool docs) | implemented | Codex docs not verified (network); see DECISIONS |
| B01 | Schemas, validator, approvals, budget | implemented | USD→CAD rate is a placeholder; link-prospector web-access question open |
| B02 | Grid, fixture scans, metrics, heatmaps | implemented | geocode.py not run live (tests mock Nominatim) |
| B03 | DataForSEO adapter | implemented (offline) · **pending live test** | API details + prices unverified (docs blocked in cloud) |
| B04 | Keyword/competitor + prospect audit | implemented | demo outputs lint-clean (B05) |
| B05 | GBP auditor/optimizer + compliance lint | implemented | demo compliance = self-review (re-check in B11) |
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

## Implemented in B03

- `tools/rank_scan.py` (standard queue + `--live`, cache, pending resume, budget check, ledger, place_id
  match with name/phone fallback, organic, keywords-probe), handmade fixtures in `tests/fixtures/dataforseo/`

## Implemented in B04

- `tools/competitors.py`, `tools/promote_prospect.py`, `tools/prospect_audit.py`,
  `templates/report/prospect-audit.html`, `knowledge/niche-playbooks/{barber,pest-control}.md`,
  validate.py + budget.py prospect support (`mode: pilot-audit`, US$1 cap)
- Demo client: keywords.json, competitors.json, gap-analysis.md. Demo prospect `prospects/_demo-prospect/`
  with a SYNTHETIC audit page

## Implemented in B05

- `tools/lint_claims.py`, `schemas/gbp_audit.schema.json`, validate.py batch/audit rules,
  `templates/gbp/{current,change-batch}.yaml`, `knowledge/gbp-categories/{barber,pest-control}.md` (all unverified)
- Demo day 2: gbp/current.yaml, audit.md/json, batch 2026-11-07, description options, services, Q&A seed,
  photo shot list, 2 compliance PASS reports, approval `A2026-11-07-gbp-apply-batch` (requested)

## Pending: B03 live smoke test (local only, ≤ US$2, operator must say "approve live test")

1. On your PC, check the DataForSEO docs + pricing against DECISIONS.md "2026-11-04 — B03" (endpoints,
   coordinate formats, status codes, item fields). Fix `tools/rank_scan.py` if anything differs.
2. Update `budget/config.yaml`: real `usd_per_task`, `prices_checked: <date>`, `prices_confirmed: true`;
   confirm `usd_to_cad` and set `rate_confirmed: true`.
3. `.env`: `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`, `GLOBAL_BUDGET_CAD_MONTH=100`.
4. Create `clients/<pilot-slug>/` (mode `pilot`, written permission, `scan.grid_size: 3`, one keyword,
   `budget_cad_month: 2.80` ≈ US$2) and validate it.
5. Run:
   `uv run python tools/rank_scan.py --client <pilot-slug> --label live-smoke --keywords "<keyword>"`
   then `uv run python tools/metrics.py --client <pilot-slug> --label live-smoke` and
   `uv run python tools/budget.py report <pilot-slug>`.
6. Record the real cost and any API differences in DECISIONS.md and SESSION_LOG.md.

## Blocked / needs the operator

- `budget/config.yaml → usd_to_cad` is a placeholder (1.40); confirm and set `rate_confirmed: true`
- `GLOBAL_BUDGET_CAD_MONTH` must be set (env or `.env`) before any paid call, otherwise budget.py refuses
- DECISIONS open question: link-prospector web access (decide before B08)

## Stubbed / not real yet

Every `tools/` script after B05 (schema_gen, site_check, …) and the site/report/card templates. Heatmaps have no basemap yet (plain grid). Agent specs reference scripts that do not
exist until their build step runs.
