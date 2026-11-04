"""Shared helpers for tools/ scripts: repo paths, YAML/JSON loading, schema access.

YAML is loaded with timestamps kept as strings, so `2026-11-04` stays the string
"2026-11-04" (JSON Schema `format: date` then checks it). This keeps YAML and JSON
files validated the same way.
"""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
SCHEMA_DIR: Path = REPO_ROOT / "schemas"


class _StringDateLoader(yaml.SafeLoader):
    """SafeLoader that does not turn dates/timestamps into datetime objects."""


_StringDateLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


class ToolError(Exception):
    """A user-facing error: printed without a traceback, exit code 1 or 2."""


def load_yaml_text(text: str) -> Any:
    return yaml.load(text, Loader=_StringDateLoader)  # noqa: S506 - SafeLoader subclass


def load_yaml(path: Path) -> Any:
    return load_yaml_text(path.read_text(encoding="utf-8"))


def dump_yaml(data: Any, path: Path) -> None:
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_data(path: Path) -> Any:
    """Load a .yaml/.yml or .json file."""
    if path.suffix in {".yaml", ".yml"}:
        return load_yaml(path)
    if path.suffix == ".json":
        return load_json(path)
    raise ToolError(f"{path}: unsupported data file type")


@lru_cache(maxsize=None)
def schema_validator(name: str) -> Draft202012Validator:
    """Return a validator for schemas/<name>.schema.json."""
    path = SCHEMA_DIR / f"{name}.schema.json"
    if not path.is_file():
        raise ToolError(f"missing schema {path}")
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def schema_errors(name: str, data: Any) -> list[str]:
    """Validate data against a named schema; return readable 'location: message' strings."""
    validator = schema_validator(name)
    out: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path]):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out


def sha256_path(path: Path) -> str:
    """SHA-256 of a file's bytes, or of a directory tree.

    A directory digest covers every file under it (sorted by POSIX relative path):
    each line is "<relpath>\\0<file sha256>\\n". Renames, edits, additions and
    deletions all change the digest.
    """
    if path.is_file():
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    if path.is_dir():
        h = hashlib.sha256()
        files = sorted(p for p in path.rglob("*") if p.is_file())
        for f in files:
            rel = f.relative_to(path).as_posix()
            h.update(f"{rel}\0{sha256_path(f)}\n".encode())
        return h.hexdigest()
    raise ToolError(f"{path}: no such file or directory")


RESULT_LINE_RE = re.compile(r"^RESULT:\s*(PASS|FAIL)\s*$", re.MULTILINE)


def parse_compliance_report(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse a compliance report: YAML front matter + a 'RESULT: PASS|FAIL' line in the body.

    Returns (front_matter or None, errors).
    """
    if not path.is_file():
        return None, [f"compliance report {path} does not exist"]
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ["compliance report has no YAML front matter (must start with '---')"]
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, ["compliance report front matter is not closed with '---'"]
    front = load_yaml_text("\n".join(lines[1:end]))
    if not isinstance(front, dict):
        return None, ["compliance report front matter is not a mapping"]
    errors = schema_errors("compliance_report", front)
    body = "\n".join(lines[end + 1 :])
    results = RESULT_LINE_RE.findall(body)
    if len(results) != 1:
        errors.append("compliance report body must contain exactly one 'RESULT: PASS' or 'RESULT: FAIL' line")
    elif front.get("result") != results[0]:
        errors.append(f"front matter result {front.get('result')!r} != body 'RESULT: {results[0]}'")
    return front, errors


SLUG_RE = re.compile(r"^_?[a-z0-9]+(-[a-z0-9]+)*$")


def find_client_dir(slug: str, root: Path = REPO_ROOT) -> Path:
    """Locate clients/<slug> or prospects/<slug> under root."""
    if not SLUG_RE.match(slug):
        raise ToolError(f"invalid client slug {slug!r}")
    for parent in ("clients", "prospects"):
        candidate = root / parent / slug
        if (candidate / "client.yaml").is_file():
            return candidate
    raise ToolError(f"no client.yaml for {slug!r} under {root / 'clients'} or {root / 'prospects'}")
