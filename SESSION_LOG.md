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

## 2026-11-04 · Claude cloud · Claude Code · B05 GBP agents + compliance lint

- Files changed: `tools/lint_claims.py` (new), `tools/validate.py` (batch fact_refs/client, gbp/audit.json
  summary), `schemas/gbp_audit.schema.json`, `templates/gbp/current.yaml`, `templates/gbp/change-batch.yaml`,
  `knowledge/gbp-categories/{barber,pest-control}.md`, `agents/gbp-auditor.md`, `agents/gbp-optimizer.md`;
  demo `clients/_demo-barber/gbp/*` (current, audit.md/json, changes/2026-11-07-batch.yaml,
  description-options, services, qa-seed, photo-shotlist), `reviews/compliance/*` (2 reports),
  `approvals/A2026-11-07-gbp-apply-batch.yaml`, questions.md Q4, gap-analysis.md (2 rewordings), log.md;
  tests `test_lint_claims.py` + 3 validator tests; DECISIONS, PROJECT_STATUS.
- Commands run (with real results):
  - `uv run pytest -q`: `141 passed in 4.65s`
  - `uv run python tools/lint_claims.py clients/_demo-barber/gbp/description-options.md --client _demo-barber`:
    first run `FLAGS: 2` (my own "not used: award… founded" note) → reworded → `PASS: 0 flag(s)`
  - lint on the batch, services, qa-seed, photo-shotlist: `PASS`. B04 gap-analysis: `FLAGS: 2` ("#1", "guarantee") → reworded → `PASS`
  - `uv run python tools/approvals.py request … --action gbp_apply_batch …`: `REQUESTED A2026-11-07-gbp-apply-batch … expires 2026-11-10, owner approval required`
  - `uv run python tools/approvals.py verify A2026-11-07-gbp-apply-batch`: exit 1 (not approved yet; expected)
  - `uv run python tools/validate.py clients/_demo-barber`: `OK … 15 file(s) checked, 0 errors`
- Bug found and fixed: the lint's YAML skip covered sibling keys of `- field:` (so `proposed` went unlinted); it now tracks the key column.
- Stubbed / not working: categories unverified (need the GBP picker). Demo compliance is self-review.
- Next: B06 (website template, schema_gen, site_check, deploy); build file suggests Codex.

## 2026-11-04 · Claude cloud · Claude Code · B06 website template, schema, site checks, publish gate

- Files changed: `templates/site/` (Astro 7.4.5 template: Base layout with JSON-LD/canonical/OG, home,
  [service], contact, 404, robots.txt endpoint, sitemap, CSS, labelled placeholder image, sample config,
  content.example.yaml, package-lock); `tools/schema_gen.py`, `tools/build_site_config.py`, `tools/site_check.py`,
  `tools/site_release.py`, `tools/deploy.sh`, `tools/deploy.ps1`; `pyproject.toml`/`uv.lock` (+extruct);
  `schemas/client.schema.json` (schema_type, cloudflare_pages_project); `agents/site-builder.md`,
  `agents/site-auditor.md`; `tests/test_site.py`, conftest (skip node_modules/dist); demo
  `clients/_demo-barber/site/` (content.yaml, generated site.config.json, template copy, audit-2026-11-08.json/.md),
  log.md; DECISIONS, PROJECT_STATUS.
- Commands run (with real results):
  - `uv run pytest -q`: `158 passed in 6.79s`
  - `uv run python tools/build_site_config.py --client _demo-barber`: `wrote clients/_demo-barber/site/site.config.json (2 service page(s), SYNTHETIC)`
    (first attempt refused: lint flagged "Demo Fade Co. (fictional), Bradford" in the contact title → reworded)
  - `cd clients/_demo-barber/site && npm install && npm run build`: `5 page(s) built … Complete!`
  - Build determinism: 3 builds (incl. clean dist) → identical digest `2aedef4e…6eb0`
  - `uv run python tools/site_check.py --client _demo-barber --local --date 2026-11-08`: 11 PASS, 1 UNKNOWN (performance_lcp), `0 must-pass failure(s)`
  - Screenshots of home (desktop) and skin-fade page (mobile) checked via a local preview server.
