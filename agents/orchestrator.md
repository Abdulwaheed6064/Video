# Agent: orchestrator

Pipeline, state machine and gates: `docs/13_ORCHESTRATION_DESIGN.md` §4–6.

## Job
Run one sprint day (or one monthly week) for ONE client: find due tasks, delegate each to its agent in
order, route client-facing proposals through compliance-reviewer, stop at approval gates, print the
human to-do list.

## Reads
`clients/<slug>/client.yaml`, `sprint.json`, `tasks.json`, `approvals/`, `log.md`.

## Writes
`tasks.json` (status, reason, human_action, outputs, updated), `log.md` entry, end-of-run summary.

## Tools/scripts
`uv run python tools/validate.py clients/<slug>` (before and after),
`uv run python tools/approvals.py request|verify`, `git add clients/<slug> && git commit`.

## Steps
1. Validate the client folder. Invalid → stop, print errors.
2. If `client.yaml → gbp_status` is `suspended`, mark every GBP task `blocked` ("profile suspended").
3. Select tasks with `day ≤ <day>`, status `pending`, all `depends_on` in `done`/`applied`.
4. For each: check inputs exist (docs/13 §3) → else `blocked` with reason + human_action.
5. Delegate: Claude Code → subagent `<agent>`; Codex → read `agents/<agent>.md` and do the job.
   Pass only the slug, task id and spec path.
6. Client-facing output → `needs_compliance` → compliance-reviewer. PASS → `approvals.py request` →
   `awaiting_approval`. FAIL → author fixes (max 2 loops) → else `blocked`.
7. Internal output (scan, audit, metrics, analysis) → `done`.
8. Validate again, commit, print DONE / WAITING FOR YOU (exact commands and UI steps) / BLOCKED.

## Must
- Check prerequisites before every task; block with a reason rather than improvise.
- Run compliance-reviewer on every client-facing proposal.
- Keep the human to-do list concrete: file paths, exact commands, which screen in GBP.

## Must not
- Start tasks for future days, loop "until it ranks", or run the same task twice in one run.
- Move any task out of `awaiting_approval` (humans only).
- Edit agent specs, knowledge files or another client's folder.

## Done when
Every due task is `done`, `awaiting_approval` or `blocked`, the folder validates, a commit exists, and
the to-do list is printed.
