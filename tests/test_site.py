"""B06: schema_gen, build_site_config, site_check (saved HTML, no network), publish gate."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import REPO, write_client
from tools import site_release
from tools.build_site_config import build, hours_display
from tools.common import ToolError, load_yaml, sha256_path
from tools.schema_gen import generate, parse_hours, verified_facts
from tools.site_check import jaccard, load_local, run_checks

SLUG = "_demo-barber"


def facts_of(client_dir: Path) -> dict:
    return verified_facts(client_dir)


def client_of(client_dir: Path) -> dict:
    return load_yaml(client_dir / "client.yaml")


# ---------------------------------------------------------------- schema_gen

def test_schema_gen_storefront(root: Path) -> None:
    c = root / "clients" / SLUG
    data = generate(client_of(c), facts_of(c))
    assert data["@type"] == "HairSalon" and data["telephone"] == "+19055550100"
    assert data["address"]["streetAddress"] == "1 Example St" and data["address"]["addressLocality"] == "Bradford"
    assert data["openingHoursSpecification"][0]["dayOfWeek"] == ["Tuesday", "Wednesday", "Thursday", "Friday"]
    assert "award" not in json.dumps(data).lower()  # F007 is only proposed


def test_schema_gen_rejects_unknown_type(root: Path) -> None:
    c = root / "clients" / SLUG
    client = client_of(c) | {"schema_type": "BestBarberShop"}
    with pytest.raises(ToolError, match="allowlist"):
        generate(client, facts_of(c))


def test_schema_gen_ignores_proposed_facts(root: Path) -> None:
    c = root / "clients" / SLUG
    facts = c / "facts.yaml"
    text = facts.read_text(encoding="utf-8")
    # make the phone fact proposed: JSON-LD must then refuse (telephone is required, proposed never used)
    text = text.replace('value: "(905) 555-0100"\n    status: verified', 'value: "(905) 555-0100"\n    status: proposed')
    facts.write_text(text, encoding="utf-8")
    with pytest.raises(ToolError, match="telephone"):
        generate(client_of(c), facts_of(c))


def test_schema_gen_sab_has_no_street_address(root: Path) -> None:
    c = root / "clients" / SLUG
    client = client_of(c)
    client["business_type"] = "service_area"
    client["location"]["address_public"] = False
    client["service_area"] = ["Bradford", "Bond Head"]
    data = generate(client, facts_of(c))
    assert "address" not in data and "geo" not in data
    assert [a["name"] for a in data["areaServed"]] == ["Bradford", "Bond Head"]
    assert "Example St" not in json.dumps(data)


def test_parse_hours_and_display() -> None:
    spec = parse_hours("Tue-Fri 10:00-19:00; Sat 9:00-17:00; Sun-Mon closed")
    assert spec[1] == {"days": ["Saturday"], "opens": "09:00", "closes": "17:00"}
    rows = hours_display("Tue-Fri 10:00-19:00; Sat 09:00-17:00; Sun-Mon closed")
    assert rows[0] == {"label": "Tuesday – Friday", "value": "10:00 – 19:00"}
    assert rows[-1] == {"label": "Monday, Sunday", "value": "Closed"}
    with pytest.raises(ToolError):
        parse_hours("whenever we feel like it")


# ---------------------------------------------------------------- build_site_config

def _content(c: Path, text: str) -> None:
    (c / "site").mkdir(exist_ok=True)
    (c / "site" / "content.yaml").write_text(text, encoding="utf-8")


BASE_CONTENT = (REPO / "clients" / SLUG / "site" / "content.yaml").read_text(encoding="utf-8")


def test_build_config_from_demo_content(root: Path) -> None:
    c = root / "clients" / SLUG
    _content(c, BASE_CONTENT)
    cfg = build(c)
    assert cfg["synthetic"] is True and [s["slug"] for s in cfg["services"]] == ["skin-fade-bradford", "beard-trim-bradford"]
    assert cfg["business"]["phone_tel"] == "+19055550100" and cfg["business"]["address_lines"][0] == "1 Example St"


def test_build_config_refuses_unverified_service_fact(root: Path) -> None:
    c = root / "clients" / SLUG
    _content(c, BASE_CONTENT.replace("fact: F006", "fact: F007"))  # F007 is a proposed attribute
    with pytest.raises(ToolError, match="F007 is not a verified service"):
        build(c)


def test_build_config_refuses_claims_in_copy(root: Path) -> None:
    c = root / "clients" / SLUG
    _content(c, BASE_CONTENT.replace("We do skin fades and beard trims, Tuesday to Saturday.",
                                     "The best barber in Bradford for 15 years."))
    with pytest.raises(ToolError, match="lint_claims"):
        build(c)


# ---------------------------------------------------------------- site_check on saved HTML

def page(title: str, h1: str, body: str, path: str, phone: str = "(905) 555-0100",
         canonical_base: str = "https://demo-fade.example.test") -> str:
    tel = "+1" + "".join(ch for ch in phone if ch.isdigit())
    jsonld = json.dumps({"@context": "https://schema.org", "@type": "HairSalon", "name": "Demo Fade Co. (fictional)",
                         "telephone": "+19055550100", "url": "https://demo-fade.example.test/",
                         "address": {"@type": "PostalAddress", "streetAddress": "1 Example St"},
                         "openingHoursSpecification": [{"@type": "OpeningHoursSpecification"}]})
    return f"""<!doctype html><html lang="en-CA"><head><title>{title}</title>
