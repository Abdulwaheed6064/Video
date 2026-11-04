"""B08: message templates lint, review card QR, review velocity, link prospects rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import zxingcpp
from PIL import Image

from tests.conftest import DEMO, REPO
from tests.helpers import hand_grid
from tools.common import ToolError, sha256_path
from tools.lint_claims import lint_text, load_context
from tools.review_card import build_kit, build_messages
from tools.review_velocity import collect, compute
from tools.validate import validate_client_dir

CTX = load_context(DEMO)
LINK = "https://g.page/r/EXAMPLE/review"


@pytest.mark.parametrize("name", ["sms.txt", "whatsapp.txt", "email.txt", "counter-script.md"])
def test_neutral_templates_pass_lint(name: str) -> None:
    text = (REPO / "templates" / "messages" / name).read_text(encoding="utf-8")
    assert lint_text(Path(name), text, CTX) == []


def test_rendered_messages_pass_lint() -> None:
    assert lint_text(Path("m.md"), build_messages("Demo Fade Co. (fictional)", LINK), CTX) == []


@pytest.mark.parametrize("variant", [
    "Hi {first_name}, leave us a Google review and get 10% off your next cut: {review_link}",
    "Review us on Google for a chance to win a free beard trim! {review_link}",
    "If you're happy with your visit, please leave a review: {review_link}",
])
def test_incentive_or_gating_variants_fail_lint(variant: str) -> None:
    rules = {f.rule for f in lint_text(Path("v.txt"), variant, CTX)}
    assert rules & {"review_incentive", "review_gating"}


def test_review_card_qr_decodes_and_is_reproducible(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    files = build_kit(client, LINK)
    kit = client / "reviews" / "request-kit"
    for kind in ("business", "a6"):
        img = Image.open(kit / f"review-card-{kind}.png")
        assert [r.text for r in zxingcpp.read_barcodes(img)] == [LINK]
        assert (kit / f"review-card-{kind}.pdf").read_bytes().startswith(b"%PDF")
    assert Image.open(kit / "review-card-business.png").size == (1050, 600)
    first = sha256_path(kit)
    build_kit(client, LINK)
    assert sha256_path(kit) == first  # approval digests stay valid on re-run
    assert any(f.name == "messages.md" for f in files)


def test_review_card_refuses_http_link(root: Path) -> None:
    with pytest.raises(ToolError, match="https"):
        build_kit(root / "clients" / "_demo-barber", "http://g.page/r/EXAMPLE/review")


def _scan(client: Path, label: str, created: str, reviews: int) -> None:
    grid = hand_grid([[1]], reviews=reviews)
    grid["created"] = created
    (client / "scans" / label).mkdir(parents=True)
    (client / "scans" / label / "grid.json").write_text(json.dumps(grid), encoding="utf-8")


def test_velocity_weekly_deltas(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    _scan(client, "baseline", "2026-11-06T10:00:00-05:00", 18)
    _scan(client, "mid", "2026-11-20T10:00:00-05:00", 24)
    _scan(client, "final", "2026-11-27T10:00:00-05:00", 25)
    data = compute(collect(client))
    assert [p["count"] for p in data["points"]] == [18, 24, 25]
    assert data["intervals"][0] == {"from": "baseline", "to": "mid", "days": 14, "delta_count": 6, "per_week": 3.0}
    assert data["intervals"][1]["per_week"] == 1.0
    assert data["overall_per_week"] == round(7 / 3, 2)


def _prospects(client: Path, rows: list[str]) -> list[str]:
    (client / "links" / "prospects.csv").write_text(
        "name,url,source_url,checked_on,verified,why_relevant,cost,contact_route,effort,status\n" + "\n".join(rows) + "\n",
        encoding="utf-8")
    return validate_client_dir(client).errors


def test_link_prospect_rules(root: Path) -> None:
    client = root / "clients" / "_demo-barber"
    ok = "A,https://a.example.test,https://src.example.test,,unverified,SYNTHETIC x,unknown,op,low,new"
    assert _prospects(client, [ok]) == []
    errs = _prospects(client, ["A,https://a.example.test,,,unverified,SYNTHETIC x,unknown,op,low,new"])
    assert any("source_url" in e for e in errs)
    errs = _prospects(client, ["A,https://a.example.test,https://s.example.test,,yes,SYNTHETIC x,unknown,op,low,new"])
    assert any("need checked_on" in e for e in errs)
    errs = _prospects(client, ["A,https://a.example.test,https://s.example.test,2026-11-11,maybe,x,unknown,op,low,new"])
    assert any("verified must be" in e for e in errs) and any("SYNTHETIC" in e for e in errs)
