# B08 — Reviews, content, link prospects

Read first: `build/README.md`, `knowledge/ranking-rules.md`, `agents/review-engine.md`, `agents/content.md`,
`agents/link-prospector.md`, `docs/11` §2 (CASL).
Where: local or cloud. Paid calls: none.

## Do

1. **`templates/review-card/`** — printable card (business-card and A6 sizes): QR code to the review link,
   short neutral text ("Thanks for visiting! Would you leave us a Google review?"), business name.
   **`tools/review_card.py --client <slug> --link <url>`** → PDF/PNG in `reviews/request-kit/`.
2. **`templates/messages/`** — neutral review-request texts (SMS, WhatsApp, email), same for every customer,
   no incentives, no sentiment screening; a 30-second counter script for staff; header note: the **owner**
   sends these to their own customers after a real visit (transactional follow-up); marketing messages
   need CASL consent; we never store customer contact data.
3. **`tools/review_velocity.py --client <slug>`** — weekly review count/rating series from scan data →
   `reviews/velocity.json`.
4. Reply templates guidance inside `agents/review-engine.md` (positive, neutral, negative with offline
   resolution; no personal data; no arguing).
5. **Demo run (all marked synthetic):** request kit; 3 reply drafts for fixture reviews in
   `reviews/inbox.md` (5★, 3★, 1★); `content/<month>/posts.md` (4 posts) + `photos.md`;
   `links/prospects.csv` (10 rows, synthetic). compliance-reviewer must PASS each; lint_claims on each.

## Tests

lint_claims passes the neutral templates and fails an incentive variant · review_card produces a PDF with
a decodable QR (use a QR decode lib or check the encoded payload) · velocity computes weekly deltas.

## Verify

```bash
uv run pytest -q
uv run python tools/review_card.py --client _demo-barber --link https://g.page/r/EXAMPLE/review
uv run python tools/validate.py clients/_demo-barber
```

## Done when

Kit, replies, posts, prospects exist for the demo with compliance PASS; tests pass; commit.
