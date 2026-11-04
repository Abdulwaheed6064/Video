# Prompts (shared by Codex and Claude Code)

Each file is the single source for one repeatable command. Claude Code's `.claude/commands/<name>.md`
just points here. In **Codex**, paste the file's text (or say "Follow prompts/<name>.md with
ARGS = ...") — replace `$ARGUMENTS` with your arguments.

| File | Claude Code | Codex |
| --- | --- | --- |
| build.md | `/build B03` | "Follow prompts/build.md with ARGS = B03" |
| status.md | `/status <slug>` | "Follow prompts/status.md with ARGS = <slug>" |
| sprint.md | `/sprint <slug> <day>` | "Follow prompts/sprint.md with ARGS = <slug> <day>" |
| scan.md | `/scan <slug> <label>` | … |
| report.md | `/report <slug> [label]` | … |
| audit-prospect.md | `/audit-prospect "<business>" <town> "<keyword>"` | … |
| review-compliance.md | `/review-compliance <slug> <file>` | … |

Codex difference: Codex has no subagents here. Wherever a prompt says "delegate to subagent X", Codex
reads `agents/X.md` and performs that job itself, one agent at a time, writing outputs before moving on.
