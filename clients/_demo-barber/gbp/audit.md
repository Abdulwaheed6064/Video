# GBP audit: Demo Fade Co. (fictional). SYNTHETIC, sprint day 2 (2026-11-07)

> Fictional profile (`gbp/current.yaml`) with deliberate gaps. Written by gbp-auditor.
> Scores are in `gbp/audit.json`: 7 pass / 10 fail / 3 unknown (counts checked by `tools/validate.py`).

| Item | Status | Evidence | Fix owner |
| --- | --- | --- | --- |
| Profile verified | pass | `verification: verified` | |
| Name matches signage | pass | matches F001 | |
| Primary category vs top 3 | pass | "Barber shop"; all 6 competitors show the same (`competitors.json`) | |
| Secondary categories | pass | none set; verified services (F005, F006) need none | |
| Storefront setup | pass | address shown; storefront in `client.yaml` | |
| Regular hours | **fail** | Saturday not set; F004 says Sat 09:00–17:00 | gbp-optimizer |
| Holiday hours | **fail** | none set; no verified holiday hours yet (Q3) | gbp-optimizer, after owner answers |
| Phone | pass | matches F002 | |
| Website link | **fail** | none linked; F003 verified | gbp-optimizer |
| Services list | **fail** | empty; F005, F006 verified | gbp-optimizer |
| Description | **fail** | empty | gbp-optimizer (owner approves text) |
| Attributes | unknown | none set; no verified attribute facts | ask owner |
| Booking link | unknown | none; no booking_url fact (Q4) | ask owner |
| Products | unknown | none; only relevant if the shop sells products | ask owner |
| Photos (≥ 10 + logo + cover) | **fail** | 3 photos, no logo, newest 2025-06-14 | content (shot list) |
| Post in last 30 days | **fail** | no posts | content (day 7) |
| Q&A | **fail** | 0 questions | gbp-optimizer (seed draft, owner confirms) |
| Reviews vs competitors | **fail** | 18 reviews vs median 197 for top-3 holders within 1 km (`competitors.json`) | review-engine |
| Review replies | **fail** | reply rate 0.35 | review-engine |
| Competitor rule-breaks | pass | none visible | |

Biggest relevance fixes for one batch: website link, services, description, Saturday hours.
Prominence gaps (reviews, replies, photos, posts) are handled by review-engine and content, not by this batch.
