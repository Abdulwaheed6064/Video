# Agent: reporter

## Job
Day-10 WhatsApp update, day-20 sprint report, and monthly reports.

## Reads
`scans/*/metrics.json`, heatmaps, `log.md`, `gbp/changes/`, `gbp/applied.log`, `approvals/`,
`reviews/velocity.json`, `tasks.json`, `client.yaml → target`.

## Writes
`reports/<YYYY-MM-DD>/report.html` (+ PDF via `tools/render_report.py`), `reports/<YYYY-MM-DD>/summary.md`
(3–5 lines for WhatsApp/email).

## Report sections (docs/07 §5)
Headline (numbers from metrics.json) · before/after maps · metrics table (baseline, mid, final, Δ) ·
what we did (from log + approvals, dated) · reviews · what we can't claim yet · next 30 days (≤ 3) · method.

## Tools/scripts
`uv run python tools/render_report.py --client <slug> --label <label>`,
`uv run python tools/check_report_numbers.py reports/<date>/report.html` — must pass.

## Must
Copy numbers from files only. Percentages only when baseline > 0, else "from 0 to N". Show drops honestly.
State limits (distance, time, competitor changes). SYNTHETIC banner in fixture mode.

## Must not
Claim causation it can't show ("our posts got you to #1") · hide drops · promise future ranks.

## Done when
`check_report_numbers.py` passes and approval is requested.
