# Niche playbook: barber shops (storefront)

> **Starting hypothesis: verify per client.** Everything below is a default to check against the client's
> verified facts and their own scan data. It is not evidence and must never be quoted to a client as fact.
> Numbers in client-facing text come only from `tools/` outputs (AGENTS.md rule 4).

Written: 2026-11-04 (B04). Review quarterly alongside `knowledge/ranking-rules.md`.

## Business type

- Almost always a **storefront**: customers come to the shop, address shown. One profile per real shop.
- Mobile/home barbers are service-area businesses; use the pest-control SAB notes for address rules.

## Keyword patterns (pick 3–5; exactly one "near me")

| Pattern | Example | Use when |
| --- | --- | --- |
| barber + town | `barber bradford` | Always a candidate; highest-intent town query |
| barber shop + town | `barber shop bradford` | Often treated as a near-duplicate of the above; probe both and keep the one with more pack variation |
| barber shop near me | `barber shop near me` | The one "near me" variant; meaningful only on the grid |
| service + town | `fade haircut bradford`, `skin fade bradford`, `beard trim bradford` | Only if the service is a **verified** fact |
| men's haircut + town | `mens haircut bradford` | If the shop positions itself as a men's cutter (verified) |
| kids haircut + town | `kids haircut bradford` | Only if kids' cuts are a verified service |

Probe candidates with `tools/rank_scan.py --mode keywords-probe` (live clients) before choosing.

## Categories (verify in the GBP category picker; names change)

- Likely primary: **Barber shop**. Compare with the categories the current top 3 actually use
  (`competitors.json → primary_category`).
- Possible secondary, only if genuinely offered: Hair salon, Men's hair salon (if it exists in the picker),
  Beauty salon (rarely right for barbers).
- Never add a category to "catch" searches for a service the shop does not provide.

## Typical services (each must be a verified fact before use)

Haircut, skin fade, taper, buzz cut, beard trim, hot towel shave, line-up/edge-up, kids' cut, hair design,
eyebrow trim. Prices only from verified `price` facts or a `price_policy` fact.

## Common gaps to check (map each to the owning agent)

| Gap | How we know | Owner |
| --- | --- | --- |
| Primary category differs from top 3 | `gbp/current.yaml` vs `competitors.json` | gbp-optimizer |
| Far fewer reviews than the top 3 within the target radius | `competitors.json → client.reviews` vs `radius_table` | review-engine |
| No website, or GBP links to a booking page only | facts `website`, `gbp/current.yaml` | site-builder |
| No services list / description | `gbp/current.yaml` | gbp-optimizer |
| Few or old photos | `gbp/current.yaml` (operator counts) | content |
| Booking link missing | facts `booking_url` | gbp-optimizer |
| Inconsistent NAP on Booksy/Fresha/Square/Facebook | `citations/found.csv` | citation |

## Review velocity (hypothesis)

Barbers see many repeat customers, so a steady weekly flow is realistic if the barber asks **every**
customer the same way (QR card at the till plus a text after the appointment). Set the target from the
client's own numbers, not from this file. Never gate or incentivise reviews (ranking-rules hard limits 4–6).

## Photo ideas (real, of the actual business, with the owner's rights)

Storefront with signage (helps people find the door), chairs/interior, barbers at work (with consent),
finished cuts (with client consent), team photo, price board (only if prices are verified facts).

## Booking platforms seen in the niche

Booksy, Fresha, Square Appointments, StyleSeat, Vagaro. If the shop uses one, its profile is a citation
(NAP must match), and the booking URL can go on GBP as the booking link.

## Watch-outs

- Competitor names stuffed with "Best Barber Bradford" etc.: **flag only** in gap-analysis. The operator
  decides whether to use Google's official "Suggest an edit". Agents never file reports.
- Never suggest adding the town or "barber" to the client's own name unless it is on the real signage.
