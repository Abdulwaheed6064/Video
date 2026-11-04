"""tools/grid.py: spacing, orientation, distances."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.common import ToolError
from tools.grid import build_grid, haversine_km, main


@pytest.mark.parametrize("spacing", [0.3, 0.7, 1.0, 2.5])
def test_spacing_within_2_percent_at_44n(spacing: float) -> None:
    pts = {(p["row"], p["col"]): p for p in build_grid(44.0, -79.5, 7, spacing)}
    for (r, c), p in pts.items():
        if (r, c + 1) in pts:  # east-west neighbour
            q = pts[(r, c + 1)]
            assert haversine_km(p["lat"], p["lng"], q["lat"], q["lng"]) == pytest.approx(spacing, rel=0.02)
        if (r + 1, c) in pts:  # north-south neighbour
            q = pts[(r + 1, c)]
            assert haversine_km(p["lat"], p["lng"], q["lat"], q["lng"]) == pytest.approx(spacing, rel=0.02)


def test_orientation_and_centre() -> None:
    pts = {(p["row"], p["col"]): p for p in build_grid(44.1145, -79.565, 7, 0.7)}
    assert len(pts) == 49
    centre = pts[(3, 3)]
    assert centre["lat"] == pytest.approx(44.1145) and centre["lng"] == pytest.approx(-79.565)
    assert centre["distance_km"] == 0
    assert pts[(0, 3)]["lat"] > centre["lat"]  # row 0 = north
    assert pts[(3, 0)]["lng"] < centre["lng"]  # col 0 = west
    assert pts[(0, 0)]["distance_km"] == pytest.approx(3 * 0.7 * 2 ** 0.5, rel=0.02)


def test_deterministic() -> None:
    assert build_grid(44.0, -79.0, 5, 1.0) == build_grid(44.0, -79.0, 5, 1.0)


def test_rejects_bad_input() -> None:
    with pytest.raises(ToolError):
        build_grid(44.0, -79.0, 0, 1.0)
    with pytest.raises(ToolError):
        build_grid(44.0, -79.0, 3, 0)


def test_cli_client(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--root", str(root), "--client", "_demo-barber"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["grid_size"] == 7 and len(data["points"]) == 49 and data["spacing_km"] == 0.7
