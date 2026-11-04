"""Check a built or live client site (agents/site-auditor.md). Reports only what it measured.

Usage:
    uv run python tools/site_check.py --client <slug> --local          # clients/<slug>/site/dist
    uv run python tools/site_check.py --client <slug> --url https://…  # live site (network; PSI if key set)

Must-pass checks (each pass / fail / unknown, with details per page):
- titles          present, 30–65 chars, contain the town and a service/niche word
- meta            meta description 70–160 chars
- h1              exactly one H1 per page
- canonical       absolute canonical equal to site URL + page path
- nap             verified name + phone on every page; no other phone in tel: links or text; street
                  address present when the address is public, absent when it is hidden
- schema          JSON-LD (extracted with extruct) has an allowlisted @type, required properties, and
                  name/phone matching verified facts
- robots          robots.txt exists with a Sitemap line; must not block all (except a synthetic demo)
- sitemap         sitemap lists every indexable page
- internal_links  no broken internal links or assets (local mode)
- similarity      no two pages > 60% similar (word 3-gram Jaccard over <main>)
- page_weight     HTML + CSS + JS + images per page under 500 KB (local mode)
- performance_lcp mobile LCP < 2.5 s from PageSpeed Insights (--url + PAGESPEED_API_KEY); otherwise unknown
Writes clients/<slug>/site/audit-<date>.json. Exit 0 = no failures (unknowns allowed), 1 = failures, 2 = error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from itertools import combinations
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml  # noqa: E402
from tools.lint_claims import NICHE_WORDS, PHONE  # noqa: E402
from tools.schema_gen import ALLOWED_TYPES, verified_facts  # noqa: E402

SIMILARITY_LIMIT = 0.60
WEIGHT_LIMIT = 500_000
LCP_LIMIT_MS = 2500
PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)[-10:]


# ---------------------------------------------------------------- page parsing

def parse_page(path: str, html: str) -> dict[str, Any]:
    import extruct
    from lxml import html as lhtml

    doc = lhtml.fromstring(html)
    title = (doc.findtext(".//title") or "").strip()
    meta = doc.xpath('//meta[@name="description"]/@content')
    canon = doc.xpath('//link[@rel="canonical"]/@href')
    robots_meta = " ".join(doc.xpath('//meta[@name="robots"]/@content')).lower()
    h1s = [" ".join(h.text_content().split()) for h in doc.xpath("//h1")]
    links = [a for a in doc.xpath("//a/@href")]
    assets = doc.xpath("//link[@rel='stylesheet']/@href") + doc.xpath("//script/@src") + doc.xpath("//img/@src")
    mains = doc.xpath("//main")
    main_text = " ".join((mains[0] if mains else doc).text_content().split())
    body_text = " ".join(doc.text_content().split())
    try:
        jsonld = extruct.extract(html, syntaxes=["json-ld"], uniform=True).get("json-ld", [])
    except Exception:  # noqa: BLE001 - malformed JSON-LD is reported as missing
        jsonld = []
    return {"path": path, "title": title, "meta_description": meta[0].strip() if meta else None,
            "canonical": canon[0].strip() if canon else None, "noindex": "noindex" in robots_meta,
            "h1": h1s, "links": links, "assets": assets, "main_text": main_text, "body_text": body_text,
            "jsonld": jsonld}


def shingles(text: str, n: int = 3) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {tuple(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def jaccard(a: str, b: str) -> float:
    sa, sb = shingles(a), shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ---------------------------------------------------------------- loading sites

def load_local(dist: Path) -> tuple[dict[str, str], dict[str, str], Callable[[str], bool], dict[str, int]]:
    """Return (pages path->html, extra files name->text, exists(path) for link checks, weight per page)."""
    if not dist.is_dir():
        raise ToolError(f"{dist} not found; build the site first (cd site && npm install && npm run build)")
    pages: dict[str, str] = {}
    for f in sorted(dist.rglob("*.html")):
        rel = f.relative_to(dist).as_posix()
        path = "/" + (rel[: -len("index.html")] if rel.endswith("index.html") else rel)
        pages[path] = f.read_text(encoding="utf-8")
    extra = {n: (dist / n).read_text(encoding="utf-8") for n in ("robots.txt", "sitemap-index.xml", "sitemap.xml")
             if (dist / n).is_file()}
    for sm in sorted(dist.glob("sitemap-*.xml")):
        extra[sm.name] = sm.read_text(encoding="utf-8")

    def exists(href: str) -> bool:
        p = urlparse(href).path
        target = dist / p.lstrip("/")
        return target.is_file() or (target / "index.html").is_file() or Path(str(target) + ".html").is_file()

    weights: dict[str, int] = {}
    for path, html in pages.items():
        page = parse_page(path, html)
        total = len(html.encode("utf-8"))
        for a in page["assets"]:
            if a.startswith("/") and not a.startswith("//"):
                f = dist / urlparse(a).path.lstrip("/")
                if f.is_file():
                    total += f.stat().st_size
        weights[path] = total
    return pages, extra, exists, weights


def load_url(base: str, fetch: Callable[[str], tuple[int, str]]) -> tuple[dict[str, str], dict[str, str]]:
    extra: dict[str, str] = {}
    for name in ("robots.txt", "sitemap-index.xml", "sitemap.xml"):
        status, text = fetch(urljoin(base + "/", name))
        if status == 200:
            extra[name] = text
    locs: list[str] = []
    for name in ("sitemap-index.xml", "sitemap.xml"):
        for loc in re.findall(r"<loc>([^<]+)</loc>", extra.get(name, "")):
            if loc.endswith(".xml"):
                status, text = fetch(loc)
                if status == 200:
                    extra[Path(urlparse(loc).path).name] = text
                    locs += re.findall(r"<loc>([^<]+)</loc>", text)
            else:
                locs.append(loc)
    pages: dict[str, str] = {}
    for loc in sorted(set(locs) or {base + "/"}):
        status, text = fetch(loc)
        if status == 200:
            pages[urlparse(loc).path or "/"] = text
    return pages, extra


# ---------------------------------------------------------------- checks

def _result(status: str, detail: str, items: list[str] | None = None) -> dict[str, Any]:
    return {"status": status, "detail": detail, "issues": items or []}


def run_checks(client: dict[str, Any], facts: dict[str, list[dict[str, Any]]], site_url: str,
               pages_html: dict[str, str], extra: dict[str, str], exists: Callable[[str], bool] | None,
               weights: dict[str, int] | None, lcp_ms: float | None, lcp_note: str) -> dict[str, Any]:
    pages = {p: parse_page(p, h) for p, h in pages_html.items()}
    indexable = {p: pg for p, pg in pages.items() if not pg["noindex"] and not p.startswith("/404")}
    town = (client.get("service_area") or [""])[0].lower()
    name = str(facts["name"][0]["value"]) if facts.get("name") else ""
    phones = {_digits(str(f["value"])) for f in facts.get("phone", [])}
    services = [str(f["value"]).lower() for f in facts.get("service", [])]
    service_words = {w for s in services for w in re.findall(r"[a-z]{4,}", s)} | NICHE_WORDS.get(str(client.get("niche")), set())
    loc = client.get("location") or {}
    address_public = bool(loc.get("address_public", True)) and client.get("business_type") != "service_area"
    street = re.sub(r"\s*\([^)]*\)\s*$", "", str(loc.get("address") or "")).split(",")[0].strip().lower()
    checks: dict[str, Any] = {}

    issues = []
    for p, pg in indexable.items():
        t = pg["title"]
        if not t:
            issues.append(f"{p}: no <title>")
            continue
        if not 30 <= len(t) <= 65:
            issues.append(f"{p}: title length {len(t)} (30–65)")
        if town and town not in t.lower():
            issues.append(f"{p}: title lacks town '{town}'")
        if not any(w in t.lower() for w in service_words):
            issues.append(f"{p}: title lacks a service word")
    checks["titles"] = _result("fail" if issues else "pass", f"{len(indexable)} indexable page(s)", issues)

    issues = []
    for p, pg in indexable.items():
        desc = pg["meta_description"]
        if not desc:
            issues.append(f"{p}: meta description missing")
        elif not 70 <= len(desc) <= 160:
            issues.append(f"{p}: meta description length {len(desc)} (70–160)")
    checks["meta"] = _result("fail" if issues else "pass", "meta description 70–160 chars", issues)

    issues = [f"{p}: {len(pg['h1'])} H1s" for p, pg in pages.items() if len(pg["h1"]) != 1]
    checks["h1"] = _result("fail" if issues else "pass", "exactly one H1 per page", issues)

    issues = []
    for p, pg in indexable.items():
        want = site_url.rstrip("/") + p
        if pg["canonical"] != want:
            issues.append(f"{p}: canonical {pg['canonical']!r} != {want!r}")
    checks["canonical"] = _result("fail" if issues else "pass", "absolute canonical = site URL + path", issues)

    issues = []
    for p, pg in pages.items():
        text = pg["body_text"]
        if name and name.lower() not in text.lower():
            issues.append(f"{p}: business name missing")
        seen_phones = {_digits(m.group(0)) for m in PHONE.finditer(text)}
        seen_phones |= {_digits(h) for h in pg["links"] if h.startswith("tel:")}
        if not seen_phones & phones:
            issues.append(f"{p}: verified phone missing")
        for other in sorted(seen_phones - phones):
            issues.append(f"{p}: phone {other} is not a verified phone (NAP mismatch)")
        if address_public and street and street not in text.lower():
            issues.append(f"{p}: street address '{street}' missing")
        if not address_public and street and street in text.lower():
            issues.append(f"{p}: hidden street address shown")
    checks["nap"] = _result("fail" if issues else "pass", "name, phone, address on every page", issues)

    issues = []
    for p, pg in indexable.items():
        blocks = [b for b in pg["jsonld"] if isinstance(b, dict)]
        biz = next((b for b in blocks if str(b.get("@type")) in ALLOWED_TYPES), None)
        if biz is None:
            issues.append(f"{p}: no LocalBusiness-type JSON-LD with an allowlisted @type")
            continue
        for prop in ("name", "telephone", "url", "openingHoursSpecification"):
            if not biz.get(prop):
                issues.append(f"{p}: JSON-LD missing {prop}")
        if not (biz.get("address") or biz.get("areaServed")):
            issues.append(f"{p}: JSON-LD missing address/areaServed")
        if not address_public and biz.get("address"):
            issues.append(f"{p}: JSON-LD shows an address for a hidden-address business")
        if name and biz.get("name") != name:
            issues.append(f"{p}: JSON-LD name {biz.get('name')!r} != verified {name!r}")
        if biz.get("telephone") and _digits(str(biz["telephone"])) not in phones:
            issues.append(f"{p}: JSON-LD telephone not a verified phone")
    checks["schema"] = _result("fail" if issues else "pass", "JSON-LD extracted with extruct", issues)

    robots = extra.get("robots.txt")
    synthetic = client.get("mode") == "fixture"
    if robots is None:
        checks["robots"] = _result("fail", "robots.txt missing")
    else:
        issues = []
        if "sitemap:" not in robots.lower():
            issues.append("no Sitemap line")
        blocks_all = re.search(r"(?im)^disallow:\s*/\s*$", robots) is not None
        if blocks_all and not synthetic:
            issues.append("robots.txt blocks the whole site")
        note = "synthetic demo blocks all crawling by design" if blocks_all and synthetic else "ok"
        checks["robots"] = _result("fail" if issues else "pass", note, issues)

    sitemap_text = " ".join(v for k, v in extra.items() if k.startswith("sitemap"))
    listed = {urlparse(u).path for u in re.findall(r"<loc>([^<]+)</loc>", sitemap_text) if not u.endswith(".xml")}
    missing = sorted(set(indexable) - listed)
    if not sitemap_text:
        checks["sitemap"] = _result("fail", "no sitemap found")
    else:
        checks["sitemap"] = _result("fail" if missing else "pass", f"{len(listed)} URL(s) listed",
                                    [f"{p}: not in sitemap" for p in missing])

    if exists is None:
        checks["internal_links"] = _result("unknown", "not checked in --url mode")
    else:
        issues = []
        for p, pg in pages.items():
            for href in pg["links"] + pg["assets"]:
                if href.startswith("/") and not href.startswith("//") and not exists(href):
                    issues.append(f"{p}: broken link {href}")
        checks["internal_links"] = _result("fail" if issues else "pass", "internal links and assets resolve",
                                           sorted(set(issues)))

    pairs = []
    for (pa, a), (pb, b) in combinations(sorted(indexable.items()), 2):
        score = round(jaccard(a["main_text"], b["main_text"]), 3)
        pairs.append({"a": pa, "b": pb, "similarity": score})
    too_similar = [f"{x['a']} vs {x['b']}: {x['similarity']}" for x in pairs if x["similarity"] > SIMILARITY_LIMIT]
    checks["similarity"] = _result("fail" if too_similar else "pass",
                                   f"max {max((x['similarity'] for x in pairs), default=0)} (limit {SIMILARITY_LIMIT})",
                                   too_similar)

    if weights is None:
        checks["page_weight"] = _result("unknown", "not measured in --url mode")
    else:
        heavy = [f"{p}: {w} bytes" for p, w in sorted(weights.items()) if w > WEIGHT_LIMIT]
        checks["page_weight"] = _result("fail" if heavy else "pass",
                                        f"max {max(weights.values(), default=0)} bytes (limit {WEIGHT_LIMIT})", heavy)

    if lcp_ms is None:
        checks["performance_lcp"] = _result("unknown", lcp_note)
    else:
        checks["performance_lcp"] = _result("fail" if lcp_ms >= LCP_LIMIT_MS else "pass",
                                            f"mobile LCP {round(lcp_ms)} ms (limit {LCP_LIMIT_MS} ms, PageSpeed Insights)")
    return {"checks": checks, "pages": sorted(pages), "similarity_pairs": pairs}


def psi_lcp(url: str, key: str) -> float:
    import httpx

    resp = httpx.get(PSI_URL, params={"url": url, "strategy": "mobile", "category": "performance", "key": key},
                     timeout=120.0)
    resp.raise_for_status()
    audits = resp.json()["lighthouseResult"]["audits"]
    return float(audits["largest-contentful-paint"]["numericValue"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a built (--local) or live (--url) client site.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local", action="store_true")
    mode.add_argument("--url")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD for the audit file name (default today)")
    args = parser.parse_args(argv)
    try:
        client_dir = find_client_dir(args.client, args.root)
        client = load_yaml(client_dir / "client.yaml")
        facts = verified_facts(client_dir)
        site_dir = client_dir / "site"
        config_path = site_dir / "site.config.json"
        site_url = (json.loads(config_path.read_text(encoding="utf-8"))["site_url"] if config_path.is_file()
                    else str(client.get("site_url") or (facts.get("website") or [{"value": ""}])[0]["value"]))
        if args.local:
            pages, extra, exists, weights = load_local(site_dir / "dist")
            lcp, note = None, "not measured: local mode (run with --url and PAGESPEED_API_KEY after a preview deploy)"
        else:
            import httpx

            def fetch(u: str) -> tuple[int, str]:
                r = httpx.get(u, timeout=30.0, follow_redirects=True, headers={"User-Agent": "MapsRankStudio site_check"})
                return r.status_code, r.text

            pages, extra = load_url(args.url.rstrip("/"), fetch)
            exists, weights = None, None
            key = os.environ.get("PAGESPEED_API_KEY")
            lcp = psi_lcp(args.url, key) if key else None
            note = "not measured: PAGESPEED_API_KEY not set" if not key else ""
        if not pages:
            raise ToolError("no pages found")
        result = run_checks(client, facts, site_url, pages, extra, exists, weights, lcp, note)
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    day = args.date or date.today().isoformat()
    out = {"schema_version": 1, "synthetic": client.get("mode") == "fixture", "client": args.client, "date": day,
           "mode": "local" if args.local else "url", "target": "site/dist" if args.local else args.url, **result}
    path = site_dir / f"audit-{day}.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    fails = [k for k, v in result["checks"].items() if v["status"] == "fail"]
    for k, v in result["checks"].items():
        print(f"{v['status'].upper():8} {k:16} {v['detail']}")
        for issue in v["issues"][:10]:
            print(f"           - {issue}")
    print(f"wrote {path.relative_to(args.root).as_posix()}: {len(fails)} must-pass failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
