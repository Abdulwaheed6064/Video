"""tools/fixture_scan.py: fixture-only, deterministic, plausible shape."""

from __future__ import annotations

from pathlib import Path
from statistics import mean

import pytest

from tests.conftest import write_client
from tools.common import ToolError, load_json, load_yaml, schema_errors
from tools.fixture_scan import main, make_scan


@pytest.fixture
def demo(root: Path) -> dict:
    return load_yaml(root / "clients" / "_demo-barber" / "client.yaml")


def _ranks(scan: dict, kw: str) -> list[tuple[float, int | None]]:
    return [(p["distance_km"], p["results"][kw]["client_rank"]) for p in scan["points"]
            if p["results"][kw]["status"] == "ok"]


def test_refuses_non_fixture_client(root: Path) -> None:
    write_client(root, "real-shop", "pilot", 15)
    assert main(["--root", str(root), "--client", "real-shop", "--label", "baseline"]) == 2
    assert not (root / "clients" / "real-shop" / "scans" / "baseline" / "grid.json").exists()
    with pytest.raises(ToolError):
        make_scan(load_yaml(root / "clients" / "real-shop" / "client.yaml"), "baseline", 7)


def test_same_seed_identical_output(root: Path) -> None:
    out = root / "clients" / "_demo-barber" / "scans" / "baseline" / "grid.json"
    assert main(["--root", str(root), "--client", "_demo-barber", "--label", "baseline", "--seed", "3"]) == 0
    first = out.read_bytes()
    assert main(["--root", str(root), "--client", "_demo-barber", "--label", "baseline", "--seed", "3"]) == 0
    assert out.read_bytes() == first
    assert main(["--root", str(root), "--client", "_demo-barber", "--label", "baseline", "--seed", "4"]) == 0
    assert out.read_bytes() != first


def test_shape_and_markers(demo: dict) -> None:
    scan = make_scan(demo, "baseline", 7)
    assert schema_errors("grid", scan) == []
    assert scan["synthetic"] is True and scan["cost_usd"] == 0 and scan["provider"] == "fixture"
    error_points = [p for p in scan["points"] if any(r["status"] == "error" for r in p["results"].values())]
    assert len(error_points) == 2
    not_found = [r for kw in scan["keywords"] for _d, r in _ranks(scan, kw) if r is None]
    assert not_found, "expected some not-found points"
    assert all(pid.startswith("fx-") for pid in scan["places"])


def test_worse_far_from_centre(demo: dict) -> None:
    scan = make_scan(demo, "baseline", 7)
    depth = scan["params"]["depth"]
    for kw in scan["keywords"]:
        ranks = _ranks(scan, kw)
        near = [r if r is not None else depth + 1 for d, r in ranks if d <= 1.0]
        far = [r if r is not None else depth + 1 for d, r in ranks if d >= 2.0]
        assert mean(near) < mean(far)


def test_improves_baseline_mid_final(demo: dict) -> None:
    def avg(label: str, kw: str) -> float:
        scan = make_scan(demo, label, 7)
        return mean(r if r is not None else 21 for _d, r in _ranks(scan, kw))

    for kw in demo["target"]["keywords"]:
        assert avg("baseline", kw) > avg("mid", kw) > avg("final", kw)


def test_competitor_ids_stable_across_labels(demo: dict) -> None:
    a, b = make_scan(demo, "baseline", 7), make_scan(demo, "final", 7)
    assert set(a["places"]) == set(b["places"])
    assert a["places"]["fx-place-01"]["name"] == b["places"]["fx-place-01"]["name"]


def test_cli_writes_valid_file(root: Path) -> None:
    assert main(["--root", str(root), "--client", "_demo-barber", "--label", "mid"]) == 0
    grid = load_json(root / "clients" / "_demo-barber" / "scans" / "mid" / "grid.json")
    assert schema_errors("grid", grid) == []


def test_bad_label_refused(root: Path) -> None:
    assert main(["--root", str(root), "--client", "_demo-barber", "--label", "../x"]) == 2
