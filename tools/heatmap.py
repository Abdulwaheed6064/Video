"""Render rank heatmaps from a scan (docs/07 §4).

Usage:
    uv run python tools/heatmap.py --client <slug> --label <label> [--compare <baseline label>]

Writes scans/<label>/heatmap-<keyword>.png (800×900 px) for every keyword, and with --compare
also scans/<label>/heatmap-<keyword>-vs-<compare>.png (1600×900 px): before | after with an
identical scale and layout. Colours: green 1–3, yellow 4–10, orange 11–20, red not found within
depth ("20+"), grey = error point (excluded, never interpolated). Each cell shows the rank; the
centre (shop) cell is outlined. Every image carries keyword, scan date, grid size, spacing, device
and provider, plus a SYNTHETIC watermark for fixture scans.
v1 is a plain grid; OpenStreetMap basemap tiles (with attribution) are a later option. No network.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_json, scan_dir, schema_errors  # noqa: E402
from tools.metrics import comparable  # noqa: E402

COLOURS: dict[str, str] = {
    "top3": "#2e9e44", "4-10": "#f2c230", "11-20": "#f08a24", "not_found": "#d6342c", "error": "#9e9e9e",
}
SINGLE_SIZE_IN = (8.0, 9.0)
DPI = 100


def keyword_slug(keyword: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-") or "keyword"


def band(rank: int | None, status: str) -> str:
    if status != "ok":
        return "error"
    if rank is None:
        return "not_found"
    if rank <= 3:
        return "top3"
    if rank <= 10:
        return "4-10"
    return "11-20"


def cell_text(rank: int | None, status: str, depth: int) -> str:
    if status != "ok":
        return "ERR"
    return f"{depth}+" if rank is None else str(rank)


def _draw(ax: Any, grid: dict[str, Any], keyword: str, title: str) -> None:
    size = int(grid["params"]["grid_size"])
    depth = int(grid["params"]["depth"])
    centre = (size - 1) // 2
    for p in grid["points"]:
        res = p["results"].get(keyword, {"client_rank": None, "status": "error"})
        x, y = p["col"], size - 1 - p["row"]  # row 0 (north) at the top
        colour = COLOURS[band(res["client_rank"], res["status"])]
        ax.add_patch(Rectangle((x, y), 1, 1, facecolor=colour, edgecolor="white", linewidth=2))
        ax.text(x + 0.5, y + 0.5, cell_text(res["client_rank"], res["status"], depth), ha="center",
                va="center", fontsize=14 if size <= 7 else 10, fontweight="bold", color="#111111")
    ax.add_patch(Rectangle((centre, size - 1 - centre), 1, 1, fill=False, edgecolor="#111111", linewidth=3))
    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=13, pad=8)
    ax.text(size / 2, -0.35, "N ↑  ·  outlined cell = business location", ha="center", va="top", fontsize=9,
            color="#444444")
    if grid.get("synthetic"):
        ax.text(0.5, 0.5, "SYNTHETIC", transform=ax.transAxes, ha="center", va="center", rotation=30,
                fontsize=56, color="#c00000", alpha=0.22, fontweight="bold")


def _caption(grid: dict[str, Any], label: str) -> str:
    p = grid["params"]
    return (f"{label} · {grid['created'][:10]} · grid {p['grid_size']}×{p['grid_size']} · "
            f"spacing {p['spacing_km']} km · {p['device']} · depth {p['depth']} · {grid['provider']}")


def _finish(fig: Figure, synthetic: bool, path: Path) -> None:
    handles = [Patch(color=COLOURS["top3"], label="1–3"), Patch(color=COLOURS["4-10"], label="4–10"),
               Patch(color=COLOURS["11-20"], label="11–20"), Patch(color=COLOURS["not_found"], label="not found (20+)"),
               Patch(color=COLOURS["error"], label="error (excluded)")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=10)
    if synthetic:
        fig.text(0.5, 0.945, "SYNTHETIC FIXTURE DATA. Not a real scan.", ha="center", va="center",
                 fontsize=10, color="#c00000", fontweight="bold")
    path.parent.mkdir(parents=True, exist_ok=True)
    FigureCanvasAgg(fig)
    fig.savefig(path, dpi=DPI, metadata={"Software": None})


def render_single(grid: dict[str, Any], keyword: str, label: str, path: Path) -> None:
    fig = Figure(figsize=SINGLE_SIZE_IN, dpi=DPI)
    fig.suptitle(f"Google Maps rank: “{keyword}”", fontsize=16, y=0.995)
    fig.text(0.5, 0.915, _caption(grid, label), ha="center", va="center", fontsize=10)
    ax = fig.add_axes((0.08, 0.12, 0.84, 0.76))
    _draw(ax, grid, keyword, "")
    _finish(fig, bool(grid.get("synthetic")), path)


def render_compare(before: dict[str, Any], after: dict[str, Any], keyword: str, before_label: str,
                   after_label: str, path: Path) -> None:
    fig = Figure(figsize=(SINGLE_SIZE_IN[0] * 2, SINGLE_SIZE_IN[1]), dpi=DPI)
    fig.suptitle(f"Google Maps rank: “{keyword}”: before vs after (same grid, same scale)", fontsize=16, y=0.995)
    for i, (grid, label, name) in enumerate(((before, before_label, "Before"), (after, after_label, "After"))):
        ax = fig.add_axes((0.04 + i * 0.5, 0.12, 0.42, 0.74))
        _draw(ax, grid, keyword, f"{name}: {_caption(grid, label)}")
    _finish(fig, bool(before.get("synthetic") or after.get("synthetic")), path)


def _load_grid(client_dir: Path, label: str) -> dict[str, Any]:
    path = scan_dir(client_dir, label) / "grid.json"
    if not path.is_file():
        raise ToolError(f"missing {path}")
    grid = load_json(path)
    errors = schema_errors("grid", grid)
    if errors:
        raise ToolError(f"{path} is invalid: {errors[0]}")
    return grid


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render heatmap PNGs (per keyword, optional before/after).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--compare", default=None, help="baseline label for a side-by-side composite")
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        grid = _load_grid(client_dir, args.label)
        before = _load_grid(client_dir, args.compare) if args.compare else None
        if before is not None:
            problems = comparable(grid, before)
            if problems:
                raise ToolError("scans are not comparable:\n  - " + "\n  - ".join(problems))
        out_dir = scan_dir(client_dir, args.label)
        written: list[Path] = []
        for kw in grid["keywords"]:
            single = out_dir / f"heatmap-{keyword_slug(kw)}.png"
            render_single(grid, kw, args.label, single)
            written.append(single)
            if before is not None:
                composite = out_dir / f"heatmap-{keyword_slug(kw)}-vs-{args.compare}.png"
                render_compare(before, grid, kw, str(args.compare), args.label, composite)
                written.append(composite)
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"wrote {path.relative_to(args.root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
