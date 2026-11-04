"""Prospect flow: validator layout, budget cap US$1, audit page, promote_prospect."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.conftest import REPO
from tools import fixture_scan, heatmap, metrics, prospect_audit
from tools.budget import check
from tools.common import load_yaml
from tools.competitors import main as competitors_main
from tools.promote_prospect import main as promote_main
from tools.validate import validate_client_dir

DEMO_PROSPECT = REPO / "prospects" / "_demo-prospect"


def make_prospect(root: Path, slug: str = "sample-shop-bradford", mode: str = "pilot-audit",
                  budget_cad: float = 5) -> Path:
    dest = root / "prospects" / slug
    shutil.copytree(DEMO_PROSPECT, dest, ignore=lambda d, names: [n for n in names if Path(d).name in {"scans", "reports"}
                                                                   and n != ".gitkeep"])
    for f in ("gap-analysis.md", "competitors.json"):
        (dest / f).unlink(missing_ok=True)
    text = (dest / "client.yaml").read_text(encoding="utf-8")
    text = text.replace("slug: _demo-prospect", f"slug: {slug}").replace("mode: fixture", f"mode: {mode}")
    text = text.replace("budget_cad_month: 0", f"budget_cad_month: {budget_cad}")
    if mode != "fixture":
        text = text.replace("synthetic: true\n", "")
    (dest / "client.yaml").write_text(text, encoding="utf-8")
    return dest


def test_demo_prospect_validates() -> None:
    assert validate_client_dir(DEMO_PROSPECT).errors == []


def test_prospect_layout_rules(root: Path) -> None:
    p = make_prospect(root)
    assert validate_client_dir(p).errors == []  # facts.yaml not required for prospects
    (p / "gbp").mkdir()
    assert any("gbp: folder not in the prospect layout" in e for e in validate_client_dir(p).errors)


def test_prospect_mode_rules(root: Path) -> None:
    p = make_prospect(root, mode="pilot")
    assert any("prospects must be mode pilot-audit" in e for e in validate_client_dir(p).errors)
    c = root / "clients" / "_demo-barber" / "client.yaml"
    c.write_text(c.read_text(encoding="utf-8").replace("mode: fixture", "mode: pilot-audit"), encoding="utf-8")
    assert any("only for prospects" in e for e in validate_client_dir(c.parent).errors)


def test_prospect_budget_capped_at_one_usd(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "100")
    make_prospect(root, budget_cad=50)  # client.yaml asks for more; US$1 hard cap wins
    ok, lines = check(root, "sample-shop-bradford", 0.9, "2026-11")
    assert ok
    ok, lines = check(root, "sample-shop-bradford", 1.1, "2026-11")
    assert not ok and any("FAIL client cap" in line for line in lines)


def test_audit_page_flow(root: Path) -> None:
    slug = "_demo-prospect"
    shutil.copytree(DEMO_PROSPECT, root / "prospects" / slug)
    args = ["--root", str(root), "--client", slug, "--label", "baseline"]
    assert fixture_scan.main(args) == 0
    assert metrics.main(args) == 0
    assert heatmap.main(args) == 0
    scan = root / "prospects" / slug / "scans" / "baseline" / "grid.json"
    assert competitors_main(["--root", str(root), "--scan", str(scan), "--client", slug]) == 0
    assert prospect_audit.main(["--root", str(root), "--prospect", slug, "--label", "baseline"]) == 0
    page = next((root / "prospects" / slug / "reports").glob("*/audit.html")).read_text(encoding="utf-8")
    assert "SYNTHETIC DEMO DATA" in page and "data:image/png;base64," in page
    assert "in the top 3 on 1 of 47" in page and page.count("<li>") == 3
    text = page.split("</style>", 1)[1]  # visible part, without CSS colour codes
    assert "guarantee" not in text.lower() and "#1" not in text


def test_audit_page_needs_exactly_three_gaps() -> None:
    with pytest.raises(prospect_audit.ToolError, match="exactly 3"):
        prospect_audit.top3_gaps("## Top 3 gaps\n\n1. one\n2. two\n\n## Next\n")
    with pytest.raises(prospect_audit.ToolError, match="no '## Top 3 gaps'"):
        prospect_audit.top3_gaps("# nothing\n")


def test_promote_moves_and_sets_pilot(root: Path) -> None:
    p = make_prospect(root)
    (p / "scans" / "baseline").mkdir(parents=True)
    (p / "scans" / "baseline" / "keep.txt").write_text("x", encoding="utf-8")
    assert promote_main(["--root", str(root), "sample-shop-bradford"]) == 0
    dest = root / "clients" / "sample-shop-bradford"
    assert not p.exists() and dest.is_dir()
    client = load_yaml(dest / "client.yaml")
    assert client["mode"] == "pilot" and client["budget_cad_month"] == 15
    assert (dest / "facts.yaml").is_file() and (dest / "gbp" / "changes").is_dir()
    assert (dest / "scans" / "baseline" / "keep.txt").is_file()
    assert "promoted from prospects/sample-shop-bradford" in (dest / "log.md").read_text(encoding="utf-8")
    assert validate_client_dir(dest).errors == []


def test_promote_refuses_if_target_exists(root: Path) -> None:
    p = make_prospect(root, slug="taken-shop")
    (root / "clients" / "taken-shop").mkdir(parents=True)
    assert promote_main(["--root", str(root), "taken-shop"]) == 1
    assert p.is_dir()  # prospect untouched


def test_promote_refuses_missing_or_invalid(root: Path) -> None:
    assert promote_main(["--root", str(root), "nobody-here"]) == 1
    p = make_prospect(root, slug="bad-shop")
    (p / "junk.txt").write_text("x", encoding="utf-8")
    assert promote_main(["--root", str(root), "bad-shop"]) == 1
    assert p.is_dir() and not (root / "clients" / "bad-shop").exists()
