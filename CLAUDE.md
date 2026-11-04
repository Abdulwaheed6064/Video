@AGENTS.md

## Claude Code specifics

- Subagents in `.claude/agents/` are thin wrappers over `agents/*.md`. Change behaviour in `agents/`, not
  in the wrapper.
- Slash commands (`.claude/commands/`) are thin wrappers over `prompts/*.md`, which Codex also uses:
  - `/build B03` — run one build step from `build/`
  - `/status <slug>` — where a client is, what's waiting on the human
  - `/sprint <slug> <day>` — run the orchestrator for one sprint day
  - `/scan <slug> <label>` — run a grid scan (fixture or capped live)
  - `/report <slug>` — sprint or monthly report
  - `/audit-prospect <business> <town> <keyword>` — free sales rank-map audit
  - `/review-compliance <slug> <file>` — independent compliance check of one proposal
- Tests: `uv run pytest -q`. Validation: `uv run python tools/validate.py clients/<slug>`.
- Prefer small, verifiable steps. Show diffs of any client-facing text before finishing.
- When delegating to a subagent, pass the client slug and the exact task id from `tasks.json`.
