"""Turn an owner-confirmed address into coordinates, always recording the source.

Usage:
    uv run python tools/geocode.py --address "123 Holland St W, Bradford, ON"
    uv run python tools/geocode.py --lat 44.1150 --lng -79.5660        # manual pin

--address queries OpenStreetMap Nominatim (free, public). This script follows its usage policy:
an identifying User-Agent, at most 1 request per second, and results cached in
.cache/geocode.json so the same address is never fetched twice. Network is used only for
--address with no cached result. Output is JSON with `lat`, `lng` and a `geocode_source`
string to copy into client.yaml -> location.geocode_source. Data © OpenStreetMap contributors (ODbL).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError  # noqa: E402

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "MapsRankStudio/0.1 (local SEO geocoding for owner-confirmed addresses; low volume)"
MIN_INTERVAL_S = 1.0

Fetcher = Callable[[str, dict[str, str], dict[str, str]], list[dict[str, Any]]]


def _http_fetch(url: str, params: dict[str, str], headers: dict[str, str]) -> list[dict[str, Any]]:
    import httpx  # imported lazily: tests never touch the network

    resp = httpx.get(url, params=params, headers=headers, timeout=20.0)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ToolError("unexpected Nominatim response")
    return data


def _normalise(address: str) -> str:
    return " ".join(address.lower().split())


def load_cache(path: Path) -> dict[str, Any]:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {"entries": {}, "last_request": 0.0}


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def geocode_address(address: str, cache_path: Path, fetch: Fetcher = _http_fetch,
                    clock: Callable[[], float] = time.time,
                    sleep: Callable[[float], None] = time.sleep,
                    today: date | None = None) -> dict[str, Any]:
    """Geocode via Nominatim with cache and ≥1 s between requests."""
    if not address.strip():
        raise ToolError("address is empty")
    key = _normalise(address)
    cache = load_cache(cache_path)
    if key in cache["entries"]:
        return {**cache["entries"][key], "cached": True}
    wait = MIN_INTERVAL_S - (clock() - float(cache.get("last_request", 0.0)))
    if wait > 0:
        sleep(wait)
    params = {"q": address, "format": "jsonv2", "limit": "1", "countrycodes": "ca", "addressdetails": "0"}
    results = fetch(NOMINATIM_URL, params, {"User-Agent": USER_AGENT})
    cache["last_request"] = clock()
    if not results:
        save_cache(cache_path, cache)
        raise ToolError(f"no Nominatim result for {address!r}; check the address or use --lat/--lng")
    top = results[0]
    day = (today or date.today()).isoformat()
    entry = {
        "lat": round(float(top["lat"]), 6),
        "lng": round(float(top["lon"]), 6),
        "display_name": str(top.get("display_name", "")),
        "geocode_source": f"OpenStreetMap Nominatim for '{address}' on {day} (© OpenStreetMap contributors)",
    }
    cache["entries"][key] = entry
    save_cache(cache_path, cache)
    return {**entry, "cached": False}


def manual_pin(lat: float, lng: float, today: date | None = None) -> dict[str, Any]:
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ToolError("lat/lng out of range")
    day = (today or date.today()).isoformat()
    return {"lat": round(lat, 6), "lng": round(lng, 6), "display_name": None,
            "geocode_source": f"manual pin {lat:.6f},{lng:.6f} set by operator on {day}", "cached": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Geocode an owner-confirmed address (OSM Nominatim, cached, ≤1 req/s) or record a manual pin.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--address")
    group.add_argument("--lat", type=float)
    parser.add_argument("--lng", type=float)
    args = parser.parse_args(argv)
    try:
        if args.address is not None:
            result = geocode_address(args.address, args.root / ".cache" / "geocode.json")
        else:
            if args.lng is None:
                parser.error("--lat needs --lng")
            result = manual_pin(args.lat, args.lng)
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - network/HTTP failures: report, don't crash
        print(f"ERROR: geocoding failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"source: {result['geocode_source']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