- Stubbed / not working: LCP not measured (needs a public preview + PAGESPEED_API_KEY). Wrangler flags and
  the no-key Maps embed URL are unverified. The publish script has never run against Cloudflare (only its
  refusal paths are tested). No OSM/Lighthouse.
- Next: B07 (Canadian citations list + nap_check).

## 2026-11-04 · Claude cloud · Claude Code · B07 citations + NAP checker

- Files changed: `knowledge/citations-canada.csv` (new), `tools/nap_check.py` (new), `agents/citation.md`,
  `tests/test_nap_check.py`, demo `clients/_demo-barber/citations/{found.csv,nap-report.md,plan.csv}`, log.md,
  DECISIONS, PROJECT_STATUS.
- Commands run (with real results):
  - WebFetch businessconnect.apple.com / bingplaces.com / yellowpages.ca / homestars.com: all `getaddrinfo ENOTFOUND` (blocked); stopped trying.
  - WebSearch ×4 to confirm current names/URLs (findings in the CSV notes + DECISIONS).
  - `uv run python tools/nap_check.py --client _demo-barber --date 2026-11-09`: correct 3, wrong 3, duplicate 1, missing 8; exit 1 (mismatches present, as designed)
  - `uv run pytest -q`: `174 passed in 7.40s`
- Stubbed / not working: no directory URL was loaded; `checked_on` is blank for all rows.
- Next: B08 (reviews, content, links, QR card). Needs a decision on link-prospector web access first (DECISIONS open question).

## 2026-11-04 · Claude cloud · Claude Code · web-access decision + B08 reviews, content, links

- Decision (operator): read-only web access for link-prospector only, with limits → AGENTS.md rule 8,
  agents/link-prospector.md, wrapper (still no Bash), DECISIONS (closes the open question). Separate commit.
- Note: PR #8 was still open when the operator said it was merged. I merged it (`c16b5de`) before starting.
- Files changed (B08): `tools/review_card.py`, `tools/review_velocity.py`, `templates/review-card/card.yaml`,
  `templates/messages/*`, `schemas/velocity.schema.json`, `tools/validate.py` (velocity + prospects.csv rules),
  `agents/review-engine.md` (reply guidance), `pyproject.toml`/`uv.lock` (+zxing-cpp dev), docs/06, tests
  `test_reviews_content.py`; demo `reviews/{inbox.md, request-kit/*, replies/2026-11-11.md, velocity.json,
  compliance/*-2026-11-11.md}`, `content/2026-11/{posts,photos}.md`, `links/prospects.csv`, 3 approvals, log.md.
- Commands run (with real results):
  - `uv run python tools/review_card.py --client _demo-barber --link https://g.page/r/EXAMPLE/review`: first run refused
    (lint flagged the counter script's own "don't offer discount/free/draw" list) → reworded → 4 card files + messages.md;
    QR decodes to the link on both cards; digest stable across runs `a07f6cdf…c110` (after pinning the PDF dates)
  - `uv run python tools/review_velocity.py --client _demo-barber`: 18 → 24 → 30, overall 4.42/week
  - lint_claims on replies: first `FLAGS: 2` (operator note quoted "free cut") → note moved to log.md → PASS; posts/photos/prospects PASS
  - `approvals.py request` ×3: A2026-11-11-review-kit (owner approval required), -review-reply, -post-publish
  - `uv run pytest -q`: `186 passed in 10.84s`; `validate.py clients/_demo-barber`: `OK … 25 file(s) checked, 0 errors`
- Stubbed / not working: demo prospects fictional/unverified; CASL wording is not legal advice; compliance is self-review.
- Next: B09 (report template, check_report_numbers, make_sprint, /sprint orchestrator).
