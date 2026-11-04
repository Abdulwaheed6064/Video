# 20-day sprint playbook (one client)

Calendar days, starting the day access is granted. `sprint.json` in the client folder is generated from
this table by B09 and drives the orchestrator.

Legend: 🤖 agent work · 🧑 your work · 👤 owner work · ✅ approval gate

## Day 0 — onboarding call (45 min)

- 👤 Owner grants **Manager** access to the Google Business Profile (Google sends you an invite;
  never accept passwords). Also: domain/website access or hosting login via their own account invite,
  Search Console access (or you set it up with their account).
- 🧑 Fill `intake/questionnaire.md` with owner: services, prices policy (show or not), hours, real address,
  storefront vs service-area, service towns, years in business, licences (pest control: Ontario structural
  exterminator licence numbers if they want them shown — verify), booking system, photos available.
- 🤖 **intake** → `client.yaml`, `facts.yaml` (proposed), `access.md`, `questions.md`.
- 👤 Owner confirms facts (send the 1-page fact sheet; they reply "confirmed" or correct). ✅ facts verified.

## Day 1 — baseline

- 🤖 **rank-tracker**: baseline 7×7 grid scan for 3–5 candidate keywords + organic positions from the shop
  location and town centre. Save heatmaps. *This is your "before" picture — never skip it.*
- 🤖 **keyword-competitor**: final `keywords.json`, `competitors.json`, `gap-analysis.md`, recommended radius.
- 🧑 Read gap analysis; set the stated target in `client.yaml` (`target: top3 within 3 km for 2 keywords`).

## Day 2 — Google profile batch

- 🧑 Copy the current GBP state into `gbp/current.yaml` (or fill from scan data; 10 minutes).
- 🤖 **gbp-auditor** → `gbp/audit.md`.
- 🤖 **gbp-optimizer** → `gbp/changes/<date>-batch.yaml`, description options, services, Q&A seed, photo list.
- 🤖 **compliance-reviewer** → PASS required.
- ✅ Owner approves description and anything customer-facing; you approve the batch.
- 🧑 Apply the batch in the GBP UI in one sitting. Record each applied field in `gbp/applied.log`
  (`tools/approvals.py consume`). Screenshot before/after.

## Days 3–7 — website + review system

- 🤖 **site-builder**: home + main service pages (or fix list for existing site). Local schema, NAP, map, CTA.
- 🤖 **site-auditor**: speed/mobile/schema/indexability. Fix until green on the must-pass list.
- ✅ Owner approves copy & photos; you approve the deploy.
- 🧑 Deploy (`tools/deploy.sh`), point GBP website link to the right page with UTM
  (`?utm_source=google&utm_medium=organic&utm_campaign=gbp`), submit sitemap in Search Console,
  request indexing for the new pages.
- 🤖 **review-engine**: request kit (QR card PDF, text template, counter sign). 🧑 drop off printed cards.
- 👤 Owner starts asking **every** customer. Target: steady flow, not a spike.

## Days 4–10 — citations

- 🤖 **citation**: `citations/plan.csv` (fix wrong first, then add missing; top ~15 only).
- 🧑/👤 Apply. Apple Business Connect and Bing Places first (Bing can import from Google).
- 🤖 `nap_check.py` re-run on day 10.

## Day 7 — first content + quick check

- 🤖 **content**: first 2 GBP posts + photo shot-list. 👤 owner sends 10+ real photos (shop, team, work).
- 🧑 Upload photos and posts.
- 🤖 **review-engine**: draft replies to all new reviews. 🧑 post replies.

## Day 10 — mid scan

- 🤖 **rank-tracker**: same grid, same keywords. 🤖 **reporter**: 5-line WhatsApp update for owner with
  before vs now heatmap for the main keyword.
- 🧑 If no movement at all: check edits went live (Google sometimes holds edits for review), check
  category, check the site is indexed. Don't start re-editing name/category in a panic.

## Day 14 — second content round

- 🤖 **content**: 2 more posts, Q&A additions. 🤖 **review-engine**: replies. 🧑 apply.

## Days 15–19 — tighten

- 🤖 **keyword-competitor**: re-run gap on the day-10 scan — what's still missing vs current top 3?
- 🤖 **site-builder**: one targeted improvement (e.g. FAQ section, service page depth).
- 🤖 **link-prospector**: first 10 real local opportunities. 🧑 pick 1–2 (chamber/BIA membership is a good
  default if affordable).

## Day 20 — final scan + report

- 🤖 **rank-tracker**: final scan, identical parameters to baseline.
- 🤖 **reporter**: sprint report (07) — before/after heatmaps, metrics table, everything delivered, what's
  next. ✅ You review every number against `metrics.json`.
- 🧑 15-minute review call; collect the second 50% of setup; start monthly plan. Ask permission to use the
  before/after as a case study (written).

## After day 20 — monthly cycle (≤ 2 h of your time per client)

| Week | Work |
| --- | --- |
| 1 | Grid scan + metrics; review replies |
| 2 | 2 posts + photo upload; 1 site/GBP improvement |
| 3 | Review replies; citation check; link opportunity |
| 4 | 2 posts; monthly report |

## Exit criteria for the sprint (what "delivered" means)

- [ ] GBP change batch applied and logged; every audit item pass or explained
- [ ] Site pages live, indexed request sent, schema valid, mobile LCP < 2.5 s
- [ ] Top ~15 citations correct
- [ ] Review kit in use; replies to all reviews in the period
- [ ] 4 posts + ≥ 10 new real photos
- [ ] Baseline, mid and final scans with identical parameters
- [ ] Report delivered with honest limits stated
