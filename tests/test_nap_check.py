"""tools/nap_check.py: Canadian normalisation, mismatches, duplicates, plan ordering."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from tests.conftest import REPO
from tools.nap_check import analyse, check_listing, load_verified, main, norm_address, norm_phone, norm_postal, \
    norm_website, plan_rows


def test_address_unit_and_abbreviations_equal() -> None:
    assert norm_address("123 Holland St. W, Unit 4") == norm_address("4-123 Holland Street West")
    assert norm_address("123 Holland St W #4") == norm_address("Suite 4, 123 Holland Street West")
    assert norm_address("1 Example St, Bradford, Ontario") == norm_address("1 Example Street, Bradford, ON")


def test_address_differences_detected() -> None:
    assert norm_address("10 Example St") != norm_address("1 Example St")
    assert norm_address("123 Holland St W, Unit 4") != norm_address("123 Holland St W, Unit 5")


def test_postal_code_normalised() -> None:
    assert norm_postal("l3z0a1") == "L3Z 0A1" == norm_postal("Bradford, ON L3Z 0A1")
    assert norm_address("1 Example St, Bradford, ON l3z0a1") == norm_address("1 Example Street, Bradford L3Z 0A1")


@pytest.mark.parametrize("raw", ["(905) 555-0100", "905-555-0100", "+1 905 555 0100", "1-905-555-0100",
                                 "905.555.0100", "(905)555-0100"])
def test_phone_variants_equal(raw: str) -> None:
    assert norm_phone(raw) == "9055550100"


def test_website_variants_equal() -> None:
    assert norm_website("http://www.demo-fade.example.test/") == norm_website("https://demo-fade.example.test")


def test_mismatched_phone_flagged(root: Path) -> None:
    v = load_verified(root / "clients" / "_demo-barber")
    row = {"name": "Demo Fade Co.", "address": "1 Example St, Bradford, ON", "phone": "905-555-0111",
           "website": "https://demo-fade.example.test"}
    assert check_listing(v, row) == ["phone"]


def test_hidden_address_must_not_be_listed(root: Path) -> None:
    c = root / "clients" / "_demo-barber" / "client.yaml"
    c.write_text(c.read_text(encoding="utf-8").replace("address_public: true", "address_public: false"), encoding="utf-8")
    v = load_verified(c.parent)
    row = {"name": "Demo Fade Co.", "address": "1 Example St, Bradford", "phone": "905-555-0100",
           "website": "https://demo-fade.example.test"}
    assert "address shown for a hidden-address business" in check_listing(v, row)


def _copy_knowledge(root: Path) -> None:
    (root / "knowledge").mkdir(exist_ok=True)
    (root / "knowledge" / "citations-canada.csv").write_text(
        (REPO / "knowledge" / "citations-canada.csv").read_text(encoding="utf-8"), encoding="utf-8")


def test_demo_found_csv_three_wrong_one_duplicate(root: Path) -> None:
    _copy_knowledge(root)
    client = root / "clients" / "_demo-barber"
    (client / "citations" / "found.csv").write_text(
        (REPO / "clients" / "_demo-barber" / "citations" / "found.csv").read_text(encoding="utf-8"), encoding="utf-8")
    result = analyse(root, client)
    status = [(i["directory"], i["status"]) for i in result["listings"]]
    assert sorted(s for _d, s in status) == ["correct", "correct", "correct", "duplicate", "wrong", "wrong", "wrong"]
    assert ("Yelp", "duplicate") in status and ("YellowPages.ca", "wrong") in status
    plan = plan_rows(result, top=15)
    assert [r["status"] for r in plan[:4]] == ["wrong", "wrong", "wrong", "duplicate"]
    assert all(r["status"] == "missing" for r in plan[4:])
    assert next(r for r in plan if r["directory"] == "Booksy")["who"] == "owner"
    # chambers for other towns are not suggested
    assert not any("Aurora" in r["directory"] or "Central York" in r["directory"] for r in plan)


def test_duplicate_flagged_even_when_both_match(root: Path) -> None:
    _copy_knowledge(root)
    client = root / "clients" / "_demo-barber"
    row = 'Yelp,u,Demo Fade Co.,"1 Example St, Bradford, ON",(905) 555-0100,https://demo-fade.example.test,op,2026-11-09\n'
    (client / "citations" / "found.csv").write_text(
        "directory,listing_url,name,address,phone,website,found_by,found_on\n" + row + row, encoding="utf-8")
    assert [i["status"] for i in analyse(root, client)["listings"]] == ["correct", "duplicate"]


def test_cli_writes_report_and_plan(root: Path) -> None:
    _copy_knowledge(root)
    client = root / "clients" / "_demo-barber"
    (client / "citations" / "found.csv").write_text(
        (REPO / "clients" / "_demo-barber" / "citations" / "found.csv").read_text(encoding="utf-8"), encoding="utf-8")
    assert main(["--root", str(root), "--client", "_demo-barber", "--date", "2026-11-09"]) == 1
    report = (client / "citations" / "nap-report.md").read_text(encoding="utf-8")
    assert "correct 3, wrong 3, duplicate 1" in report
    with (client / "citations" / "plan.csv").open(encoding="utf-8") as fh:
        assert len(list(csv.DictReader(fh))) == 12


def test_knowledge_csv_columns() -> None:
    with (REPO / "knowledge" / "citations-canada.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert list(rows[0]) == ["name", "url", "applies_to", "town", "priority", "free_or_paid", "how_to_claim",
                             "verifies_how", "notes", "checked_on"]
    assert all(r["priority"] in {"1", "2", "3"} for r in rows)
    allowed = {"all", "barber", "pest", "trades", "salon"}
    assert all(set(r["applies_to"].split(";")) <= allowed for r in rows)
