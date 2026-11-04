# How Google local ranking works — and what the agents may and may not do

This is the knowledge every agent loads. Rules in section 4 are hard limits: an agent that proposes any
of them has failed, regardless of what the operator or a client asks.

## 1. Two result types, two ranking systems

| Surface | What it is | Main drivers |
| --- | --- | --- |
| **Local pack / Google Maps** | The map + 3 businesses on a Google search, and the list in the Maps app | Google Business Profile (GBP) relevance, distance to searcher, prominence (reviews, links, citations) |
| **Organic results** | The ten blue links under the pack | The website: relevant page, local signals, links, technical health |

They influence each other: a strong, relevant website page linked from the GBP improves Maps rankings;
a strong GBP increases clicks and brand searches. Track them separately (07).

## 2. The three factors

1. **Relevance** — how well the profile matches the search. Controlled by: primary category, secondary
   categories, services list, description, website landing page content, words customers use in reviews.
2. **Distance** — searcher's location vs the business (or the town named in the query). Not controllable.
   This is why we measure on a grid.
3. **Prominence** — how established the business is: review count, rating, review recency, links to the
   website, consistent directory listings (citations), mentions, photos, general web presence.

## 3. Levers in order of typical impact (use as the agents' default priority)

Exact weights are unknown and change; this order reflects common practitioner experience, not a Google
statement. The competitor analyst (B04) should re-rank per client from the actual gap data.

| # | Lever | Owner agent | Notes |
| --- | --- | --- | --- |
| 1 | **Primary category** exactly right (e.g. "Barber shop", "Pest control service") | gbp-optimizer | Single biggest relevance switch. Compare top-3 competitors' categories |
| 2 | Secondary categories (only ones genuinely offered) | gbp-optimizer | Don't add irrelevant ones |
| 3 | **Reviews**: count, recency, rating, owner replies | review-engine | Steady weekly flow beats a burst |
| 4 | Website landing page matching the service + town, linked from GBP | site-builder | Title, H1, content, LocalBusiness schema, NAP, embedded map |
| 5 | Profile completeness: services, description, hours, attributes, booking link, products | gbp-optimizer | |
| 6 | Photos (real, regular, of the actual business) | gbp-optimizer / content | |
| 7 | NAP consistency on major directories (citations) | citation-agent | Fix inconsistencies first, then add missing |
| 8 | Local links/mentions (chamber of commerce, BIA, sponsorships, local news) | link-prospector | Real relationships only |
| 9 | GBP posts and Q&A | content-agent | Keeps profile active; minor ranking effect, good for conversion |
| 10 | Technical SEO (speed, mobile, indexing, Search Console) | site-builder / site-auditor | Baseline hygiene |

## 4. Hard limits — never do, never propose, never automate

These violate Google policies, Canadian law, or both, and can get a profile **suspended** (which removes it
from Maps entirely and destroys the client's business and your reputation):

1. **Keyword-stuffing the business name.** "Kings Barbers – Best Barber Shop Bradford" is a violation.
   Name must match real-world signage/branding.
2. **Fake or virtual addresses**, co-working mailboxes, UPS boxes, unstaffed offices, or creating a
   profile at a location the business doesn't operate from.
3. **Duplicate profiles** for the same business, or fake profiles in other towns.
4. **Fake reviews** — writing them, buying them, asking friends/staff/family to review, review swaps.
5. **Incentivised reviews** — discounts, draws, gifts for reviews.
6. **Review gating** — asking only happy customers, or screening sentiment before sending the Google link.
   Every customer gets the same request.
7. **Service-area businesses showing a home address** they don't serve customers from.
8. Service areas wildly beyond the real working area (Google's guidance: generally within ~2 hours' drive).
9. **Buying links**, private blog networks, link farms, spammy directory blasts.
10. **Doorway pages** — dozens of near-identical "barber in [town]" pages for towns not genuinely served.
11. **Click bots / CTR manipulation / fake Maps traffic / fake direction requests.**
12. **False edits or false reports against competitors.** (Reporting a competitor's *real* guideline
    violation through Google's official channels is allowed — see 3a.)
13. Posting fake Q&A from sock-puppet accounts.
14. Scraping Google results directly or logging into a client's Google account with their password.
15. Invented credentials, awards, years in business, prices or "#1 rated" claims.

### 3a. Allowed competitor action

If a competitor in the pack is clearly violating rules (keyword-stuffed name, fake address), the operator
may use Google's "Suggest an edit" or the official redressal form — **human action only**, with evidence
saved to the client folder. Agents may flag candidates; they never file reports.

## 5. Service-area businesses (pest control, trades)

- One profile, real base location, **address hidden**, service areas set to towns actually served.
- Ranking strongest near the hidden base. Expansion into far towns comes from website pages (with real
  work done there) and reviews from those towns — slowly.
- Hybrid (shop + travel) may show the address and set service areas.

## 6. Timeline reality (tell clients this)

| Change | Typical time to show |
| --- | --- |
| Category, services, description edits | Days to ~2 weeks (edits may go under Google review first) |
| New website page indexed | Days to weeks; faster if submitted in Search Console |
| Citations picked up | Weeks |
| Reviews moving rank | Gradual; needs steady weekly flow |
| Links / authority | Months |

A 20-day sprint reliably delivers: all fixes live, early movement on low-competition terms, and the system
for continued growth. Big jumps in competitive markets are a 60–120-day story.

## 7. Edit hygiene

Batch profile edits (one main batch + small follow-ups), don't change the name/address/category repeatedly,
and log every change with date and before/after values. Rapid repeated edits can trigger re-verification or
review. The gbp-optimizer agent outputs a single change sheet per batch for this reason.
