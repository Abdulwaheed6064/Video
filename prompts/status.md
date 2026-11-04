# Client status

ARGS: $ARGUMENTS   (client slug)

Read-only. For `clients/<slug>/`:
1. `uv run python tools/validate.py clients/<slug>` — report pass/fail.
2. From client.yaml: mode, niche, business_type, target, sprint start date → today's sprint day.
3. From tasks.json: counts by status; list every `awaiting_approval` (with approval id and exact human
   steps) and every `blocked` (reason + human_action).
4. Open questions in questions.md.
5. Latest scan label and headline metrics from its metrics.json (copy numbers, don't compute).
6. Budget used this month: `uv run python tools/budget.py report <slug>`.
Print a short status board. Change no files.
