# B10 — Clean dry run, then live baseline on a pilot

Read first: `build/README.md`, `docs/05`, `docs/11`, `docs/12` §3, `docs/13` §12.
Where: **local only** (real data, API keys). Paid calls: ≤ US$10.

## Part 1 — fixture dry run from a clean clone

1. Write `RUNBOOK.md`: install (uv, Node), `.env` setup, daily commands, how to approve/apply/consume, how
   to start a new client, how to switch Claude Code ↔ Codex, how to recover from a blocked task.
2. `git clone` the repo into a temp folder; follow ONLY `RUNBOOK.md` to run the demo sprint days 0→20.
3. Fix every bit of friction in docs or scripts. Record minutes per step in `SESSION_LOG.md`.

## Part 2 — live pilot (STOP and ask before starting)

Only after the operator confirms in this session: (a) the business name, (b) the owner's **written**
permission is saved in the client folder, (c) the operator has **Manager** access to the GBP,
(d) DataForSEO is funded and `.env` is set.

1. `clients/<slug>/` in `mode: pilot`, `budget_cad_month` set; fill `intake/` from the operator's notes.
2. Run intake → send the fact sheet → operator marks facts verified.
3. Find and confirm the GBP `place_id` (rank_scan match flow, human confirms).
4. Baseline scan (full keywords, cap US$10) → metrics → heatmaps → keyword-competitor gap analysis.
5. **STOP** after baseline + gap analysis. From here the operator runs `/sprint <slug> <day>` daily.

## Done when

RUNBOOK works from a clean clone; pilot baseline exists with real heatmaps and gap analysis; commit
(client folder only in the private repo).
