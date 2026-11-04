---
result: PASS
sha256: a07f6cdf2edc9d728a8f275ec104274c0ae1711880932045ceaf2753268fc110
file: reviews/request-kit
date: 2026-11-11
reviewer: "Claude Code (cloud), same tool as the author, so not independent; re-review in Codex at B11"
---
# Compliance review: reviews/request-kit (SYNTHETIC demo)

RESULT: PASS

Review request kit (cards + messages). Checked against `knowledge/ranking-rules.md`, `facts.yaml`, `client.yaml` and the FAIL list in
`agents/compliance-reviewer.md`.

- Same neutral request to every customer on the cards, SMS, WhatsApp, email and counter script.
- No incentives (nothing offered for a review); no gating (no 'if you're happy', no star rating requested).
- No staff/family/friends suggestion; the counter script explicitly says not to.
- Business name exactly as F001; no claims; QR decodes to the review link (zxing test).
- CASL: the owner sends to their own customers after a real visit, no promotions; we store no customer data.
- Pre-check: lint_claims on the card text + messages (enforced by tools/review_card.py) → PASS.

Line-level issues: none.
