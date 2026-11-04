# Maps Rank Studio

A one-person local-SEO service, run by AI agents inside VS Code, that gets small local businesses
(barbers, pest control, salons, trades) into the **Google Maps 3-pack** and higher in **Google Search**
for "service + town" searches like `barber shop bradford` or `pest control newmarket`.

- **Scope now:** Google Business Profile + website + citations + reviews + rank tracking. **SEO only.**
- **Not now:** Google Ads / Local Services Ads (planned add-on, see `docs/11` §6).
- **Runtime:** Claude Code and Codex in VS Code on your subscriptions. No server, no database,
  no API-billed LLM. Python scripts do every measurement. The repo is the memory.

---

## Open this first

| If you want to… | Open |
| --- | --- |
| Understand the whole system in 10 minutes | [docs/13_ORCHESTRATION_DESIGN.md](docs/13_ORCHESTRATION_DESIGN.md) |
| **Start building (step by step)** | [build/README.md](build/README.md) → then `build/B00_bootstrap.md` |
| Spend your Claude cloud credits well | [docs/14_CLOUD_CREDITS_AND_USAGE.md](docs/14_CLOUD_CREDITS_AND_USAGE.md) |
| Know what you can promise a client | [docs/01_OFFER_PROMISE_AND_PRICING.md](docs/01_OFFER_PROMISE_AND_PRICING.md) |
| Know what the agents may never do | [knowledge/ranking-rules.md](knowledge/ranking-rules.md) |
| See every agent's job | [agents/](agents/) (canonical specs) |
| Run a client sprint (after build) | `/sprint <slug> <day>` in Claude Code, or `prompts/sprint.md` in Codex |

## Folder map

```text
maps-rank-studio/
├── README.md               ← you are here
├── AGENTS.md               ← rules every AI agent follows (Codex reads this; Claude imports it)
├── CLAUDE.md               ← Claude Code project file (imports AGENTS.md)
├── PROJECT_STATUS.md       ← what's built / stubbed / next  (agents update it)
├── DECISIONS.md            ← dated decisions + verified doc links
├── SESSION_LOG.md          ← one entry per AI session
├── docs/                   ← the design pack (00–14)
├── build/                  ← B00–B11: one markdown file per build step → paste into Claude Code / Codex
├── agents/                 ← 14 canonical agent specs (tool-agnostic)
├── .claude/agents/         ← thin Claude Code subagent wrappers → agents/*.md
├── .claude/commands/       ← /sprint /status /scan /report /audit-prospect /review-compliance /build
├── prompts/                ← the same commands as plain prompts for Codex
├── knowledge/              ← ranking rules, niche playbooks, category notes, directory list
├── tools/  schemas/  templates/  tests/  budget/   ← built during B00–B09
└── clients/                ← one folder per client (private; created per client)
```

## The 3 rules that make this safe

1. **Agents propose, scripts measure, you approve, you publish.** No agent touches a live Google profile,
   website or directory.
2. **Numbers only from scripts.** Ranks, review counts and percentages come from `tools/` output files.
3. **Hard limits are absolute.** No keyword-stuffed names, fake addresses, fake/incentivised/gated reviews,
   doorway pages, bought links or click manipulation — these get profiles suspended.
