"""tools/geocode.py: Nominatim call is mocked; cache, rate limit, source string."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tools.common import ToolError
from tools.geocode import USER_AGENT, geocode_address, manual_pin


class FakeFetch:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def __call__(self, url: str, params: dict[str, str], headers: dict[str, str]) -> list[dict[str, Any]]:
        self.calls.append((url, params, headers))
        return self.results


RESULT = [{"lat": "44.1150001", "lon": "-79.5660004", "display_name": "Holland St W, Bradford, Ontario"}]


def test_geocode_records_source_and_caches(tmp_path: Path) -> None:
    fetch = FakeFetch(RESULT)
    cache = tmp_path / ".cache" / "geocode.json"
    first = geocode_address("123 Holland St W, Bradford, ON", cache, fetch=fetch, clock=lambda: 1000.0,
                            sleep=lambda s: None, today=date(2026, 11, 4))
    assert first["lat"] == 44.115 and first["lng"] == -79.566
    assert "OpenStreetMap Nominatim" in first["geocode_source"] and "2026-11-04" in first["geocode_source"]
    assert fetch.calls[0][2]["User-Agent"] == USER_AGENT
    assert fetch.calls[0][1]["countrycodes"] == "ca"
    second = geocode_address("123  holland st w, bradford, on", cache, fetch=fetch, clock=lambda: 1000.5,
                             sleep=lambda s: None)
    assert second["cached"] is True and len(fetch.calls) == 1


def test_rate_limit_sleeps(tmp_path: Path) -> None:
    fetch = FakeFetch(RESULT)
    cache = tmp_path / "geo.json"
    slept: list[float] = []
    geocode_address("a st", cache, fetch=fetch, clock=lambda: 1000.0, sleep=slept.append)
    geocode_address("b st", cache, fetch=fetch, clock=lambda: 1000.2, sleep=slept.append)
    assert slept and slept[-1] == pytest.approx(0.8)


def test_no_result_raises(tmp_path: Path) -> None:
    with pytest.raises(ToolError):
        geocode_address("nowhere", tmp_path / "g.json", fetch=FakeFetch([]), clock=lambda: 0.0,
                        sleep=lambda s: None)


def test_manual_pin() -> None:
    pin = manual_pin(44.115, -79.566, today=date(2026, 11, 4))
    assert pin["geocode_source"].startswith("manual pin 44.115000,-79.566000")
    with pytest.raises(ToolError):
        manual_pin(95, 0)
