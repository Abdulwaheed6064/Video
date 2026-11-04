# B06 — Website template, schema, site checks, deploy

Read first: `build/README.md`, `agents/site-builder.md`, `agents/site-auditor.md`, `docs/02` §3,
`knowledge/ranking-rules.md`. Load any frontend-design guidance available in your tool.
Where: local or cloud (Node + Python). Suggested: Codex with a strong model. Paid calls: none.

## Do

1. **`templates/site/`** — Astro starter driven by `site.config.json` (generated from verified facts):
   home, one page per service keyword, contact; NAP block in footer; Google Maps embed (iframe, no API
   key); click-to-call; booking button; LocalBusiness JSON-LD in `<head>`; `sitemap.xml`; `robots.txt`;
   canonical tags; 404; Open Graph. Mobile-first, system fonts or one self-hosted font, images via
   Astro's image pipeline, no client-side JS framework needed. Clean, trustworthy local-business look;
   neutral placeholder images clearly labelled "replace with real photo".
2. **`tools/build_site_config.py --client <slug>`** — verified facts + keywords → `site/site.config.json`;
   refuses proposed facts.
3. **`tools/schema_gen.py --client <slug>`** — JSON-LD from verified facts; schema.org type from an
   allowlist (`HairSalon`, `BeautySalon`, `HomeAndConstructionBusiness`, `Plumber`, `Electrician`,
   `HVACBusiness`, `LocalBusiness`, …); required properties check (name, address or areaServed, telephone,
   url, openingHoursSpecification); SAB → `areaServed` and no street address.
4. **`tools/site_check.py --client <slug> [--local | --url <url>]`** — PageSpeed Insights API (key from env)
   or local Lighthouse if installed; extruct schema extraction + required props; title/H1/meta per page
   (service + town present, length limits); NAP match vs facts; robots/sitemap/canonical; broken internal
   links; page similarity (> 60% → flag). Writes `site/audit-<date>.json`. Tests use saved HTML, no network.
5. **`tools/deploy.sh <slug>`** (+ `tools/deploy.ps1` for Windows) — builds; computes the build output
   digest; runs `approvals.py verify` for a `site_deploy` approval matching that digest; prints exactly what
   it will deploy and where (Cloudflare Pages project name from client.yaml); asks y/N; deploys with
   `npx wrangler pages deploy`; writes a receipt; `approvals.py consume`. Never run by an agent.
6. Build the demo site locally (no deploy). Run site_check `--local`. Show the operator the pages and report.

## Tests

schema_gen rejects unknown types and proposed facts · SAB output has no street address · site_check
flags two pages > 60% similar · NAP mismatch detected · deploy script refuses without valid approval
(test the verify step, not the deploy).

## Verify

```bash
uv run pytest -q
uv run python tools/build_site_config.py --client _demo-barber
cd clients/_demo-barber/site && npm install && npm run build && cd -
uv run python tools/site_check.py --client _demo-barber --local
```

## Done when

Demo site builds, site_check must-pass list green (or each failure explained), tests pass, commit.
