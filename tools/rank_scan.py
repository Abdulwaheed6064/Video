"""Live rank data from DataForSEO: Google Maps grid scans and organic checks (docs/07 §2).

Usage:
    uv run python tools/rank_scan.py --client <slug> --label <baseline|mid|final|YYYY-MM-DD>
        [--keywords "kw one" "kw two"] [--mode grid|keywords-probe] [--organic] [--live] [--new-baseline]

What it does, in order:
1. Refuses fixture-mode clients (use tools/fixture_scan.py) and refuses parameter changes vs
   scans/baseline/grid.json unless --new-baseline.
2. Builds the grid with tools/grid.py (keywords-probe = one point at the centre).
3. Reuses every cached raw response in scans/<label>/raw/ (identical request = cache hit) and every
   task already posted but not yet fetched (raw/pending.json). Re-runs NEVER re-buy those.
4. Estimates the cost of what is left from budget/config.yaml prices, then runs the same check as
   `tools/budget.py check`. Aborts if prices are unconfirmed or a cap would be exceeded.
5. Posts tasks to the standard queue (default) or the live endpoint (--live only), records the actual
   charged cost in budget/ledger.csv, polls for results and caches each raw response.
6. Matches the client by client.yaml place_id. If that is missing it falls back to a name/phone match,
   writes the candidate to questions.md and marks the scan `client_match: unconfirmed`.
7. Writes scans/<label>/grid.json (docs/06 §6). Failed points get `status: error` and are listed in
   `failures`; `complete` is false if any job failed or is still queued.

Credentials come from DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD (environment, else those two keys from
.env). They are never printed, logged or written to any file.
Exit codes: 0 complete · 1 refused (fixture, budget, prices, params) · 2 error · 3 incomplete scan.

DataForSEO API details (endpoints, coordinate formats, status codes) are UNVERIFIED (see DECISIONS.md
2026-11-04 B03) and must be checked against the current docs before the first live run.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import budget  # noqa: E402
from tools.common import (  # noqa: E402
    REPO_ROOT,
    ToolError,
    find_client_dir,
    load_json,
    load_yaml,
    scan_dir,
    schema_errors,
)
from tools.grid import build_grid  # noqa: E402
from tools.heatmap import keyword_slug  # noqa: E402

API_BASE = "https://api.dataforseo.com/v3/"
ENDPOINTS: dict[str, dict[str, str]] = {
    "maps": {"post": "serp/google/maps/task_post", "get": "serp/google/maps/task_get/advanced/{id}",
             "live": "serp/google/maps/live/advanced"},
    "organic": {"post": "serp/google/organic/task_post", "get": "serp/google/organic/task_get/advanced/{id}",
                "live": "serp/google/organic/live/advanced"},
}
STATUS_OK = 20000
STATUS_CREATED = 20100
STATUS_QUEUED = {40601, 40602}  # task handed / task in queue: not ready yet
MAX_TASKS_PER_POST = 100
ORGANIC_RADIUS = 200  # location_coordinate "lat,lng,radius" for organic SERP
DEFAULT_ZOOM = "15z"  # location_coordinate "lat,lng,zoom" for Maps SERP
CRED_KEYS = ("DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD")


class Refused(Exception):
    """A deliberate refusal (exit 1): fixture client, budget, prices or parameter mismatch."""


class Transport(Protocol):
    def __call__(self, method: str, path: str, body: Any | None = None) -> dict[str, Any]: ...


# ---------------------------------------------------------------- credentials + HTTP

def read_credentials(root: Path) -> tuple[str, str]:
    values = {k: os.environ.get(k) for k in CRED_KEYS}
    env_file = root / ".env"
    if not all(values.values()) and env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() in CRED_KEYS and not values.get(key.strip()):
                values[key.strip()] = value.strip().strip('"').strip("'")
    login, password = values["DATAFORSEO_LOGIN"], values["DATAFORSEO_PASSWORD"]
    if not login or not password:
        raise ToolError("DataForSEO credentials missing: set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD in .env")
    return login, password


class HttpTransport:
    """Real HTTP transport (httpx, basic auth). Error messages never include credentials."""

    def __init__(self, login: str, password: str) -> None:
        import httpx

        self._httpx = httpx
        self._client = httpx.Client(base_url=API_BASE, auth=httpx.BasicAuth(login, password), timeout=60.0,
                                    headers={"User-Agent": "MapsRankStudio/0.1 rank_scan"})

    def __call__(self, method: str, path: str, body: Any | None = None) -> dict[str, Any]:
        try:
            resp = self._client.request(method, path, json=body)
            resp.raise_for_status()
            data = resp.json()
        except self._httpx.HTTPStatusError as exc:
            raise ToolError(f"DataForSEO HTTP {exc.response.status_code} on {path}") from None
        except self._httpx.HTTPError as exc:
            raise ToolError(f"DataForSEO request failed on {path}: {type(exc).__name__}") from None
        if not isinstance(data, dict):
            raise ToolError(f"unexpected DataForSEO response on {path}")
        return data


def default_transport_factory(root: Path) -> Transport:
    login, password = read_credentials(root)
    return HttpTransport(login, password)


# ---------------------------------------------------------------- jobs + cache

@dataclass(frozen=True)
class Job:
    kind: str  # maps | organic
    key: str  # cache file stem, also the DataForSEO task tag
    keyword: str
    lat: float
    lng: float
    row: int | None = None
    col: int | None = None
    point: str | None = None


def task_body(job: Job, params: dict[str, Any]) -> dict[str, Any]:
    if job.kind == "maps":
        coord = f"{job.lat:.7f},{job.lng:.7f},{params['zoom']}"
    else:
        coord = f"{job.lat:.7f},{job.lng:.7f},{ORGANIC_RADIUS}"
    return {
        "keyword": job.keyword,
        "location_coordinate": coord,
        "language_code": params["language"],
        "device": params["device"],
        "os": "android" if params["device"] == "mobile" else "windows",
        "depth": params["depth"],
        "tag": job.key,
    }


def build_jobs(points: list[dict[str, Any]], keywords: list[str], organic_points: list[tuple[str, float, float]]
               ) -> list[Job]:
    jobs: list[Job] = []
    for p in points:
        for kw in keywords:
            jobs.append(Job("maps", f"maps-r{p['row']}-c{p['col']}-{keyword_slug(kw)}", kw, p["lat"], p["lng"],
                            row=p["row"], col=p["col"]))
    for name, lat, lng in organic_points:
        for kw in keywords:
            jobs.append(Job("organic", f"organic-{name}-{keyword_slug(kw)}", kw, lat, lng, point=name))
    return jobs


def _read_json(path: Path) -> Any | None:
    try:
        return load_json(path) if path.is_file() else None
    except json.JSONDecodeError:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def cached(raw_dir: Path, job: Job, body: dict[str, Any]) -> dict[str, Any] | None:
    data = _read_json(raw_dir / f"{job.key}.json")
    if isinstance(data, dict) and data.get("request") == body:
        return data
    return None


# ---------------------------------------------------------------- prices + estimate

def load_prices(root: Path) -> dict[str, Any]:
    cfg = load_yaml(root / "budget" / "config.yaml") or {}
    d = cfg.get("dataforseo") or {}
    prices = d.get("usd_per_task") or {}
    for k in ("maps_standard", "maps_live", "organic_standard", "organic_live"):
        if not isinstance(prices.get(k), (int, float)) or prices[k] < 0:
            raise ToolError(f"budget/config.yaml: dataforseo.usd_per_task.{k} must be a number >= 0")
    return {"confirmed": bool(d.get("prices_confirmed")), "usd_per_task": prices}


def estimate_usd(jobs: list[Job], depth: int, live: bool, prices: dict[str, Any]) -> float:
    mult = max(1, math.ceil(depth / 100))
    queue = "live" if live else "standard"
    return round(sum(prices["usd_per_task"][f"{j.kind}_{queue}"] * mult for j in jobs), 6)


# ---------------------------------------------------------------- buying + fetching

def _record(root: Path, slug: str, endpoint: str, units: int, cost: float, label: str, day: str) -> None:
    if units:
        budget.append_row(root, {"date": day, "client": slug, "provider": "dataforseo", "endpoint": endpoint,
                                 "units": units, "cost_usd": round(cost, 6), "scan_id": label})


def post_standard(transport: Transport, jobs: list[Job], params: dict[str, Any], pending: dict[str, Any],
                  pending_path: Path, failures: list[str], record: Callable[[str, int, float], None],
                  now: str) -> None:
    by_kind: dict[str, list[Job]] = {}
    for j in jobs:
        by_kind.setdefault(j.kind, []).append(j)
    for kind, kind_jobs in by_kind.items():
        for start in range(0, len(kind_jobs), MAX_TASKS_PER_POST):
            batch = kind_jobs[start:start + MAX_TASKS_PER_POST]
            resp = transport("POST", ENDPOINTS[kind]["post"], [task_body(j, params) for j in batch])
            by_tag = {j.key: j for j in batch}
            created, cost = 0, 0.0
            for task in resp.get("tasks") or []:
                tag = (task.get("data") or {}).get("tag")
                job = by_tag.pop(tag, None) if tag else None
                if job is None:
                    continue
                cost += float(task.get("cost") or 0)
                if task.get("status_code") == STATUS_CREATED and task.get("id"):
                    created += 1
                    pending[job.key] = {"id": task["id"], "kind": kind, "posted_at": now,
                                        "request": task_body(job, params)}
                else:
                    failures.append(f"{job.key}: task_post {task.get('status_code')} {task.get('status_message')}")
            for job in by_tag.values():
                failures.append(f"{job.key}: no task returned by task_post")
            _write_json(pending_path, pending)
            record(ENDPOINTS[kind]["post"], created, cost)


def fetch_pending(transport: Transport, pending: dict[str, Any], pending_path: Path, raw_dir: Path,
                  wait_s: float, poll_s: float, sleep: Callable[[float], None], clock: Callable[[], float],
                  now: str) -> None:
    deadline = clock() + wait_s
    while pending:
        for key in list(pending):
            entry = pending[key]
            resp = transport("GET", ENDPOINTS[entry["kind"]]["get"].format(id=entry["id"]))
            task = (resp.get("tasks") or [{}])[0]
            code = task.get("status_code")
            if code in STATUS_QUEUED:
                continue
            _write_json(raw_dir / f"{key}.json", {"request": entry["request"], "task": task, "fetched_at": now,
                                                  "endpoint": ENDPOINTS[entry["kind"]]["get"],
                                                  "cost_usd": float(task.get("cost") or 0)})
            del pending[key]
            _write_json(pending_path, pending)
        if not pending or clock() >= deadline:
            break
        sleep(poll_s)


def buy_live(transport: Transport, jobs: list[Job], params: dict[str, Any], raw_dir: Path,
             record: Callable[[str, int, float], None], now: str) -> None:
    spent: dict[str, list[float]] = {}
    try:
        for job in jobs:
            body = task_body(job, params)
            resp = transport("POST", ENDPOINTS[job.kind]["live"], [body])
            task = (resp.get("tasks") or [{}])[0]
            cost = float(task.get("cost") or 0)
            spent.setdefault(job.kind, []).append(cost)
            _write_json(raw_dir / f"{job.key}.json", {"request": body, "task": task, "fetched_at": now,
                                                      "endpoint": ENDPOINTS[job.kind]["live"], "cost_usd": cost})
    finally:
        for kind, costs in spent.items():
            record(ENDPOINTS[kind]["live"], len(costs), sum(costs))


# ---------------------------------------------------------------- parsing

def _norm_name(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split())


def _digits(text: str | None) -> str:
    return re.sub(r"\D", "", text or "")[-10:]


def _task_items(raw: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
    task = raw.get("task") or {}
    if task.get("status_code") != STATUS_OK:
        return None, f"{task.get('status_code')} {task.get('status_message')}"
    result = task.get("result") or []
    if not result:
        return None, "no result in task"
    return list(result[0].get("items") or []), None


def maps_listings(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Organic Maps listings (no ads), ordered by rank_group."""
    out = []
    for it in items:
        if it.get("type") != "maps_search":
            continue
        pid = it.get("place_id") or (f"cid:{it['cid']}" if it.get("cid") else None)
        if not pid or not isinstance(it.get("rank_group"), int):
            continue
        rating = it.get("rating") or {}
        out.append({
            "place_id": str(pid), "rank": it["rank_group"], "name": str(it.get("title") or pid),
            "primary_category": it.get("category"), "rating": rating.get("value"),
            "reviews": rating.get("votes_count"), "website": it.get("url") or it.get("domain"),
            "lat": it.get("latitude"), "lng": it.get("longitude"), "phone": it.get("phone"),
            "address": it.get("address"),
        })
    return sorted(out, key=lambda x: x["rank"])


