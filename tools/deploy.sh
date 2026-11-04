#!/usr/bin/env bash
# Publish ONE client's site to Cloudflare Pages.  HUMAN ONLY: agents must never run this
# (AGENTS.md rule 6; .claude/settings.json denies it). Usage: tools/deploy.sh <client-slug>
#
# 1. builds clients/<slug>/site (npm ci + npm run build; SKIP_BUILD=1 to use the existing dist/)
# 2. tools/site_release.py preflight: build digest must match an approved, unexpired site_deploy
#    approval with a compliance PASS for that digest. Otherwise it stops here.
# 3. shows exactly what goes where and asks y/N
# 4. npx wrangler pages deploy (you must be logged in: npx wrangler login)
# 5. tools/site_release.py consume: receipt in site/ + approval marked consumed
set -euo pipefail

slug="${1:?usage: tools/deploy.sh <client-slug>}"
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
root="${MRS_ROOT:-$repo}"   # MRS_ROOT: tests only (points at a temporary copy of the repo data)
site="$root/clients/$slug/site"
cd "$repo"

if [[ ! -d "$site" ]]; then
  echo "REFUSED: $site does not exist" >&2
  exit 1
fi

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  (cd "$site" && npm ci --no-audit --no-fund && npm run build)
fi

if ! preflight="$(uv run python tools/site_release.py --root "$root" preflight "$slug")"; then
  echo "$preflight"
  echo "REFUSED: no valid site_deploy approval for this exact build. Nothing was published." >&2
  exit 1
fi
echo "$preflight"

approval="$(grep '^APPROVAL=' <<<"$preflight" | cut -d= -f2-)"
project="$(grep '^PROJECT=' <<<"$preflight" | cut -d= -f2-)"
digest="$(grep '^DIGEST=' <<<"$preflight" | cut -d= -f2-)"

echo
echo "About to publish:"
echo "  folder   : $site/dist"
echo "  digest   : $digest"
echo "  project  : $project (Cloudflare Pages, production branch main)"
echo "  approval : $approval"
read -r -p "Publish now? [y/N] " answer
if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
  echo "Cancelled. Nothing was published."
  exit 1
fi

npx --yes wrangler pages deploy "$site/dist" --project-name "$project" --branch main
uv run python tools/site_release.py --root "$root" consume "$slug" "$approval" --by "${OPERATOR:-operator}"
echo "Done. Next: point the GBP website link at the right page (with UTM) and submit the sitemap in Search Console."