<meta name="description" content="A meta description long enough to pass the seventy character minimum for this test page.">
<link rel="canonical" href="{canonical_base}{path}"><script type="application/ld+json">{jsonld}</script></head>
<body><header><a href="/">Demo Fade Co. (fictional)</a><a href="tel:{tel}">{phone}</a></header>
<main><h1>{h1}</h1><p>{body}</p></main>
<footer>Demo Fade Co. (fictional) 1 Example St, Bradford, ON <a href="tel:{tel}">{phone}</a></footer></body></html>"""


def make_dist(root: Path, pages: dict[str, str]) -> Path:
    dist = root / "clients" / SLUG / "site" / "dist"
    for path, html in pages.items():
        f = dist / path.strip("/") / "index.html" if path != "/" else dist / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
    locs = "".join(f"<url><loc>https://demo-fade.example.test{p}</loc></url>" for p in pages)
    (dist / "sitemap-0.xml").write_text(f"<urlset>{locs}</urlset>", encoding="utf-8")
    (dist / "robots.txt").write_text("User-agent: *\nDisallow: /\n\nSitemap: https://demo-fade.example.test/sitemap-index.xml\n",
                                     encoding="utf-8")
    return dist


LONG_A = ("A skin fade takes the sides and back down to bare skin and blends into longer hair on top. "
          "Tell your barber where the blend should start; low, mid and high fades look quite different. ") * 3
LONG_B = ("A beard trim brings the length down evenly, cleans the neckline under the jaw and tidies the cheek line "
          "so the shape looks deliberate. Say whether you are keeping length or going shorter. ") * 3


def check(root: Path, pages: dict[str, str]) -> dict:
    c = root / "clients" / SLUG
    dist = make_dist(root, pages)
    html, extra, exists, weights = load_local(dist)
    return run_checks(client_of(c), facts_of(c), "https://demo-fade.example.test", html, extra, exists, weights,
                      None, "not measured")["checks"]


def test_site_check_good_pages_pass(root: Path) -> None:
    checks = check(root, {
        "/": page("Barber shop in Bradford | Demo Fade Co. (fictional)", "Barber shop in Bradford",
                  "Skin fades and beard trims in Bradford, Tuesday to Saturday.", "/"),
        "/skin-fade-bradford/": page("Skin fade haircut in Bradford | Demo Fade Co.", "Skin fade in Bradford", LONG_A,
                                     "/skin-fade-bradford/"),
        "/beard-trim-bradford/": page("Beard trim in Bradford | Demo Fade Co. (fictional)", "Beard trim in Bradford",
                                      LONG_B, "/beard-trim-bradford/"),
    })
    failing = {k: v for k, v in checks.items() if v["status"] == "fail"}
    assert failing == {}
    assert checks["performance_lcp"]["status"] == "unknown"


def test_site_check_flags_similar_pages(root: Path) -> None:
    checks = check(root, {
        "/skin-fade-bradford/": page("Skin fade haircut in Bradford | Demo Fade Co.", "Skin fade in Bradford", LONG_A,
                                     "/skin-fade-bradford/"),
        "/fade-bond-head/": page("Skin fade haircut in Bradford, Bond Head | Demo", "Skin fade in Bond Head",
                                 LONG_A.replace("bare skin", "the skin"), "/fade-bond-head/"),
    })
    assert checks["similarity"]["status"] == "fail"
    assert jaccard(LONG_A, LONG_B) < 0.6


def test_site_check_detects_nap_mismatch(root: Path) -> None:
    checks = check(root, {
        "/": page("Barber shop in Bradford | Demo Fade Co. (fictional)", "Barber shop in Bradford", LONG_A, "/",
                  phone="(905) 555-0199"),
    })
    assert checks["nap"]["status"] == "fail"
    assert any("not a verified phone" in i for i in checks["nap"]["issues"])


def test_site_check_flags_seo_basics(root: Path) -> None:
    bad = page("Hi", "Barber", LONG_A, "/").replace("<h1>Barber</h1>", "<h1>Barber</h1><h1>Again</h1>")
    bad = bad.replace('href="https://demo-fade.example.test/"', 'href="/wrong/"').replace('<a href="/">', '<a href="/missing/">')
    checks = check(root, {"/": bad})
    for key in ("titles", "h1", "canonical", "internal_links"):
        assert checks[key]["status"] == "fail", key


# ---------------------------------------------------------------- publish gate

def pilot_site(root: Path, project: str | None = "demo-pilot-site") -> Path:
    c = write_client(root, "pilot-shop", "pilot", 15)
    if project:
        with (c / "client.yaml").open("a", encoding="utf-8") as fh:
            fh.write(f"cloudflare_pages_project: {project}\n")
    dist = c / "site" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html>ok</html>", encoding="utf-8")
    return c


def approve_site(root: Path, c: Path, digest: str | None = None) -> str:
    from tools.approvals import main as approvals_main

    digest = digest or sha256_path(c / "site" / "dist")
    (c / "reviews" / "compliance" / "site-2026-11-08.md").write_text(
        f"---\nresult: PASS\nsha256: {digest}\nfile: site/dist\ndate: 2026-11-08\n---\nRESULT: PASS\n", encoding="utf-8")
    base = ["--root", str(root)]
    assert approvals_main(base + ["request", "--client", "pilot-shop", "--action", "site_deploy", "--artifact", "site/dist",
                                  "--compliance-report", "reviews/compliance/site-2026-11-08.md",
                                  "--requested-by", "agent:site-builder", "--now", "2026-11-08T10:00:00-05:00"]) == 0
    aid = "A2026-11-08-site-deploy"
    assert approvals_main(base + ["approve", aid, "--by", "A", "--owner-by", "owner via email",
                                  "--owner-at", "2026-11-08T09:00:00-05:00", "--now", "2026-11-08T10:05:00-05:00"]) == 0
    return aid


def test_preflight_refuses_fixture_client(root: Path) -> None:
    ok, lines = site_release.preflight(root, SLUG)
    assert not ok and "never published" in lines[0]


def test_preflight_refuses_without_project_or_approval(root: Path) -> None:
    c = pilot_site(root, project=None)
    assert "cloudflare_pages_project" in site_release.preflight(root, "pilot-shop")[1][0]
    with (c / "client.yaml").open("a", encoding="utf-8") as fh:
        fh.write("cloudflare_pages_project: demo-pilot-site\n")
    ok, lines = site_release.preflight(root, "pilot-shop")
    assert not ok and "no site_deploy approval" in lines[0]


def test_preflight_refuses_changed_build_and_accepts_exact_one(root: Path) -> None:
    from datetime import datetime

    c = pilot_site(root)
    approve_site(root, c)
    now = datetime.fromisoformat("2026-11-08T12:00:00-05:00")
    ok, lines = site_release.preflight(root, "pilot-shop", now)
    assert ok and lines[0] == "APPROVAL=A2026-11-08-site-deploy" and lines[1] == "PROJECT=demo-pilot-site"
    (c / "site" / "dist" / "index.html").write_text("<html>changed after approval</html>", encoding="utf-8")
    ok, lines = site_release.preflight(root, "pilot-shop", now)
    assert not ok and "!= this build" in lines[0]


def test_publish_script_refuses_without_valid_approval(root: Path, tmp_path: Path) -> None:
    pilot_site(root)
    fakebin = tmp_path / "bin"
    fakebin.mkdir()
    marker = tmp_path / "npx-called"
    (fakebin / "npx").write_text(f"#!/bin/sh\ntouch {marker}\n", encoding="utf-8")
    (fakebin / "npx").chmod(0o755)
    env = {**os.environ, "MRS_ROOT": str(root), "SKIP_BUILD": "1", "PATH": f"{fakebin}{os.pathsep}{os.environ['PATH']}"}
    script = REPO / "tools" / ("deploy" + ".sh")
    proc = subprocess.run(["bash", str(script), "pilot-shop"], env=env, capture_output=True, text=True, input="y\n",
                          timeout=120)
    assert proc.returncode == 1
    assert "REFUSED" in proc.stdout + proc.stderr
    assert not marker.exists(), "wrangler (npx) must not be called without a valid approval"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_publish_script_refuses_fixture_demo(root: Path, tmp_path: Path) -> None:
    dist = root / "clients" / SLUG / "site" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("x", encoding="utf-8")
    env = {**os.environ, "MRS_ROOT": str(root), "SKIP_BUILD": "1"}
    script = REPO / "tools" / ("deploy" + ".sh")
    proc = subprocess.run(["bash", str(script), SLUG], env=env, capture_output=True, text=True, input="y\n", timeout=120)
    assert proc.returncode == 1 and "never published" in proc.stdout