def match_client(client: dict[str, Any], verified_phone: str | None,
                 listings_by_job: dict[str, list[dict[str, Any]]]) -> tuple[str | None, str, dict[str, Any] | None]:
    """Return (client place id, client_match, candidate listing for questions.md)."""
    if client.get("place_id"):
        return str(client["place_id"]), "confirmed", None
    name = _norm_name(str(client.get("display_name", "")))
    phone = _digits(verified_phone)
    scores: Counter[str] = Counter()
    examples: dict[str, dict[str, Any]] = {}
    for listings in listings_by_job.values():
        for li in listings:
            score = (2 if phone and _digits(li.get("phone")) == phone else 0) + \
                    (1 if name and _norm_name(li["name"]) == name else 0)
            if score:
                scores[li["place_id"]] += score
                examples.setdefault(li["place_id"], li)
    if not scores:
        return None, "not_found", None
    best = scores.most_common(1)[0][0]
    return best, "unconfirmed", examples[best]


def organic_position(items: list[dict[str, Any]], domain: str | None) -> int | None:
    if not domain:
        return None
    for it in sorted((i for i in items if i.get("type") == "organic" and isinstance(i.get("rank_group"), int)),
                     key=lambda i: i["rank_group"]):
        d = str(it.get("domain") or "").lower().removeprefix("www.")
        if d == domain or d.endswith("." + domain):
            return int(it["rank_group"])
    return None


