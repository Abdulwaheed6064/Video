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

## 2026-11-04 — B00: tool formats verified against official docs

Checked 2026-11-04 (Claude Code cloud session):

- Claude Code subagents: https://code.claude.com/docs/en/sub-agents. Frontmatter `name` + `description`
  are required; `tools` (comma list) and `model` (`sonnet`/`opus`/`haiku`/`fable`/full id/`inherit`) are
  optional. Our 14 wrappers are valid as written, so nothing changed.
- Slash commands: https://code.claude.com/docs/en/slash-commands. "Custom commands have been merged
  into skills." `.claude/commands/*.md` still works; `.claude/skills/<name>/SKILL.md` is preferred for
  new work. `description`, `argument-hint` and `$ARGUMENTS` still work. Decision: keep the command
  files as they are, because they already work and stay thin wrappers over `prompts/`. Moving them to
  skills is optional and not needed now.
- CLAUDE.md imports: https://code.claude.com/docs/en/memory. `@path` imports are supported, and
  `@AGENTS.md` in CLAUDE.md is the documented way to share one file. Claude Code also reads AGENTS.md
  natively, but only when there's no CLAUDE.md, so keep the import.
- Permissions: https://code.claude.com/docs/en/permissions and https://code.claude.com/docs/en/settings.
  `Bash(cmd *)` (space + trailing `*`; legacy `:*` is equivalent), `Read(./.env)` path rules and
  `deny` lists match our template. Added `$schema`. Cloud sessions read the committed
  `.claude/settings.json` for single-repo sessions.
- Codex (AGENTS.md discovery, `codex exec`, project prompts/skills): **NOT verified**. The official
  docs are on developers.openai.com, which this cloud session's network blocks. The
  github.com/openai/codex/docs files only point there. Third-party sources say project skills live
  in `.agents/skills/` and custom prompts in `~/.codex/prompts/` (user level only), but that is
  unconfirmed. Codex keeps using "Follow prompts/<name>.md with ARGS = …", which works either way.
  **Open question:** re-check from a local machine before the first Codex step (B06).

## 2026-11-04 — B00: `.claude/settings.json` installed without the `git push` deny

Decision: Installed `templates/claude/settings.json` as `.claude/settings.json` (template updated to
match) but removed `Bash(git push*)` from `deny`. The operator approved this.
Reason: The build runs in cloud sessions that must push their `claude/*` branch for a PR. Deploys stay
denied (`Bash(*deploy*)`), and `.env`, `curl` and `wget` are still denied. docs/09 §6 still shows the
old shape and is reference only.

## 2026-11-04 — B00: `synthetic: true` key on demo client YAML files

Decision: `clients/_demo-barber/client.yaml` and `facts.yaml` carry a top-level `synthetic: true`
(docs/06 §2–3 don't list it). B01 schemas must allow an optional boolean `synthetic` on these files.
Reason: B00 requires every demo file to be marked synthetic, and a machine-readable flag is safer than
a comment alone.

## 2026-11-04 — B01: contracts, validator, approvals, budget

- **Schemas** are JSON Schema 2020-12 in `schemas/*.schema.json`. YAML is loaded with dates kept as
  strings (`tools/common.py`), so YAML and JSON validate the same way (`format: date`).
- **Approval actions:** added `review_kit` (gate G3) and `report_send` (gate G7) to the docs/06 §7
  enum. docs/13 §6 has those gates but the enum had no action for them, while review-engine and
  reporter both "request approval". docs/06, review-engine and reporter are updated to match.
- **Owner approval default per action** (overridable with `--owner-required yes|no`): required for
  `gbp_apply_batch`, `site_deploy` and `review_kit`; not required for the others (docs/13 §6).
- **Compliance report format:** YAML front matter `result / sha256 / file / date / reviewer` plus one
  `RESULT: PASS|FAIL` line in the body that must match. approvals.py refuses `request` unless a PASS
  report exists for that exact digest and file. agents/compliance-reviewer.md is updated.
- **Scan folders are `scans/<label>/`** (baseline, mid, final, YYYY-MM-DD, m<YYYY-MM>), not
  `scans/<date>/`. rank-tracker, keyword-competitor and docs/13 already used labels; docs/04 and
  docs/06 now match.
- **Directory artifacts** (e.g. `reviews/request-kit/`, a site build) are hashed as a tree:
  SHA-256 over sorted `relpath\0sha256(file)` lines.
- **consume records:** `gbp_apply_batch` → `gbp/applied.log` (TSV: time, id, artifact, digest, field,
  by); `site_deploy` → `site/deploy-receipt-<id>.yaml`; other actions → `applied_fields` in the
  approval file itself.
- **Budget:** caps are monthly in CAD. Ledger costs are USD, converted with `budget/config.yaml →
  usd_to_cad`. That rate is a **placeholder (1.40, `rate_confirmed: false`)**; the operator must confirm it.
  If `GLOBAL_BUDGET_CAD_MONTH` is unset, every paid call is refused (fail closed). budget.py reads
  only that one key from `.env`, and only when it is not already in the environment. An estimate of 0
  always passes; fixture clients have a CA$0 cap.
- **New optional client.yaml keys:** `synthetic`, `site_url` (site-auditor reads "live URL from
  client.yaml" but no key existed), `scan.depth`.
- **Validator layout rule:** only the docs/06 §1 files and folders may sit at the top level of a client
  folder (`.gitkeep`, `.DS_Store` and `Thumbs.db` are ignored).
- **Settings side effect:** the `Bash(*deploy*)` deny rule blocks one-line shell commands that contain
  "deploy" (seen: `echo "deploy test"` denied), so commit messages must avoid the word. Observed gap:
  a multi-line heredoc containing the word was *not* blocked, so treat the rule as a guard rail, not a
  lock. Deploys stay manual and approval-gated (docs/13 §6); B06's deploy script should check
  `approvals.py verify` itself.

## 2026-11-04 — OPEN QUESTION: link-prospector web access vs "only tools/ make network calls"

AGENTS.md says only `tools/` scripts make network calls. But `.claude/agents/link-prospector.md` grants
WebSearch/WebFetch, agents/link-prospector.md says "verify each URL loads", and docs/13 §7 says it
"needs web research". These contradict, and B01 doesn't resolve it.
Options: (a) allow free, read-only web research for link-prospector only, written into AGENTS.md
rule 8 as an exception; (b) add a `tools/url_check.py` script and drop WebFetch from the wrapper.
Operator to decide before B08.
