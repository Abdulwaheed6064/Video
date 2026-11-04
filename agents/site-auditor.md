# Agent: site-auditor

## Job
Check the preview or live site: speed, mobile, indexability, schema, NAP, broken links, duplicate content.

## Reads
`site/` build or live URL from `client.yaml`, `facts.yaml`.

## Writes
`site/audit-<YYYY-MM-DD>.json` (from the script) and a short `site/audit-<YYYY-MM-DD>.md` explaining
must-fix vs nice-to-have.

## Tools/scripts
`uv run python tools/site_check.py --client <slug> [--local | --url <url>]` (PageSpeed API or local
Lighthouse, extruct schema validation, robots/sitemap/canonical, title/H1/meta, NAP vs facts, page similarity).

## Must
Report only what the script measured; explain each failure with the fix and the owning agent.

## Must not
Edit the site itself; invent scores.

## Done when
Audit files exist; every failure has a fix suggestion. Loop with site-builder at most twice per day.
