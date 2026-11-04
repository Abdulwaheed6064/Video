"""tools/validate.py: demo validates clean; bad files are caught with readable errors."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import DEMO
from tools.validate import main, validate_client_dir


def _grid(synthetic: bool | None = True) -> dict:
    grid = {
        "schema_version": 1,
        "provider": "fixture",
        "endpoint": "fixture/maps",
        "params": {"grid_size": 1, "spacing_km": 0.7, "center": [44.1145, -79.565], "device": "mobile",
                   "language": "en", "depth": 20},
        "keywords": ["barber bradford"],
        "points": [{"row": 0, "col": 0, "lat": 44.1145, "lng": -79.565,
                    "results": {"barber bradford": {"client_rank": 4, "top3": ["a", "b", "c"],
                                                    "status": "ok"}}}],
        "complete": True,
        "cost_usd": 0,
        "created": "2026-11-05T14:02:00-05:00",
    }
    if synthetic is not None:
        grid["synthetic"] = synthetic
    return grid


def _errors(client_dir: Path) -> list[str]:
    return validate_client_dir(client_dir).errors


def test_demo_client_validates_clean() -> None:
    report = validate_client_dir(DEMO)
    assert report.errors == []
    assert main([str(DEMO)]) == 0


def test_fact_with_unknown_status(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    facts = client / "facts.yaml"
    facts.write_text(facts.read_text(encoding="utf-8").replace("status: proposed", "status: maybe"),
                     encoding="utf-8")
    errors = _errors(client)
    assert any("unknown status 'maybe'" in e for e in errors)
    assert main([str(client)]) == 1


def test_grid_without_synthetic(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "scans" / "baseline").mkdir()
    (client / "scans" / "baseline" / "grid.json").write_text(json.dumps(_grid(None)), encoding="utf-8")
    errors = _errors(client)
    assert any("grid.json must carry `synthetic`" in e for e in errors)


def test_fixture_grid_must_be_synthetic_true(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "scans" / "baseline").mkdir()
    (client / "scans" / "baseline" / "grid.json").write_text(json.dumps(_grid(False)), encoding="utf-8")
    assert any("must carry `synthetic: true`" in e for e in _errors(client))


def test_valid_synthetic_grid_passes(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "scans" / "baseline").mkdir()
    (client / "scans" / "baseline" / "grid.json").write_text(json.dumps(_grid(True)), encoding="utf-8")
    assert _errors(client) == []


@pytest.mark.parametrize("task, needle", [
    ({"id": "T2-1", "day": 2, "agent": "gbp-auditor", "status": "blocked", "human_action": "x"},
     "reason"),
    ({"id": "T2-1", "day": 2, "agent": "gbp-auditor", "status": "blocked", "reason": "x"},
     "human_action"),
    ({"id": "T2-1", "day": 2, "agent": "gbp-auditor", "status": "skipped"}, "reason"),
    ({"id": "T2-1", "day": 2, "agent": "gbp-auditor", "status": "finished"}, "is not one of"),
])
def test_bad_tasks(root: Path, task: dict, needle: str) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "tasks.json").write_text(json.dumps({"schema_version": 1, "synthetic": True, "tasks": [task]}),
                                       encoding="utf-8")
    errors = _errors(client)
    assert errors and any(needle in e for e in errors)


def test_task_unknown_dependency(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    tasks = {"schema_version": 1, "synthetic": True, "tasks": [
        {"id": "T2-1", "day": 2, "agent": "gbp-auditor", "status": "pending", "depends_on": ["T9-9"]}]}
    (client / "tasks.json").write_text(json.dumps(tasks), encoding="utf-8")
    assert any("depends_on unknown task T9-9" in e for e in _errors(client))


def test_unknown_top_level_file(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "notes.txt").write_text("hi", encoding="utf-8")
    (client / "random").mkdir()
    errors = _errors(client)
    assert any("notes.txt: file not in the docs/06" in e for e in errors)
    assert any("random: folder not in the docs/06" in e for e in errors)


def test_fixture_file_without_synthetic(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "keywords.json").write_text(json.dumps({"schema_version": 1, "keywords": [
        {"id": "K1", "keyword": "barber bradford", "intent": "local-service", "priority": 1, "on_grid": True}]}),
        encoding="utf-8")
    assert any("keywords.json: fixture-mode client" in e for e in _errors(client))


def test_slug_must_match_folder(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    path = client / "client.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("slug: _demo-barber", "slug: other-shop"),
                    encoding="utf-8")
    assert any("!= folder name" in e for e in _errors(client))


def test_missing_required_files(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "facts.yaml").unlink()
    assert any("facts.yaml: required file missing" in e for e in _errors(client))


def test_verified_fact_needs_verifier(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    facts = client / "facts.yaml"
    text = facts.read_text(encoding="utf-8").replace("    verified_by: owner\n    verified_on: 2026-11-04\n", "", 1)
    facts.write_text(text, encoding="utf-8")
    assert any("verified_by" in e for e in _errors(client))


def test_bad_compliance_report(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    (client / "reviews" / "compliance" / "x-2026-11-06.md").write_text("no front matter\n", encoding="utf-8")
    assert any("front matter" in e for e in _errors(client))
