"""tools/budget.py: client cap, global cap, fixture cap 0, ledger record/report."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import write_client
from tools.budget import check, main

MONTH = "2026-11"


def run(root: Path, *args: str) -> int:
    return main(["--root", str(root), *args])


def add_row(root: Path, client: str, cost_usd: float, day: str = "2026-11-03") -> None:
    with (root / "budget" / "ledger.csv").open("a", encoding="utf-8") as fh:
        fh.write(f"{day},{client},dataforseo,serp/google/maps,49,{cost_usd},baseline\n")


def test_fixture_client_any_positive_estimate_fails(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "100")
    ok, lines = check(root, "_demo-barber", 0.01, MONTH)
    assert not ok and any("fixture mode" in line for line in lines)
    assert run(root, "check", "_demo-barber", "0.01", "--month", MONTH) == 1


def test_fixture_client_zero_estimate_ok(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "100")
    assert check(root, "_demo-barber", 0, MONTH)[0]


def test_fixture_cap_zero_even_if_client_yaml_sets_budget(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "100")
    write_client(root, "rich-fixture", "fixture", 500)
    assert not check(root, "rich-fixture", 1.0, MONTH)[0]


def test_over_client_cap_fails(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "1000")
    write_client(root, "pilot-shop", "pilot", 15)  # CA$15
    add_row(root, "pilot-shop", 10.0)  # US$10 = CA$14 at 1.40
    ok, lines = check(root, "pilot-shop", 1.0, MONTH)  # +CA$1.40 -> 15.40 > 15
    assert not ok and any("FAIL client cap" in line for line in lines)
    assert check(root, "pilot-shop", 0.5, MONTH)[0]  # +CA$0.70 -> 14.70 <= 15


def test_spend_from_other_months_ignored(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "1000")
    write_client(root, "pilot-shop", "pilot", 15)
    add_row(root, "pilot-shop", 10.0, day="2026-10-30")
    assert check(root, "pilot-shop", 5.0, MONTH)[0]  # CA$7 <= 15


def test_over_global_cap_fails(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "20")
    write_client(root, "pilot-a", "pilot", 100)
    write_client(root, "pilot-b", "production", 100)
    add_row(root, "pilot-b", 13.0)  # CA$18.20 spent globally
    ok, lines = check(root, "pilot-a", 2.0, MONTH)  # +CA$2.80 -> 21.00 > 20
    assert not ok and any("FAIL global cap" in line for line in lines)
    assert not any("FAIL client cap" in line for line in lines)


def test_global_cap_unset_fails_closed(root: Path) -> None:
    write_client(root, "pilot-a", "pilot", 100)
    ok, lines = check(root, "pilot-a", 0.5, MONTH)
    assert not ok and any("is not set" in line for line in lines)


def test_global_cap_read_from_dotenv(root: Path) -> None:
    write_client(root, "pilot-a", "pilot", 100)
    (root / ".env").write_text("OTHER=1\nGLOBAL_BUDGET_CAD_MONTH=50\n", encoding="utf-8")
    assert check(root, "pilot-a", 0.5, MONTH)[0]


def test_record_then_report(root: Path, monkeypatch: pytest.MonkeyPatch,
                            capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "100")
    write_client(root, "pilot-a", "pilot", 15)
    assert run(root, "record", "--client", "pilot-a", "--provider", "dataforseo", "--endpoint",
               "serp/google/maps", "--units", "49", "--cost-usd", "0.25", "--scan-id", "baseline",
               "--date", "2026-11-05") == 0
    lines = (root / "budget" / "ledger.csv").read_text(encoding="utf-8").splitlines()
    assert lines[-1] == "2026-11-05,pilot-a,dataforseo,serp/google/maps,49,0.25,baseline"
    capsys.readouterr()
    assert run(root, "report", "--month", MONTH) == 0
    out = capsys.readouterr().out
    assert "pilot-a" in out and "_demo-barber" in out and "TOTAL spent US$0.25" in out


def test_record_rejects_negative_cost(root: Path) -> None:
    write_client(root, "pilot-a", "pilot", 15)
    assert run(root, "record", "--client", "pilot-a", "--provider", "x", "--endpoint", "y", "--units", "1",
               "--cost-usd", "-1", "--scan-id", "s") == 2


def test_broken_ledger_fails_closed(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "100")
    write_client(root, "pilot-a", "pilot", 15)
    with (root / "budget" / "ledger.csv").open("a", encoding="utf-8") as fh:
        fh.write("2026-11-03,pilot-a,dataforseo,serp,49,not-a-number,baseline\n")
    assert run(root, "check", "pilot-a", "0.1", "--month", MONTH) == 2


def test_unknown_client(root: Path) -> None:
    assert run(root, "check", "nobody", "0.1") == 2
