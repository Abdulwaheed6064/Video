"""Generate clients/<slug>/site/site.config.json from VERIFIED facts + the site-builder's copy.

Usage:
    uv run python tools/build_site_config.py --client <slug> [--refresh-template]

- First run: copies templates/site/ into clients/<slug>/site/ (no node_modules/dist). Later runs only
  rewrite site.config.json, unless --refresh-template.
- Business details (name, phone, website, hours, services, address, booking link) come only from facts
  with status: verified, plus location from client.yaml. A service page whose `fact` is not a verified
  `service` fact is refused. So is a page whose copy fails tools/lint_claims.py.
- Page copy comes from clients/<slug>/site/content.yaml (written by the site-builder agent; see
  templates/site/content.example.yaml). Without it, minimal factual defaults are generated (they will be
  similar to each other; site_check will say so).
- JSON-LD from tools/schema_gen.py is embedded.
No network.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml  # noqa: E402
from tools.lint_claims import lint_text, load_context  # noqa: E402
from tools.schema_gen import DAYS, generate, parse_hours, phone_e164, verified_facts  # noqa: E402

TEMPLATE_DIR = REPO_ROOT / "templates" / "site"
SKIP_COPY = {"node_modules", "dist", ".astro", "content.example.yaml"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def hours_display(text: str) -> list[dict[str, str]]:
    """Group days with identical hours for display, closed days last."""
    spec = parse_hours(text)
    by_day = {d: f"{h['opens']} – {h['closes']}" for h in spec for d in h["days"]}
    rows: list[dict[str, str]] = []
    run: list[str] = []
    for d in DAYS:
        if d not in by_day:
            continue
        if run and by_day[run[-1]] == by_day[d] and DAYS.index(d) == DAYS.index(run[-1]) + 1:
            run.append(d)
            continue
        if run:
            rows.append({"label": run[0] if len(run) == 1 else f"{run[0]} – {run[-1]}", "value": by_day[run[0]]})
        run = [d]
    if run:
        rows.append({"label": run[0] if len(run) == 1 else f"{run[0]} – {run[-1]}", "value": by_day[run[0]]})
    closed = [d for d in DAYS if d not in by_day]
    if closed:
        rows.append({"label": ", ".join(closed), "value": "Closed"})
    return rows


def default_content(name: str, town: str, services: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "home": {"title": f"{name} | Barber shop in {town}" if services else f"{name} | {town}",
                 "meta_description": f"{name} in {town}. Services: " + ", ".join(s["value"] for s in services) + ".",
                 "h1": f"{name} in {town}", "intro": [f"{name} in {town}."]},
        "contact": {"title": f"Contact {name} in {town}", "meta_description": f"Phone, hours and map for {name} in {town}.",
                    "h1": "Contact and hours", "intro": []},
        "services": [{"fact": s["id"], "slug": slugify(f"{s['value']} {town}"), "title": f"{s['value']} in {town} | {name}",
                      "meta_description": f"{s['value']} at {name} in {town}.", "h1": f"{s['value']} in {town}",
                      "body": [f"{s['value']} at {name} in {town}."], "image_alt": f"{s['value']} at {name}"}
                     for s in services],
    }


def _texts(content: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for sec in ("home", "contact"):
        page = content.get(sec) or {}
        out += [str(page.get(k, "")) for k in ("title", "meta_description", "h1")] + [str(p) for p in page.get("intro", [])]
    for s in content.get("services", []):
        out += [str(s.get(k, "")) for k in ("title", "meta_description", "h1", "image_alt")] + [str(p) for p in s.get("body", [])]
    return out


def build(client_dir: Path, today: date | None = None) -> dict[str, Any]:
    client = load_yaml(client_dir / "client.yaml")
    facts = verified_facts(client_dir)
    jsonld = generate(client, facts)  # also enforces the required verified data

    def first(key: str) -> str | None:
        return str(facts[key][0]["value"]) if facts.get(key) else None

    name, phone, website, hours = first("name"), first("phone"), first("website"), first("hours")
    loc = client["location"]
    address_public = bool(loc.get("address_public", True)) and client.get("business_type") != "service_area"
    town = (client.get("service_area") or [""])[0]
    address_lines: list[str] = []
    if address_public and loc.get("address"):
        addr = jsonld["address"]
        address_lines = [addr["streetAddress"], f"{addr['addressLocality']}, {addr['addressRegion']}"
                         + (f" {addr['postalCode']}" if addr.get("postalCode") else "")]
        town = addr["addressLocality"]

    services = facts.get("service", [])
    service_by_id = {str(s["id"]): s for s in services}
    content_path = client_dir / "site" / "content.yaml"
    content = load_yaml(content_path) if content_path.is_file() else default_content(str(name), town, services)

    pages = []
    seen: set[str] = set()
    for s in content.get("services", []):
        fid = str(s.get("fact"))
        if fid not in service_by_id:
            raise ToolError(f"service page {s.get('slug')!r}: fact {fid} is not a verified service fact")
        slug = str(s.get("slug"))
        if not SLUG_RE.match(slug) or slug in seen or slug in {"contact", "404"}:
            raise ToolError(f"service page slug {slug!r} is invalid or duplicated")
        seen.add(slug)
        body = [str(p) for p in s.get("body", [])]
        if not body:
            raise ToolError(f"service page {slug!r} has no body copy")
        pages.append({"slug": slug, "name": str(service_by_id[fid]["value"]), "fact_ref": fid,
                      "keyword": s.get("keyword"), "title": str(s["title"]), "meta_description": str(s["meta_description"]),
                      "h1": str(s["h1"]), "body": body, "image_alt": str(s.get("image_alt") or service_by_id[fid]["value"])})

    ctx = load_context(client_dir)
    flagged = lint_text(Path("content.md"), "\n".join(_texts(content)), ctx)
    if flagged:
        raise ToolError("site copy fails lint_claims:\n  - " + "\n  - ".join(f"[{f.rule}] {f.text}: {f.message}"
                                                                          for f in flagged))

    lat, lng = loc["lat"], loc["lng"]
    map_q = f"{lat},{lng}" if address_public else quote(f"{town}, ON")
    home = content["home"]
    contact = content["contact"]
    return {
        "synthetic": client.get("mode") == "fixture",
        "site_url": str(client.get("site_url") or website).rstrip("/"),
        "lang": "en-CA",
        "business": {
            "name": name,
            "phone_display": phone,
            "phone_tel": phone_e164(str(phone)),
            "address_public": address_public,
            "address_lines": address_lines,
            "town": town,
            "service_area": list(client.get("service_area") or []),
            "hours": hours_display(str(hours)),
            "booking_url": first("booking_url"),
            "directions_url": f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" if address_public else None,
        },
        "map_embed_url": f"https://www.google.com/maps?q={map_q}&z=15&output=embed",
        "jsonld": jsonld,
        "home": {"title": str(home["title"]), "meta_description": str(home["meta_description"]), "h1": str(home["h1"]),
                 "intro": [str(p) for p in home.get("intro", [])]},
        "contact": {"title": str(contact["title"]), "meta_description": str(contact["meta_description"]),
                    "h1": str(contact["h1"]), "intro": [str(p) for p in contact.get("intro", [])]},
        "services": pages,
        "placeholder_images": True,
        "generated_by": "tools/build_site_config.py",
        "generated_on": (today or date.today()).isoformat(),
    }


def scaffold(site_dir: Path, refresh: bool) -> bool:
    if (site_dir / "package.json").is_file() and not refresh:
        return False
    site_dir.mkdir(parents=True, exist_ok=True)
    for item in TEMPLATE_DIR.iterdir():
        if item.name in SKIP_COPY or item.name == "site.config.json":
            continue
        dest = site_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*SKIP_COPY))
        else:
            shutil.copy2(item, dest)
    gitkeep = site_dir / ".gitkeep"
    if gitkeep.exists():
        gitkeep.unlink()
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write site/site.config.json from verified facts + site/content.yaml.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    parser.add_argument("--refresh-template", action="store_true", help="re-copy templates/site over the client site")
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        if client_dir.parent.name != "clients":
            raise ToolError("sites are built for clients only, not prospects")
        config = build(client_dir)
        site_dir = client_dir / "site"
        copied = scaffold(site_dir, args.refresh_template)
        (site_dir / "site.config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n",
                                                   encoding="utf-8", newline="\n")
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    rel = site_dir.relative_to(args.root).as_posix()
    print(f"{'scaffolded ' + rel + ' from templates/site; ' if copied else ''}wrote {rel}/site.config.json "
          f"({len(config['services'])} service page(s){', SYNTHETIC' if config['synthetic'] else ''})")
    print(f"next: cd {rel} && npm install && npm run build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