def client_domain(client: dict[str, Any], facts: dict[str, Any] | None) -> str | None:
    url = client.get("site_url")
    if not url and facts:
        url = next((f["value"] for f in facts.get("facts", []) if f.get("key") == "website"
                    and f.get("status") == "verified"), None)
    if not url:
        return None
    host = re.sub(r"^https?://", "", str(url)).split("/")[0].lower()
    return host.removeprefix("www.") or None


def note_unconfirmed(client_dir: Path, candidate: dict[str, Any], label: str, day: str) -> None:
    path = client_dir / "questions.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else "# Open questions\n\n"
    if candidate["place_id"] in text:
        return
    nums = [int(n) for n in re.findall(r"^\| Q(\d+) ", text, flags=re.MULTILINE)]
    q = f"Q{max(nums, default=0) + 1}"
    line = (f"| {q} | rank_scan ({label}) matched the client by name/phone to Google listing "
            f"'{candidate['name']}' at '{candidate.get('address') or 'no address'}' "
            f"(place_id {candidate['place_id']}). Is this the business? If yes, put the place_id in "
            f"client.yaml | Ranks in scans/{label} are unconfirmed until then | {day} | — |\n")
    if "| # |" not in text:
        text += "\n| # | Question | Why we need it | Asked | Answer |\n| --- | --- | --- | --- | --- |\n"
    path.write_text(text.rstrip("\n") + "\n" + line, encoding="utf-8", newline="\n")


