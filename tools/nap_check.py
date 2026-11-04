"""Compare directory listings (citations/found.csv) with the verified NAP and draft citations/plan.csv.

Usage:
    uv run python tools/nap_check.py --client <slug> [--top 15]

Inputs:
- verified facts: name, phone(s), website; address from client.yaml location (owner-confirmed);
- clients/<slug>/citations/found.csv: directory, listing_url, name, address, phone, website, found_by, found_on
  (what the operator or a script saw on each directory; one row per listing);
- knowledge/citations-canada.csv (directories that apply to the client's niche and town).
Normalises Canadian formats before comparing: St/Street, Rd/Road, W/West…; unit "Unit 5" / "#5" / "5-123";
postal code case/spacing; ON/Ontario; phone +1/dashes/brackets; website scheme/www/trailing slash.
Status per listing: correct | wrong (field diffs) | duplicate (same directory listed more than once);
directories in the knowledge list with no listing: missing.
Writes citations/nap-report.md and a DRAFT citations/plan.csv (wrong -> duplicate -> missing, then
priority, top N), which the citation agent reviews. Exit 0 if every listing is correct, 1 otherwise.
No network.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml  # noqa: E402
from tools.schema_gen import verified_facts  # noqa: E402

FOUND_FIELDS = ["directory", "listing_url", "name", "address", "phone", "website", "found_by", "found_on"]
PLAN_FIELDS = ["directory", "url", "status", "fields_to_fix", "enter_name", "enter_address", "enter_phone",
               "enter_website", "who", "priority", "notes"]
STREET_TYPES = {"st": "street", "str": "street", "rd": "road", "ave": "avenue", "av": "avenue", "blvd": "boulevard",
                "dr": "drive", "cres": "crescent", "cr": "crescent", "ct": "court", "crt": "court", "ln": "lane",
                "hwy": "highway", "pkwy": "parkway", "pl": "place", "sq": "square", "trl": "trail", "terr": "terrace",
                "cir": "circle", "gdns": "gardens", "pt": "point", "conc": "concession", "sdrd": "sideroad"}
DIRECTIONS = {"w": "west", "e": "east", "n": "north", "s": "south", "nw": "northwest", "ne": "northeast",
              "sw": "southwest", "se": "southeast"}
PROVINCES = {"on", "ontario"}
COUNTRY = {"canada", "ca"}
POSTAL = re.compile(r"\b([abceghj-nprstvxy]\d[abceghj-nprstv-z])\s*(\d[abceghj-nprstv-z]\d)\b", re.I)
UNIT_WORD = re.compile(r"\b(?:unit|suite|ste|apt|apartment)\s*#?\s*([a-z0-9]+)\b|#\s*([a-z0-9]+)\b", re.I)
UNIT_DASH = re.compile(r"^\s*([a-z0-9]+)\s*-\s*(\d+\b)", re.I)
OWNER_DIRECTORIES = ("facebook", "booksy", "fresha", "styleseat")


@dataclass(frozen=True)
class Address:
    unit: str | None
    tokens: tuple[str, ...]
    postal: str | None


def norm_postal(text: str) -> str | None:
    m = POSTAL.search(text or "")
    return (m.group(1) + " " + m.group(2)).upper() if m else None


def norm_address(text: str) -> Address:
    s = re.sub(r"\([^)]*\)", " ", text or "").lower()
    postal = norm_postal(s)
    s = POSTAL.sub(" ", s)
    unit = None
    m = UNIT_WORD.search(s)
    if m:
        unit = (m.group(1) or m.group(2)).lower()
        s = s[: m.start()] + " " + s[m.end():]
    else:
        m = UNIT_DASH.match(s)
        if m:
            unit = m.group(1).lower()
            s = m.group(2) + s[m.end():]
    words = re.findall(r"[a-z0-9]+", s)
    out = []
    for w in words:
        w = STREET_TYPES.get(w, w)
        w = DIRECTIONS.get(w, w)
        if w in PROVINCES or w in COUNTRY:
            continue
        out.append(w)
    return Address(unit=unit, tokens=tuple(out), postal=postal)


def norm_phone(text: str) -> str:
    return re.sub(r"\D", "", text or "")[-10:]


def norm_website(text: str) -> str:
    s = (text or "").strip().lower()
    s = re.sub(r"^https?://", "", s)
    s = s.removeprefix("www.")
    s = s.split("?")[0].split("#")[0]
    return s.rstrip("/")


def norm_name(text: str) -> str:
    s = re.sub(r"\([^)]*\)", " ", text or "").lower().replace("&", " and ")
    return " ".join(re.findall(r"[a-z0-9]+", s))


def compare_address(verified: Address, listed: Address) -> list[str]:
    diffs = []
    if verified.tokens != listed.tokens:
        diffs.append("address")
    elif (verified.unit or None) != (listed.unit or None):
        diffs.append("address (unit)")
    if verified.postal and listed.postal != verified.postal:
        diffs.append("postal code" if listed.postal else "postal code missing")
    return diffs


@dataclass
class Verified:
    name: str
    phones: list[str]
    website: str | None
    address: str | None
    address_public: bool


def load_verified(client_dir: Path) -> Verified:
    client = load_yaml(client_dir / "client.yaml")
    facts = verified_facts(client_dir)
    if not facts.get("name") or not facts.get("phone"):
        raise ToolError("need verified name and phone facts before checking citations")
    loc = client.get("location") or {}
    public = bool(loc.get("address_public", True)) and client.get("business_type") != "service_area"
    return Verified(name=str(facts["name"][0]["value"]), phones=[str(f["value"]) for f in facts["phone"]],
                    website=str(facts["website"][0]["value"]) if facts.get("website") else None,
                    address=loc.get("address"), address_public=public)


def check_listing(v: Verified, row: dict[str, str]) -> list[str]:
    diffs = []
    if norm_name(row.get("name", "")) != norm_name(v.name):
        diffs.append("name")
    if norm_phone(row.get("phone", "")) not in {norm_phone(p) for p in v.phones}:
        diffs.append("phone")
    if v.website and norm_website(row.get("website", "")) != norm_website(v.website):
        diffs.append("website" if row.get("website") else "website missing")
    listed_addr = (row.get("address") or "").strip()
    if v.address_public:
        if not listed_addr:
            diffs.append("address missing")
        elif v.address:
            diffs += compare_address(norm_address(v.address), norm_address(listed_addr))
    elif listed_addr and re.search(r"\d", listed_addr):
        diffs.append("address shown for a hidden-address business")
    return diffs


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(fh)]


def directories_for(root: Path, client: dict[str, Any]) -> list[dict[str, str]]:
    path = root / "knowledge" / "citations-canada.csv"
    if not path.is_file():
        raise ToolError(f"missing {path}")
    niche = str(client.get("niche"))
    groups = {"all"} | ({"barber", "salon"} if niche == "barber" else {"pest", "trades"} if niche == "pest-control"
                        else {niche})
    towns = {t.lower() for t in client.get("service_area") or []}
    out = []
    for r in read_csv(path):
        applies = {a.strip() for a in r.get("applies_to", "").split(";")}
        if not applies & groups:
            continue
        if r.get("town") and r["town"].lower() not in towns:
            continue
        out.append(r)
    return out


def analyse(root: Path, client_dir: Path) -> dict[str, Any]:
    client = load_yaml(client_dir / "client.yaml")
    v = load_verified(client_dir)
    found_path = client_dir / "citations" / "found.csv"
    found = read_csv(found_path) if found_path.is_file() else []
    if found and set(FOUND_FIELDS) - set(found[0]):
        raise ToolError(f"{found_path}: columns must be {','.join(FOUND_FIELDS)}")
    listings = [{**r, "diffs": check_listing(v, r)} for r in found]
    # Per directory: the primary listing is the first one that matches (else the first one);
    # every other listing on the same directory is a duplicate to remove or merge.
    primary: dict[str, int] = {}
    for i, item in enumerate(listings):
        key = item["directory"].lower()
        if key not in primary or (listings[primary[key]]["diffs"] and not item["diffs"]):
            primary[key] = i
    for i, item in enumerate(listings):
        if primary[item["directory"].lower()] != i:
            item["status"] = "duplicate"
        else:
            item["status"] = "wrong" if item["diffs"] else "correct"
    known = directories_for(root, client)
    found_names = {r["directory"].lower() for r in found}
    missing = [d for d in known if d["name"].lower() not in found_names]
    return {"verified": v, "listings": listings, "missing": missing, "known": {d["name"].lower(): d for d in known}}


def plan_rows(result: dict[str, Any], top: int) -> list[dict[str, str]]:
    v: Verified = result["verified"]
    order = {"wrong": 0, "duplicate": 1, "missing": 2}
    rows = []
    for item in result["listings"]:
        if item["status"] == "correct":
            continue
        meta = result["known"].get(item["directory"].lower(), {})
        rows.append({"directory": item["directory"], "url": item.get("listing_url") or meta.get("url", ""),
                     "status": item["status"],
                     "fields_to_fix": "; ".join(item["diffs"]) if item["status"] == "wrong"
                     else "remove or merge into the correct listing",
                     "priority": meta.get("priority", "3"), "notes": ""})
    for d in result["missing"]:
        rows.append({"directory": d["name"], "url": d.get("url", ""), "status": "missing", "fields_to_fix": "create listing",
                     "priority": d.get("priority", "3"), "notes": d.get("how_to_claim", "")})
    for r in rows:
        r.update({"enter_name": v.name, "enter_address": (v.address or "") if v.address_public else "(hidden: service area only)",
                  "enter_phone": v.phones[0], "enter_website": v.website or "",
                  "who": "owner" if any(o in r["directory"].lower() for o in OWNER_DIRECTORIES) else "operator"})
    rows.sort(key=lambda r: (order[r["status"]], int(r["priority"] or 3), r["directory"].lower()))
    return rows[:top]


def write_outputs(client_dir: Path, result: dict[str, Any], plan: list[dict[str, str]], day: str,
                  synthetic: bool) -> None:
    cit = client_dir / "citations"
    cit.mkdir(parents=True, exist_ok=True)
    with (cit / "plan.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PLAN_FIELDS, lineterminator="\n")
        w.writeheader()
        for r in plan:
            w.writerow({k: r.get(k, "") for k in PLAN_FIELDS})
    v: Verified = result["verified"]
    tag = " SYNTHETIC" if synthetic else ""
    counts = Counter(item["status"] for item in result["listings"])
    lines = [f"# NAP report{tag}: {v.name}", "",
             f"Generated by `tools/nap_check.py` on {day}. Verified NAP: **{v.name}** · "
             f"{v.address if v.address_public else '(address hidden, service area)'} · {', '.join(v.phones)} · {v.website or '-'}",
             "",
             f"Listings checked: {len(result['listings'])} (correct {counts.get('correct', 0)}, wrong {counts.get('wrong', 0)}, "
             f"duplicate {counts.get('duplicate', 0)}). Directories with no listing found: {len(result['missing'])}.",
             "", "| Directory | Status | Differences | Listed name | Listed address | Listed phone | Listed website |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for item in result["listings"]:
        lines.append(f"| {item['directory']} | {item['status']} | {', '.join(item['diffs']) or '-'} | {item.get('name', '')} | "
                     f"{item.get('address', '')} | {item.get('phone', '')} | {item.get('website', '')} |")
    lines += ["", "## Not found (missing)", ""]
    lines += [f"- {d['name']} (priority {d.get('priority')})" for d in result["missing"]] or ["- none"]
    lines += ["", f"Draft plan: `citations/plan.csv` ({len(plan)} rows; wrong first, then duplicates, then missing). "
              "The citation agent reviews it; the operator/owner applies it by hand."]
    (cit / "nap-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diff citations/found.csv against verified NAP; draft plan.csv.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        result = analyse(args.root, client_dir)
        plan = plan_rows(result, args.top)
        client = load_yaml(client_dir / "client.yaml")
        write_outputs(client_dir, result, plan, args.date or date.today().isoformat(), client.get("mode") == "fixture")
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    bad = [i for i in result["listings"] if i["status"] != "correct"]
    for i in result["listings"]:
        print(f"{i['status']:9} {i['directory']}: {', '.join(i['diffs']) or 'matches verified NAP'}")
    print(f"missing   {len(result['missing'])} directories with no listing")
    print(f"wrote citations/nap-report.md and citations/plan.csv ({len(plan)} rows)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
