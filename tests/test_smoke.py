"""B00 smoke test: dependencies import and the demo client files parse.

No network. Real schema validation arrives in B01 (tools/validate.py).
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
DEMO = REPO / "clients" / "_demo-barber"


@pytest.mark.parametrize(
    "module",
    ["yaml", "jsonschema", "pydantic", "matplotlib", "qrcode", "PIL", "httpx", "tools"],
)
def test_imports(module: str) -> None:
    importlib.import_module(module)


def test_demo_client_is_fixture_and_synthetic() -> None:
    client = yaml.safe_load((DEMO / "client.yaml").read_text(encoding="utf-8"))
    assert client["mode"] == "fixture"
    assert client["synthetic"] is True
    assert client["slug"] == "_demo-barber"
    assert client["budget_cad_month"] == 0


def test_demo_facts_statuses() -> None:
    facts = yaml.safe_load((DEMO / "facts.yaml").read_text(encoding="utf-8"))
    assert facts["synthetic"] is True
    statuses = [f["status"] for f in facts["facts"]]
    assert statuses.count("verified") == 6
    assert statuses.count("proposed") == 1
    assert statuses.count("rejected") == 1
    ids = [f["id"] for f in facts["facts"]]
    assert len(ids) == len(set(ids))


def test_budget_ledger_header_only() -> None:
    lines = (REPO / "budget" / "ledger.csv").read_text(encoding="utf-8").splitlines()
    assert lines == ["date,client,provider,endpoint,units,cost_usd,scan_id"]