def assemble(client: dict[str, Any], facts: dict[str, Any] | None, params: dict[str, Any], mode: str,
             keywords: list[str], points: list[dict[str, Any]], jobs: list[Job], raws: dict[str, dict[str, Any]],
             failures: list[str], organic: bool, endpoint: str, created: str) -> tuple[dict[str, Any], dict | None]:
    listings: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, str] = {}
    for job in jobs:
        raw = raws.get(job.key)
        if raw is None:
            errors[job.key] = "not fetched (still queued or failed to post); re-run to fetch without re-buying"
            continue
        items, err = _task_items(raw)
        if err:
            errors[job.key] = err
        elif job.kind == "maps":
            listings[job.key] = maps_listings(items or [])
    verified_phone = next((f["value"] for f in (facts or {}).get("facts", []) if f.get("key") == "phone"
                           and f.get("status") == "verified"), None)
    client_id, client_match, candidate = match_client(client, verified_phone, listings)

    places: dict[str, dict[str, Any]] = {}
    for lst in listings.values():
        for li in lst:
            places.setdefault(li["place_id"], {k: li[k] for k in ("name", "primary_category", "rating", "reviews",
                                                                 "website", "lat", "lng")})
    depth = int(params["depth"])
    out_points = []
    for p in points:
        results: dict[str, Any] = {}
        for kw in keywords:
            key = f"maps-r{p['row']}-c{p['col']}-{keyword_slug(kw)}"
            if key in errors:
                results[kw] = {"client_rank": None, "top3": [], "status": "error", "error": errors[key],
                               "raw": f"raw/{key}.json"}
                continue
            lst = listings.get(key, [])
            rank = next((li["rank"] for li in lst if li["place_id"] == client_id and li["rank"] <= depth), None)
            results[kw] = {"client_rank": rank, "top3": [li["place_id"] for li in lst[:3]], "status": "ok",
                           "raw": f"raw/{key}.json"}
        out_points.append({**p, "results": results})

    organic_rows = []
    if organic:
        domain = client_domain(client, facts)
        for job in (j for j in jobs if j.kind == "organic"):
            if job.key in errors:
                organic_rows.append({"point": job.point, "lat": job.lat, "lng": job.lng, "keyword": job.keyword,
                                     "position": None, "status": "error"})
                continue
            items, _ = _task_items(raws[job.key])
            pos = organic_position(items or [], domain)
            organic_rows.append({"point": job.point, "lat": job.lat, "lng": job.lng, "keyword": job.keyword,
                                 "position": pos if pos is None or pos <= depth else None, "status": "ok"})
        if not domain:
            failures.append("organic: no client domain (client.yaml site_url or verified website fact)")

    all_failures = failures + [f"{k}: {v}" for k, v in sorted(errors.items())]
    grid: dict[str, Any] = {
        "schema_version": 1,
        "synthetic": False,
        "provider": "dataforseo",
        "endpoint": endpoint,
        "params": params,
        "mode": mode,
        "keywords": keywords,
        "client_place_id": client_id,
        "client_match": client_match,
        "places": places,
        "points": out_points,
        "complete": not errors and not failures,
        "failures": all_failures,
        "cost_usd": round(sum(float(r.get("cost_usd") or 0) for r in raws.values()), 6),
        "created": created,
    }
    if organic:
        grid["organic"] = organic_rows
    return grid, candidate


