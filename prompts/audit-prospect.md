# Free rank-map audit for a prospect (sales tool)

ARGS: $ARGUMENTS   (format: `"<business name>" <town> "<keyword>"`)

1. Create `prospects/<slug>/` (slug = business-town, lowercase-hyphenated) with client.yaml
   `mode: pilot-audit`, budget cap US$1. Public data only — we have no access and no relationship.
2. Ask the operator for the shop's coordinates or address if not given; geocode with tools/geocode.py.
3. rank-tracker: one 7×7 scan, one keyword (budget check first).
4. keyword-competitor: competitors.json + top 3 gaps only.
5. reporter: one page — heatmap, competitor table, "3 reasons you're not top 3", no promises.
6. compliance-reviewer on the page. Never claim problems not verified from data.
Print the page path. Do not contact the business.
