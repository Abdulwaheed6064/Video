"""Spend ledger and monthly caps for paid data calls (docs/06 §9).

Usage:
    uv run python tools/budget.py check <client> <estimated_cost_usd> [--month YYYY-MM]
    uv run python tools/budget.py record --client <slug> --provider dataforseo --endpoint serp/google/maps \
        --units 49 --cost-usd 0.25 --scan-id baseline [--date YYYY-MM-DD]
    uv run python tools/budget.py report [client] [--month YYYY-MM]

Caps (per calendar month, CAD):
- client: client.yaml -> budget_cad_month; clients in `mode: fixture` always have cap 0;
  prospects in `mode: pilot-audit` never more than US$1 (converted to CAD)
- global: env GLOBAL_BUDGET_CAD_MONTH (read from the environment, or that one key from .env);
  if it is not set, every paid call is refused (fail closed)
Ledger costs are USD, converted with budget/config.yaml -> usd_to_cad.

`check` exits 0 if the estimate fits both caps, 1 if it doesn't, 2 on bad input.
Every paid call must run `check` first, then `record` after. No network.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml, schema_errors  # noqa: E402

LEDGER_FIELDS: list[str] = ["date", "client", "provider", "endpoint", "units", "cost_usd", "scan_id"]
GLOBAL_ENV = "GLOBAL_BUDGET_CAD_MONTH"
PROSPECT_CAP_USD = 1.0  # hard cap for a pilot-audit prospect (sales audit), docs/13 §11
EPS = 1e-9


@dataclass(frozen=True)
class Config:
    usd_to_cad: float
    rate_confirmed: bool


def ledger_path(root: Path) -> Path:
    return root / "budget" / "ledger.csv"


def load_config(root: Path) -> Config:
    path = root / "budget" / "config.yaml"
    if not path.is_file():
        raise ToolError(f"missing {path}")
    data = load_yaml(path) or {}
    rate = data.get("usd_to_cad")
    if not isinstance(rate, (int, float)) or isinstance(rate, bool) or rate <= 0:
        raise ToolError(f"{path}: usd_to_cad must be a positive number")
    return Config(usd_to_cad=float(rate), rate_confirmed=bool(data.get("rate_confirmed", False)))


def global_cap_cad(root: Path) -> float | None:
    """Global monthly cap in CAD from the environment, else from that single key in .env."""
    raw = os.environ.get(GLOBAL_ENV)
    if raw is None:
        env_file = root / ".env"
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                key, sep, value = line.partition("=")
                if sep and key.strip() == GLOBAL_ENV:
                    raw = value.strip().strip('"').strip("'")
                    break
    if raw is None or raw == "":
        return None
    try:
        cap = float(raw)
    except ValueError as exc:
        raise ToolError(f"{GLOBAL_ENV} must be a number, got {raw!r}") from exc
    if cap < 0:
        raise ToolError(f"{GLOBAL_ENV} must be >= 0")
    return cap


def read_ledger(root: Path) -> list[dict[str, Any]]:
    """Read and validate every ledger row (fails closed on any bad row)."""
    path = ledger_path(root)
    if not path.is_file():
        raise ToolError(f"missing {path}; create it with the header row: {','.join(LEDGER_FIELDS)}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        header = [h.strip() for h in (reader.fieldnames or [])]
        if header != LEDGER_FIELDS:
            raise ToolError(f"{path}: header must be {','.join(LEDGER_FIELDS)}, got {','.join(header)}")
        for lineno, raw in enumerate(reader, start=2):
            clean = {k.strip(): (v or "").strip() for k, v in raw.items() if k is not None}
            try:
                row: dict[str, Any] = {**clean, "units": int(clean["units"]),
                                       "cost_usd": float(clean["cost_usd"])}
            except (KeyError, ValueError) as exc:
                raise ToolError(f"{path}:{lineno}: bad number ({exc})") from exc
            errors = schema_errors("ledger_row", row)
            if errors:
                raise ToolError(f"{path}:{lineno}: {errors[0]}")
            rows.append(row)
    return rows


def month_spend_usd(rows: list[dict[str, Any]], month: str, client: str | None = None) -> float:
    return sum(r["cost_usd"] for r in rows
               if r["date"].startswith(month + "-") and (client is None or r["client"] == client))


def client_cap_cad(client_dir: Path, usd_to_cad: float) -> tuple[float, str]:
    """Monthly cap in CAD: fixture = 0; pilot-audit prospects never above US$1 (docs/13 §11)."""
    client = load_yaml(client_dir / "client.yaml") or {}
    mode = client.get("mode")
    if mode == "fixture":
        return 0.0, "fixture"
    cap = client.get("budget_cad_month")
    if not isinstance(cap, (int, float)) or isinstance(cap, bool) or cap < 0:
        raise ToolError(f"{client_dir / 'client.yaml'}: budget_cad_month must be a number >= 0")
    if mode == "pilot-audit":
        return min(float(cap), PROSPECT_CAP_USD * usd_to_cad), "pilot-audit"
    return float(cap), str(mode)


def this_month() -> str:
    return date.today().strftime("%Y-%m")


def _month(value: str | None) -> str:
    if value is None:
        return this_month()
    try:
        date.fromisoformat(value + "-01")
    except ValueError as exc:
        raise ToolError(f"--month must be YYYY-MM, got {value!r}") from exc
    return value


def _rate_warning(config: Config) -> None:
    if not config.rate_confirmed:
        print("WARNING budget/config.yaml: usd_to_cad is an unconfirmed placeholder; "
              "check it and set rate_confirmed: true")


# ---------------------------------------------------------------- commands

def check(root: Path, slug: str, est_usd: float, month: str) -> tuple[bool, list[str]]:
    """Return (ok, lines). ok is False if the estimate would break any cap."""
    if est_usd < 0:
        raise ToolError("estimated cost must be >= 0")
    client_dir = find_client_dir(slug, root)
    config = load_config(root)
    rows = read_ledger(root)
    rate = config.usd_to_cad
    est_cad = est_usd * rate
    cap, mode = client_cap_cad(client_dir, rate)
    spent_client = month_spend_usd(rows, month, slug) * rate
    spent_all = month_spend_usd(rows, month) * rate
    gcap = global_cap_cad(root)
    lines = [f"month {month}; estimate US${est_usd:.2f} = CA${est_cad:.2f} (rate {rate})"]
    ok = True

    if est_usd == 0:
        lines.append("estimate is 0: no paid call, nothing to check")
        return True, lines

    if mode == "fixture":
        ok = False
        lines.append(f"FAIL client {slug} is in fixture mode: paid calls are not allowed (cap CA$0)")
    elif spent_client + est_cad > cap + EPS:
        ok = False
        lines.append(f"FAIL client cap: spent CA${spent_client:.2f} + estimate CA${est_cad:.2f} "
                     f"> cap CA${cap:.2f}")
    else:
        lines.append(f"ok   client cap: spent CA${spent_client:.2f} + estimate CA${est_cad:.2f} "
                     f"<= cap CA${cap:.2f}")

    if gcap is None:
        ok = False
        lines.append(f"FAIL global cap: {GLOBAL_ENV} is not set (paid calls refused until it is)")
    elif spent_all + est_cad > gcap + EPS:
        ok = False
        lines.append(f"FAIL global cap: spent CA${spent_all:.2f} + estimate CA${est_cad:.2f} "
                     f"> cap CA${gcap:.2f}")
    else:
        lines.append(f"ok   global cap: spent CA${spent_all:.2f} + estimate CA${est_cad:.2f} "
                     f"<= cap CA${gcap:.2f}")
    return ok, lines


def cmd_check(args: argparse.Namespace) -> int:
    _rate_warning(load_config(args.root))
    ok, lines = check(args.root, args.client, args.est_usd, _month(args.month))
    for line in lines:
        print(line)
    print("OK: within budget" if ok else "REFUSED: over budget, do not make the call")
    return 0 if ok else 1


def append_row(root: Path, row: dict[str, Any]) -> None:
    """Validate and append one ledger row (refuses to append to a broken ledger)."""
    find_client_dir(str(row.get("client")), root)
    read_ledger(root)
    errors = schema_errors("ledger_row", row)
    if errors:
        raise ToolError(f"invalid ledger row: {'; '.join(errors)}")
    with ledger_path(root).open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=LEDGER_FIELDS, lineterminator="\n").writerow(row)


def cmd_record(args: argparse.Namespace) -> int:
    row: dict[str, Any] = {
        "date": args.date or date.today().isoformat(),
        "client": args.client,
        "provider": args.provider,
        "endpoint": args.endpoint,
        "units": args.units,
        "cost_usd": args.cost_usd,
        "scan_id": args.scan_id,
    }
    append_row(args.root, row)
    print(f"RECORDED {row['date']} {args.client} {args.provider} {args.endpoint} "
          f"units={args.units} US${args.cost_usd:.4f} scan={args.scan_id}")
    return 0


def _known_clients(root: Path) -> list[str]:
    slugs = {p.parent.name for parent in ("clients", "prospects")
             for p in (root / parent).glob("*/client.yaml")}
    return sorted(slugs)


def cmd_report(args: argparse.Namespace) -> int:
    root: Path = args.root
    config = load_config(root)
    _rate_warning(config)
    month = _month(args.month)
    rows = read_ledger(root)
    rate = config.usd_to_cad
    slugs = [args.client] if args.client else sorted(set(_known_clients(root)) | {r["client"] for r in rows})
    print(f"Budget report {month} (USD->CAD {rate})")
    print(f"{'client':<32} {'mode':<11} {'spent USD':>10} {'spent CAD':>10} {'cap CAD':>8} {'left CAD':>9}")
    for slug in slugs:
        spent_usd = month_spend_usd(rows, month, slug)
        try:
            cap, mode = client_cap_cad(find_client_dir(slug, root), rate)
            cap_s, left_s = f"{cap:.2f}", f"{cap - spent_usd * rate:.2f}"
        except ToolError:
            mode, cap_s, left_s = "unknown", "-", "-"
        print(f"{slug:<32} {mode:<11} {spent_usd:>10.2f} {spent_usd * rate:>10.2f} {cap_s:>8} {left_s:>9}")
    total_usd = month_spend_usd(rows, month)
    gcap = global_cap_cad(root)
    gcap_s = f"CA${gcap:.2f}" if gcap is not None else f"not set ({GLOBAL_ENV}); paid calls refused"
    print(f"TOTAL spent US${total_usd:.2f} = CA${total_usd * rate:.2f}; global cap {gcap_s}")
    return 0


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Budget ledger and monthly caps for paid data calls.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="exit non-zero if an estimated cost would exceed a cap")
    p.add_argument("client")
    p.add_argument("est_usd", type=float, help="estimated cost in USD")
    p.add_argument("--month", default=None, help="YYYY-MM (default: current month)")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("record", help="append one row to budget/ledger.csv after a paid call")
    p.add_argument("--client", required=True)
    p.add_argument("--provider", required=True)
    p.add_argument("--endpoint", required=True)
    p.add_argument("--units", type=int, required=True)
    p.add_argument("--cost-usd", type=float, required=True)
    p.add_argument("--scan-id", required=True)
    p.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("report", help="spend vs caps for one or all clients")
    p.add_argument("client", nargs="?", default=None)
    p.add_argument("--month", default=None, help="YYYY-MM (default: current month)")
    p.set_defaults(func=cmd_report)
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
