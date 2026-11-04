# B09 — Reporter + orchestrator (/sprint)

Read first: `build/README.md`, `docs/05`, `docs/07` §5–7, `docs/13` (all), `agents/orchestrator.md`,
`agents/reporter.md`, `prompts/sprint.md`.
Where: local or cloud. Suggested: Claude Code with a strong model. Paid calls: none.

## Do

1. **`templates/report/report.html`** + **`tools/render_report.py --client <slug> --label <label>`** →
   HTML (and PDF if a headless browser / weasyprint is available; otherwise document how). Sections per
   docs/07 §5. SYNTHETIC banner on every page and image in fixture mode. Before/after heatmaps side by side.
2. **`tools/check_report_numbers.py <report.html> --client <slug>`** — extracts every number from the
   report text and fails if any is not traceable to `metrics.json`, `velocity.json`, `tasks.json` counts
   or dates in `log.md` (allowlist for grid size/years in dates).
3. **`tools/make_sprint.py <slug> --start YYYY-MM-DD [--monthly YYYY-MM]`** — generates `sprint.json` and
   `tasks.json` from docs/05 (and docs/13 §3 dependency graph): task ids `T<day>-<n>`, agent, depends_on,
   inputs, outputs, `requires_approval`, human tasks (`agent: human`) for every gate in docs/13 §6.
4. **`tools/tasks.py`** — small helper the orchestrator uses: `due <slug> <day>`, `set <slug> <task> <status>
   [--reason --human-action]`, `todo <slug>` (prints the DONE / WAITING FOR YOU / BLOCKED board). Enforces
   the state machine in docs/13 §4 (illegal transitions rejected; only `--by-human` can leave
   awaiting_approval).
5. Check `agents/orchestrator.md`, `prompts/sprint.md`, `prompts/status.md`, `prompts/scan.md`,
   `prompts/report.md` against the real scripts and fix commands/paths.
6. **Full fixture sprint for the demo**: days 0, 1, 2, 3, 7, 10, 14, 20 using fixture scans, simulating the
   human gates with `tasks.py set --by-human` and `approvals.py approve/consume`. Produce the final
   report with SYNTHETIC banner. Print the to-do board after each day into `SESSION_LOG.md`.

## Tests

check_report_numbers fails on an injected number · make_sprint produces valid tasks.json with no cycles ·
tasks.py rejects pending→applied and agent-side approval exits · "from 0 to N" rendering when baseline 0.

## Verify

```bash
uv run pytest -q
uv run python tools/make_sprint.py _demo-barber --start 2026-11-10
uv run python tools/tasks.py todo _demo-barber
uv run python tools/check_report_numbers.py clients/_demo-barber/reports/<date>/report.html --client _demo-barber
```

## Done when

`/sprint _demo-barber <day>` works end to end in fixture mode; final report passes the number check; commit.
