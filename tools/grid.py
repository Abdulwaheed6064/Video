"""Build an N×N grid of search points around a centre (docs/07 §1).

Usage:
    uv run python tools/grid.py --client <slug>
    uv run python tools/grid.py --lat 44.1145 --lng -79.565 --size 7 --spacing-km 0.7

Row 0 is the northern edge, col 0 the western edge. Longitude spacing is corrected for
latitude, so neighbouring points are `spacing_km` apart on the ground. Each point records
its great-circle distance from the centre. Prints JSON to stdout (or --out FILE). No network.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml  # noqa: E402

EARTH_RADIUS_KM = 6371.0088  # IUGG mean radius


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def build_grid(lat: float, lng: float, size: int, spacing_km: float) -> list[dict[str, Any]]:
    """Return size×size points, row-major, row 0 = north, col 0 = west."""
    if size < 1:
        raise ToolError("grid size must be >= 1")
    if spacing_km <= 0:
        raise ToolError("spacing must be > 0 km")
    if not (-85 < lat < 85):
        raise ToolError("latitude out of range for a grid")
    half = (size - 1) / 2
    dlat = math.degrees(spacing_km / EARTH_RADIUS_KM)
    dlng = math.degrees(spacing_km / (EARTH_RADIUS_KM * math.cos(math.radians(lat))))
    points: list[dict[str, Any]] = []
    for row in range(size):
        for col in range(size):
            plat = round(lat + (half - row) * dlat, 6)
            plng = round(lng + (col - half) * dlng, 6)
            points.append({
                "row": row,
                "col": col,
                "lat": plat,
                "lng": plng,
                "distance_km": round(haversine_km(lat, lng, plat, plng), 3),
            })
    return points


def grid_for_client(client_dir: Path) -> dict[str, Any]:
    client = load_yaml(client_dir / "client.yaml")
    scan = client["scan"]
    loc = client["location"]
    return {
        "center": [loc["lat"], loc["lng"]],
        "grid_size": scan["grid_size"],
        "spacing_km": scan["spacing_km"],
        "points": build_grid(float(loc["lat"]), float(loc["lng"]), int(scan["grid_size"]),
                             float(scan["spacing_km"])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an N×N grid of search coordinates (JSON).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", help="client slug: use client.yaml centre and scan settings")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lng", type=float)
    parser.add_argument("--size", type=int, default=7)
    parser.add_argument("--spacing-km", type=float, default=1.0)
    parser.add_argument("--out", type=Path, help="write JSON here instead of stdout")
    args = parser.parse_args(argv)
    try:
        if args.client:
            data = grid_for_client(find_client_dir(args.client, args.root))
        elif args.lat is not None and args.lng is not None:
            data = {"center": [args.lat, args.lng], "grid_size": args.size, "spacing_km": args.spacing_km,
                    "points": build_grid(args.lat, args.lng, args.size, args.spacing_km)}
        else:
            parser.error("give --client, or --lat and --lng")
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(data, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {len(data['points'])} points to {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
