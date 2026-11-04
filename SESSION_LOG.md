# Session log

Append one entry per AI session. Newest at the bottom.

Template:

```text
## YYYY-MM-DD HH:MM · <Claude Code | Codex | Claude cloud> · <model> · <task e.g. B03 or sprint kings-barbers day 2>
- Files changed:
- Commands run (with real results):
- Stubbed / not working:
- Next:
```

---

## 2026-11-03 · Claude Code (desktop) · Opus 5.5 · planning

- Files changed: moved draft pack 00–12 into `docs/`; added README, AGENTS.md, CLAUDE.md, PROJECT_STATUS,
  DECISIONS, this log, `docs/13`, `docs/14`, `build/B00–B11`, `agents/*` (14), `.claude/agents/*`,
  `.claude/commands/*`, `prompts/*`, `knowledge/ranking-rules.md`, `.claude/settings.json`,
  `.gitignore`, `.env.example`.
- Commands run: none beyond file moves. No code, no tests yet.
- Stubbed: all of `tools/`, `schemas/`, `templates/`, `tests/`.
- Next: B00.

## 2026-11-04 · Claude cloud · Claude Code · B00 bootstrap

- Files changed: `DECISIONS.md` (verified doc links, settings decision, `synthetic` key),
  `PROJECT_STATUS.md`, `.claude/settings.json` (new), `templates/claude/settings.json` (`$schema`
  added, `git push` deny removed), `pyproject.toml`, `uv.lock`, `.python-version`, `tools/__init__.py`,
  `tests/__init__.py`, `tests/test_smoke.py`, `budget/ledger.csv`, `clients/_demo-barber/**`
  (client.yaml, facts.yaml, questions.md, access.md, log.md, intake/questionnaire.md, intake/notes.md,
  `.gitkeep` folders per docs/06 §1).
- Commands run (with real results):
  - WebFetch code.claude.com docs (sub-agents, slash-commands, memory, settings, permissions): OK, findings in DECISIONS.
  - WebFetch developers.openai.com: failed (`getaddrinfo ENOTFOUND`; host not allowed by the session network).
  - `uv init --bare --python 3.12 --name maps-rank-studio`: initialized. `uv add pyyaml jsonschema pydantic matplotlib qrcode pillow httpx`: OK. `uv add --dev pytest`: OK (pytest 9.2.0).
  - `uv run python --version`: Python 3.12.3.
  - `uv run pytest -q`: `11 passed in 1.55s`.
  - `git log --oneline -1`: the `B00: bootstrap` commit, made right after this entry.
- Stubbed / not working: Codex formats not verified (network). `tools/validate.py` doesn't exist yet
  (B01). Step 7 (`gh repo create`) skipped: the repo already exists on GitHub (abdulwaheed6064/seo).
- Next: B01. Its schemas must accept `synthetic: true` on client.yaml/facts.yaml.

## 2026-11-04 · Claude cloud · Claude Code · B01 contracts, validator, approvals, budget

- Files changed: `schemas/` (client, facts, keywords, competitors, grid, metrics, approval, tasks,
  ledger_row, gbp_change_batch, compliance_report), `tools/common.py`, `tools/validate.py`,
  `tools/approvals.py`, `tools/budget.py`, `budget/config.yaml`, `tests/conftest.py`,
  `tests/test_validate.py`, `tests/test_approvals.py`, `tests/test_budget.py`; spec fixes in
  `agents/compliance-reviewer.md`, `agents/review-engine.md`, `agents/reporter.md`, `docs/04`, `docs/06`;
  `DECISIONS.md`, `PROJECT_STATUS.md`.
- Commands run (with real results):
  - `uv run pytest -q`: `57 passed in 1.36s`
  - `uv run python tools/validate.py clients/_demo-barber`: `OK clients/_demo-barber: 2 file(s) checked, 0 errors`
  - `uv run python tools/approvals.py --help`: usage printed, exit 0
  - `uv run python tools/budget.py report`: exit 0; `_demo-barber fixture 0.00 … cap 0.00`;
    `global cap not set (GLOBAL_BUDGET_CAD_MONTH); paid calls refused`; placeholder-rate warning
  - `uv run python tools/budget.py check _demo-barber 0.10`: exit 1 (fixture mode + global cap unset)
- Stubbed / not working: USD→CAD rate is an unconfirmed placeholder. metrics.schema.json covers core
  fields only (B02 owns metrics.py). link-prospector web-access contradiction recorded as an open question.
- Next: B02 (grid, geocode, fixture scans, metrics, heatmaps).

## 2026-11-04 · Claude cloud · Claude Code · B02 grid, geocode, fixture scans, metrics, heatmaps

- Files changed: `tools/grid.py`, `tools/geocode.py`, `tools/fixture_scan.py`, `tools/metrics.py`,
  `tools/heatmap.py`, `tools/common.py` (scan label check), `tools/validate.py`, `schemas/grid.schema.json`
  (optional places/organic/client_place_id/distance_km), tests (`helpers.py`, `test_grid.py`, `test_geocode.py`,
  `test_fixture_scan.py`, `test_metrics.py`, `test_heatmap.py`, conftest copies demo without scans),
  `clients/_demo-barber/` (client.yaml radius 1.5, log.md, scans/{baseline,mid,final}/ grid+metrics+PNGs),
  `docs/06`, `.gitignore` (.cache/), `DECISIONS.md`, `PROJECT_STATUS.md`.
