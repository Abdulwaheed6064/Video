# Tools, services and budget (CAD)

Planning numbers, not quotes. Recheck every price at signup and record it in `DECISIONS.md` with the date.
USD→CAD at an illustrative 1.38.

## 1. Stack

| Need | Choice | Cost | Notes |
| --- | --- | --- | --- |
| Agent runtime | **Claude Code** + **Codex** in VS Code, on subscriptions you already pay for | Existing | Interactive use; heavy runs count against your plan's usage limits — keep runs small |
| Scripts | Python 3.12 + `uv` | Free | `tools/` CLIs, pytest |
| Rank data | DataForSEO (Maps + Organic SERP) | Pay-as-you-go; minimum deposit (≈US$50 at last check) | Hard cap via `tools/budget.py` |
| Site speed | Google PageSpeed Insights API (free key) or local Lighthouse | Free | |
| Structured data | `extruct` / schema validation locally + Google Rich Results Test manually | Free | |
| Client sites | Astro static sites | Free | One template, per-client config |
| Hosting | Cloudflare Pages (free tier) under **your** account, or client's own account | Free–low | Client owns the domain |
| Search data | Google Search Console (client's property, you as user) | Free | CSV export → `scans/` |
| Geocoding | OpenStreetMap Nominatim (low volume, follow usage policy) or manual pin | Free | Store source |
| Heatmap base | OSM tiles with attribution, or plain grid | Free | |
| QR cards | Python `qrcode` + HTML→PDF | Free | |
| Optional later | BrightLocal / Local Falcon / Whitespark | Monthly | Only if citations or scan volume justify |
| Domains | Client-owned | Client pays | Never register a client's domain in your name |

**Not used:** Anthropic/OpenAI API billing, Supabase, Workers, Resend, n8n, any GBP automation tool that
needs a client password.

## 2. Monthly costs

| Item | 1 client | 5 clients | 10 clients |
| --- | ---: | ---: | ---: |
| Rank data (sprint month higher) | $5 | $20 | $40 |
| Hosting | $0 | $0 | $0–7 |
| Printing review cards | $5 | $15 | $25 |
| Misc / contingency | $10 | $20 | $30 |
| **Cash total** | **~$20** | **~$55** | **~$100** |

Your subscriptions (Claude, ChatGPT) are existing overhead. If heavy usage forces a higher tier, add it here.

## 3. Time per client (the real cost)

| Phase | Your hours | Notes |
| --- | ---: | --- |
| Sales audit + call | 1 | Mostly automated scan + gap |
| 20-day sprint | 8–12 | Onboarding, approvals, GBP UI, citations, deploy, report call |
| Monthly | ≤ 2 | Scan, posts, replies, report |

## 4. Unit economics (hypothesis, CAD before HST)

Value your time at $35/h.

| Scenario | Revenue | Cash cost | Your time | Contribution |
| --- | ---: | ---: | ---: | ---: |
| Storefront setup ($750, 10 h) | $750 | $15 | $350 | **$385** |
| Storefront monthly ($249, 2 h) | $249 | $8 | $70 | **$171** |
| Service-area setup ($1,200, 14 h) | $1,200 | $25 | $490 | **$685** |
| Service-area monthly ($399, 3 h) | $399 | $12 | $105 | **$282** |
| Pilot setup ($300, 14 h — learning) | $300 | $20 | $490 | **−$210** (accepted cost of the case study) |
| 10 storefront clients monthly | $2,490 | $100 | $700 | **$1,690** |

Biggest risk: monthly work creeping past 2 hours. Track your minutes per client in `log.md`.

## 5. Value to the client (use in the pitch)

| Business | Value of one new regular customer | New regulars/month to cover $249 |
| --- | --- | --- |
| Barber ($35 cut, every 4 weeks, ~1 year) | ~$450/yr | < 1 |
| Pest control ($300 avg job) | ~$300 | 1 |

Ask the owner for their real numbers; don't invent them.

## 6. Spending gates

| Stage | Cap |
| --- | --- |
| Building + fixture (B00–B09) | $0 paid calls (fixture mode) |
| First live scans on your test/pilot business (B10) | US$50 deposit, ≤ US$10 used |
| First paying clients | `budget_cad_month` per client (default $15) + global cap $100/mo |

Business costs outside this: business registration (sole prop / Ontario BIN), HST registration once you
pass the small-supplier threshold, a one-time lawyer review of your agreement, and optionally liability
insurance. Check these with an accountant — not decided here.
