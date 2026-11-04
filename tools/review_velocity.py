"""Review count/rating over time, from scan data only → clients/<slug>/reviews/velocity.json.

Usage:
    uv run python tools/review_velocity.py --client <slug>

Reads every scans/<label>/grid.json that has the client's place in `places` (review count + rating are
provider data captured at scan time; docs/07 §3 "Reviews"). Probe scans (mode keywords-probe) are included
too, since they carry the same listing data. Points are ordered by scan date. For each consecutive pair it
computes delta_count, days and per_week = delta_count / (days / 7); `overall_per_week` covers first → last.
Weekly velocity is only as fine-grained as the scans (e.g. day 1, 10, 20). Never interpolated. No network.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_json, load_yaml, schema_errors  # noqa: E402


def collect(client_dir: Path) -> list[dict[str, Any]]:
    points = []
    for grid_path in sorted((client_dir / "scans").glob("*/grid.json")):
        grid = load_json(grid_path)
        pid = grid.get("client_place_id")
        place = (grid.get("places") or {}).get(pid) if pid else None
        if not place or place.get("reviews") is None:
            continue
        points.append({"label": grid_path.parent.name, "date": str(grid["created"])[:10],
                       "count": int(place["reviews"]), "rating": place.get("rating"),
                       "source": f"scans/{grid_path.parent.name}/grid.json", "synthetic": bool(grid.get("synthetic"))})
    points.sort(key=lambda p: (p["date"], p["label"]))
    return points


def _per_week(delta: int, days: int) -> float | None:
    return round(delta / (days / 7), 2) if days > 0 else None


def compute(points: list[dict[str, Any]]) -> dict[str, Any]:
    intervals = []
    for a, b in zip(points, points[1:]):
        days = (date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days
        delta = b["count"] - a["count"]
        intervals.append({"from": a["label"], "to": b["label"], "days": days, "delta_count": delta,
                          "per_week": _per_week(delta, days)})
    overall = None
    if len(points) >= 2:
        days = (date.fromisoformat(points[-1]["date"]) - date.fromisoformat(points[0]["date"])).days
        overall = _per_week(points[-1]["count"] - points[0]["count"], days)
    return {"points": [{k: p[k] for k in ("label", "date", "count", "rating", "source")} for p in points],
            "intervals": intervals, "overall_per_week": overall}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review velocity from scan data (writes reviews/velocity.json).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        client = load_yaml(client_dir / "client.yaml")
        points = collect(client_dir)
        if not points:
            raise ToolError("no scan with the client's review count yet (run a scan first)")
        data = {"schema_version": 1, "synthetic": client.get("mode") == "fixture" or any(p["synthetic"] for p in points),
                "client": args.client, **compute(points)}
        errors = schema_errors("velocity", data)
        if errors:
            raise ToolError(f"velocity.json would be invalid: {errors[0]}")
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    out = client_dir / "reviews" / "velocity.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    for p in data["points"]:
        print(f"{p['date']} {p['label']:10} reviews {p['count']} rating {p['rating']}")
    for i in data["intervals"]:
        print(f"  {i['from']} → {i['to']}: +{i['delta_count']} in {i['days']} days = {i['per_week']}/week")
    print(f"overall {data['overall_per_week']}/week · wrote {out.relative_to(args.root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
