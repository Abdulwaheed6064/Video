"""Builders for hand-made scan grids used across tests."""

from __future__ import annotations

from typing import Any

from tools.grid import build_grid

ERR = "E"


def hand_grid(ranks: list[list[int | None | str]], keyword: str = "barber bradford", *, spacing_km: float = 1.0,
              depth: int = 20, synthetic: bool = True, center: tuple[float, float] = (44.1145, -79.565),
              reviews: int | None = None) -> dict[str, Any]:
    """Square grid from a matrix of ranks: int = rank, None = not found, "E" = error point."""
    size = len(ranks)
    points = build_grid(center[0], center[1], size, spacing_km)
    out_points = []
    for p in points:
        value = ranks[p["row"]][p["col"]]
        if value == ERR:
            res: dict[str, Any] = {"client_rank": None, "top3": [], "status": "error", "error": "x"}
        else:
            res = {"client_rank": value, "top3": [], "status": "ok"}
        out_points.append({**p, "results": {keyword: res}})
    grid: dict[str, Any] = {
        "schema_version": 1,
        "synthetic": synthetic,
        "provider": "test",
        "endpoint": "test/maps",
        "params": {"grid_size": size, "spacing_km": spacing_km, "center": list(center), "device": "mobile",
                   "language": "en", "depth": depth},
        "keywords": [keyword],
        "client_place_id": "client-1",
        "points": out_points,
        "complete": True,
        "cost_usd": 0,
        "created": "2026-11-05T10:00:00-05:00",
    }
    if reviews is not None:
        grid["places"] = {"client-1": {"name": "Client", "reviews": reviews, "rating": 4.5}}
    return grid
