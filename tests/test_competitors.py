"""tools/competitors.py on a hand-built grid: shares correct, sorted, radius table."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers import ERR, hand_grid
from tools.common import load_json, schema_errors
from tools.competitors import build, main

KW = "barber bradford"


def _grid() -> dict:
    # 3x3, 1 km spacing; client rank at centre 1, elsewhere outside top 3; one error point.
    grid = hand_grid([[5, 6, ERR], [7, 1, 8], [9, 10, 11]], reviews=12)
    top3 = {
        (0, 0): ["A", "B", "C"], (0, 1): ["A", "B", "C"], (1, 0): ["A", "C", "B"],
        (1, 1): ["client-1", "A", "B"], (1, 2): ["B", "A", "C"], (2, 0): ["A", "B", "D"],
        (2, 1): ["A", "D", "B"], (2, 2): ["B", "D", "A"],
    }
    for p in grid["points"]:
        res = p["results"][KW]
        if res["status"] == "ok":
            res["top3"] = top3[(p["row"], p["col"])]
    grid["places"].update({
        "A": {"name": "Alpha", "reviews": 300, "rating": 4.8, "primary_category": "Barber shop",
              "website": "https://a.example.test", "lat": 44.1145, "lng": -79.565},
        "B": {"name": "Beta", "reviews": 100, "rating": 4.4, "primary_category": "Barber shop",
              "website": None, "lat": None, "lng": None},
        "C": {"name": "Gamma", "reviews": 50, "rating": 4.0, "primary_category": "Hair salon"},
        "D": {"name": "Delta", "reviews": None, "rating": None},
    })
    return grid


def test_shares_and_sorting() -> None:
    data = build(_grid(), "scans/baseline/grid.json", top=None)
    assert schema_errors("competitors", data) == []
    names = [c["name"] for c in data["competitors"]]
    assert names == ["Alpha", "Beta", "Gamma", "Delta"]
    by = {c["name"]: c for c in data["competitors"]}
    assert by["Alpha"]["grid_top3_points"][KW] == 8 and by["Alpha"]["grid_top3_share"][KW] == 1.0
    assert by["Beta"]["grid_top3_share"][KW] == 1.0  # B is in every top 3 too, fewer reviews -> second
    assert by["Gamma"]["grid_top3_points"][KW] == 4 and by["Gamma"]["grid_top3_share"][KW] == 0.5
    assert by["Delta"]["grid_top3_share"][KW] == 0.375
    assert by["Alpha"]["distance_km"] == 0.0 and by["Beta"]["distance_km"] is None
    assert "client-1" not in {c["place_id"] for c in data["competitors"]}


def test_client_summary_and_radius_table() -> None:
    data = build(_grid(), "scans/baseline/grid.json")
    assert data["client"]["reviews"] == 12 and data["client"]["grid_top3_share"][KW] == 0.125
    rows = {r["radius_km"]: r for r in data["radius_table"][KW]}
    assert rows[0.5]["valid_points"] == 1 and rows[0.5]["client_top3_points"] == 1
    assert rows[0.5]["top3_competitors"] == 2  # A and B at the centre
    assert rows[0.5]["top3_competitor_reviews_median"] == 200
    assert rows[1.0]["valid_points"] == 5  # centre + 4 neighbours (1 km)
    full = data["radius_table"][KW][-1]
    assert full["valid_points"] == 8 and full["top3_competitor_reviews_max"] == 300


def test_top_n() -> None:
    assert len(build(_grid(), "x", top=2)["competitors"]) == 2


def test_cli_and_one_folder_rule(root: Path, tmp_path: Path) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "scans" / "baseline").mkdir(parents=True)
    scan = client / "scans" / "baseline" / "grid.json"
    scan.write_text(json.dumps(_grid()), encoding="utf-8")
    assert main(["--root", str(root), "--scan", str(scan), "--client", "_demo-barber"]) == 0
    out = load_json(client / "competitors.json")
    assert out["source_scan"] == "scans/baseline/grid.json" and out["synthetic"] is True
    other = tmp_path / "elsewhere.json"
    other.write_text(json.dumps(_grid()), encoding="utf-8")
    assert main(["--root", str(root), "--scan", str(other), "--client", "_demo-barber"]) == 2


@pytest.mark.parametrize("top", [0, 3])
def test_cli_top(root: Path, top: int) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "scans" / "baseline").mkdir(parents=True)
    scan = client / "scans" / "baseline" / "grid.json"
    scan.write_text(json.dumps(_grid()), encoding="utf-8")
    assert main(["--root", str(root), "--scan", str(scan), "--client", "_demo-barber", "--top", str(top)]) == 0
    assert len(load_json(client / "competitors.json")["competitors"]) == (4 if top == 0 else 3)
