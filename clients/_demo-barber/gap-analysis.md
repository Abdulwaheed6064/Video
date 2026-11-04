# Gap analysis: Demo Fade Co. (fictional). SYNTHETIC

> SYNTHETIC demo data from `tools/fixture_scan.py`. Not a real business, not a real scan.
> Written by keyword-competitor (B04, fixture run). Numbers: `scans/baseline/metrics.json` and
> `competitors.json` (from `scans/baseline/grid.json`). Facts: verified entries in `facts.yaml` only.

## In 3 minutes: why the shop is not in the top 3

Searches from the shop's own block put it at #1. A few hundred metres away, six other barber shops take
the top 3. They all have far more reviews and a website on their listing. For “barber bradford” the shop is
in the top 3 on 1 of 47 search points, and on 1 of 13 within 1.5 km (`scans/baseline/metrics.json`).

## Baseline numbers (`scans/baseline/metrics.json`)

| Keyword | Top 3 | Found (top 20) | ARP found only | ARP, not found = 21 | Top 3 within 1.5 km |
| --- | --- | --- | --- | --- | --- |
| K1 barber bradford | 1 of 47 | 45 of 47 | 12.58 | 12.94 | 1 of 13 |
| K2 barber shop near me | 1 of 47 | 47 of 47 | 10.98 | 10.98 | 1 of 13 |
| K3 fade haircut bradford | 1 of 47 | 35 of 47 | 14.66 | 16.28 | 1 of 13 |

2 error points per keyword are excluded (listed in `error_cells`).

## Gaps, ranked by expected impact

| # | Gap | Evidence | Owner |
| --- | --- | --- | --- |
| 1 | **Reviews.** 18 reviews vs a median of 197 (max 246) for the 6 places that hold top-3 spots within 1 km | `competitors.json → client.reviews`, `radius_table["barber bradford"]` | review-engine |
| 2 | **No website on the listing.** The scan shows no website for the client; all 6 competitors list one. Verified website exists (F003) | `scans/baseline/grid.json → places`, `competitors.json`, `facts.yaml` F003 | gbp-optimizer (link), site-builder (landing page) |
| 3 | **Fade relevance is weakest.** K3 found on 35 of 47 points vs 45 and 47 for K1/K2. Skin fade is a verified service (F005) | `scans/baseline/metrics.json`, `facts.yaml` F005 | gbp-optimizer (services list), site-builder (service page) |
| 4 | **Organic: not in the top 10 from the shop.** Positions 13 (K1), 14 (K2), 17 (K3) at the shop point | `scans/baseline/metrics.json → organic` | site-builder |
| 5 | **Category: no gap seen in the scan.** Client and all 6 competitors show "Barber shop" | `competitors.json → primary_category` | gbp-auditor to confirm secondary categories |
| 6 | **Not measurable yet:** photos, description, hours, posts, Q&A, booking link | needs `gbp/current.yaml` | gbp-auditor |
| 7 | **Not measurable yet:** directory listings (NAP) | needs `citations/found.csv` | citation |
| 8 | Local links: low priority during the sprint | n/a | link-prospector (day 15) |

## Recommended target

- **Keywords for the promise:** K1 + K2. They are the highest-intent searches and the client is found on
  45 and 47 of 47 points. K3 stays tracked but not promised.
- **Radius: 1.0 km** (9 valid grid points). Within 1.0 km the client holds 1 of 9 top-3 spots, and the
  places holding the others have a median of 197 reviews against the client's 18
  (`competitors.json → radius_table`). The "#3 has under ~3× the client's reviews" test fails at every
  radius in this scan, so a wider promise is not supported by the data. 1.0 km is the smallest ring with
  enough points to measure.
- Operator: copy into `client.yaml → target` (currently `radius_km: 1.5`, a fictional demo value) if you
  agree. This is a stated target, not a guarantee (docs/01).

## Competitor flags

None. No competitor name in this scan contains added keywords or towns.
