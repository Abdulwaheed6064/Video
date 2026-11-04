"""Compute rank metrics from one scan, with deltas against a baseline (docs/07 §3).

Usage:
    uv run python tools/metrics.py --client <slug> --label <label> [--baseline <label>]

Reads scans/<label>/grid.json and writes scans/<label>/metrics.json. This script is the ONLY
source of rank numbers: agents and reports copy from metrics.json and never compute their own.

Per keyword:
- valid_points / error_points (error points are excluded from every metric and listed in error_cells)
- found_points, top3_points, found_share, top3_share
- arp_found_only (mean rank where found) and arp_not_found_as_depth_plus_1 (not found = depth+1)
- target_radius: top-3 share over points within client.yaml -> target.radius_km (the promise number)
- organic: position at each organic check point (null = not in top `depth`)
- delta vs baseline: {baseline, current, change, pct_change} when baseline > 0, else {from: 0, to: N}
Also: client review count/rating from scan data, and the option-A guarantee check
(ARP with not-found = depth+1 lower than baseline).
Refuses a comparison if the scan parameters, keywords or client place differ. No network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import (  # noqa: E402
    REPO_ROOT,
    ToolError,
    find_client_dir,
    load_json,
    load_yaml,
    scan_dir,
    schema_errors,
)
from tools.grid import haversine_km  # noqa: E402

DELTA_METRICS: tuple[str, ...] = (
    "arp_found_only", "arp_not_found_as_depth_plus_1", "found_points", "top3_points", "found_share",
    "top3_share",
)


def _share(n: int, d: int) -> float | None:
    return round(n / d, 4) if d else None


def _mean(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _distance(point: dict[str, Any], center: list[float]) -> float:
    if "distance_km" in point:
        return float(point["distance_km"])
    return haversine_km(center[0], center[1], point["lat"], point["lng"])


def keyword_metrics(grid: dict[str, Any], keyword: str, radius_km: float) -> dict[str, Any]:
    depth = int(grid["params"]["depth"])
    center = grid["params"]["center"]
    ranks: list[int | None] = []
    in_radius: list[int | None] = []
    error_cells: list[list[int]] = []
    for p in grid["points"]:
        res = p["results"].get(keyword)
        if res is None or res["status"] != "ok":
            error_cells.append([p["row"], p["col"]])
            continue
        ranks.append(res["client_rank"])
        if _distance(p, center) <= radius_km + 1e-9:
            in_radius.append(res["client_rank"])
    found = [r for r in ranks if r is not None]
    top3 = [r for r in found if r <= 3]
    radius_top3 = [r for r in in_radius if r is not None and r <= 3]
    organic = {o["point"]: (o["position"] if o["status"] == "ok" else "error")
               for o in grid.get("organic", []) if o["keyword"] == keyword}
    return {
        "valid_points": len(ranks),
        "error_points": len(error_cells),
        "error_cells": error_cells,
        "found_points": len(found),
        "top3_points": len(top3),
        "arp_found_only": _mean(found),
        "arp_not_found_as_depth_plus_1": _mean([r if r is not None else depth + 1 for r in ranks]),
        "top3_share": _share(len(top3), len(ranks)),
        "found_share": _share(len(found), len(ranks)),
        "target_radius": {
            "radius_km": radius_km,
            "valid_points": len(in_radius),
            "top3_points": len(radius_top3),
            "top3_share": _share(len(radius_top3), len(in_radius)),
        },
        "organic": organic,
    }


def delta(baseline: float | int | None, current: float | int | None) -> dict[str, Any]:
    """docs/07 §3: percentage only when baseline > 0, else 'from 0 to N'."""
    if baseline is None or current is None:
        return {"baseline": baseline, "current": current, "change": None}
    change = round(current - baseline, 4)
    if baseline > 0:
        return {"baseline": baseline, "current": current, "change": change,
                "pct_change": round(change / baseline * 100, 1)}
    return {"from": baseline, "to": current}


def comparable(current: dict[str, Any], base: dict[str, Any]) -> list[str]:
    problems = []
    for key in sorted(set(current["params"]) | set(base["params"])):
        if current["params"].get(key) != base["params"].get(key):
            problems.append(f"params.{key}: {base['params'].get(key)!r} (baseline) != "
                            f"{current['params'].get(key)!r}")
    if sorted(current["keywords"]) != sorted(base["keywords"]):
        problems.append(f"keywords differ: {base['keywords']} (baseline) != {current['keywords']}")
    if current.get("client_place_id") != base.get("client_place_id"):
        problems.append("client_place_id differs")
    if bool(current.get("synthetic")) != bool(base.get("synthetic")):
        problems.append("one scan is synthetic and the other is not")
    return problems


def _reviews(grid: dict[str, Any]) -> dict[str, Any] | None:
    pid = grid.get("client_place_id")
    place = (grid.get("places") or {}).get(pid) if pid else None
    if not place:
        return None
    return {"count": place.get("reviews"), "rating": place.get("rating")}


def compute(grid: dict[str, Any], radius_km: float, label: str,
            base: dict[str, Any] | None = None, base_label: str | None = None) -> dict[str, Any]:
    if base is not None:
        problems = comparable(grid, base)
        if problems:
            raise ToolError("scans are not comparable (start a new baseline instead):\n  - "
                            + "\n  - ".join(problems))
    keywords: dict[str, Any] = {}
    for kw in grid["keywords"]:
        m = keyword_metrics(grid, kw, radius_km)
        if base is not None:
            b = keyword_metrics(base, kw, radius_km)
            d = {name: delta(b[name], m[name]) for name in DELTA_METRICS}
            d["target_radius_top3_share"] = delta(b["target_radius"]["top3_share"],
                                                  m["target_radius"]["top3_share"])
            d["target_radius_top3_points"] = delta(b["target_radius"]["top3_points"],
                                                   m["target_radius"]["top3_points"])
            arp_b, arp_c = b["arp_not_found_as_depth_plus_1"], m["arp_not_found_as_depth_plus_1"]
            d["guarantee_option_a_met"] = (arp_b is not None and arp_c is not None and arp_c < arp_b)
            m["delta"] = d
        else:
            m["delta"] = None
        keywords[kw] = m
    out: dict[str, Any] = {
        "schema_version": 1,
        "synthetic": bool(grid.get("synthetic")),
        "label": label,
        "source_scan": f"scans/{label}/grid.json",
        "baseline_scan": f"scans/{base_label}/grid.json" if base is not None else None,
        "params": grid["params"],
        "complete": bool(grid.get("complete")),
        "provider": grid.get("provider"),
        "created": grid["created"],
        "reviews": _reviews(grid),
        "keywords": keywords,
    }
    if base is not None:
        rb, rc = _reviews(base), out["reviews"]
        out["reviews_delta"] = (delta(rb.get("count"), rc.get("count")) if rb and rc else None)
    return out


def _load_grid(client_dir: Path, label: str) -> dict[str, Any]:
    path = scan_dir(client_dir, label) / "grid.json"
    if not path.is_file():
        raise ToolError(f"missing {path}")
    grid = load_json(path)
    errors = schema_errors("grid", grid)
    if errors:
        raise ToolError(f"{path} is invalid: {errors[0]}")
    return grid


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute docs/07 §3 metrics for one scan (writes metrics.json).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--baseline", default=None, help="label of the scan to compare against")
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        client = load_yaml(client_dir / "client.yaml")
        radius = float(client["target"]["radius_km"])
        grid = _load_grid(client_dir, args.label)
        base = _load_grid(client_dir, args.baseline) if args.baseline else None
        metrics = compute(grid, radius, args.label, base, args.baseline)
        errors = schema_errors("metrics", metrics)
        if errors:
            raise ToolError(f"computed metrics.json is invalid: {errors[0]}")
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    out = scan_dir(client_dir, args.label) / "metrics.json"
    out.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8", newline="\n")
    tag = "SYNTHETIC " if metrics["synthetic"] else ""
    print(f"{tag}metrics written: {out.relative_to(args.root).as_posix()}")
    for kw, m in metrics["keywords"].items():
        line = (f"  {kw!r}: top3 {m['top3_points']}/{m['valid_points']}, found {m['found_points']}, "
                f"ARP(found) {m['arp_found_only']}, ARP(nf=depth+1) {m['arp_not_found_as_depth_plus_1']}, "
                f"radius top3 {m['target_radius']['top3_points']}/{m['target_radius']['valid_points']}, "
                f"errors {m['error_points']}")
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
