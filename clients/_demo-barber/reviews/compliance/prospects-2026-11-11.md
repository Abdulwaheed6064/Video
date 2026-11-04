---
result: PASS
sha256: 4e0c6fd6b12d392cff3042fc04fa598fad2cf0b417b2aac1bd751a22e695dd9a
file: links/prospects.csv
date: 2026-11-11
reviewer: "Claude Code (cloud), same tool as the author, so not independent; re-review in Codex at B11"
---
# Compliance review: links/prospects.csv (SYNTHETIC demo)

RESULT: PASS

Link prospects (operator decides). Checked against `knowledge/ranking-rules.md`, `facts.yaml`, `client.yaml` and the FAIL list in
`agents/compliance-reviewer.md`.

- All 10 rows are fictional (example.test), marked SYNTHETIC and `unverified` with an empty checked_on (nothing was loaded).
- No bought links, PBNs, guest-post farms or link exchanges; editorial or real-relationship opportunities only.
- Contact is by the operator/owner only; the agent contacted no one. Paid items show cost 'unknown' (not estimated).
- lint_claims → PASS; validate.py link-prospect rules → OK.

Line-level issues: none.
