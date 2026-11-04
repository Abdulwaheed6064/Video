---
result: PASS
sha256: 7f52e428363c4c51dc4f5e24491dcaad6b1379451951a42c1f6e3f61f02ec492
file: gbp/description-options.md
date: 2026-11-07
reviewer: "Claude Code (cloud), same tool as the author, so not independent; re-review in Codex at B11"
---
# Compliance review: gbp/description-options.md (SYNTHETIC demo)

RESULT: PASS

Pre-check: `uv run python tools/lint_claims.py clients/_demo-barber/gbp/description-options.md --client _demo-barber` → `PASS: 0 flag(s)`.

- Both options use verified facts only (F001, F002, F004, F005, F006) plus the town from `client.yaml`.
- No superlatives, awards, years, prices or ranking language. F007 (proposed) and F008 (rejected) are
  named only as "not used".
- Business name exactly as F001; no keywords or towns attached to it.
- Both are well under the 750-character limit (lengths stated in the file, from Python `len()`).

Line-level issues: none. This file goes to the owner to choose an option; it is not applied to Google
by itself.
