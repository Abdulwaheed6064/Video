# Claude cloud credits, subscriptions and usage — how to spend them well

Written 3 November 2026. Check your own Settings → Usage page; plans and credit rules change.

## 1. What uses what

| Where you run it | What it bills against | Can see your local folder? |
| --- | --- | --- |
| Claude Code **in VS Code / terminal / desktop app on your PC** (local session) | Your Claude **subscription usage limits** | Yes |
| Claude Code **cloud session** (claude.ai/code, or "cloud" target in the desktop app) | **Cloud session credits first** (your $100), then normal plan usage | **No** — it clones a **GitHub repo** into a cloud machine |
| Codex in VS Code / CLI | Your ChatGPT subscription | Yes (local) |
| `tools/` scripts (DataForSEO etc.) | DataForSEO prepaid balance | — |

**Important:** a local session like the one that wrote these files does **not** spend the $100 cloud credit.
To use the credit, the work has to run as a cloud session, and a cloud session can only work on code that
is in a GitHub repository.

## 2. Your $100 credit expires 5 Nov 2026, 2:59 AM EST — best use

Cloud sessions are ideal for **build steps that are pure code and need no secrets and no real client data**.
That is exactly B00–B02 and B04–B09 (all fixture mode).

| Build step | Run in cloud? | Why |
| --- | --- | --- |
| B00 bootstrap | ✅ Yes | Pure setup |
| B01 schemas, validator, approvals, budget | ✅ Yes | Pure code + tests |
| B02 grid, fixture scans, metrics, heatmaps | ✅ Yes | Pure code + tests |
| B03 DataForSEO adapter | ✅ Code + recorded-fixture tests in cloud · ❌ the **live** smoke test (needs `.env` secrets) — do that locally |
| B04–B09 | ✅ Yes (fixture mode) | Pure code + demo client |
| B10 live baseline | ❌ Local only | Real client data + API keys |
| B11 audit | ✅ or Codex locally | Independent review |
| Real client sprints | ❌ Local only | Client data must stay in your private repo/PC; secrets |

### Steps to use the credit before it expires

1. Create a **private** GitHub repository (e.g. `maps-rank-studio`). Keep it private — later it may hold
   client data.
2. From this folder: `git init`, commit, add the remote, push `main`. (Ask Claude Code locally to do it:
   "git init, commit everything, create a private GitHub repo maps-rank-studio with gh and push".)
3. Open **claude.ai/code** (or start a cloud session from the desktop app), pick the repo.
4. Paste the contents of `build/B00_bootstrap.md` as the first message. Let it finish, open a PR,
   review it, merge.
5. In the **same** cloud session (so it keeps context, cheaper than starting over), send
   "Now do build/B01_contracts_validator_approvals_budget.md". Repeat B02, B04… one step at a time,
   merging each PR before the next.
6. Pull the merged `main` to your PC and keep going locally once the credit is gone.

Rule of thumb: **one build step per cloud turn, review every PR**. Don't paste all steps at once; a long
unreviewed run is how you burn credit on work you later throw away.

## 3. Keeping subscription usage low (after the credit)

- Scripts do the heavy lifting — scans, metrics, heatmaps, validation cost zero tokens.
- Give an agent only its spec + the client files it needs. Never "read the whole repo".
- Strong model (Opus) only for: keyword-competitor, gbp-optimizer, compliance-reviewer, B11 audit.
  Mid (Sonnet) for most work. Fast (Haiku) for posts, citations, mechanical edits.
- Split work between Claude Code and Codex: when one subscription is near its limit, continue in the other.
  The repo holds the state, so either tool can pick up.
- If a run loops or rewrites the same file, stop it and narrow the task.
