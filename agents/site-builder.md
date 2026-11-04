# Agent: site-builder

## Job
Build or fix the website assets that help ranking: home page + one page per main service (+ real served-area
pages for service-area businesses), from the Astro template.

## Reads
`facts.yaml` (verified), `keywords.json`, `gap-analysis.md`, `templates/site/`, photos in `assets/`
(with rights note), `site/audit-*.md` (when fixing).

## Writes
- `site/content.yaml`: the page copy (home, contact, one entry per verified service: `fact`, `slug`,
  `keyword`, `title` 30–65 chars "Service in Town | Name", `meta_description` 70–160, `h1`, `body`
  paragraphs, `image_alt`). Shape: `templates/site/content.example.yaml`. General descriptions of a service
  are fine; anything about *this* business must be a verified fact.
- `site/site.config.json`: generated only by `tools/build_site_config.py` (never hand-edited). The first
  run copies the Astro template from `templates/site/`.
- `site/build-notes.md`. For an existing
site: `site/fix-list.md` + patches, no migration without a decision in `DECISIONS.md`.

## Tools/scripts
`uv run python tools/build_site_config.py --client <slug>` (refuses unverified service facts and copy that
fails `lint_claims`; embeds JSON-LD from `tools/schema_gen.py`), then `cd clients/<slug>/site && npm install
&& npm run build`, then `uv run python tools/site_check.py --client <slug> --local`.
For approval, the artifact is `site/dist` (tree digest; the build is deterministic):
`uv run python tools/approvals.py request --client <slug> --action site_deploy --artifact site/dist …`.

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
