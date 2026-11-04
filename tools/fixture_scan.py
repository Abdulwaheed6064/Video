"""Deterministic fake grid scan for fixture-mode clients ONLY (docs/03 §5).

Usage:
    uv run python tools/fixture_scan.py --client _demo-barber --label baseline [--seed 7]

Writes clients/<slug>/scans/<label>/grid.json with `synthetic: true`, `cost_usd: 0` and
provider `fixture`. The numbers are made up to exercise metrics, heatmaps and reports, and
they are NEVER evidence about a real business:
- ranks get worse with distance from the centre and improve baseline -> mid -> final
  (any other label is treated like final);
- exactly 2 grid points fail with `status: error`; far points may be not found (`client_rank: null`);
- 6 fake competitors with stable place_ids appear in each point's top 3.
The same client, label and seed always give byte-identical output. Refuses any client whose
client.yaml mode is not `fixture`. No network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import (  # noqa: E402
    REPO_ROOT,
    ToolError,
    find_client_dir,
    load_yaml,
    scan_dir,
    schema_errors,
)
from tools.grid import build_grid, haversine_km  # noqa: E402

STAGES: dict[str, int] = {"baseline": 0, "mid": 1, "final": 2}
DAY_OFFSET: dict[str, int] = {"baseline": 1, "mid": 10, "final": 20}
# Per-keyword shape: (rank at centre, rank lost per km, rank gained per stage).
PROFILES: tuple[tuple[float, float, float], ...] = ((1.0, 6.5, 2.5), (2.0, 5.0, 2.0), (2.5, 8.0, 3.0))
N_COMPETITORS = 6
N_ERROR_POINTS = 2


def _rng(*parts: object) -> random.Random:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _scan_date(client: dict[str, Any], label: str) -> date:
    try:
        return date.fromisoformat(label)
    except ValueError:
        pass
    start = date.fromisoformat(str(client.get("sprint_start") or client["created"]))
    return start + timedelta(days=DAY_OFFSET.get(label, DAY_OFFSET["final"]))


def make_scan(client: dict[str, Any], label: str, seed: int) -> dict[str, Any]:
    if client.get("mode") != "fixture":
        raise ToolError(f"client {client.get('slug')!r} is in mode {client.get('mode')!r}: "
                        "fixture_scan.py only runs for mode: fixture (use rank_scan.py for real data)")
    slug = str(client["slug"])
    scan = client["scan"]
    depth = int(scan.get("depth", 20))
    lat, lng = float(client["location"]["lat"]), float(client["location"]["lng"])
    size, spacing = int(scan["grid_size"]), float(scan["spacing_km"])
    keywords: list[str] = list(client["target"]["keywords"])
    stage = STAGES.get(label, STAGES["final"])
    points = build_grid(lat, lng, size, spacing)

    # Fake competitors: stable across labels for the same client + seed.
    comp_rng = _rng(seed, slug, "competitors")
    places: dict[str, dict[str, Any]] = {}
    client_id = str(client.get("place_id") or f"fx-client-{slug.strip('_')}")
    places[client_id] = {
        "name": str(client["display_name"]), "primary_category": "Barber shop", "rating": 4.6,
        "reviews": 18 + 6 * stage, "website": None, "lat": lat, "lng": lng,
    }
    competitors: list[str] = []
    for i in range(1, N_COMPETITORS + 1):
        pid = f"fx-place-{i:02d}"
        competitors.append(pid)
        places[pid] = {
            "name": f"Synthetic Competitor {i} (fixture)",
            "primary_category": "Barber shop",
            "rating": round(comp_rng.uniform(4.1, 4.9), 1),
            "reviews": comp_rng.randint(30, 250) + 2 * stage,
            "website": f"https://competitor-{i}.example.test",
            "lat": round(lat + comp_rng.uniform(-0.02, 0.02), 6),
            "lng": round(lng + comp_rng.uniform(-0.03, 0.03), 6),
        }

    # Exactly N_ERROR_POINTS failing points (never the centre), fixed for this scan.
    centre = ((size - 1) // 2, (size - 1) // 2)
    cells = [(p["row"], p["col"]) for p in points if (p["row"], p["col"]) != centre]
    errors = set(_rng(seed, slug, label, "errors").sample(cells, min(N_ERROR_POINTS, len(cells))))

    out_points: list[dict[str, Any]] = []
    for p in points:
        results: dict[str, dict[str, Any]] = {}
        for k, kw in enumerate(keywords):
            if (p["row"], p["col"]) in errors:
                results[kw] = {"client_rank": None, "top3": [], "status": "error",
                               "error": "synthetic provider timeout"}
                continue
            base, per_km, gain = PROFILES[k % len(PROFILES)]
            r = _rng(seed, slug, label, kw, p["row"], p["col"])
            raw = base + p["distance_km"] * per_km - stage * gain + r.uniform(-1.5, 1.5)
            rank: int | None = max(1, round(raw))
            if rank > depth:
                rank = None
            ordered = sorted(competitors, key=lambda pid: haversine_km(
                p["lat"], p["lng"], places[pid]["lat"], places[pid]["lng"]) + r.uniform(0, 1.5))
            top3 = ordered[:3]
            if rank is not None and rank <= 3:
                top3 = (ordered[: rank - 1] + [client_id] + ordered[rank - 1:])[:3]
            results[kw] = {"client_rank": rank, "top3": top3, "status": "ok"}
        out_points.append({**p, "results": results})

    organic: list[dict[str, Any]] = []
    north = next(p for p in points if p["row"] == 0 and p["col"] == centre[1])
    for k, kw in enumerate(keywords):
        for name, pt, extra in (("shop", {"lat": lat, "lng": lng}, 0), ("grid-north-edge", north, 6)):
            r = _rng(seed, slug, label, kw, "organic", name)
            pos: int | None = max(1, 12 + 3 * k + extra - 4 * stage + r.randint(-1, 1))
            organic.append({"point": name, "lat": pt["lat"], "lng": pt["lng"], "keyword": kw,
                            "position": pos if pos <= depth else None, "status": "ok"})

    tz = ZoneInfo(str(client.get("timezone", "America/Toronto")))
    created = datetime.combine(_scan_date(client, label), time(10, 0), tzinfo=tz).isoformat(timespec="seconds")
    return {
        "schema_version": 1,
        "synthetic": True,
        "provider": "fixture",
        "endpoint": "fixture/maps",
        "params": {"grid_size": size, "spacing_km": spacing, "center": [lat, lng],
                   "device": scan["device"], "language": scan["language"], "depth": depth},
        "keywords": keywords,
        "client_place_id": client_id,
        "places": places,
        "points": out_points,
        "organic": organic,
        "complete": True,
        "cost_usd": 0,
        "created": created,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a deterministic SYNTHETIC grid.json (fixture clients only).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    parser.add_argument("--label", required=True, help="baseline | mid | final | YYYY-MM-DD | m<YYYY-MM>")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        client = load_yaml(client_dir / "client.yaml")
        scan = make_scan(client, args.label, args.seed)
        errors = schema_errors("grid", scan)
        if errors:
            raise ToolError(f"generated grid.json is invalid: {errors[0]}")
        out = scan_dir(client_dir, args.label) / "grid.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8", newline="\n")
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    n_err = sum(1 for p in scan["points"] if any(v["status"] == "error" for v in p["results"].values()))
    print(f"SYNTHETIC scan written: {out.relative_to(args.root).as_posix()} "
          f"({len(scan['points'])} points × {len(scan['keywords'])} keywords, {n_err} error points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
