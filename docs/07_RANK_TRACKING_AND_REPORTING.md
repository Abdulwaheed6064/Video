# Rank tracking and reporting

The rank map is both your **product proof** and your **sales tool**. It must be repeatable, honest and
cheap.

## 1. Why a grid

One "rank check" from one spot tells you almost nothing about Maps — results change block by block. A grid
of search points around the business shows where it wins and where it doesn't.

Defaults (store in `client.yaml → scan`):

| Setting | Storefront (barber) | Service-area (pest) |
| --- | --- | --- |
| Grid | 7×7 = 49 points | 7×7 or 9×9 |
| Spacing | 0.5–1.0 km (town) / 0.3–0.5 km (Toronto) | 1.5–3 km |
| Centre | Shop location | Base location (hidden address still has coordinates) |
| Device | mobile | mobile |
| Depth | 20 results | 20 results |
| Keywords | 3–5 | 3–5 |

**Never change grid, spacing, centre, depth or keywords between baseline and final scan.** If you must,
start a new baseline and say so in the report.

## 2. Data source

Use a paid SERP data provider; never scrape Google yourself.

- **Primary: DataForSEO Google Maps SERP API** — returns ranked Maps results for a keyword at a given
  coordinate, including place IDs, ratings and review counts. Billed per task (per 100 results), with a
  cheaper standard queue and a pricier live mode. Minimum deposit and current prices must be checked at
  signup (B03).
- **Organic positions:** DataForSEO Google Organic SERP for "keyword" from 2–3 points (shop, town centre).
- **Fallback for sales audits:** manual spot checks in a private window with location set, saved as
  screenshots — label as "manual spot check", not a grid.

Do not use the Google Places API for ranking: it's built for displaying places in apps, its result order
isn't the Maps ranking, and its terms restrict storing results.

Cost envelope (verify): ~49 points × 4 keywords ≈ 200 tasks per scan. At a fraction of a cent per task in
the standard queue, a scan costs on the order of **US$0.50–2**. Sprint (3 scans) + 2 monthly scans ≈ a few
dollars per client per month. `tools/budget.py` enforces caps regardless.

## 3. Metrics (computed only by `tools/metrics.py`)

| Metric | Definition |
| --- | --- |
| **ARP** — average rank position | Mean of `client_rank` over points where found; points not found count as `depth+1` (21). Report both versions if any not-found points |
| **Top-3 share** | Points where `client_rank ≤ 3` / valid points |
| **Found share** | Points where client appears within depth / valid points |
| **SoLV** (share of local voice) | Same as top-3 share; keep one name in reports — use "Top-3 share" with clients |
| **Target-radius top-3 share** | Top-3 share restricted to points within `target.radius_km` — **this is the number tied to the promise** |
| **Organic position** | Position of client's domain in organic results at each check point, or "not in top 20" |
| **Reviews** | Count and rating from scan data at scan time; weekly velocity = Δcount / weeks |
| **Δ** | Final − baseline for each metric; percentages only when baseline > 0, else "from 0 to N" |

Guarantee checks (01) use these exact definitions:

- Option A: final ARP (not-found = 21) lower than baseline ARP, same parameters.
- Option B: number of grid points with `client_rank ≤ 3` for the named keyword ≥ N.

## 4. Heatmaps

`tools/heatmap.py` renders each keyword's grid as a 7×7 coloured map over a light basemap (OpenStreetMap
tiles with attribution, or a plain grid if offline): green 1–3, yellow 4–10, orange 11–20, red 20+, grey =
error. Every image carries: keyword, date, grid size/spacing, device, "SYNTHETIC" if fixture.

Before/after are always the same scale and layout, side by side.

## 5. The sprint report (day 20)

One HTML page (`templates/report/`), exportable to PDF. Sections, in order:

1. **Headline** — one sentence, numbers only from `metrics.json`:
   "For 'barber bradford', you're now top 3 on 31 of 49 points (was 6)."
2. **Before / after maps** for each keyword.
3. **Metrics table** — baseline, mid, final, Δ.
4. **What we did** — checklist from `log.md` and approvals (dates).
5. **Reviews** — count/rating then and now; reply rate.
6. **What we can't claim yet** — e.g. "Rankings respond to many signals, including competitor changes; we
   can show what changed, not prove which change caused it." "Service-area expansion takes longer."
7. **Next 30 days** — up to 3 actions.
8. **Method** — grid parameters, provider, dates, limitations.

The reporter agent writes the narrative; every number is pulled from files. You check every number before
sending (B09 adds a script that diffs numbers in the HTML against `metrics.json`).

## 6. The free "rank map audit" (sales version)

- One keyword, one 7×7 scan, competitor table, three biggest gaps from `gap-analysis.md`.
- One page: "Here's where you show up today. Here's who beats you and why."
- Costs you well under a dollar of data and ~20 minutes. Only use public data; no access needed.
- Never send a prospect an audit claiming problems you haven't verified.

## 7. Monthly report (short)

Same structure, one keyword map per page, 1 page total + WhatsApp summary:
"Top-3 share for 'barber bradford': 63% (last month 55%). 9 new reviews, all replied. Next: ..."
