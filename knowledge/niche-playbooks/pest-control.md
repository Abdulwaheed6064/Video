# Niche playbook: pest control (service-area business)

> **Starting hypothesis: verify per client.** Everything below is a default to check against the client's
> verified facts, current regulations and their own scan data. It is not evidence and must never be quoted
> to a client as fact. Numbers in client-facing text come only from `tools/` outputs.

Written: 2026-11-04 (B04). Review quarterly; re-check the licence notes against the Ontario government
before any client-facing use.

## Business type and address rules

- Usually a **service-area business (SAB)**: technicians go to the customer. One profile, real base
  location, **address hidden**, service areas = towns actually served (ranking-rules hard limits 2, 3, 7, 8).
- A home-based operator must not show the home address. No virtual offices or mailbox addresses.
- Grid: centre = the hidden base coordinates; wider spacing (docs/07 §1: 1.5–3 km). Expect strength near
  the base and slower gains in far towns.

## Keyword patterns (pick 3–5; exactly one "near me")

| Pattern | Example | Use when |
| --- | --- | --- |
| pest control + town | `pest control newmarket` | Always a candidate |
| exterminator + town | `exterminator newmarket` | Common alternative wording; probe it |
| pest + removal/control + town | `mice removal aurora`, `rat control aurora`, `bed bug treatment newmarket`, `wasp nest removal aurora` | Only for **verified** services |
| pest control near me | `pest control near me` | The one "near me" variant |
| wildlife (raccoon/squirrel) | `raccoon removal newmarket` | Only if wildlife work is verified; wildlife and insects can be different businesses and categories |

## Categories (verify in the GBP category picker)

- Likely primary: **Pest control service**. Check what the top 3 use in `competitors.json`.
- Possible secondary, only if genuinely offered: Wildlife and animal control service (or similar picker
  wording), Exterminator (if present in the picker).

## Ontario licence notes (VERIFY before use, never assume)

- Commercial pest control in Ontario is regulated under the Pesticides Act and its regulation; applying
  structural pesticides commercially generally requires an exterminator licence and an operator licence
  for the business. Confirm the current rules and the licence holder's details with the owner and the
  Ontario government before mentioning licences anywhere.
- Licence numbers appear in client-facing text only as a verified `licence` fact (with source), and only if
  the owner wants them shown.

## Seasonal patterns (hypothesis; confirm with the owner and scan history)

- Spring/summer: ants, wasps, spiders, stinging insects. Late summer/fall: mice and rodents moving indoors.
  Bed bugs: year-round.
- Plan posts and service-page emphasis around the client's own seasonal job mix, not this list.

## Common gaps to check

| Gap | How we know | Owner |
| --- | --- | --- |
| Address shown for a home-based SAB | `gbp/current.yaml`, intake notes | gbp-optimizer (flag as high-risk) |
| Service areas missing or far beyond the real area | `gbp/current.yaml`, facts `service_area` | gbp-optimizer |
| No page per main verified service | site audit | site-builder |
| Few reviews vs the top 3 near the base | `competitors.json → radius_table` | review-engine |
| Missing on HomeStars / TrustedPros / Houzz (if relevant) | `citations/found.csv` | citation |

## Lead-gen and spam competitors to watch (flag only)

- Pay-per-call "lead generation" listings with generic names (e.g. "Pest Control Newmarket"), with no real
  business behind them, often with fake addresses or several near-identical profiles.
- Signs: exact-match keyword names, no website or a thin template site, a shared phone number across towns,
  addresses that are mailboxes or residences.
- **Agents only flag** these in `gap-analysis.md` with evidence. The **operator** decides whether to use
  Google's official channels (ranking-rules hard limit 12). Never copy their tactics, even to "match" them.

## Photo ideas

Technicians and the branded vehicle (with consent), equipment, before/after of exclusion work (no
customer addresses or faces), team, base exterior if it is a real staffed location.
