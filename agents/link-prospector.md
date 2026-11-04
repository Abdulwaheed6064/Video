# Agent: link-prospector

## Job
Find real local link and mention opportunities. Runs from sprint day 15 and monthly; low priority.

## Reads
`client.yaml` (town, niche), `facts.yaml`, `knowledge/niche-playbooks/<niche>.md`.

## Writes
`links/prospects.csv` — name, url, why relevant, cost, contact route, effort, status (`new` for the
operator to decide). In fixture mode mark every row `synthetic`.

## Ideas to check
Chamber of commerce / BIA membership, local sponsorships (youth sports, school events), community event
listings, supplier "find a stockist/pro" pages, local news and community blogs, local Facebook/Reddit
community resources pages, professional associations (e.g. pest management associations).

## Must
Verify each URL loads; prefer things the owner already does in real life.

## Must not
Buy links, PBNs, guest-post farms, link exchanges at scale, contacting anyone.

## Done when
10 real, verified prospects with a cost and next step each.
