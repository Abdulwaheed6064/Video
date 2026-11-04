"""Build competitors.json from one scan (docs/06 §5). Numbers come only from the scan.

Usage:
    uv run python tools/competitors.py --scan clients/<slug>/scans/<label>/grid.json --client <slug> [--top 10]

For every place seen in the scan except the client: name, category, rating, review count, website,
distance from the client's location, and per keyword how many valid grid points it holds a top-3 spot on
(and that as a share). Sorted by mean top-3 share (highest first), then reviews, then place_id.
Also writes `client` (the client's own numbers from the same scan) and `radius_table` (per keyword and
radius: client top-3 share, and the median and max review counts of places holding top-3 spots inside
that radius), which keyword-competitor uses for the radius recommendation.
Writes <client folder>/competitors.json (or --out). No network.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_json, schema_errors  # noqa: E402
from tools.grid import haversine_km  # noqa: E402

RADII_KM: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0)


def _share(n: int, d: int) -> float | None:
    return round(n / d, 4) if d else None


def _point_distance(p: dict[str, Any], center: list[float]) -> float:
    return float(p["distance_km"]) if "distance_km" in p else haversine_km(center[0], center[1], p["lat"], p["lng"])


def build(grid: dict[str, Any], source_scan: str, top: int | None = 10) -> dict[str, Any]:
    center = grid["params"]["center"]
    keywords: list[str] = list(grid["keywords"])
    places: dict[str, dict[str, Any]] = grid.get("places") or {}
    client_id = grid.get("client_place_id")

    valid = {kw: 0 for kw in keywords}
    holds: dict[str, dict[str, int]] = {}
    for p in grid["points"]:
        for kw in keywords:
            res = p["results"].get(kw)
            if not res or res["status"] != "ok":
                continue
            valid[kw] += 1
            for pid in res.get("top3", []):
                holds.setdefault(pid, {k: 0 for k in keywords})[kw] += 1

    ids = (set(places) | set(holds)) - {client_id}
    competitors = []
    for pid in ids:
        info = places.get(pid, {})
        counts = holds.get(pid, {k: 0 for k in keywords})
        lat, lng = info.get("lat"), info.get("lng")
        competitors.append({
            "place_id": pid,
            "name": info.get("name") or pid,
            "primary_category": info.get("primary_category"),
            "rating": info.get("rating"),
            "reviews": info.get("reviews"),
            "website": info.get("website"),
            "distance_km": (round(haversine_km(center[0], center[1], lat, lng), 2)
                            if lat is not None and lng is not None else None),
            "grid_top3_points": {kw: counts[kw] for kw in keywords},
            "grid_top3_share": {kw: _share(counts[kw], valid[kw]) for kw in keywords},
        })

    def sort_key(c: dict[str, Any]) -> tuple[float, int, str]:
        shares = [s for s in c["grid_top3_share"].values() if s is not None]
        mean = sum(shares) / len(shares) if shares else 0.0
        return (-mean, -(c["reviews"] if c["reviews"] is not None else -1), c["place_id"])

    competitors.sort(key=sort_key)
    if top is not None:
        competitors = competitors[:top]

    client_counts = holds.get(client_id, {k: 0 for k in keywords}) if client_id else {k: 0 for k in keywords}
    cinfo = places.get(client_id, {}) if client_id else {}
    client = {
        "place_id": client_id,
        "match": grid.get("client_match", "confirmed" if client_id else None),
        "name": cinfo.get("name"),
        "primary_category": cinfo.get("primary_category"),
        "rating": cinfo.get("rating"),
        "reviews": cinfo.get("reviews"),
        "grid_top3_share": {kw: _share(client_counts[kw], valid[kw]) for kw in keywords},
    }

    max_dist = max((_point_distance(p, center) for p in grid["points"]), default=0.0)
    full_radius = math.ceil(max_dist * 100 - 1e-9) / 100  # round UP so the farthest points stay inside
    radii = [r for r in RADII_KM if r < full_radius] + [full_radius]
    radius_table: dict[str, list[dict[str, Any]]] = {}
    for kw in keywords:
        rows = []
        for r in sorted(set(radii)):
            n_valid = n_client = 0
            holders: set[str] = set()
            for p in grid["points"]:
                res = p["results"].get(kw)
                if not res or res["status"] != "ok" or _point_distance(p, center) > r + 1e-9:
                    continue
                n_valid += 1
                if res["client_rank"] is not None and res["client_rank"] <= 3:
                    n_client += 1
                holders.update(pid for pid in res.get("top3", []) if pid != client_id)
            reviews = [places[h]["reviews"] for h in holders
                       if h in places and isinstance(places[h].get("reviews"), int)]
            rows.append({
                "radius_km": r,
                "valid_points": n_valid,
                "client_top3_points": n_client,
                "client_top3_share": _share(n_client, n_valid),
                "top3_competitors": len(holders),
                "top3_competitor_reviews_median": statistics.median(reviews) if reviews else None,
                "top3_competitor_reviews_max": max(reviews) if reviews else None,
            })
        radius_table[kw] = rows

    return {
        "schema_version": 1,
        "synthetic": bool(grid.get("synthetic")),
        "source_scan": source_scan,
        "keywords": keywords,
        "client": client,
        "competitors": competitors,
        "radius_table": radius_table,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract the competitor table from a scan (writes competitors.json).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--scan", required=True, type=Path, help="path to scans/<label>/grid.json")
    parser.add_argument("--client", required=True)
    parser.add_argument("--top", type=int, default=10, help="keep the top N competitors (0 = all)")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root).resolve()
        scan_path = (args.scan if args.scan.is_absolute() else Path.cwd() / args.scan).resolve()
        if not scan_path.is_relative_to(client_dir):
            raise ToolError(f"scan {args.scan} is not inside {client_dir} (one client folder per run)")
        if not scan_path.is_file():
            raise ToolError(f"missing {scan_path}")
        grid = load_json(scan_path)
        errors = schema_errors("grid", grid)
        if errors:
            raise ToolError(f"{scan_path} is invalid: {errors[0]}")
        data = build(grid, scan_path.relative_to(client_dir).as_posix(), args.top or None)
        errors = schema_errors("competitors", data)
        if errors:
            raise ToolError(f"generated competitors.json is invalid: {errors[0]}")
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    out = args.out or client_dir / "competitors.json"
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    tag = "SYNTHETIC " if data["synthetic"] else ""
    shown = out.resolve().relative_to(args.root.resolve()).as_posix() if out.resolve().is_relative_to(args.root.resolve()) else out.as_posix()
    print(f"{tag}competitors written: {shown} ({len(data['competitors'])} competitors, "
          f"source {data['source_scan']})")
    for c in data["competitors"][:5]:
        shares = ", ".join(f"{k}: {v}" for k, v in c["grid_top3_share"].items())
        print(f"  {c['name']}: reviews {c['reviews']}, rating {c['rating']}, {c['distance_km']} km, top3 share {shares}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
