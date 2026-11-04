# Run one sprint day

ARGS: $ARGUMENTS   (format: `<slug> <day>` — day is 0–20, or `m<YYYY-MM>-w<1-4>` for monthly)

Follow `agents/orchestrator.md` and `docs/13_ORCHESTRATION_DESIGN.md` §4–5.
1. `uv run python tools/validate.py clients/<slug>` — stop if invalid.
2. Select tasks in tasks.json with day ≤ <day>, status pending, dependencies done/applied.
3. For each task in order, check inputs, then:
   - Claude Code: delegate to the subagent named in the task's `agent` field.
   - Codex: read `agents/<agent>.md` and do that job yourself, one at a time.
4. Send every client-facing proposal through compliance-reviewer (prefer the other tool). PASS →
   `uv run python tools/approvals.py request ...` → awaiting_approval. FAIL → fix ≤ 2 times → blocked.
5. Stop at approval gates. Never start future days. Never apply external changes.
6. Validate again, append log.md, commit `<slug> day <day>`.
7. Print: DONE / WAITING FOR YOU (exact commands + GBP UI steps) / BLOCKED (reason + human action).
