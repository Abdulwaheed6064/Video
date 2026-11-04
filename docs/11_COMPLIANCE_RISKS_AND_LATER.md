# Compliance, risks and what comes later

Not legal advice. Before signing your first paying client, have an Ontario lawyer review your client
agreement and your guarantee wording once, and an accountant confirm registration and HST.

## 1. Google rules that matter most

| Source (check current versions) | What it means for you |
| --- | --- |
| Guidelines for representing your business on Google | Real name, real address, correct storefront vs service-area setup, no keyword stuffing |
| Maps user-contributed content policy | No fake, incentivised or selectively solicited reviews; no conflicts of interest (staff/owner reviews) |
| Google Search spam policies | No doorway pages, scaled low-value content, link schemes |
| Google's "Do you need an SEO?" guidance | Says no one can guarantee a #1 ranking — expect informed clients to know this |
| Google Business Profile API policies (later) | Specific, express user consent for automated actions; access approval required |

Keep a copy of the current versions' key points in `knowledge/ranking-rules.md` and refresh quarterly.

## 2. Canadian law touchpoints

| Area | Relevance | Your control |
| --- | --- | --- |
| **Competition Act** — misleading representations, including performance claims not based on adequate and proper testing | Your ranking promise; anything you write for clients ("#1 rated", "award-winning") | Use 01's measured promise; client claims only from verified facts; keep case-study evidence |
| Competition Act — fake/misleading reviews | Fake reviews are misleading advertising, not just a Google issue | review-engine hard limits |
| **CASL** (anti-spam) | Your own cold outreach by email/SMS to businesses; owners' review-request messages | Prefer in-person/phone outreach; for email, rely only on valid exceptions or consent and always identify yourself + unsubscribe; owner sends review requests to their own customers |
| **PIPEDA** | You hold owner contact details, review text, photos | Minimal data, private repo, delete on exit, no customer lists |
| Ontario consumer / contract basics | Refund terms, guarantee wording | Written agreement, exact guarantee option text |
| Pest control licensing (Ontario) | Licence claims on pages/GBP | Only show licence numbers the owner provides and you've verified |

## 3. Client agreement checklist

- Parties, start date, scope (01 §2 list), price, HST, payment schedule.
- The exact guarantee option text (A/B/C) and how it's measured (07 §3, grid parameters fixed at baseline).
- "Google controls rankings; we don't guarantee any position except as stated in the guarantee clause."
- Client responsibilities: Manager access, fact confirmation within 2 business days, asking every customer
  for reviews, sending photos.
- Ownership: client owns domain, GBP, content, photos; you own templates and tools.
- Prohibited requests: you won't do anything in 02 §4 even if asked.
- Cancellation, export and handover; data deletion within 30 days after exit.
- Permission (separate tick box) to use before/after as a case study.

## 4. Risk register

| Risk | Likelihood / impact | Mitigation | Trigger to act |
| --- | --- | --- | --- |
| Profile suspended after edits | Low–Med / Severe | Compliance gate, batched edits, no name/address games | Any suspension → stop all edits, follow Google reinstatement, tell owner same day |
| No movement in 20 days | Med / High | Qualify by competition; promise radius not city; option A guarantee | Day-10 scan flat → check edits live, indexing, category |
| Owner doesn't ask for reviews | High / High | QR card at the till, weekly nudge, count in report | < 3 reviews in first 2 weeks |
| Over-promising in sales | Med / High | Script in 12, guarantee wording fixed | Any "#1 guaranteed" phrasing in your materials |
| Monthly work creep | High / Med | 2-hour budget, written scope | 2 months over budget → reprice |
| Rank data cost/provider change | Low / Med | Adapter in rank_scan.py, cached raws | Price change > 50% |
| AI-written errors reach a client | Med / Med | Verified facts only, compliance agent, your approval | Any error → add a test case |
| Subscription usage limits slow you down | Med / Low | Scripts do the heavy work; small agent runs | Hitting limits weekly |
| Competitor spam outranks client | Med / Med | Report real violations via official channels (human only) | Obvious stuffed names in pack |
| Losing access (owner removes you) | Low / Med | Client owns everything; export on exit | — |

## 5. Stop / change rules

- After 10 sales conversations with no paid pilot → change niche or offer before building more.
- After 3 sprints, if fewer than 2 show clear movement on the target metric → revisit the playbook before
  selling more.
- If any client asks for a prohibited tactic → decline in writing; end the engagement if they insist.

## 6. Later (deliberately not built now)

| Later | Prerequisite | Notes |
| --- | --- | --- |
| **Google Ads / Local Services Ads** | 3+ happy SEO clients asking for faster leads; client-funded budget | Separate offer: setup + management fee; you never front ad spend. LSA ("Google Guaranteed/Screened") fits pest control and trades. Add an `ads-*` agent set with hard spend approvals |
| GBP API automation (posts, replies, edits) | Google API access approval; profiles active 60+ days | Replaces "you apply in the UI" with an approved script; approval gate stays |
| Review-request automation | Owner's booking/POS system integration | Must send to every customer, no gating |
| Multi-location clients | Repeatable single-location results | One grid per location |
| Hosted dashboard for clients | > 10 clients, frequent "how are we doing?" questions | Files in 06 map to tables |
| Apple Maps / Bing deep optimisation | Clients asking | Citation agent already covers basics |
