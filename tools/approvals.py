"""Digest-bound approvals for external changes (docs/06 §7, gates docs/13 §6).

Usage:
    uv run python tools/approvals.py hash <file-or-dir>
    uv run python tools/approvals.py request --client <slug> --action <action> --artifact <path> \
        --compliance-report <path> --requested-by agent:<name> [--owner-required yes|no] [--expires-days 3]
    uv run python tools/approvals.py approve <id> --by <operator> \
        [--owner-by "owner via WhatsApp" --owner-at <ISO time> --owner-evidence <path>]
    uv run python tools/approvals.py reject <id> --by <operator> --reason "<why>"
    uv run python tools/approvals.py verify <id>
    uv run python tools/approvals.py consume <id> --by <operator> [--fields a,b,c]

Paths (artifact, compliance report, evidence) are relative to the client folder.
An approval is valid only while:
- the artifact's current SHA-256 equals `artifact_sha256` (edit -> re-approve);
- a compliance report with `RESULT: PASS` exists for that same digest and file;
- owner approval is recorded when `owner_approval.required` is true;
- it is approved, not expired, not rejected and not yet consumed (consume once only).

`consume` writes the applied fields to gbp/applied.log (gbp_apply_batch) or a
receipt under site/ (site_deploy), then marks the approval consumed. Humans run
approve/reject/consume; agents may only run hash, request and verify.
Exit 0 = ok, 1 = refused/invalid, 2 = usage error. No network.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import (  # noqa: E402
    REPO_ROOT,
    ToolError,
    dump_yaml,
    find_client_dir,
    load_yaml,
    parse_compliance_report,
    schema_errors,
    sha256_path,
)

ACTIONS: tuple[str, ...] = (
    "gbp_apply_batch", "site_deploy", "post_publish", "review_reply", "review_kit", "citation_update",
    "report_send",
)
# docs/13 §6: owner signs off on GBP batch (description), site copy and the review kit.
OWNER_REQUIRED_DEFAULT: dict[str, bool] = {
    "gbp_apply_batch": True,
    "site_deploy": True,
    "review_kit": True,
    "post_publish": False,
    "review_reply": False,
    "citation_update": False,
    "report_send": False,
}
ID_RE = re.compile(r"^A[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(-[a-z0-9]+)*$")


# ---------------------------------------------------------------- helpers

def client_now(client_dir: Path, now: str | None) -> datetime:
    """Current time in the client's timezone (or the parsed --now override)."""
    tz = ZoneInfo(str(load_yaml(client_dir / "client.yaml").get("timezone", "America/Toronto")))
    if now:
        parsed = datetime.fromisoformat(now)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=tz)
    return datetime.now(tz)


