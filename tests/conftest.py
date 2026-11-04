"""Shared pytest fixtures: a throwaway repo root with a copy of the demo client."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DEMO = REPO / "clients" / "_demo-barber"
LEDGER_HEADER = "date,client,provider,endpoint,units,cost_usd,scan_id\n"


def copy_demo(dest: Path) -> Path:
    """Copy the demo client without its generated scans (scans/ keeps only .gitkeep)."""
    shutil.copytree(DEMO, dest, ignore=lambda d, names: [n for n in names if Path(d).name == "scans"
                                                          and n != ".gitkeep"])
    return dest


def write_client(root: Path, slug: str, mode: str, budget_cad: float) -> Path:
    """Copy the demo client to root/clients/<slug>, changing slug, mode and budget."""
    dest = copy_demo(root / "clients" / slug)
    text = (dest / "client.yaml").read_text(encoding="utf-8")
    text = text.replace("slug: _demo-barber", f"slug: {slug}")
    text = text.replace("mode: fixture", f"mode: {mode}")
    text = text.replace("budget_cad_month: 0", f"budget_cad_month: {budget_cad}")
    if mode != "fixture":
        text = text.replace("synthetic: true\n", "")
    (dest / "client.yaml").write_text(text, encoding="utf-8")
    return dest


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fake repo root: demo client copy, budget config and an empty ledger."""
    monkeypatch.delenv("GLOBAL_BUDGET_CAD_MONTH", raising=False)
    (tmp_path / "budget").mkdir()
    shutil.copy(REPO / "budget" / "config.yaml", tmp_path / "budget" / "config.yaml")
    (tmp_path / "budget" / "ledger.csv").write_text(LEDGER_HEADER, encoding="utf-8")
    copy_demo(tmp_path / "clients" / "_demo-barber")
    return tmp_path
