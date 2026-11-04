"""tools/heatmap.py: PNG size, bands, before/after composite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from tests.helpers import ERR, hand_grid
from tools.heatmap import band, cell_text, keyword_slug, main, render_compare, render_single

KW = "barber bradford"


def test_bands() -> None:
    assert band(1, "ok") == "top3" and band(3, "ok") == "top3"
    assert band(4, "ok") == "4-10" and band(10, "ok") == "4-10"
    assert band(11, "ok") == "11-20" and band(20, "ok") == "11-20"
    assert band(None, "ok") == "not_found"
    assert band(None, "error") == "error"
    assert cell_text(None, "ok", 20) == "20+" and cell_text(None, "error", 20) == "ERR"


def test_keyword_slug() -> None:
    assert keyword_slug("Barber shop near me") == "barber-shop-near-me"


def test_single_png_size(tmp_path: Path) -> None:
    out = tmp_path / "h.png"
    render_single(hand_grid([[ERR, 2, None], [4, 1, 12], [7, 8, 9]]), KW, "baseline", out)
    with Image.open(out) as img:
        assert img.size == (800, 900)
        # centre cell (rank 1) must be painted green somewhere in the image
        colours = img.convert("RGB").getcolors(maxcolors=1 << 20) or []
        assert (46, 158, 68) in {c for _n, c in colours}


def test_compare_png_size(tmp_path: Path) -> None:
    out = tmp_path / "c.png"
    grid = hand_grid([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    render_compare(grid, grid, KW, "baseline", "final", out)
    with Image.open(out) as img:
        assert img.size == (1600, 900)


def test_cli_writes_single_and_composite(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    for label in ("baseline", "final"):
        (client / "scans" / label).mkdir(parents=True)
        (client / "scans" / label / "grid.json").write_text(json.dumps(hand_grid([[1, 2], [3, None]])),
                                                            encoding="utf-8")
    assert main(["--root", str(root), "--client", "_demo-barber", "--label", "final", "--compare", "baseline"]) == 0
    assert (client / "scans" / "final" / "heatmap-barber-bradford.png").is_file()
    assert (client / "scans" / "final" / "heatmap-barber-bradford-vs-baseline.png").is_file()


def test_cli_refuses_mismatched_compare(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    client = root / "clients" / "_demo-barber"
    for label, spacing in (("baseline", 1.0), ("final", 0.5)):
        (client / "scans" / label).mkdir(parents=True)
        (client / "scans" / label / "grid.json").write_text(
            json.dumps(hand_grid([[1, 2], [3, 4]], spacing_km=spacing)), encoding="utf-8")
    assert main(["--root", str(root), "--client", "_demo-barber", "--label", "final", "--compare", "baseline"]) == 1
    assert "not comparable" in capsys.readouterr().err
