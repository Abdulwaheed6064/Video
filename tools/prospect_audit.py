"""Render the one-page prospect rank-map audit (docs/07 §6, docs/13 §11).

Usage:
    uv run python tools/prospect_audit.py --prospect <slug> --label <label> [--keyword "<kw>"]

Fills templates/report/prospect-audit.html from files only:
- headline numbers from prospects/<slug>/scans/<label>/metrics.json
- the heatmap PNG (embedded, so the page prints on its own)
- the competitor table from competitors.json (top 5 by top-3 share, plus the business itself)
- exactly 3 gaps from the "## Top 3 gaps" section of gap-analysis.md (written by keyword-competitor
  and checked by compliance-reviewer)
Writes prospects/<slug>/reports/<scan date>/audit.html. Refuses if any input is missing, or the gaps
section does not have exactly 3 items. Adds a SYNTHETIC banner for synthetic data. No network.
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import sys
from pathlib import Path
from string import Template
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, load_json, load_yaml, scan_dir  # noqa: E402
from tools.heatmap import keyword_slug  # noqa: E402

TEMPLATE = REPO_ROOT / "templates" / "report" / "prospect-audit.html"
GAP_HEADING = re.compile(r"^##\s+Top 3 gaps\s*$", re.IGNORECASE | re.MULTILINE)
ITEM = re.compile(r"^\s*(?:\d+\.|[-*])\s+(.+)$")


def top3_gaps(text: str) -> list[str]:
    m = GAP_HEADING.search(text)
    if not m:
        raise ToolError("gap-analysis.md has no '## Top 3 gaps' section")
    body = text[m.end():]
    nxt = re.search(r"^##\s", body, flags=re.MULTILINE)
    items = [ITEM.match(line).group(1).strip() for line in (body[: nxt.start()] if nxt else body).splitlines()
             if ITEM.match(line)]
    if len(items) != 3:
        raise ToolError(f"'## Top 3 gaps' must list exactly 3 items, found {len(items)}")
    return items


def _inline(md: str) -> str:
    """Escape, then allow **bold** and `code` only."""
    out = html.escape(md)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", out)


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{round(x * 100)}%"


def render(prospect_dir: Path, label: str, keyword: str | None = None) -> Path:
    client = load_yaml(prospect_dir / "client.yaml")
    sdir = scan_dir(prospect_dir, label)
    for need in (sdir / "metrics.json", prospect_dir / "competitors.json", prospect_dir / "gap-analysis.md"):
        if not need.is_file():
            raise ToolError(f"missing {need.relative_to(prospect_dir).as_posix()}")
    metrics: dict[str, Any] = load_json(sdir / "metrics.json")
    comps: dict[str, Any] = load_json(prospect_dir / "competitors.json")
    kw = keyword or next(iter(metrics["keywords"]))
    if kw not in metrics["keywords"]:
        raise ToolError(f"keyword {kw!r} not in metrics.json")
    m = metrics["keywords"][kw]
    png = sdir / f"heatmap-{keyword_slug(kw)}.png"
    if not png.is_file():
        raise ToolError(f"missing {png.relative_to(prospect_dir).as_posix()}; run tools/heatmap.py first")
    gaps = top3_gaps((prospect_dir / "gap-analysis.md").read_text(encoding="utf-8"))

    name = str(client["display_name"])
    headline = (f"For “{kw}”, {name} is in the top 3 on {m['top3_points']} of {m['valid_points']} "
                f"search points on this map, and appears in the top {metrics['params']['depth']} on "
                f"{m['found_points']}.")
    rows = []
    cl = comps.get("client") or {}
    rows.append(f'          <tr class="client"><td>{html.escape(name)}</td>'
                f'<td class="num">{_pct((cl.get("grid_top3_share") or {}).get(kw))}</td>'
                f'<td class="num">{cl.get("reviews") if cl.get("reviews") is not None else "–"}</td>'
                f'<td class="num">{cl.get("rating") if cl.get("rating") is not None else "–"}</td>'
                f'<td class="num">–</td></tr>')
    ranked = sorted(comps["competitors"], key=lambda c: -((c.get("grid_top3_share") or {}).get(kw) or 0))[:5]
    for c in ranked:
        dist = f"{c['distance_km']} km" if c.get("distance_km") is not None else "–"
        rows.append(f'          <tr><td>{html.escape(c["name"])}</td>'
                    f'<td class="num">{_pct((c.get("grid_top3_share") or {}).get(kw))}</td>'
                    f'<td class="num">{c["reviews"] if c.get("reviews") is not None else "–"}</td>'
                    f'<td class="num">{c["rating"] if c.get("rating") is not None else "–"}</td>'
                    f'<td class="num">{dist}</td></tr>')
    p = metrics["params"]
    synthetic = bool(metrics.get("synthetic"))
    page = Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        business=html.escape(name),
        keyword=html.escape(kw),
        scan_date=html.escape(metrics["created"][:10]),
        points=p["grid_size"] * p["grid_size"],
        headline=html.escape(headline),
        heatmap_src="data:image/png;base64," + base64.b64encode(png.read_bytes()).decode("ascii"),
        competitor_rows="\n".join(rows),
        gap_items="\n".join(f"        <li>{_inline(g)}</li>" for g in gaps),
        provider=html.escape(str(metrics.get("provider") or "")),
        grid_size=p["grid_size"],
        spacing_km=p["spacing_km"],
        device=html.escape(p["device"]),
        depth=p["depth"],
        metrics_path=f"scans/{label}/metrics.json",
        competitors_path="competitors.json",
        synthetic_banner=('<div class="synthetic">SYNTHETIC DEMO DATA: not a real business, not a real scan</div>'
                          if synthetic else ""),
    )
    out = prospect_dir / "reports" / metrics["created"][:10] / "audit.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8", newline="\n")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the one-page prospect audit HTML from scan files.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--prospect", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--keyword", default=None)
    args = parser.parse_args(argv)
    try:
        pdir = args.root / "prospects" / args.prospect
        if not (pdir / "client.yaml").is_file():
            raise ToolError(f"no prospect at {pdir}")
        out = render(pdir, args.label, args.keyword)
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {out.relative_to(args.root).as_posix()}  (send through compliance-reviewer before printing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
