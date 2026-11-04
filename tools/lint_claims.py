"""Lint client-facing text for claims and policy risks before compliance review.

Usage:
    uv run python tools/lint_claims.py <file> --client <slug> [--json]

Flags, with line numbers (knowledge/ranking-rules.md hard limits):
- name_change     a GBP batch proposes a business name different from the verified `name` fact
- name_stuffing   the business name followed by town/service/superlative words ("X – Best Barber Bradford")
- unverified_claim  best / #1 / top-rated / award / certified / licensed / years / since YYYY ...
                    without a matching verified fact (best, #1, top-rated, number one: never allowed)
- review_incentive  "review" near % off / discount / free / draw / chance to win / gift / prize ...
- review_gating   "if you're happy", "if not, contact us first", "5-star review" ...
- address         a street address or postal code not in client.yaml (any address for a hidden-address SAB)
- phone           a phone number not in the verified facts
- ranking_promise "guarantee", "#1 on Google", "top of Google", "first page" ...
In GBP change batches only `proposed` values are linted (current values describe today's profile,
reasons are internal notes). Exit 0 = no flags, 1 = flags, 2 = error. The lint is deliberately strict:
reword rather than argue with it. It does NOT replace compliance-reviewer. No network.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml, load_yaml_text  # noqa: E402

NICHE_WORDS: dict[str, set[str]] = {
    "barber": {"barber", "barbers", "barbershop", "haircut", "haircuts", "fade", "fades", "shave", "beard",
               "salon", "cuts"},
    "pest-control": {"pest", "pests", "control", "exterminator", "exterminators", "extermination", "mice",
                     "rats", "rodent", "rodents", "bed", "bugs", "wasp", "wasps", "termite", "termites",
                     "removal", "wildlife"},
}
SUPERLATIVE_WORDS: set[str] = {"best", "top", "#1", "no.1", "cheap", "cheapest", "affordable", "near", "rated",
                               "leading", "premier", "number"}
STOPWORDS: set[str] = {"near", "me", "in", "the", "a", "and", "of", "for"}

ALWAYS_FLAG = [
    (re.compile(r"\bbest\b", re.I), "superlative 'best' (no fact can verify it)"),
    (re.compile(r"#\s?1\b|\bno\.\s?1\b|\bnumber\s+one\b", re.I), "'#1' / 'number one' claim"),
    (re.compile(r"\btop[-\s]rated\b|\bhighest[-\s]rated\b", re.I), "'top-rated' claim"),
]
FACT_CLAIMS = [
    (re.compile(r"\baward", re.I), "award", "attribute", re.compile(r"award", re.I)),
    (re.compile(r"\bcertified\b|\bcertification\b", re.I), "certified", "licence", None),
    (re.compile(r"\blicen[cs]ed\b|\blicen[cs]e\s+(no|number|#)", re.I), "licensed", "licence", None),
    (re.compile(r"\b\d+\+?\s+years?\b|\bsince\s+(19|20)\d\d\b|\bestablished\b|\bfounded\b", re.I), "years in business",
     "year_founded", None),
]
INCENTIVE = re.compile(r"%\s*off|\bdiscount|\bfree\b|\bdraw\b|\bchance to win\b|\bgift\b|\bprize\b|\bcoupon\b|"
                       r"\bvoucher\b|\breward\b|\bin exchange\b|\bfreebie\b|\bentered to win\b", re.I)
REVIEW = re.compile(r"\breviews?\b|\brate us\b|\bstars?\b", re.I)
GATING = re.compile(r"\bif you(?:'| a)re happy\b|\bif you (?:enjoyed|loved|liked)\b|\bhappy with (?:us|your)\b.*review|"
                    r"\bif not,? (?:please )?(?:contact|tell|call|email|message|let)\b|\bcontact us first\b|"
                    r"\btell us privately\b|\bbefore (?:leaving|posting) a review\b|\b(?:5|five)[-\s]star review\b|"
                    r"\bonly (?:leave|post) a review\b|\bunhappy\b.*\b(?:contact|tell|call)\b", re.I)
PROMISE = re.compile(r"\bguarantee[ds]?\b|\b#\s?1 on google\b|\btop of google\b|\bfirst page\b|\bpage one\b|"
                     r"\bnumber one on google\b|\brank (?:you )?(?:#\s?1|first|number one)\b|\bwe will rank\b|"
                     r"\bguaranteed (?:top|ranking|#)", re.I)
ADDRESS = re.compile(r"\b\d{1,6}\s+(?:[A-Z][\w'.-]*\s+){1,4}(?:St|Street|Rd|Road|Ave|Avenue|Blvd|Boulevard|Dr|Drive|"
                     r"Cres|Crescent|Way|Lane|Ln|Ct|Court|Pl|Place|Hwy|Highway|Line|Sideroad|Pkwy|Parkway|Trail|"
                     r"Terrace|Circle|Sq|Square)\b\.?(?:\s+[NSEW]\b)?")
POSTAL = re.compile(r"\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z]\s?\d[ABCEGHJ-NPRSTV-Z]\d\b")
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
YAML_KEY = re.compile(r"^(\s*)(?:-\s+)?([A-Za-z_][\w-]*):(\s|$)")
SKIP_YAML_KEYS: set[str] = {"current", "reason", "ui_path", "fact_refs", "field", "risk", "date", "client",
                            "schema_version", "synthetic", "id"}


@dataclass
class Flag:
    line: int
    rule: str
    text: str
    message: str


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split())


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)[-10:]


@dataclass
class Context:
    names: list[str]
    verified_name: str | None
    verified: dict[str, list[str]]
    phones: set[str]
    address: str | None
    address_public: bool
    stuffing_words: set[str]


def load_context(client_dir: Path) -> Context:
    client = load_yaml(client_dir / "client.yaml")
    facts = load_yaml(client_dir / "facts.yaml") if (client_dir / "facts.yaml").is_file() else {"facts": []}
    verified: dict[str, list[str]] = {}
    for f in facts.get("facts", []):
        if f.get("status") == "verified":
            verified.setdefault(str(f["key"]), []).append(str(f["value"]))
    vname = (verified.get("name") or [None])[0]
    names = []
    for n in (vname, client.get("display_name")):
        if n:
            names.append(n)
            core = re.sub(r"\s*\([^)]*\)\s*$", "", n).strip()
            if core and core != n:
                names.append(core)
    loc = client.get("location") or {}
    towns = {t.lower() for t in client.get("service_area") or []}
    addr = loc.get("address")
    if addr and "," in addr:
        towns.add(addr.split(",")[1].strip().lower().split(" (")[0])
    words = set(towns) | NICHE_WORDS.get(str(client.get("niche")), set()) | SUPERLATIVE_WORDS
    for kw in (client.get("target") or {}).get("keywords") or []:
        words |= {w for w in _norm(kw).split() if w not in STOPWORDS}
    for svc in verified.get("service", []):
        words |= {w for w in _norm(svc).split() if len(w) >= 4}
    return Context(names=sorted(set(names), key=len, reverse=True), verified_name=vname, verified=verified,
                   phones={_digits(p) for p in verified.get("phone", [])}, address=addr,
                   address_public=bool(loc.get("address_public", True)), stuffing_words=words)


def lintable_lines(path: Path, text: str) -> list[tuple[int, str]]:
    """(line number, text) pairs to lint. For YAML, skip keys that are not client-facing text."""
    lines = text.splitlines()
    if path.suffix not in {".yaml", ".yml"}:
        return [(i + 1, line) for i, line in enumerate(lines)]
    out: list[tuple[int, str]] = []
    skip_indent: int | None = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            continue
        m = YAML_KEY.match(line)
        if m:
            col = m.start(2)  # column of the key itself ("- field:" -> column of "field")
            if skip_indent is not None and col <= skip_indent:
                skip_indent = None
            if skip_indent is None and m.group(2) in SKIP_YAML_KEYS:
                skip_indent = col
                continue
        elif skip_indent is not None and line.strip() and (len(line) - len(line.lstrip())) <= skip_indent \
                and not line.lstrip().startswith("- "):
            skip_indent = None
        if skip_indent is None:
            out.append((i + 1, line))
    return out


def _name_stuffing(line: str, ctx: Context) -> str | None:
    for name in ctx.names:
        for m in re.finditer(re.escape(name), line, flags=re.I):
            rest = line[m.end():]
            sep = re.match(r"\s*[-–—|:]\s*(.+)", rest)
            tail = sep.group(1) if sep else rest
            words = _norm(tail).split()[:4] if sep else _norm(tail).split()[:1]
            hits = [w for w in words if w in ctx.stuffing_words or w == "1"]
            if hits:
                return f"business name followed by {', '.join(repr(h) for h in hits)}; name must match signage"
    return None


def _has_fact(ctx: Context, key: str, must: re.Pattern[str] | None) -> bool:
    values = ctx.verified.get(key, [])
    return any(must.search(v) for v in values) if must else bool(values)


def lint_text(path: Path, text: str, ctx: Context) -> list[Flag]:
    flags: list[Flag] = []
    pairs = lintable_lines(path, text)
    by_no = dict(pairs)
    for no, line in pairs:
        if not line.strip():
            continue
        short = line.strip()[:160]
        msg = _name_stuffing(line, ctx)
        if msg:
            flags.append(Flag(no, "name_stuffing", short, msg))
        for rx, what in ALWAYS_FLAG:
            if rx.search(line):
                flags.append(Flag(no, "unverified_claim", short, what))
        for rx, what, key, must in FACT_CLAIMS:
            if rx.search(line) and not _has_fact(ctx, key, must):
                flags.append(Flag(no, "unverified_claim", short, f"'{what}' claim without a verified `{key}` fact"))
        window = " ".join(by_no.get(n, "") for n in (no - 1, no, no + 1))
        if INCENTIVE.search(line) and REVIEW.search(window) or REVIEW.search(line) and INCENTIVE.search(window):
            flags.append(Flag(no, "review_incentive", short, "possible review incentive (no rewards for reviews)"))
        if GATING.search(line):
            flags.append(Flag(no, "review_gating", short, "possible review gating (same request to every customer)"))
        if PROMISE.search(line):
            flags.append(Flag(no, "ranking_promise", short, "ranking promise / guarantee language"))
        for m in list(ADDRESS.finditer(line)) + list(POSTAL.finditer(line)):
            found = _norm(m.group(0))
            if not ctx.address_public:
                flags.append(Flag(no, "address", short, f"address {m.group(0)!r} shown for a hidden-address business"))
            elif not ctx.address or found not in _norm(ctx.address):
                flags.append(Flag(no, "address", short, f"address {m.group(0)!r} is not the client's address"))
        for m in PHONE.finditer(line):
            if _digits(m.group(0)) not in ctx.phones:
                flags.append(Flag(no, "phone", short, f"phone {m.group(0)!r} is not a verified phone fact"))

    if path.suffix in {".yaml", ".yml"}:
        try:
            data = load_yaml_text(text)
        except Exception:  # noqa: BLE001 - not YAML we understand: line lint only
            data = None
        if isinstance(data, dict) and isinstance(data.get("changes"), list):
            for change in data["changes"]:
                if isinstance(change, dict) and change.get("field") == "name":
                    proposed = str(change.get("proposed"))
                    if ctx.verified_name is None or proposed != ctx.verified_name:
                        no = next((n for n, line in enumerate(text.splitlines(), 1) if proposed in line
                                   and "proposed" in line), 0)
                        flags.append(Flag(no, "name_change", proposed[:160],
                                          f"proposed name {proposed!r} != verified name {ctx.verified_name!r}"))
    seen: set[tuple[int, str, str]] = set()
    unique = []
    for f in flags:
        key = (f.line, f.rule, f.message)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return sorted(unique, key=lambda f: (f.line, f.rule))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Flag unverifiable claims and policy risks in client-facing text.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("file", type=Path)
    parser.add_argument("--client", required=True)
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        if not args.file.is_file():
            raise ToolError(f"no such file {args.file}")
        flags = lint_text(args.file, args.file.read_text(encoding="utf-8"), load_context(client_dir))
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"file": args.file.as_posix(), "client": args.client, "result": "FLAGS" if flags else "PASS",
                          "flags": [asdict(f) for f in flags]}, indent=2, ensure_ascii=False))
    else:
        for f in flags:
            print(f"{args.file.as_posix()}:{f.line}: [{f.rule}] {f.message}\n    {f.text}")
        print(f"{'FLAGS' if flags else 'PASS'}: {len(flags)} flag(s) in {args.file.as_posix()}")
    return 1 if flags else 0


if __name__ == "__main__":
    raise SystemExit(main())
