# B07 — Citations (directory listings)

Read first: `build/README.md`, `agents/citation.md`, `docs/02` §3.
Where: local or cloud (web access needed to verify URLs). Paid calls: none.

## Do

1. **`knowledge/citations-canada.csv`** — columns: `name, url, applies_to (all|barber|pest|trades|salon),
   priority (1-3), free_or_paid, how_to_claim, verifies_how (phone/postcard/email), notes, checked_on`.
   Seed: Google Business Profile, Apple Business Connect, Bing Places, Facebook, Yelp.ca, YellowPages.ca,
   Foursquare, BBB (members), Canada411, Cylex Canada, local chamber of commerce (Bradford West
   Gwillimbury, Newmarket, Aurora — as examples), Booksy, Fresha, StyleSeat (barbers), HomeStars,
   TrustedPros, Houzz (pest/trades). **Verify each URL loads and is current**, record `checked_on`;
   drop dead ones and note why.
2. **`tools/nap_check.py --client <slug>`** — normalise Canadian addresses (St/Street, Rd/Road, W/West,
   unit formats "Unit 5" / "#5" / "5-", postal code spacing/case, province ON/Ontario), phone formats
   (+1, dashes, brackets), website (http/https, trailing slash, www); diff `citations/found.csv` vs
   verified facts; write `citations/nap-report.md` + update statuses in a draft plan.
3. Finalise `agents/citation.md` if needed: `plan.csv` fix-first ordering, top ~15, owner/operator assignment.
4. Demo run with a hand-made `citations/found.csv` with 3 mismatches and 1 duplicate.

## Tests

normaliser equates "123 Holland St. W, Unit 4" with "4-123 Holland Street West"; postal "l3z0a1" ==
"L3Z 0A1"; phone variants equal; mismatched phone flagged; duplicate flagged.

## Verify

```bash
uv run pytest -q
uv run python tools/nap_check.py --client _demo-barber
```

## Done when

Directory list verified and dated; demo plan.csv + nap-report.md correct; commit.
