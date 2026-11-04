# Project status

Last updated: 2026-11-04 (B00, Claude Code cloud)

## Current phase

**B00 implemented → ready for B01.** Next action: `/build B01`.

## Build steps

| Step | Name | Status | Notes |
| --- | --- | --- | --- |
| B00 | Bootstrap (uv, git, demo client, verify tool docs) | implemented | Codex docs not verified (network); see DECISIONS |
| B01 | Schemas, validator, approvals, budget | not started | |
| B02 | Grid, fixture scans, metrics, heatmaps | not started | |
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

## Stubbed / not real yet

Every real script under `tools/`, plus `schemas/` and the site/report/card templates. `tests/` has only the smoke test. Agent specs reference scripts that do not
exist until their build step runs.
