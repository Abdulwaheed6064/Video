# Decisions

Dated, append-only. Format: `## YYYY-MM-DD — title` then decision, reason, alternatives rejected.

## 2026-11-03 — Scope is Google Maps + Google Search SEO only

Decision: The product is ranking in the Google Maps 3-pack and organic Google Search for service + town
searches. Google Ads / Local Services Ads are out of scope until 3+ SEO clients ask for faster leads
(docs/11 §6).
Reason: Operator's selling point is Maps ranking; Ads needs client-funded spend and a separate agent set.

## 2026-11-03 — Repo layout: canonical specs + thin wrappers

Decision: Agent behaviour lives once in `agents/*.md`. Claude Code wrappers (`.claude/agents/`) and
commands (`.claude/commands/`) only point at `agents/` and `prompts/`. Codex reads `AGENTS.md`,
`agents/` and `prompts/` directly.
Reason: Both tools must run the same agents without drift.

## 2026-11-03 — The selling promise

Decision: Sell "everything Google looks at fixed in 20 days + before/after rank map; target top 3 within
[radius] km for 2–3 main searches; movement guarantee (option A)". Never "#1 guaranteed" or "everyone in
Toronto". See docs/01.
Reason: Maps ranking depends on searcher location; Google states nobody can guarantee #1; Competition Act
risk on unsubstantiated performance claims.

## 2026-11-03 — Planning-time assumptions to verify in B00

- Claude Code: `.claude/agents/*.md` frontmatter (`name`, `description`, `tools`, `model`),
  `.claude/commands/*.md` with `$ARGUMENTS`, `CLAUDE.md` `@import`, `.claude/settings.json`
  permissions allow/deny syntax. Skills (`.claude/skills/`) may be the preferred form now — check.
- Codex: reads `AGENTS.md`; non-interactive `codex exec`; whether project-level custom prompts are
  supported (else paste `prompts/*.md`).
- B00 must confirm each against current official docs and record links + date below.
