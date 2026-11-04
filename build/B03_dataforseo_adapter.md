# B03 — DataForSEO adapter (live rank data)

Read first: `build/README.md`, `docs/07` §2, `docs/08`, `docs/06` §6 and §9.
Where: code + recorded-fixture tests anywhere (cloud OK). **Live smoke test: local only** (needs `.env`).
Paid calls: ≤ US$2, only on explicit operator approval.

## Do

1. Read DataForSEO's **current** docs for Google Maps SERP and Google Organic SERP (task_post / task_get
   standard queue, and live). Record in `DECISIONS.md` with date: endpoint paths, the coordinate parameter
   format (`location_coordinate` = "lat,lng,zoom" or similar — verify), language, device, depth, result
   fields (place_id / cid, rank, rating, reviews_count, category), and **current prices + minimum deposit**.
2. **`tools/rank_scan.py`**
   `--client <slug> --label <baseline|mid|final|YYYY-MM-DD> [--keywords ...] [--mode grid|keywords-probe]
   [--organic] [--live] [--new-baseline]`
   - Refuses network for fixture clients (tells you to use fixture_scan.py).
   - Reads credentials from env (`DATAFORSEO_LOGIN/PASSWORD`) — never logs them.
   - Builds points with grid.py; estimates cost; runs `budget.check` before posting; aborts on failure.
   - Standard queue by default; `--live` only with the explicit flag.
   - Caches raw responses per point × keyword in `scans/<label>/raw/`; re-runs never re-buy cached points.
   - Matches the client by `place_id` from client.yaml. If missing: fallback name+phone match, writes the
     candidate into `questions.md` for human confirmation, and marks the scan `client_match: unconfirmed`.
   - `--organic`: organic SERP from the centre + town-centre point; stores the client's domain position.
   - Writes `grid.json` per docs/06 §6, `complete: false` + listed failures if any point failed; records
     actual cost to `budget/ledger.csv`.
   - Same-params check vs baseline unless `--new-baseline`.
3. Tests with recorded/handmade response fixtures in `tests/fixtures/dataforseo/` (no network): parsing,
   place_id matching, not-found → null, cache hit = no cost, budget abort, fixture-mode refusal,
   param mismatch refusal, credentials never appear in output/logs.
4. **Live smoke test — only if the operator types "approve live test" in this session**: 1 keyword,
   3×3 grid, on a business the operator names, cap US$2. Otherwise write it up in PROJECT_STATUS.md as
   "pending live test" with the exact command.

## Verify

```bash
uv run pytest -q
uv run python tools/rank_scan.py --help
uv run python tools/rank_scan.py --client _demo-barber --label x   # must refuse (fixture)
```

## Done when

Adapter tested offline; prices recorded; live test done or documented as pending; commit `B03: ...`.