- Commands run (with real results):
  - `uv run pytest -q`: `92 passed in 3.14s`
  - `uv run python tools/fixture_scan.py --client _demo-barber --label baseline` (also mid, final):
    `SYNTHETIC scan written: … (49 points × 3 keywords, 2 error points)`
  - `uv run python tools/metrics.py --client _demo-barber --label baseline`: e.g. `'barber bradford': top3 1/47, found 45, ARP(found) 12.58, ARP(nf=depth+1) 12.94, radius top3 1/13, errors 2`
  - `uv run python tools/metrics.py --client _demo-barber --label final --baseline baseline`: `'barber bradford': top3 7/47 … radius top3 7/13`
  - `uv run python tools/heatmap.py --client _demo-barber --label final --compare baseline`: 6 PNGs written (3 single 800×900, 3 composites 1600×900)
  - `uv run python tools/validate.py clients/_demo-barber`: `OK clients/_demo-barber: 8 file(s) checked, 0 errors`
- Stubbed / not working: geocode.py was never called live (Nominatim mocked in tests). Heatmaps have
  no basemap. All demo numbers are synthetic.
- Next: B03 (DataForSEO adapter). Code and mocked tests can run in the cloud; the live test needs your API keys on your PC.

## 2026-11-04 · Claude cloud · Claude Code · B03 DataForSEO adapter (code; live test skipped by operator)

- Files changed: `tools/rank_scan.py` (new), `tools/budget.py` (`append_row`), `budget/config.yaml`
  (dataforseo placeholder prices, unconfirmed), `schemas/grid.schema.json` (mode, client_match, failures,
  params.zoom), `schemas/client.schema.json` (scan.zoom, scan.town_centre), `tests/test_rank_scan.py`,
  `tests/fixtures/dataforseo/{maps,organic}_task_get.json` (handmade), `docs/06`, `DECISIONS.md`,
  `PROJECT_STATUS.md`.
- Commands run (with real results):
  - WebFetch docs.dataforseo.com / dataforseo.com: `getaddrinfo ENOTFOUND` (blocked by session network);
    WebSearch used instead, and findings are marked unverified in DECISIONS.
  - `uv run pytest -q`: `107 passed in 3.82s`
  - `uv run python tools/rank_scan.py --help`: usage printed, exit 0
  - `uv run python tools/rank_scan.py --client _demo-barber --label x`: `REFUSED: client _demo-barber is in fixture mode: no paid calls. Use: uv run python tools/fixture_scan.py …`, exit 1
  - `uv run python tools/validate.py clients/_demo-barber`: `OK … 8 file(s) checked, 0 errors`
- Stubbed / not working: no live call made (operator: skip live test in cloud). DataForSEO endpoints,
  fields and prices are unverified, and prices_confirmed: false blocks paid calls until checked.
- Next: B04 (cloud). The B03 live smoke test runs on the operator's PC; steps are in PROJECT_STATUS.md.

## 2026-11-04 · Claude cloud · Claude Code · B04 keywords, competitors, prospect audit

- Files changed: `tools/competitors.py`, `tools/promote_prospect.py`, `tools/prospect_audit.py` (new);
  `tools/validate.py` (prospect layout + mode rules), `tools/budget.py` (pilot-audit US$1 cap);
  `schemas/client.schema.json` (pilot-audit), `schemas/competitors.schema.json` (client, radius_table,
  grid_top3_points); `templates/report/prospect-audit.html`; `knowledge/niche-playbooks/{barber,pest-control}.md`;
  `agents/keyword-competitor.md`, `prompts/audit-prospect.md`; demo client keywords.json, competitors.json,
  gap-analysis.md, log.md; `prospects/_demo-prospect/` (fixture scan, metrics, heatmap, competitors,
  gap-analysis, audit page); tests `test_competitors.py`, `test_prospects.py`; docs/06, DECISIONS, PROJECT_STATUS.
- Commands run (with real results):
  - `uv run pytest -q`: `122 passed in 4.68s`
  - `uv run python tools/competitors.py --scan clients/_demo-barber/scans/baseline/grid.json --client _demo-barber`: `SYNTHETIC competitors written: … (6 competitors, source scans/baseline/grid.json)`
  - `uv run python tools/validate.py clients/_demo-barber`: `OK … 10 file(s) checked, 0 errors`
  - `uv run python tools/validate.py prospects/_demo-prospect`: `OK … 4 file(s) checked, 0 errors`
  - `uv run python tools/prospect_audit.py --prospect _demo-prospect --label baseline`: wrote `reports/2026-11-05/audit.html` (screenshot checked)
- Bug found and fixed: competitors.py dropped the corner points from the "whole grid" radius row (rounding down).
- Stubbed / not working: the demo gap analyses and audit page are not compliance-reviewed (B05 brings
  lint_claims). The prospect flow has only run in fixture mode.
- Next: B05 (GBP auditor/optimizer, category notes, lint_claims).
