"""Validate one client (or prospect) folder against docs/06 and schemas/.

Usage:
    uv run python tools/validate.py clients/<slug>

Checks every present data file against its JSON Schema, plus cross-file rules:
- client.yaml and facts.yaml must exist; client.yaml slug == folder name
- fact ids unique; fact status in {proposed, verified, rejected}
- every scans/<label>/grid.json carries `synthetic`
- in fixture mode every data file carries `synthetic: true`
- tasks.json / sprint.json: unique ids, depends_on refer to existing ids
- approvals/<id>.yaml: id == file name, client == slug
- reviews/compliance/*.md: front matter + matching RESULT line
- nothing at the top level outside the docs/06 §1 layout

Exit code 0 = valid, 1 = invalid, 2 = usage error. No network.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import (  # noqa: E402
    LABEL_RE,
    SLUG_RE,
    ToolError,
    load_data,
    parse_compliance_report,
    schema_errors,
)

# docs/06 §1 top-level layout.
TOP_LEVEL_FILES: dict[str, str | None] = {
    "client.yaml": "client",
    "facts.yaml": "facts",
    "keywords.json": "keywords",
    "competitors.json": "competitors",
    "sprint.json": "tasks",
    "tasks.json": "tasks",
    "access.md": None,
    "questions.md": None,
    "gap-analysis.md": None,
    "log.md": None,
}
TOP_LEVEL_DIRS: set[str] = {
    "intake", "gbp", "site", "citations", "reviews", "content", "links", "scans", "approvals", "reports",
    "assets",
}
IGNORED_NAMES: set[str] = {".gitkeep", ".DS_Store", "Thumbs.db"}
REQUIRED_FILES: tuple[str, ...] = ("client.yaml", "facts.yaml")
# Prospects (docs/13 §11): public data only, a subset of the client layout.
PROSPECT_FILES: set[str] = {"client.yaml", "facts.yaml", "keywords.json", "competitors.json", "gap-analysis.md",
                            "questions.md", "log.md"}
PROSPECT_DIRS: set[str] = {"scans", "reports", "reviews", "approvals"}
PROSPECT_REQUIRED_FILES: tuple[str, ...] = ("client.yaml",)


@dataclass
class Report:
    root: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked: int = 0

    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def error(self, path: Path, msg: str) -> None:
        self.errors.append(f"{self.rel(path)}: {msg}")

    def warn(self, path: Path, msg: str) -> None:
        self.warnings.append(f"{self.rel(path)}: {msg}")


def _load(report: Report, path: Path) -> Any | None:
    try:
        data = load_data(path)
    except (OSError, ValueError, yaml.YAMLError, ToolError) as exc:  # JSONDecodeError is a ValueError
        report.error(path, f"cannot parse: {exc}")
        return None
    report.checked += 1
    return data


def _check_schema(report: Report, path: Path, schema: str, data: Any) -> None:
    for msg in schema_errors(schema, data):
        report.error(path, msg)


def _check_synthetic(report: Report, path: Path, data: Any, fixture: bool) -> None:
    if fixture and not (isinstance(data, dict) and data.get("synthetic") is True):
        report.error(path, "fixture-mode client: file must carry `synthetic: true`")
    elif not fixture and isinstance(data, dict) and data.get("synthetic") is True:
        report.warn(path, "file is marked synthetic in a non-fixture client")


def _check_facts(report: Report, path: Path, data: Any) -> None:
    if not isinstance(data, dict) or not isinstance(data.get("facts"), list):
        return
    seen: set[str] = set()
    for i, fact in enumerate(data["facts"]):
        if not isinstance(fact, dict):
            continue
        fid = fact.get("id")
        if isinstance(fid, str):
            if fid in seen:
                report.error(path, f"facts/{i}: duplicate fact id {fid}")
            seen.add(fid)
        status = fact.get("status")
        if status not in {"proposed", "verified", "rejected"}:
            report.error(path, f"facts/{i} ({fid}): unknown status {status!r} "
                               "(allowed: proposed, verified, rejected)")


def _check_tasks(report: Report, path: Path, data: Any) -> None:
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        return
    tasks = [t for t in data["tasks"] if isinstance(t, dict)]
    ids = [t.get("id") for t in tasks]
    seen: set[Any] = set()
    for tid in ids:
        if tid in seen:
            report.error(path, f"duplicate task id {tid}")
        seen.add(tid)
    for t in tasks:
        for dep in t.get("depends_on", []) or []:
            if dep not in seen:
                report.error(path, f"task {t.get('id')}: depends_on unknown task {dep}")
        if t.get("status") == "blocked" and not t.get("reason"):
            report.error(path, f"task {t.get('id')}: status blocked without `reason`")


def _iter_files(directory: Path, pattern: str) -> Iterable[Path]:
    if directory.is_dir():
        yield from sorted(p for p in directory.glob(pattern) if p.is_file())


def validate_client_dir(client_dir: Path) -> Report:
    """Validate a client folder; returns a Report (errors empty = valid)."""
    client_dir = client_dir.resolve()
    report = Report(root=client_dir.parent.parent if client_dir.parent.name in {"clients", "prospects"}
                    else client_dir.parent)
    if not client_dir.is_dir():
        report.error(client_dir, "not a directory")
        return report

    prospect = client_dir.parent.name == "prospects"
    required = PROSPECT_REQUIRED_FILES if prospect else REQUIRED_FILES
    allowed_files = PROSPECT_FILES if prospect else set(TOP_LEVEL_FILES)
    allowed_dirs = PROSPECT_DIRS if prospect else TOP_LEVEL_DIRS
    layout = "prospect layout (docs/13 §11)" if prospect else "docs/06 §1 layout"

    for name in required:
        if not (client_dir / name).is_file():
            report.error(client_dir / name, "required file missing")

    # Top-level layout.
    for entry in sorted(client_dir.iterdir()):
        if entry.name in IGNORED_NAMES:
            continue
        if entry.is_dir():
            if entry.name not in allowed_dirs:
                report.error(entry, f"folder not in the {layout}")
        elif entry.name not in allowed_files:
            report.error(entry, f"file not in the {layout} (propose new files in DECISIONS.md)")

    # client.yaml first: it decides fixture mode.
    fixture = False
    slug = client_dir.name
    client_path = client_dir / "client.yaml"
    if client_path.is_file():
        client = _load(report, client_path)
        if client is not None:
            _check_schema(report, client_path, "client", client)
            if isinstance(client, dict):
                fixture = client.get("mode") == "fixture"
                mode = client.get("mode")
                if prospect and mode not in {"pilot-audit", "fixture"}:
                    report.error(client_path, f"prospects must be mode pilot-audit (or fixture for demos), got {mode!r}")
                if not prospect and mode == "pilot-audit":
                    report.error(client_path, "mode pilot-audit is only for prospects/ (promote_prospect.py sets pilot)")
                if client.get("slug") != slug:
                    report.error(client_path, f"slug {client.get('slug')!r} != folder name {slug!r}")
                _check_synthetic(report, client_path, client, fixture)
    if not SLUG_RE.match(slug):
        report.error(client_dir, f"folder name {slug!r} is not a valid slug")

    # Other top-level data files.
    for name, schema in TOP_LEVEL_FILES.items():
        path = client_dir / name
        if schema is None or name == "client.yaml" or not path.is_file():
            continue
        data = _load(report, path)
        if data is None:
            continue
        _check_schema(report, path, schema, data)
        _check_synthetic(report, path, data, fixture)
        if schema == "facts":
            _check_facts(report, path, data)
        elif schema == "tasks":
            _check_tasks(report, path, data)

    # Scans.
    scans = client_dir / "scans"
    if scans.is_dir():
        for scan_dir in sorted(p for p in scans.iterdir() if p.is_dir()):
            if not LABEL_RE.match(scan_dir.name):
                report.error(scan_dir, "scan label must be lowercase letters/digits/hyphens "
                                       "(e.g. baseline, mid, final, 2026-11-05)")
            grid = scan_dir / "grid.json"
            if grid.is_file():
                data = _load(report, grid)
                if data is not None:
                    if isinstance(data, dict) and "synthetic" not in data:
                        report.error(grid, "grid.json must carry `synthetic` (true for fixture scans)")
                    _check_schema(report, grid, "grid", data)
                    _check_synthetic(report, grid, data, fixture)
            metrics = scan_dir / "metrics.json"
            if metrics.is_file():
                data = _load(report, metrics)
                if data is not None:
                    _check_schema(report, metrics, "metrics", data)
                    _check_synthetic(report, metrics, data, fixture)

    # Approvals.
    for path in _iter_files(client_dir / "approvals", "*.yaml"):
        data = _load(report, path)
        if data is None:
            continue
        _check_schema(report, path, "approval", data)
        _check_synthetic(report, path, data, fixture)
        if isinstance(data, dict):
            if data.get("id") != path.stem:
                report.error(path, f"id {data.get('id')!r} != file name {path.stem!r}")
            if data.get("client") != slug:
                report.error(path, f"client {data.get('client')!r} != {slug!r}")

    # GBP change batches.
    for path in _iter_files(client_dir / "gbp" / "changes", "*.yaml"):
        data = _load(report, path)
        if data is None:
            continue
        _check_schema(report, path, "gbp_change_batch", data)
        _check_synthetic(report, path, data, fixture)

    # Compliance reports.
    for path in _iter_files(client_dir / "reviews" / "compliance", "*.md"):
        report.checked += 1
        _front, errs = parse_compliance_report(path)
        for msg in errs:
            report.error(path, msg)

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a client folder (clients/<slug> or prospects/<slug>) against docs/06.",
    )
    parser.add_argument("client_dir", type=Path, help="path to the client folder, e.g. clients/_demo-barber")
    args = parser.parse_args(argv)
    try:
        report = validate_client_dir(args.client_dir)
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for w in report.warnings:
        print(f"WARNING {w}")
    if report.errors:
        for e in report.errors:
            print(f"ERROR {e}")
        print(f"INVALID {args.client_dir.as_posix()}: {len(report.errors)} error(s), "
              f"{report.checked} file(s) checked")
        return 1
    print(f"OK {args.client_dir.as_posix()}: {report.checked} file(s) checked, 0 errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
