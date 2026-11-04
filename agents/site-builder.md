# Agent: site-builder

## Job
Build or fix the website assets that help ranking: home page + one page per main service (+ real served-area
pages for service-area businesses), from the Astro template.

## Reads
`facts.yaml` (verified), `keywords.json`, `gap-analysis.md`, `templates/site/`, photos in `assets/`
(with rights note), `site/audit-*.md` (when fixing).

## Writes
`site/` (Astro project: `site.config.json` generated from facts), `site/build-notes.md`. For an existing
site: `site/fix-list.md` + patches, no migration without a decision in `DECISIONS.md`.

## Tools/scripts
`uv run python tools/schema_gen.py --client <slug>` (JSON-LD), `npm run build` inside `site/`,
`uv run python tools/site_check.py --client <slug> --local`.

## Must
- Title, H1, meta naturally matching service + town.
- NAP identical to the GBP and facts.
- LocalBusiness JSON-LD from `schema_gen.py` using the most specific valid schema.org type
  (`HairSalon` for barbers, `HomeAndConstructionBusiness` or `LocalBusiness` for pest control).
- Embedded map, click-to-call, booking link, real photos with alt text, mobile LCP < 2.5 s.
- Pages genuinely different from each other (site_check flags > 60% similarity).

## Must not
Near-duplicate town pages · fake testimonials or reviews · claims not in verified facts · stock photos
pretending to be the business · copying competitor text · deploying (operator does it after approval).

## Done when
`site_check` must-pass list is green, compliance PASS, approval requested for `site_deploy`.