def ts(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def inside(client_dir: Path, rel: str) -> Path:
    """Resolve a client-relative path, refusing anything outside the client folder."""
    if Path(rel).is_absolute():
        raise ToolError(f"path must be relative to the client folder: {rel}")
    path = (client_dir / rel).resolve()
    if not path.is_relative_to(client_dir.resolve()):
        raise ToolError(f"path escapes the client folder: {rel}")
    return path


def approval_path(root: Path, approval_id: str, client: str | None) -> Path:
    if not ID_RE.match(approval_id):
        raise ToolError(f"invalid approval id {approval_id!r}")
    if client:
        path = find_client_dir(client, root) / "approvals" / f"{approval_id}.yaml"
        if not path.is_file():
            raise ToolError(f"no approval {approval_id} for client {client}")
        return path
    matches = sorted(root.glob(f"clients/*/approvals/{approval_id}.yaml")) + sorted(
        root.glob(f"prospects/*/approvals/{approval_id}.yaml"))
    if not matches:
        raise ToolError(f"no approval file named {approval_id}.yaml under clients/ or prospects/")
    if len(matches) > 1:
        raise ToolError(f"approval id {approval_id} exists for several clients; pass --client")
    return matches[0]


def check_compliance(client_dir: Path, report_rel: str, artifact_rel: str, digest: str) -> list[str]:
    """Problems with the compliance report for this artifact digest (empty = PASS for this digest)."""
    try:
        report_path = inside(client_dir, report_rel)
    except ToolError as exc:
        return [str(exc)]
    front, errors = parse_compliance_report(report_path)
    if front is None:
        return errors
    problems = list(errors)
    if front.get("result") != "PASS":
        problems.append(f"compliance report {report_rel} is not PASS (result: {front.get('result')!r})")
    if front.get("sha256") != digest:
        problems.append(f"compliance report {report_rel} reviewed digest {front.get('sha256')!r}, "
                        f"artifact digest is {digest}")
    if Path(str(front.get("file", ""))).as_posix() != Path(artifact_rel).as_posix():
        problems.append(f"compliance report {report_rel} is for file {front.get('file')!r}, "
                        f"not {artifact_rel!r}")
    return problems


def problems_for(approval: dict[str, Any], client_dir: Path, today: date, stage: str) -> list[str]:
    """All reasons an approval can't proceed. stage: 'approve' (status requested) or 'use'."""
    problems = [f"schema: {m}" for m in schema_errors("approval", approval)]
    if problems:
        return problems
    status = approval["status"]
    if status == "consumed":
        problems.append(f"already consumed at {approval.get('consumed_at')}; consume works once only")
    elif status == "rejected":
        reason = (approval.get("rejection") or {}).get("reason", "no reason recorded")
        problems.append(f"rejected: {reason}")
    elif status == "expired":
        problems.append("status is expired")
    elif stage == "approve" and status != "requested":
        problems.append(f"status is {status}, expected requested")
    elif stage == "use" and status != "approved":
        problems.append(f"status is {status}, not approved")

    if today > date.fromisoformat(approval["expires"]):
        problems.append(f"expired on {approval['expires']} (today {today.isoformat()}); request a new approval")

    try:
        artifact = inside(client_dir, approval["artifact"])
        current = sha256_path(artifact)
        if current != approval["artifact_sha256"]:
            problems.append(f"artifact {approval['artifact']} changed since request "
                            f"(digest {current} != approved {approval['artifact_sha256']}); edit -> re-approve")
    except ToolError as exc:
        problems.append(str(exc))

    problems += check_compliance(client_dir, approval["compliance_report"], approval["artifact"],
                                 approval["artifact_sha256"])

    if stage == "use":
        owner = approval["owner_approval"]
        if owner.get("required") and not (owner.get("by") and owner.get("at")):
            problems.append("owner approval required but not recorded (owner_approval.by / .at)")
        operator = approval["operator_approval"]
        if not (operator.get("by") and operator.get("at")):
            problems.append("operator approval not recorded")
    return problems


def _refuse(problems: list[str], what: str) -> int:
    print(f"REFUSED {what}:")
    for p in problems:
        print(f"  - {p}")
    return 1


# ---------------------------------------------------------------- commands

def cmd_hash(args: argparse.Namespace) -> int:
    print(sha256_path(Path(args.path)))
    return 0


def cmd_request(args: argparse.Namespace) -> int:
    root: Path = args.root
    client_dir = find_client_dir(args.client, root)
    now = client_now(client_dir, args.now)
    artifact = inside(client_dir, args.artifact)
    digest = sha256_path(artifact)
    problems = check_compliance(client_dir, args.compliance_report, args.artifact, digest)
    if problems:
        return _refuse(problems, "request (compliance PASS for this exact digest is required first)")

    base = args.id or f"A{now.date().isoformat()}-{args.action.replace('_', '-')}"
    approval_id, n = base, 1
    approvals_dir = client_dir / "approvals"
    while (approvals_dir / f"{approval_id}.yaml").exists():
        if args.id:
            return _refuse([f"approval {approval_id} already exists"], "request")
        n += 1
        approval_id = f"{base}-{n}"

    owner_required = (OWNER_REQUIRED_DEFAULT[args.action] if args.owner_required is None
                      else args.owner_required == "yes")
    client = load_yaml(client_dir / "client.yaml")
    approval: dict[str, Any] = {"id": approval_id}
    if client.get("mode") == "fixture":
        approval["synthetic"] = True
    approval.update({
        "client": args.client,
        "action": args.action,
        "artifact": Path(args.artifact).as_posix(),
        "artifact_sha256": digest,
        "compliance_report": Path(args.compliance_report).as_posix(),
        "requested_by": args.requested_by,
        "requested_at": ts(now),
        "owner_approval": {"required": owner_required, "by": None, "at": None, "evidence": None},
        "operator_approval": {"by": None, "at": None},
        "expires": (now.date() + timedelta(days=args.expires_days)).isoformat(),
        "status": "requested",
        "consumed_at": None,
    })
    errors = schema_errors("approval", approval)
    if errors:
        return _refuse(errors, "request")
    dump_yaml(approval, approvals_dir / f"{approval_id}.yaml")
    print(f"REQUESTED {approval_id} ({args.action}) digest {digest}, expires {approval['expires']}, "
          f"owner approval {'required' if owner_required else 'not required'}")
    return 0


def _load_approval(args: argparse.Namespace) -> tuple[Path, Path, dict[str, Any]]:
    path = approval_path(args.root, args.id, args.client)
    client_dir = path.parent.parent
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise ToolError(f"{path}: not a mapping")
    return path, client_dir, data


def cmd_approve(args: argparse.Namespace) -> int:
    path, client_dir, approval = _load_approval(args)
    now = client_now(client_dir, args.now)
    problems = problems_for(approval, client_dir, now.date(), stage="approve")
    owner = approval.get("owner_approval") or {}
    if args.owner_by or args.owner_at or args.owner_evidence:
        if not (args.owner_by and args.owner_at):
            problems.append("--owner-by and --owner-at go together")
        if args.owner_evidence:
            try:
                if not inside(client_dir, args.owner_evidence).exists():
                    problems.append(f"owner evidence {args.owner_evidence} does not exist")
            except ToolError as exc:
                problems.append(str(exc))
        owner = {**owner, "by": args.owner_by, "at": args.owner_at, "evidence": args.owner_evidence}
    if owner.get("required") and not (owner.get("by") and owner.get("at")):
        problems.append("owner approval is required for this action: pass --owner-by and --owner-at "
                        "(and --owner-evidence)")
    if problems:
        return _refuse(problems, f"approve {args.id}")
    approval["owner_approval"] = owner
    approval["operator_approval"] = {"by": args.by, "at": ts(now)}
    approval["status"] = "approved"
    dump_yaml(approval, path)
    print(f"APPROVED {args.id} by {args.by}; valid until {approval['expires']}")
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    path, client_dir, approval = _load_approval(args)
    now = client_now(client_dir, args.now)
    if approval.get("status") not in {"requested", "approved"}:
        return _refuse([f"status is {approval.get('status')}"], f"reject {args.id}")
    approval["status"] = "rejected"
    approval["rejection"] = {"by": args.by, "at": ts(now), "reason": args.reason}
    dump_yaml(approval, path)
    print(f"REJECTED {args.id}: {args.reason}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    _path, client_dir, approval = _load_approval(args)
    now = client_now(client_dir, args.now)
    problems = problems_for(approval, client_dir, now.date(), stage="use")
    if problems:
        print(f"INVALID {args.id}:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"VALID {args.id} ({approval['action']}) artifact {approval['artifact']} "
          f"digest {approval['artifact_sha256']}")
    return 0


def _batch_fields(client_dir: Path, artifact_rel: str) -> list[str]:
    batch = load_yaml(inside(client_dir, artifact_rel))
    errors = schema_errors("gbp_change_batch", batch)
    if errors:
        raise ToolError(f"{artifact_rel} is not a valid GBP change batch: {errors[0]}")
    return [str(c["field"]) for c in batch["changes"]]


def cmd_consume(args: argparse.Namespace) -> int:
    path, client_dir, approval = _load_approval(args)
    now = client_now(client_dir, args.now)
    problems = problems_for(approval, client_dir, now.date(), stage="use")
    if problems:
        return _refuse(problems, f"consume {args.id}")
    requested = [f.strip() for f in args.fields.split(",") if f.strip()] if args.fields else None
    action = approval["action"]
    stamp = ts(now)

    if action == "gbp_apply_batch":
        available = _batch_fields(client_dir, approval["artifact"])
        fields = requested or available
        unknown = [f for f in fields if f not in available]
        if unknown:
            return _refuse([f"fields not in the approved batch: {', '.join(unknown)}"], f"consume {args.id}")
        record = client_dir / "gbp" / "applied.log"
        record.parent.mkdir(parents=True, exist_ok=True)
        with record.open("a", encoding="utf-8", newline="\n") as fh:
            for f in fields:
                fh.write(f"{stamp}\t{args.id}\t{approval['artifact']}\t{approval['artifact_sha256']}"
                         f"\t{f}\t{args.by}\n")
    elif action == "site_deploy":
        fields = requested or [approval["artifact"]]
        record = client_dir / "site" / f"deploy-receipt-{args.id}.yaml"
        dump_yaml({"approval": args.id, "artifact": approval["artifact"],
                   "artifact_sha256": approval["artifact_sha256"], "applied_by": args.by,
                   "applied_at": stamp, "fields": fields}, record)
    else:
        fields = requested or [approval["artifact"]]
        record = path

    approval["status"] = "consumed"
    approval["consumed_at"] = stamp
    approval["applied_fields"] = fields
    approval["applied_record"] = record.relative_to(client_dir).as_posix()
    dump_yaml(approval, path)
    print(f"CONSUMED {args.id}: {len(fields)} field(s) recorded in {approval['applied_record']}")
    return 0


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, decide, verify and consume digest-bound approvals (docs/06 §7).",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("hash", help="print the SHA-256 of a file or directory")
    p.add_argument("path")
    p.set_defaults(func=cmd_hash)

    p = sub.add_parser("request", help="create approvals/<id>.yaml (needs a PASS compliance report)")
    p.add_argument("--client", required=True)
    p.add_argument("--action", required=True, choices=ACTIONS)
    p.add_argument("--artifact", required=True, help="client-relative path of the exact file/dir")
    p.add_argument("--compliance-report", required=True, help="client-relative path of the PASS report")
    p.add_argument("--requested-by", required=True, help="e.g. agent:gbp-optimizer")
    p.add_argument("--owner-required", choices=("yes", "no"), default=None,
                   help="override the per-action default")
    p.add_argument("--expires-days", type=int, default=3)
    p.add_argument("--id", default=None, help="explicit approval id (default A<date>-<action>)")
    p.add_argument("--now", default=None, help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_request)

    for name, func, helptext in (("approve", cmd_approve, "operator approves (human only)"),
                                 ("reject", cmd_reject, "operator rejects (human only)"),
                                 ("verify", cmd_verify, "check an approval is valid right now"),
                                 ("consume", cmd_consume, "record what was applied; once only (human only)")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("id")
        p.add_argument("--client", default=None)
        p.add_argument("--now", default=None, help=argparse.SUPPRESS)
        if name in {"approve", "reject", "consume"}:
            p.add_argument("--by", required=True, help="who (operator initials or name)")
        if name == "approve":
            p.add_argument("--owner-by", default=None, help='e.g. "owner via WhatsApp"')
            p.add_argument("--owner-at", default=None, help="when the owner approved (ISO time)")
            p.add_argument("--owner-evidence", default=None, help="client-relative path to proof")
        if name == "reject":
            p.add_argument("--reason", required=True)
        if name == "consume":
            p.add_argument("--fields", default=None, help="comma-separated fields actually applied")
        p.set_defaults(func=func)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
