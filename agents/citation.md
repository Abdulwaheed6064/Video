# Agent: citation

## Job
Make name / address / phone / website consistent and present on the directories that matter in Canada.

## Reads
`facts.yaml` (verified), `client.yaml` (address, address_public, niche, service_area),
`knowledge/citations-canada.csv`, `citations/found.csv` (what the operator saw on each directory:
`directory, listing_url, name, address, phone, website, found_by, found_on`, one row per listing).

## Writes
- `citations/plan.csv`, starting from the DRAFT written by `tools/nap_check.py`. Columns: `directory, url,
  status (wrong | duplicate | missing), fields_to_fix, enter_name, enter_address, enter_phone,
  enter_website, who (operator | owner), priority, notes`.
- `citations/nap-report.md` (written by the script; add a short "what to do first" note if useful).

## Tools/scripts
`uv run python tools/nap_check.py --client <slug>`. It normalises Canadian address/phone/website formats,
diffs every listing against the verified NAP, marks duplicates, adds the directories with no listing
(filtered by niche and town) and orders the draft plan.

## Must
- Order: fix **wrong** first → remove/merge **duplicates** → add **missing**. Keep the top ~15 only.
- Priority first: Apple Business Connect, Bing Places, Facebook, Yelp, YellowPages.ca, Foursquare,
  then local chamber/BIA and niche sites (barbers: Booksy/Fresha **only if the shop already uses them**;
  pest/trades: HomeStars, TrustedPros, Houzz).
- Review the draft: delete "missing" rows the business wouldn't really use (a booking app it doesn't use,
  a paid membership the owner doesn't want). Say why in `notes`.
- Use exactly the verified NAP strings (the `enter_*` columns); the business name exactly as on signage.
- `who`: owner for accounts the owner must hold (Facebook Page, booking platforms); operator otherwise.
- Check `knowledge/citations-canada.csv → notes` before relying on a URL; several rows are unverified.

## Must not
Create listings at fake addresses; show a hidden address for a service-area business; mass-submit to
junk directories; use paid "blast" services; create a second listing instead of fixing a duplicate.

## Done when
plan.csv covers the top ~15 with owner/operator assignment; nap-report lists every mismatch.
