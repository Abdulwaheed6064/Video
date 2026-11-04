"""tools/metrics.py on hand-built 3×3 grids."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers import ERR, hand_grid
from tools.common import ToolError, load_json, schema_errors
from tools.metrics import compute, delta, main

KW = "barber bradford"


def test_all_found() -> None:
    grid = hand_grid([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    m = compute(grid, radius_km=1.0, label="baseline")["keywords"][KW]
    assert m["valid_points"] == 9 and m["error_points"] == 0 and m["found_points"] == 9
    assert m["top3_points"] == 3 and m["top3_share"] == pytest.approx(0.3333)
    assert m["found_share"] == 1.0
    assert m["arp_found_only"] == 5.0 and m["arp_not_found_as_depth_plus_1"] == 5.0
    # radius 1.0 km at 1 km spacing: centre + 4 orthogonal neighbours (ranks 2, 4, 5, 6, 8)
    assert m["target_radius"]["valid_points"] == 5 and m["target_radius"]["top3_points"] == 1


def test_some_not_found() -> None:
    grid = hand_grid([[None, 2, None], [4, 1, 6], [None, 8, None]])
    m = compute(grid, 1.0, "baseline")["keywords"][KW]
    assert m["found_points"] == 5 and m["valid_points"] == 9
    assert m["arp_found_only"] == pytest.approx((2 + 4 + 1 + 6 + 8) / 5, abs=0.01)
    assert m["arp_not_found_as_depth_plus_1"] == pytest.approx((2 + 4 + 1 + 6 + 8 + 4 * 21) / 9, abs=0.01)
    assert m["found_share"] == pytest.approx(0.5556)


def test_error_points_excluded_and_listed() -> None:
    grid = hand_grid([[ERR, 2, 3], [4, 1, 6], [7, 8, ERR]])
    m = compute(grid, 1.0, "baseline")["keywords"][KW]
    assert m["valid_points"] == 7 and m["error_points"] == 2
    assert m["error_cells"] == [[0, 0], [2, 2]]
    assert m["arp_found_only"] == pytest.approx((2 + 3 + 4 + 1 + 6 + 7 + 8) / 7, abs=0.01)


def test_zero_baseline_uses_from_to() -> None:
    base = hand_grid([[None] * 3 for _ in range(3)])
    final = hand_grid([[None, 2, None], [5, 1, 3], [None, None, None]])
    m = compute(final, 1.0, "final", base, "baseline")
    d = m["keywords"][KW]["delta"]
    assert d["top3_points"] == {"from": 0, "to": 3}
    assert d["found_points"] == {"from": 0, "to": 4}
    assert d["arp_found_only"]["change"] is None  # baseline had no found points
    assert d["arp_not_found_as_depth_plus_1"]["pct_change"] == pytest.approx(
        round((m["keywords"][KW]["arp_not_found_as_depth_plus_1"] - 21) / 21 * 100, 1))
    assert d["guarantee_option_a_met"] is True
    assert m["baseline_scan"] == "scans/baseline/grid.json"


def test_positive_baseline_pct() -> None:
    assert delta(4, 6) == {"baseline": 4, "current": 6, "change": 2, "pct_change": 50.0}
    assert delta(0, 5) == {"from": 0, "to": 5}
    assert delta(None, 5)["change"] is None


def test_refuses_mismatched_params() -> None:
    base = hand_grid([[1, 2, 3], [4, 5, 6], [7, 8, 9]], spacing_km=1.0)
    final = hand_grid([[1, 2, 3], [4, 5, 6], [7, 8, 9]], spacing_km=0.5)
    with pytest.raises(ToolError, match="spacing_km"):
        compute(final, 1.0, "final", base, "baseline")
    with pytest.raises(ToolError, match="keywords"):
        compute(hand_grid([[1]], keyword="other"), 1.0, "final", hand_grid([[1]]), "baseline")
    with pytest.raises(ToolError, match="synthetic"):
        compute(hand_grid([[1]], synthetic=False), 1.0, "final", hand_grid([[1]]), "baseline")


def test_reviews_delta() -> None:
    base = hand_grid([[1]], reviews=10)
    final = hand_grid([[1]], reviews=16)
    m = compute(final, 1.0, "final", base, "baseline")
    assert m["reviews"] == {"count": 16, "rating": 4.5}
    assert m["reviews_delta"]["change"] == 6


def test_output_matches_schema() -> None:
    grid = hand_grid([[ERR, 2, None], [4, 1, 6], [7, 8, 9]])
    assert schema_errors("metrics", compute(grid, 1.5, "baseline")) == []


def test_cli_writes_file_and_refuses_mismatch(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    for label, spacing in (("baseline", 1.0), ("final", 0.5)):
        (client / "scans" / label).mkdir(parents=True)
        (client / "scans" / label / "grid.json").write_text(
            json.dumps(hand_grid([[1, 2, 3], [4, 5, 6], [7, 8, 9]], spacing_km=spacing)), encoding="utf-8")
    args = ["--root", str(root), "--client", "_demo-barber"]
    assert main([*args, "--label", "baseline"]) == 0
    assert load_json(client / "scans" / "baseline" / "metrics.json")["keywords"][KW]["top3_points"] == 3
    assert main([*args, "--label", "final", "--baseline", "baseline"]) == 1
    assert not (client / "scans" / "final" / "metrics.json").exists()
