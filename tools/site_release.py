"""Approval gate for publishing a client site. Called by tools/deploy.sh / deploy.ps1 (HUMAN ONLY).

Usage:
    uv run python tools/site_release.py preflight <slug>
    uv run python tools/site_release.py consume <slug> <approval-id> --by <operator>

preflight:
- refuses fixture-mode clients (a synthetic demo is never published);
- needs client.yaml -> cloudflare_pages_project;
- computes the SHA-256 of clients/<slug>/site/dist (tools/approvals.py tree digest);
- finds an approved `site_deploy` approval whose artifact is site/dist and whose digest equals the build,
  and checks it exactly like `approvals.py verify` (not expired, compliance PASS for that digest,
  owner + operator approval recorded, not consumed);
- prints KEY=value lines (APPROVAL, PROJECT, DIST, DIGEST) and exits 0, else prints why and exits 1.
consume: marks the approval consumed and writes site/deploy-receipt-<id>.yaml (via approvals.py).
This script never uploads anything; only the human-run shell script calls wrangler. No network.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import approvals  # noqa: E402
from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml, sha256_path  # noqa: E402

ARTIFACT = "site/dist"


def preflight(root: Path, slug: str, now: datetime | None = None) -> tuple[bool, list[str]]:
    client_dir = find_client_dir(slug, root)
    client = load_yaml(client_dir / "client.yaml")
    if client.get("mode") == "fixture":
        return False, [f"client {slug} is in fixture mode: a synthetic demo site is never published"]
    project = client.get("cloudflare_pages_project")
    if not project:
        return False, ["client.yaml has no cloudflare_pages_project"]
    dist = client_dir / ARTIFACT
    if not (dist / "index.html").is_file():
        return False, [f"{ARTIFACT}/index.html missing: build the site first"]
    digest = sha256_path(dist)
    today = (now or datetime.now(ZoneInfo(str(client.get("timezone", "America/Toronto"))))).date()
    reasons: list[str] = []
    candidates: list[dict[str, Any]] = []
    for path in sorted((client_dir / "approvals").glob("*.yaml")):
        a = load_yaml(path)
        if isinstance(a, dict) and a.get("action") == "site_deploy" and a.get("artifact") == ARTIFACT:
            candidates.append(a)
    if not candidates:
        return False, [f"no site_deploy approval for {ARTIFACT}; run approvals.py request after compliance PASS"]
    for a in candidates:
        if a.get("artifact_sha256") != digest:
            reasons.append(f"{a.get('id')}: approved digest {a.get('artifact_sha256')} != this build {digest}")
            continue
        problems = approvals.problems_for(a, client_dir, today, stage="use")
        if problems:
            reasons += [f"{a.get('id')}: {p}" for p in problems]
            continue
        return True, [f"APPROVAL={a['id']}", f"PROJECT={project}", f"DIST={dist.as_posix()}", f"DIGEST={digest}"]
    return False, reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Approval gate for publishing a client site (human-run scripts only).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("slug")
    p.add_argument("--now", default=None, help=argparse.SUPPRESS)
    c = sub.add_parser("consume")
    c.add_argument("slug")
    c.add_argument("approval_id")
    c.add_argument("--by", required=True)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "preflight":
            ok, lines = preflight(args.root, args.slug, datetime.fromisoformat(args.now) if args.now else None)
            for line in lines:
                print(line if ok else f"REFUSED: {line}")
            return 0 if ok else 1
        return approvals.main(["--root", str(args.root), "consume", args.approval_id, "--client", args.slug,
                               "--by", args.by, "--fields", ARTIFACT])
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