# ---------------------------------------------------------------- main flow

def same_params(new: dict[str, Any], keywords: list[str], base: dict[str, Any]) -> list[str]:
    problems = [f"params.{k}: baseline {base['params'].get(k)!r} != {new.get(k)!r}"
                for k in sorted(set(new) | set(base["params"])) if new.get(k) != base["params"].get(k)]
    if sorted(keywords) != sorted(base["keywords"]):
        problems.append(f"keywords: baseline {base['keywords']} != {keywords}")
    return problems


def run_scan(root: Path, slug: str, label: str, *, keywords: list[str] | None = None, mode: str = "grid",
             organic: bool = False, live: bool = False, new_baseline: bool = False,
             transport_factory: Callable[[Path], Transport] = default_transport_factory,
             wait_s: float = 3600.0, poll_s: float = 60.0, sleep: Callable[[float], None] = time.sleep,
             clock: Callable[[], float] = time.time, now: datetime | None = None,
             month: str | None = None) -> dict[str, Any]:
    client_dir = find_client_dir(slug, root)
    client = load_yaml(client_dir / "client.yaml")
    if client.get("mode") == "fixture":
        raise Refused(f"client {slug} is in fixture mode: no paid calls. "
                      f"Use: uv run python tools/fixture_scan.py --client {slug} --label {label}")
    facts = load_yaml(client_dir / "facts.yaml") if (client_dir / "facts.yaml").is_file() else None
    out_dir = scan_dir(client_dir, label)
    raw_dir = out_dir / "raw"
    tz = ZoneInfo(str(client.get("timezone", "America/Toronto")))
    moment = now or datetime.now(tz)
    stamp, day = moment.isoformat(timespec="seconds"), moment.date().isoformat()

    scan_cfg = client["scan"]
    lat, lng = float(client["location"]["lat"]), float(client["location"]["lng"])
    kws = list(keywords or client["target"]["keywords"])
    size = 1 if mode == "keywords-probe" else int(scan_cfg["grid_size"])
    params = {"grid_size": size, "spacing_km": float(scan_cfg["spacing_km"]), "center": [lat, lng],
              "device": scan_cfg["device"], "language": scan_cfg["language"],
              "depth": int(scan_cfg.get("depth", 20)), "zoom": str(scan_cfg.get("zoom", DEFAULT_ZOOM))}

    baseline_grid = client_dir / "scans" / "baseline" / "grid.json"
    if mode == "grid" and baseline_grid.is_file() and not new_baseline:
        problems = same_params(params, kws, load_json(baseline_grid))
        if problems:
            raise Refused("parameters differ from scans/baseline (use --new-baseline to start over, "
                          "and say so in the report):\n  - " + "\n  - ".join(problems))

    points = build_grid(lat, lng, size, params["spacing_km"])
    organic_points: list[tuple[str, float, float]] = []
    if organic:
        organic_points.append(("shop", lat, lng))
        tc = scan_cfg.get("town_centre")
        if tc:
            organic_points.append(("town-centre", float(tc[0]), float(tc[1])))
    jobs = build_jobs(points, kws, organic_points)

    pending_path = raw_dir / "pending.json"
    pending: dict[str, Any] = _read_json(pending_path) or {}
    raws: dict[str, dict[str, Any]] = {}
    to_buy: list[Job] = []
    for job in jobs:
        body = task_body(job, params)
        hit = cached(raw_dir, job, body)
        if hit is not None:
            raws[job.key] = hit
        elif job.key in pending and pending[job.key].get("request") == body and not live:
            continue
        else:
            to_buy.append(job)

    failures: list[str] = []
    bought = 0
    if to_buy or pending:
        transport: Transport | None = None
        if to_buy:
            prices = load_prices(root)
            if not prices["confirmed"]:
                raise Refused("budget/config.yaml: dataforseo prices are unconfirmed. Check the current "
                              "DataForSEO pricing, update usd_per_task and set prices_confirmed: true")
            est = estimate_usd(to_buy, params["depth"], live, prices)
            ok, lines = budget.check(root, slug, est, month or moment.strftime("%Y-%m"))
            for line in lines:
                print(line)
            if not ok:
                raise Refused(f"budget check failed for {len(to_buy)} task(s), estimate US${est:.4f}")
            transport = transport_factory(root)

            def record(endpoint: str, units: int, cost: float) -> None:
                _record(root, slug, endpoint, units, cost, label, day)

            if live:
                buy_live(transport, to_buy, params, raw_dir, record, stamp)
                for job in to_buy:
                    hit = cached(raw_dir, job, task_body(job, params))
                    if hit is not None:
                        raws[job.key] = hit
            else:
                post_standard(transport, to_buy, params, pending, pending_path, failures, record, stamp)
            bought = len(to_buy)
        if pending and not live:
            transport = transport or transport_factory(root)
            fetch_pending(transport, pending, pending_path, raw_dir, wait_s, poll_s, sleep, clock, stamp)
            for job in jobs:
                if job.key not in raws:
                    hit = cached(raw_dir, job, task_body(job, params))
                    if hit is not None:
                        raws[job.key] = hit

    endpoint = ENDPOINTS["maps"]["live" if live else "get"].replace("/{id}", "")
    grid, candidate = assemble(client, facts, params, mode, kws, points, jobs, raws, failures, organic,
                               endpoint, stamp)
    errors = schema_errors("grid", grid)
    if errors:
        raise ToolError(f"assembled grid.json is invalid: {errors[0]}")
    _write_json(out_dir / "grid.json", grid)
    if candidate is not None:
        note_unconfirmed(client_dir, candidate, label, day)
    grid["_bought"] = bought  # informational only, not written
    return grid


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="DataForSEO Maps grid scan / keyword probe with caching, budget check and place_id matching.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    parser.add_argument("--label", required=True, help="baseline | mid | final | YYYY-MM-DD | probe-…")
    parser.add_argument("--keywords", nargs="+", default=None, help="override client.yaml target.keywords")
    parser.add_argument("--mode", choices=("grid", "keywords-probe"), default="grid")
    parser.add_argument("--organic", action="store_true", help="also check organic positions (shop, town centre)")
    parser.add_argument("--live", action="store_true", help="use the pricier live endpoint instead of the queue")
    parser.add_argument("--new-baseline", action="store_true", help="allow parameters to differ from baseline")
    parser.add_argument("--wait-minutes", type=float, default=60.0, help="how long to poll the standard queue")
    parser.add_argument("--poll-seconds", type=float, default=60.0, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        grid = run_scan(args.root, args.client, args.label, keywords=args.keywords, mode=args.mode,
                        organic=args.organic, live=args.live, new_baseline=args.new_baseline,
                        wait_s=args.wait_minutes * 60, poll_s=args.poll_seconds)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    n_err = sum(1 for p in grid["points"] for r in p["results"].values() if r["status"] == "error")
    print(f"scan written: scans/{args.label}/grid.json · bought {grid['_bought']} task(s) · "
          f"client_match {grid['client_match']} · error results {n_err} · cost US${grid['cost_usd']:.4f}")
    if grid["client_match"] == "unconfirmed":
        print("HUMAN: confirm the matched listing in questions.md, then set place_id in client.yaml")
    if not grid["complete"]:
        print("INCOMPLETE: " + "; ".join(grid["failures"][:5]) + (" …" if len(grid["failures"]) > 5 else ""))
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
