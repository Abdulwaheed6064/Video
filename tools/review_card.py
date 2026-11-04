"""Build the review-request kit: printable QR cards + owner-ready messages (agents/review-engine.md).

Usage:
    uv run python tools/review_card.py --client <slug> --link https://g.page/r/XXXX/review

Writes clients/<slug>/reviews/request-kit/:
- review-card-business.png / .pdf (3.5 × 2 in) and review-card-a6.png / .pdf (A6), 300 dpi, QR -> link
- messages.md: SMS / WhatsApp / email texts + counter script + "how to get the link", filled from
  templates/messages/ with the verified business name and the review link
The card text comes from templates/review-card/card.yaml and is neutral (same request to everyone, no
incentives). All text is run through lint_claims; any flag aborts. The link must be https. A link that
doesn't look like a Google review link only gives a warning, because Google changes link formats.
Fixture clients get "SYNTHETIC" on every card. No network.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Any

import qrcode
from PIL import Image, ImageDraw, ImageFont

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.common import REPO_ROOT, ToolError, find_client_dir, load_yaml  # noqa: E402
from tools.lint_claims import lint_text, load_context  # noqa: E402
from tools.schema_gen import verified_facts  # noqa: E402

CARD_TEMPLATE = REPO_ROOT / "templates" / "review-card" / "card.yaml"
PDF_DATE = time.gmtime(946684800)  # 2000-01-01T00:00:00Z
MESSAGES = REPO_ROOT / "templates" / "messages"
GOOGLE_LINK = re.compile(r"^https://(g\.page/r/[\w-]+/review|search\.google\.com/local/writereview\?placeid=[\w-]+|"
                         r"www\.google\.com/maps/place/.+|maps\.app\.goo\.gl/[\w-]+)", re.I)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    import matplotlib

    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf" / name
    return ImageFont.truetype(str(path), size)


def _fit(draw: ImageDraw.ImageDraw, text: str, max_w: int, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    while size > 8:
        font = _font(size, bold)
        if draw.textlength(text, font=font) <= max_w:
            return font
        size -= 2
    return _font(size, bold)


def qr_image(link: str, px: int) -> Image.Image:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2, box_size=10)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").get_image().convert("RGB")
    return img.resize((px, px), Image.Resampling.NEAREST)


def render_card(kind: str, cfg: dict[str, Any], name: str, link: str, synthetic: bool) -> Image.Image:
    size = cfg["sizes"][kind]
    dpi = int(cfg["dpi"])
    w, h = round(size["width_in"] * dpi), round(size["height_in"] * dpi)
    c = cfg["colours"]
    img = Image.new("RGB", (w, h), c["background"])
    d = ImageDraw.Draw(img)
    pad = round(0.12 * dpi)
    if kind == "business":
        q = h - 2 * pad
        img.paste(qr_image(link, q), (w - pad - q, pad))
        text_w = w - q - 3 * pad
        lines = [(text, _fit(d, text, text_w, base, bold), colour)
                 for text, base, bold, colour in ((name, 64, True, c["ink"]), (cfg["headline"], 50, False, c["accent"]),
                                                  (cfg["ask"], 44, True, c["ink"]), (cfg["hint"], 34, False, c["muted"]))]
        y = (h - sum(round(f.size * 1.45) for _t, f, _c in lines)) // 2  # centre the text block vertically
        for text, font, colour in lines:
            d.text((pad, y), text, font=font, fill=colour)
            y += round(font.size * 1.45)
    else:
        y = pad * 2
        for text, base, bold, colour in ((name, 96, True, c["ink"]), (cfg["headline"], 80, False, c["accent"])):
            font = _fit(d, text, w - 2 * pad, base, bold)
            d.text(((w - d.textlength(text, font=font)) / 2, y), text, font=font, fill=colour)
            y += round(font.size * 1.5)
        q = min(w - 4 * pad, h - y - 5 * pad)
        img.paste(qr_image(link, q), ((w - q) // 2, y))
        y += q + pad
        for text, base, bold, colour in ((cfg["ask"], 64, True, c["ink"]), (cfg["hint"], 48, False, c["muted"])):
            font = _fit(d, text, w - 2 * pad, base, bold)
            d.text(((w - d.textlength(text, font=font)) / 2, y), text, font=font, fill=colour)
            y += round(font.size * 1.5)
    if synthetic:
        font = _font(28, True)
        d.text((pad, h - pad - 28), "SYNTHETIC DEMO: not for printing", font=font, fill="#b00020")
    return img


def build_messages(name: str, link: str) -> str:
    parts = ["# Review request kit: messages", "",
             "For the **owner** to send to their own customers after a real visit. Same message to everyone; "
             "no incentives; no screening. Read `templates/messages/README.md` (CASL note) first.", ""]
    for fname, title in (("sms.txt", "SMS"), ("whatsapp.txt", "WhatsApp"), ("email.txt", "Email")):
        text = (MESSAGES / fname).read_text(encoding="utf-8").strip()
        parts += [f"## {title}", "", "```text", text.replace("{business_name}", name).replace("{review_link}", link),
                  "```", ""]
    for fname in ("counter-script.md", "how-to-get-review-link.md"):
        body = (MESSAGES / fname).read_text(encoding="utf-8").strip()
        parts += [re.sub(r"^# ", "## ", body, count=1), ""]
    return "\n".join(parts)


def build_kit(client_dir: Path, link: str) -> list[Path]:
    if not link.startswith("https://"):
        raise ToolError("review link must start with https://")
    if not GOOGLE_LINK.match(link):
        print(f"WARNING: {link} does not look like a Google review link; test it on a phone before printing")
    client = load_yaml(client_dir / "client.yaml")
    facts = verified_facts(client_dir)
    if not facts.get("name"):
        raise ToolError("no verified name fact")
    name = str(facts["name"][0]["value"])
    cfg = load_yaml(CARD_TEMPLATE)
    messages = build_messages(name, link)
    card_text = "\n".join([name, cfg["headline"], cfg["ask"], cfg["hint"]])
    flags = lint_text(Path("kit.md"), card_text + "\n" + messages, load_context(client_dir))
    if flags:
        raise ToolError("request kit text fails lint_claims:\n  - " + "\n  - ".join(f"[{f.rule}] {f.text}" for f in flags))
    out = client_dir / "reviews" / "request-kit"
    out.mkdir(parents=True, exist_ok=True)
    synthetic = client.get("mode") == "fixture"
    written = []
    for kind in ("business", "a6"):
        img = render_card(kind, cfg, name, link, synthetic)
        png = out / f"review-card-{kind}.png"
        pdf = out / f"review-card-{kind}.pdf"
        img.save(png, dpi=(cfg["dpi"], cfg["dpi"]), optimize=True)
        # Fixed PDF dates: the kit is approved by digest (approvals.py), so output must be reproducible.
        img.save(pdf, "PDF", resolution=float(cfg["dpi"]), creationDate=PDF_DATE, modDate=PDF_DATE)
        written += [png, pdf]
    md = out / "messages.md"
    md.write_text(("> SYNTHETIC demo kit: fictional business.\n\n" if synthetic else "") + messages + "\n",
                  encoding="utf-8", newline="\n")
    (out / ".gitkeep").unlink(missing_ok=True)
    return written + [md]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the review-request kit (QR cards + owner messages).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--client", required=True)
    parser.add_argument("--link", required=True, help="the business's Google review link (https)")
    args = parser.parse_args(argv)
    try:
        files = build_kit(find_client_dir(args.client, args.root), args.link)
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for f in files:
        print(f"wrote {f.relative_to(args.root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
