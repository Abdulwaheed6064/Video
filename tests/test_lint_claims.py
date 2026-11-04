"""tools/lint_claims.py against the demo client's verified facts."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import DEMO
from tools.lint_claims import load_context, lint_text, main

CTX = load_context(DEMO)


def rules(text: str, suffix: str = ".md") -> list[str]:
    return [f.rule for f in lint_text(Path(f"x{suffix}"), text, CTX)]


def test_flags_name_stuffing() -> None:
    r = rules("Demo Fade Co. – Best Barber Bradford")
    assert "name_stuffing" in r and "unverified_claim" in r


@pytest.mark.parametrize("text", ["Demo Fade Co. Bradford", "Demo Fade Co. | Barber Shop",
                                  "Demo Fade Co. (fictional) - Fade Haircut Bradford"])
def test_flags_other_stuffing(text: str) -> None:
    assert "name_stuffing" in rules(text)


def test_flags_review_incentive() -> None:
    assert "review_incentive" in rules("Leave a review for 10% off your next cut!")
    assert "review_incentive" in rules("Post a Google review and you'll be entered\ninto our monthly draw.")


@pytest.mark.parametrize("text", [
    "If you're happy with your cut, please leave us a review.",
    "Loved it? Review us on Google. If not, contact us first so we can fix it.",
    "Please leave us a 5-star review!",
])
def test_flags_gating(text: str) -> None:
    assert "review_gating" in rules(text)


def test_flags_unverified_award() -> None:
    # F007 "Award-winning" is only *proposed* in the demo facts.
    assert "unverified_claim" in rules("Award-winning fades in Bradford.")


def test_flags_ranking_promise() -> None:
    r = rules("We guarantee #1 on Google Maps.")
    assert "ranking_promise" in r and "unverified_claim" in r


def test_flags_years_without_fact() -> None:
    assert "unverified_claim" in rules("Cutting hair in Bradford for 15 years.")
    assert "unverified_claim" in rules("Serving Bradford since 2009.")  # F008 is rejected


def test_flags_unknown_phone_and_address() -> None:
    assert "phone" in rules("Call us at (905) 555-0199.")
    assert "address" in rules("Visit us at 45 Holland St W, Bradford.")
    assert "address" in rules("Postal code L3Z 2A1")


def test_verified_phone_and_address_pass() -> None:
    assert rules("Call (905) 555-0100 or visit 1 Example St, Bradford.") == []


def test_clean_description_passes() -> None:
    text = ("Demo Fade Co. is a barber shop in Bradford. We do skin fades and beard trims, "
            "Tuesday to Saturday. Walk in or call (905) 555-0100 to book.")
    assert rules(text) == []


def test_batch_lints_proposed_only_and_flags_name_change() -> None:
    batch = """schema_version: 1
client: _demo-barber
date: 2026-11-07
changes:
  - field: name
    current: "Demo Fade Co. - Best Barber Bradford"
    proposed: "Demo Fade Co. Barbers Bradford"
    reason: "Best barber in town per owner"
    fact_refs: [F001]
    ui_path: "Edit profile > Business name"
    risk: high
  - field: description
    current: "Best barber, #1 in Bradford"
    proposed: "Skin fades and beard trims in Bradford."
    reason: "x"
    fact_refs: [F005]
    ui_path: "Edit profile > Description"
    risk: low
"""
    flags = lint_text(Path("b.yaml"), batch, CTX)
    lines = {f.line for f in flags}
    assert {f.rule for f in flags} == {"name_change", "name_stuffing"}
    assert lines == {7}  # only the proposed name line; current/reason lines are not linted


def test_cli_exit_codes(root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = tmp_path / "good.md"
    good.write_text("Skin fades and beard trims in Bradford.\n", encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text("Best barber in Bradford, guaranteed.\n", encoding="utf-8")
    assert main(["--root", str(root), str(good), "--client", "_demo-barber"]) == 0
    assert main(["--root", str(root), str(bad), "--client", "_demo-barber", "--json"]) == 1
    assert '"result": "FLAGS"' in capsys.readouterr().out
    assert main(["--root", str(root), str(tmp_path / "missing.md"), "--client", "_demo-barber"]) == 2
