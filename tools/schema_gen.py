"""LocalBusiness JSON-LD from VERIFIED facts only (agents/site-builder.md).

Usage:
    uv run python tools/schema_gen.py --client <slug> [--out FILE]

- schema.org @type comes from an allowlist: client.yaml `schema_type` if set, else the niche default
  (barber -> HairSalon, pest-control -> HomeAndConstructionBusiness). Anything else is refused.
- Only facts with status: verified are read; proposed/rejected facts are never used.
- Required: name, telephone, url, openingHoursSpecification, and address (storefront/hybrid) or
  areaServed (service-area). Missing any -> refused with the list.
- Service-area businesses get areaServed (towns) and NO street address or geo coordinates.
Prints JSON-LD (or writes --out). No network.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml  # noqa: E402

ALLOWED_TYPES: set[str] = {
    "LocalBusiness", "HairSalon", "BeautySalon", "NailSalon", "DaySpa", "HealthAndBeautyBusiness",
    "HomeAndConstructionBusiness", "Plumber", "Electrician", "HVACBusiness", "RoofingContractor",
    "GeneralContractor", "HousePainter", "Locksmith", "MovingCompany", "AutoRepair", "Dentist",
    "ProfessionalService",
}
NICHE_DEFAULT_TYPE: dict[str, str] = {"barber": "HairSalon", "pest-control": "HomeAndConstructionBusiness"}
DAYS: list[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_ABBR: dict[str, int] = {d[:3].lower(): i for i, d in enumerate(DAYS)}
SEGMENT = re.compile(r"^\s*([A-Za-z]{3})[a-z]*\s*(?:-\s*([A-Za-z]{3})[a-z]*)?\s+(closed|\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})\s*$",
                     re.I)


def parse_hours(text: str) -> list[dict[str, Any]]:
    """'Tue-Fri 10:00-19:00; Sat 09:00-17:00; Sun-Mon closed' -> [{days:[...], opens, closes}] (open days only)."""
    out: list[dict[str, Any]] = []
    for seg in text.split(";"):
        if not seg.strip():
            continue
        m = SEGMENT.match(seg)
        if not m:
            raise ToolError(f"cannot parse hours segment {seg.strip()!r}; use e.g. 'Tue-Fri 10:00-19:00; Sun closed'")
        a, b, value = m.group(1).lower(), (m.group(2) or m.group(1)).lower(), m.group(3).lower()
        if a not in DAY_ABBR or b not in DAY_ABBR:
            raise ToolError(f"unknown day in hours segment {seg.strip()!r}")
        i, j = DAY_ABBR[a], DAY_ABBR[b]
        days = [DAYS[(i + k) % 7] for k in range(((j - i) % 7) + 1)]
        if value == "closed":
            continue
        opens, closes = (v.strip() for v in value.split("-"))
        out.append({"days": days, "opens": opens.zfill(5), "closes": closes.zfill(5)})
    return out


def parse_address(address: str) -> dict[str, str]:
    """'1 Example St, Bradford, ON L3Z 0A1 (fictional)' -> PostalAddress fields (CA)."""
    clean = re.sub(r"\s*\([^)]*\)\s*$", "", address).strip()
    parts = [p.strip() for p in clean.split(",") if p.strip()]
    if len(parts) < 3:
        raise ToolError(f"address {address!r} needs 'street, town, province [postal code]'")
    region_postal = parts[2]
    m = re.match(r"^([A-Z]{2})\s*([A-Z]\d[A-Z]\s?\d[A-Z]\d)?$", region_postal.upper())
    if not m:
        raise ToolError(f"address {address!r}: expected a province code like 'ON' after the town")
    out = {"@type": "PostalAddress", "streetAddress": parts[0], "addressLocality": parts[1],
           "addressRegion": m.group(1), "addressCountry": "CA"}
    if m.group(2):
        out["postalCode"] = m.group(2)
    return out


def verified_facts(client_dir: Path) -> dict[str, list[dict[str, Any]]]:
    facts = load_yaml(client_dir / "facts.yaml") or {}
    out: dict[str, list[dict[str, Any]]] = {}
    for f in facts.get("facts", []):
        if f.get("status") == "verified":
            out.setdefault(str(f["key"]), []).append(f)
    return out


def phone_e164(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        digits = "1" + digits
    if len(digits) != 11 or not digits.startswith("1"):
        raise ToolError(f"phone {phone!r} is not a 10-digit North American number")
    return "+" + digits


def generate(client: dict[str, Any], facts: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    stype = str(client.get("schema_type") or NICHE_DEFAULT_TYPE.get(str(client.get("niche")), "LocalBusiness"))
    if stype not in ALLOWED_TYPES:
        raise ToolError(f"schema type {stype!r} is not in the allowlist: {', '.join(sorted(ALLOWED_TYPES))}")

    def first(key: str) -> str | None:
        return str(facts[key][0]["value"]) if facts.get(key) else None

    name, phone, url, hours = first("name"), first("phone"), first("website"), first("hours")
    missing = [k for k, v in (("name", name), ("telephone", phone), ("url", url),
                              ("openingHoursSpecification", hours)) if not v]
    sab = client.get("business_type") == "service_area" or not (client.get("location") or {}).get("address_public", True)
    area = [str(f["value"]) for f in facts.get("service_area", [])] or list(client.get("service_area") or [])
    address = (client.get("location") or {}).get("address")
    if sab and not area:
        missing.append("areaServed")
    if not sab and not address:
        missing.append("address")
    if missing:
        raise ToolError("cannot build JSON-LD; missing verified data: " + ", ".join(missing))

    data: dict[str, Any] = {"@context": "https://schema.org", "@type": stype, "name": name,
                            "telephone": phone_e164(str(phone)), "url": str(url).rstrip("/") + "/"}
    if sab:
        data["areaServed"] = [{"@type": "City", "name": t} for t in area]
    else:
        data["address"] = parse_address(str(address))
        loc = client["location"]
        data["geo"] = {"@type": "GeoCoordinates", "latitude": loc["lat"], "longitude": loc["lng"]}
        if area:
            data["areaServed"] = [{"@type": "City", "name": t} for t in area]
    data["openingHoursSpecification"] = [
        {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"], "opens": h["opens"], "closes": h["closes"]}
        for h in parse_hours(str(hours))
    ]
    services = [str(f["value"]) for f in facts.get("service", [])]
    if services:
        data["makesOffer"] = [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s}} for s in services]
    if first("booking_url"):
        data["potentialAction"] = {"@type": "ReserveAction", "target": first("booking_url")}
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LocalBusiness JSON-LD from verified facts (allowlisted types).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        data = generate(load_yaml(client_dir / "client.yaml"), verified_facts(client_dir))
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
