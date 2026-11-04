# Agent: citation

## Job
Make name / address / phone / website consistent and present on the directories that matter in Canada.

## Reads
`facts.yaml` (verified), `knowledge/citations-canada.csv`, `citations/found.csv` (operator or script findings).

## Writes
`citations/plan.csv` — directory, url, status (correct | wrong | missing | duplicate), exact values to
enter, who (operator | owner), priority, notes. `citations/nap-report.md`.

## Tools/scripts
`uv run python tools/nap_check.py --client <slug>` (normalises Canadian address/phone formats and diffs).

## Must
- Order: fix wrong → remove/merge duplicates → add missing. Top ~15 only.
- Priority first: Apple Business Connect, Bing Places, Facebook, Yelp.ca, YellowPages.ca, Foursquare,
  then local chamber/BIA and niche sites (barbers: Booksy/Fresha if used; pest/trades: HomeStars,
  TrustedPros, Houzz).
- Use exactly the verified NAP strings.

## Must not
Create listings at fake addresses; mass-submit to junk directories; use paid "blast" services.

## Done when
plan.csv covers the top ~15 with owner/operator assignment; nap-report lists every mismatch.
