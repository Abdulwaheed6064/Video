"""Promote a signed prospect to a client: prospects/<slug>/ -> clients/<slug>/ (docs/13 §11).

Usage:
    uv run python tools/promote_prospect.py <slug> [--budget-cad 15]

- Refuses if prospects/<slug> is missing or invalid, or clients/<slug> already exists.
- mode pilot-audit -> pilot (a fixture demo prospect stays fixture); budget_cad_month set from
  --budget-cad (default 15, docs/08 §6).
- Adds the missing client files and folders from docs/06 §1 (facts.yaml, access.md, questions.md,
  log.md, intake/, gbp/, site/, ...). Audit scans are kept as a *candidate* baseline; the day-1 baseline
  is re-scanned with the full keyword set anyway.
- Builds the client folder next to clients/ first, validates it, then renames it into place and removes
  the prospect folder. Nothing is half-moved on failure.
Run it only after the agreement is signed and written permission is on file. No network.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, SLUG_RE, ToolError, dump_yaml, load_yaml  # noqa: E402
from tools.validate import validate_client_dir  # noqa: E402

CLIENT_DIRS: tuple[str, ...] = (
    "intake", "gbp/changes", "gbp/screenshots", "site", "citations", "reviews/request-kit", "reviews/replies",
    "reviews/compliance", "content", "links", "scans", "approvals", "reports", "assets",
)


class Refused(Exception):
    pass


def promote(root: Path, slug: str, budget_cad: float, today: date | None = None) -> Path:
    if not SLUG_RE.match(slug):
        raise ToolError(f"invalid slug {slug!r}")
    src = root / "prospects" / slug
    dest = root / "clients" / slug
    if not (src / "client.yaml").is_file():
        raise Refused(f"no prospect at {src}")
    if dest.exists():
        raise Refused(f"{dest} already exists; refusing to overwrite a client folder")
    report = validate_client_dir(src)
    if report.errors:
        raise Refused("prospect folder is invalid; fix it first:\n  - " + "\n  - ".join(report.errors))

    day = (today or date.today()).isoformat()
    staging = root / "clients" / f".promoting-{slug.strip('_')}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(src, staging)
    moved = False
    try:
        client = load_yaml(staging / "client.yaml")
        fixture = client.get("mode") == "fixture"
        if client.get("mode") == "pilot-audit":
            client["mode"] = "pilot"
        client["budget_cad_month"] = 0 if fixture else budget_cad
        dump_yaml(client, staging / "client.yaml")

        tag = " — SYNTHETIC" if fixture else ""
        if not (staging / "facts.yaml").is_file():
            facts = {"schema_version": 1, "facts": []}
            if fixture:
                facts = {"schema_version": 1, "synthetic": True, "facts": []}
            dump_yaml(facts, staging / "facts.yaml")
        if not (staging / "access.md").is_file():
            (staging / "access.md").write_text(
                f"# Access — {client['display_name']}{tag}\n\n| System | Access | Status | Notes |\n"
                "| --- | --- | --- | --- |\n| Google Business Profile | Manager invite (never a password) | waiting | |\n"
                "| Website / DNS | owner's own account invite | waiting | |\n| Search Console | user invite | waiting | |\n",
                encoding="utf-8", newline="\n")
        if not (staging / "questions.md").is_file():
            (staging / "questions.md").write_text(
                f"# Open questions — {client['display_name']}{tag}\n\n| # | Question | Why we need it | Asked | Answer |\n"
                "| --- | --- | --- | --- | --- |\n", encoding="utf-8", newline="\n")
        log = staging / "log.md"
        prior = log.read_text(encoding="utf-8") if log.is_file() else f"# Log — {client['display_name']}{tag}\n"
        log.write_text(prior.rstrip("\n") + f"\n\n## {day} · promoted from prospects/{slug}\n"
                       f"- mode {client['mode']}, budget_cad_month {client['budget_cad_month']}; audit scans kept "
                       "as candidate baseline only\n- HUMAN NEXT: confirm signed agreement + written permission; "
                       "run intake (day 0); re-scan baseline on day 1 with the full keyword set\n",
                       encoding="utf-8", newline="\n")
        for d in CLIENT_DIRS:
            folder = staging / d
            folder.mkdir(parents=True, exist_ok=True)
            if not any(folder.iterdir()):
                (folder / ".gitkeep").write_text("", encoding="utf-8")

        # The validator checks slug == folder name, so validate under the final name.
        staging.rename(dest)
        moved = True
        report = validate_client_dir(dest)
        if report.errors:
            raise Refused("promoted folder would be invalid:\n  - " + "\n  - ".join(report.errors))
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        if moved and dest.exists():
            shutil.rmtree(dest)  # we created it moments ago; the prospect is untouched
        raise
    shutil.rmtree(src)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Move a signed prospect into clients/ (mode pilot).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("slug")
    parser.add_argument("--budget-cad", type=float, default=15.0, help="monthly scan cap for the new client (CAD)")
    args = parser.parse_args(argv)
    try:
        dest = promote(args.root, args.slug, args.budget_cad)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"PROMOTED prospects/{args.slug} -> {dest.relative_to(args.root).as_posix()}")
    print("HUMAN NEXT: signed agreement + written permission on file; run intake (day 0); "
          "day-1 baseline re-scan with the full keyword set")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
