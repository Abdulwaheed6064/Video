"""tools/rank_scan.py with a fake DataForSEO transport (no network)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.conftest import write_client
from tools import rank_scan
from tools.common import load_json, schema_errors
from tools.rank_scan import Refused, run_scan

FIXTURES = Path(__file__).parent / "fixtures" / "dataforseo"
MAPS = json.loads((FIXTURES / "maps_task_get.json").read_text(encoding="utf-8"))
ORGANIC = json.loads((FIXTURES / "organic_task_get.json").read_text(encoding="utf-8"))
SLUG = "test-shop"
LOGIN, PASSWORD = "LOGIN_SENTINEL_7781", "PASS_SENTINEL_9934"


class FakeDFS:
    """Fake DataForSEO: task_post creates tasks, task_get returns the handmade fixture."""

    def __init__(self, *, queued: bool = False, not_found_tags: set[str] | None = None,
                 error_tags: set[str] | None = None, cost: float = 0.0006) -> None:
        self.queued = queued
        self.not_found_tags = not_found_tags or set()
        self.error_tags = error_tags or set()
        self.cost = cost
        self.calls: list[tuple[str, str]] = []
        self.tags: dict[str, str] = {}

    def _result(self, kind: str, tag: str) -> dict[str, Any]:
        resp = copy.deepcopy(MAPS if kind == "maps" else ORGANIC)
        task = resp["tasks"][0]
        task["data"]["tag"] = tag
        if tag in self.error_tags:
            task.update(status_code=40501, status_message="Invalid Field (test)", result=None)
        elif tag in self.not_found_tags:
            items = task["result"][0]["items"]
            task["result"][0]["items"] = [i for i in items if i.get("place_id") != "ChIJ_client_test"]
        return resp

    def __call__(self, method: str, path: str, body: Any | None = None) -> dict[str, Any]:
        self.calls.append((method, path))
        kind = "maps" if "/maps/" in path else "organic"
        if path.endswith("task_post"):
            tasks = []
            for t in body:
                tid = f"id-{t['tag']}"
                self.tags[tid] = t["tag"]
                tasks.append({"id": tid, "status_code": 20100, "status_message": "Task Created.",
                              "cost": self.cost, "data": dict(t)})
            return {"status_code": 20000, "tasks": tasks}
        if "task_get" in path:
            tid = path.rsplit("/", 1)[-1]
            if self.queued:
                return {"status_code": 20000, "tasks": [{"id": tid, "status_code": 40602,
                                                         "status_message": "Task In Queue."}]}
            return self._result(kind, self.tags[tid])
        if path.endswith("live/advanced"):
            resp = self._result(kind, body[0]["tag"])
            resp["tasks"][0]["cost"] = self.cost * 3
            return resp
        raise AssertionError(f"unexpected call {method} {path}")

    @property
    def posts(self) -> int:
        return sum(1 for m, _ in self.calls if m == "POST")


def no_network(_root: Path) -> Any:
    raise AssertionError("transport must not be created")


@pytest.fixture
def shop(root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "100")
    monkeypatch.setenv("DATAFORSEO_LOGIN", LOGIN)
    monkeypatch.setenv("DATAFORSEO_PASSWORD", PASSWORD)
    client = write_client(root, SLUG, "pilot", 15)
    text = (client / "client.yaml").read_text(encoding="utf-8")
    text = text.replace("display_name: \"Demo Fade Co. (fictional)\"", "display_name: \"Test Shop Barbers\"")
    text = text.replace("place_id: null", "place_id: ChIJ_client_test")
    text = text.replace("grid_size: 7", "grid_size: 3")
    text = text.replace("keywords: [\"barber bradford\", \"barber shop near me\", \"fade haircut bradford\"]",
                        "keywords: [\"barber bradford\"]")
    (client / "client.yaml").write_text(text, encoding="utf-8")
    cfg = root / "budget" / "config.yaml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("prices_confirmed: false", "prices_confirmed: true"),
                   encoding="utf-8")
    return client


def factory(fake: FakeDFS):
    def make(root: Path) -> FakeDFS:
        rank_scan.read_credentials(root)  # same path as the real factory
        return fake
    return make


def ledger_rows(root: Path) -> list[str]:
    return (root / "budget" / "ledger.csv").read_text(encoding="utf-8").splitlines()[1:]


def scan(root: Path, fake: FakeDFS, **kw: Any) -> dict[str, Any]:
    return run_scan(root, SLUG, kw.pop("label", "baseline"), transport_factory=factory(fake), wait_s=0, poll_s=0,
                    sleep=lambda s: None, month="2026-11", **kw)


def test_fixture_client_refused(root: Path) -> None:
    with pytest.raises(Refused, match="fixture_scan.py"):
        run_scan(root, "_demo-barber", "x", transport_factory=no_network)
    assert rank_scan.main(["--root", str(root), "--client", "_demo-barber", "--label", "x"]) == 1


def test_unconfirmed_prices_refused(shop: Path, root: Path) -> None:
    cfg = root / "budget" / "config.yaml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("prices_confirmed: true", "prices_confirmed: false"),
                   encoding="utf-8")
    with pytest.raises(Refused, match="prices are unconfirmed"):
        run_scan(root, SLUG, "baseline", transport_factory=no_network)


def test_budget_abort_before_any_call(shop: Path, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GLOBAL_BUDGET_CAD_MONTH", "0.001")
    with pytest.raises(Refused, match="budget check failed"):
        run_scan(root, SLUG, "baseline", transport_factory=no_network, month="2026-11")
    assert ledger_rows(root) == []


def test_happy_path_parsing_and_ledger(shop: Path, root: Path) -> None:
    fake = FakeDFS(not_found_tags={"maps-r0-c0-barber-bradford"})
    grid = scan(root, fake)
    assert schema_errors("grid", load_json(shop / "scans" / "baseline" / "grid.json")) == []
    assert grid["complete"] is True and grid["synthetic"] is False and grid["client_match"] == "confirmed"
    pts = {(p["row"], p["col"]): p["results"]["barber bradford"] for p in grid["points"]}
    assert pts[(1, 1)]["client_rank"] == 2  # rank_group among maps_search items, ad ignored
    assert pts[(1, 1)]["top3"] == ["ChIJ_rival_one", "ChIJ_client_test", "ChIJ_rival_two"]
    assert pts[(0, 0)]["client_rank"] is None  # not found -> null
    assert grid["places"]["ChIJ_rival_one"]["reviews"] == 212
    assert "cid:555" in grid["places"]  # no place_id -> cid fallback
    assert "ChIJ_ad_test" not in grid["places"]
    rows = ledger_rows(root)
    assert len(rows) == 1 and rows[0].split(",")[3] == "serp/google/maps/task_post"
    assert rows[0].split(",")[4] == "9" and float(rows[0].split(",")[5]) == pytest.approx(9 * 0.0006)
    assert grid["cost_usd"] == 0  # task_get responses carry no cost; spend is in the ledger
    assert load_json(shop / "scans" / "baseline" / "raw" / "pending.json") == {}


def test_cache_hit_costs_nothing(shop: Path, root: Path) -> None:
    scan(root, FakeDFS())
    second = FakeDFS()
    grid = scan(root, second, )
    assert second.calls == [] and grid["_bought"] == 0
    assert len(ledger_rows(root)) == 1


def test_queued_tasks_resume_without_rebuying(shop: Path, root: Path) -> None:
    first = FakeDFS(queued=True)
    grid = scan(root, first)
    assert grid["complete"] is False and first.posts == 1
    pending = load_json(shop / "scans" / "baseline" / "raw" / "pending.json")
    assert len(pending) == 9
    second = FakeDFS()
    second.tags = first.tags
    grid = scan(root, second)
    assert second.posts == 0 and grid["complete"] is True
    assert len(ledger_rows(root)) == 1


def test_error_task_is_listed(shop: Path, root: Path) -> None:
    grid = scan(root, FakeDFS(error_tags={"maps-r2-c2-barber-bradford"}))
    assert grid["complete"] is False
    assert any("maps-r2-c2" in f and "40501" in f for f in grid["failures"])
    cell = next(p for p in grid["points"] if p["row"] == 2 and p["col"] == 2)["results"]["barber bradford"]
    assert cell["status"] == "error" and cell["client_rank"] is None


def test_place_id_fallback_unconfirmed(shop: Path, root: Path) -> None:
    path = shop / "client.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("place_id: ChIJ_client_test", "place_id: null"),
                    encoding="utf-8")
    grid = scan(root, FakeDFS())
    assert grid["client_match"] == "unconfirmed" and grid["client_place_id"] == "ChIJ_client_test"
    questions = (shop / "questions.md").read_text(encoding="utf-8")
    assert "ChIJ_client_test" in questions and "| Q4 |" in questions
    scan(root, FakeDFS())  # re-run must not duplicate the question
    assert (shop / "questions.md").read_text(encoding="utf-8").count("ChIJ_client_test") == 1


def test_param_mismatch_refused_unless_new_baseline(shop: Path, root: Path) -> None:
    scan(root, FakeDFS())
    path = shop / "client.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("spacing_km: 0.7", "spacing_km: 1.0"), encoding="utf-8")
    with pytest.raises(Refused, match="spacing_km"):
        scan(root, FakeDFS(), label="final")
    grid = scan(root, FakeDFS(), label="baseline", new_baseline=True)
    assert grid["params"]["spacing_km"] == 1.0


def test_organic_positions(shop: Path, root: Path) -> None:
    path = shop / "client.yaml"
    text = path.read_text(encoding="utf-8").replace("  language: en\n", "  language: en\n  town_centre: [44.11, -79.56]\n")
    path.write_text(text + "site_url: https://www.testshop.example.test\n", encoding="utf-8")
    grid = scan(root, FakeDFS(), organic=True)
    assert {(o["point"], o["position"]) for o in grid["organic"]} == {("shop", 3), ("town-centre", 3)}
    assert any(r.split(",")[3] == "serp/google/organic/task_post" for r in ledger_rows(root))


def test_live_mode_uses_live_endpoint(shop: Path, root: Path) -> None:
    fake = FakeDFS()
    grid = scan(root, fake, live=True)
    assert grid["complete"] and all(p.endswith("live/advanced") for _m, p in fake.calls)
    rows = ledger_rows(root)
    assert rows[0].split(",")[3] == "serp/google/maps/live/advanced"
    assert grid["cost_usd"] == pytest.approx(9 * 0.0018)


def test_probe_mode_single_point(shop: Path, root: Path) -> None:
    grid = scan(root, FakeDFS(), label="probe-1", mode="keywords-probe", keywords=["barber bradford", "fade bradford"])
    assert grid["params"]["grid_size"] == 1 and len(grid["points"]) == 1 and grid["mode"] == "keywords-probe"


def test_credentials_never_written_or_printed(shop: Path, root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scan(root, FakeDFS(queued=True))
    scan(root, FakeDFS(error_tags={"maps-r0-c0-barber-bradford"}), label="mid")
    out = capsys.readouterr()
    blobs = [out.out, out.err] + [p.read_text(encoding="utf-8", errors="ignore") for p in root.rglob("*")
                                  if p.is_file() and p.suffix in {".json", ".csv", ".md", ".yaml"}]
    for blob in blobs:
        assert LOGIN not in blob and PASSWORD not in blob


def test_http_errors_do_not_leak_credentials() -> None:
    t = rank_scan.HttpTransport(LOGIN, PASSWORD)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"status_message": "auth failed"})

    t._client = httpx.Client(base_url=rank_scan.API_BASE, auth=httpx.BasicAuth(LOGIN, PASSWORD),
                             transport=httpx.MockTransport(handler))
    with pytest.raises(rank_scan.ToolError) as exc:
        t("POST", "serp/google/maps/task_post", [{}])
    assert "401" in str(exc.value) and LOGIN not in str(exc.value) and PASSWORD not in str(exc.value)


def test_missing_credentials(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATAFORSEO_LOGIN", raising=False)
    monkeypatch.delenv("DATAFORSEO_PASSWORD", raising=False)
    with pytest.raises(rank_scan.ToolError, match="credentials missing"):
        rank_scan.read_credentials(root)
