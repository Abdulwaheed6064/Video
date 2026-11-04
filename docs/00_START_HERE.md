# Maps Rank Studio — start here

Version 2.0 · 3 November 2026 · Replaces the "Local Growth Studio" draft (v1.0, 13 Sep 2026)
Market: Ontario, Canada — starting with the Newmarket / Bradford / Aurora / York Region / north GTA belt.

## What this is

A one-person local-SEO service, run by AI agents inside VS Code, that gets small local businesses
(barbers, pest control, salons, trades) ranking higher in **Google Maps (the local 3-pack)** and
**Google Search** for "service + town" searches such as `barber shop bradford` or `pest control newmarket`.

The agents are not a hosted SaaS. They are prompt files + small scripts in one Git repository that you
run with your **Claude Code** and **Codex** subscriptions. Each client is a folder. Each step of the work
is an agent with a fixed job, fixed inputs, fixed outputs and a human approval gate before anything
touches the client's real Google profile or website.

## What changed from the old draft

| Old draft | This version |
| --- | --- |
| Electrical contractors, Birmingham UK, GBP pricing | Barbers / pest control / local trades, Ontario, CAD pricing |
| Website + enquiry capture + monthly report as the product | **Google Maps + Google Search ranking** as the product; website only as a ranking asset |
| Runtime app on Cloudflare Workers + Supabase + Resend + Anthropic API | **No runtime app.** Agents run in VS Code on your subscriptions; deterministic Python scripts; files in Git |
| Operator console, tenant DB, outbox, webhooks | Folder per client, JSON/YAML state, approval files |
| UK GDPR / ICO | PIPEDA, CASL, Competition Act (Canada) |
| Google Ads mentioned in the capability map | **Removed.** Ads is a later add-on (see 11) |

Kept from the old draft because they were right: verified facts only, no invented claims, approval before
anything public, separate test vs real client work, budgets and session logs, honest reporting.

## The selling promise — read 01 before you pitch anyone

Your draft promise is: *"Within 20 days I will bring your business to the top of Google Maps — when anyone
searches 'pest in Toronto' your name comes first."*

Do not sell it in that form. Three reasons, all covered in 01:

1. **It is not technically true for "anyone".** Maps results depend on where the searcher is standing.
   A pest company in Scarborough cannot be #1 for a searcher in Etobicoke, no matter what you do.
2. **Google itself says no one can guarantee a #1 ranking**, and its "hiring an SEO" guidance tells
   business owners to treat that promise as a red flag. Savvy owners have heard it from scam agencies.
3. **In Canada, the Competition Act restricts performance claims that aren't based on adequate testing.**
   Until you have your own before/after case studies, a hard ranking guarantee is a legal and refund risk.

01 gives you a sharper promise that is still bold, is measurable, and you can actually keep:
*"In 20 days your Google profile and site are fully fixed, and I'll show you a before/after map of exactly
where you rank around your shop. Target: top 3 within [X] km for your main searches — if we don't move,
your first month is free."*

## Reading order

| File | What it gives you |
| --- | --- |
| [01_OFFER_PROMISE_AND_PRICING.md](01_OFFER_PROMISE_AND_PRICING.md) | The promise, qualification, guarantee design, pricing |
| [02_HOW_GOOGLE_LOCAL_RANKING_WORKS.md](02_HOW_GOOGLE_LOCAL_RANKING_WORKS.md) | Ranking levers, what's allowed, what gets profiles suspended |
| [03_SYSTEM_ARCHITECTURE.md](03_SYSTEM_ARCHITECTURE.md) | Repo layout, how agents/scripts/files fit, modes, gates |
| [04_AGENT_ROSTER.md](04_AGENT_ROSTER.md) | Every agent: job, inputs, outputs, tools, guardrails, done-criteria |
| [05_20_DAY_SPRINT_PLAYBOOK.md](05_20_DAY_SPRINT_PLAYBOOK.md) | Day-by-day plan for one client |
| [06_DATA_CONTRACTS.md](06_DATA_CONTRACTS.md) | Exact file formats every agent reads and writes |
| [07_RANK_TRACKING_AND_REPORTING.md](07_RANK_TRACKING_AND_REPORTING.md) | Grid rank tracking, metrics, the client report |
| [08_TOOLS_SERVICES_AND_BUDGET.md](08_TOOLS_SERVICES_AND_BUDGET.md) | Paid/free services, CAD cost model, unit economics |
| [09_CLAUDE_CODE_AND_CODEX_SETUP.md](09_CLAUDE_CODE_AND_CODEX_SETUP.md) | CLAUDE.md, AGENTS.md, agent wrapper templates, how to run both tools |
| [10_BUILD_PLAN_FOR_CLAUDE_CODE.md](10_BUILD_PLAN_FOR_CLAUDE_CODE.md) | Pointer to `build/` — the B00–B11 step files you run |
| [11_COMPLIANCE_RISKS_AND_LATER.md](11_COMPLIANCE_RISKS_AND_LATER.md) | Google policies, Canadian law, risk register, Ads later |
| [12_SALES_AND_ONBOARDING.md](12_SALES_AND_ONBOARDING.md) | Finding clients, the pitch, access, onboarding checklist |
| [13_ORCHESTRATION_DESIGN.md](13_ORCHESTRATION_DESIGN.md) | **How the agents run together**: layers, dependency graph, task state machine, gates, which tool runs what |
| [14_CLOUD_CREDITS_AND_USAGE.md](14_CLOUD_CREDITS_AND_USAGE.md) | Subscriptions vs Claude cloud credits; which build steps to run in the cloud |

## How to use this pack with Claude Code / Codex

The repo is already laid out (docs are in `docs/`, agents in `agents/`, rules in `AGENTS.md`).

1. Open the `maps-rank-studio/` folder in VS Code.
2. Read `docs/13_ORCHESTRATION_DESIGN.md` once — it is the map of the whole system.
3. Run the build steps in `build/` in order: in Claude Code type `/build B00`; in Codex say
   `Follow prompts/build.md with ARGS = B00`. One step per session.
4. Each step ends by updating `PROJECT_STATUS.md` and `SESSION_LOG.md` and committing.
5. Switch freely between Claude Code and Codex — the repository, not the chat, holds the state.
6. Before your first paying client, run the whole pipeline on **your own test business or a friend's
   business with written permission** (B10). Never practise on a fake Google Business Profile.

## First 30 days at a glance

| Week | You | Agents |
| --- | --- | --- |
| 1 | Set up repo, DataForSEO account, read 02 | B00–B03: skeleton, client schema, rank-grid scanner |
| 2 | Pick 1 friendly pilot business (free or cheap) | B04–B07: competitor, GBP audit, site, citations agents |
| 3 | Run the 20-day sprint on the pilot | B08–B09: reviews, reporter, orchestrator `/sprint` |
| 4 | Pitch 10 local businesses with the pilot's before/after map | B10–B11: dry run, audit, fixes |
