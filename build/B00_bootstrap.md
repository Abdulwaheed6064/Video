# B00 — Bootstrap

Read first: `build/README.md` (universal rules), `README.md`, `docs/03`, `docs/09`, `docs/13`, `DECISIONS.md`.
Where: local or cloud. Paid calls: none.

## Already exists (from the planning session — do not recreate, only fix if wrong)

`AGENTS.md`, `CLAUDE.md`, `PROJECT_STATUS.md`, `DECISIONS.md`, `SESSION_LOG.md`, `.gitignore`,
`.env.example`, `docs/00–14`, `agents/*.md` (14), `.claude/agents/*.md` (14), `.claude/commands/*.md`,
`prompts/*.md`, `knowledge/ranking-rules.md`, `templates/claude/settings.json`.

## Do

1. **Verify tool formats against current official docs** and record links + date in `DECISIONS.md`:
   - Claude Code: `CLAUDE.md` `@` imports; `.claude/agents/*.md` frontmatter (`name`, `description`,
     `tools`, `model`); `.claude/commands/*.md` with `$ARGUMENTS` and `argument-hint` (or whether
     `.claude/skills/` is now preferred); `.claude/settings.json` permission rule syntax.
   - Codex: `AGENTS.md` discovery; `codex exec` non-interactive; whether project-level prompts/skills exist.
   - Fix any wrapper/command file whose format is outdated. Keep `agents/` and `prompts/` as the source.
2. **Install Claude permissions:** copy `templates/claude/settings.json` to `.claude/settings.json`
   (fix the syntax if step 1 found differences). Ask the operator to approve this write — it changes
   Claude Code's own permissions.
3. **Python project:** `uv init --python 3.12` (no sample app), then
   `uv add pyyaml jsonschema pydantic matplotlib qrcode pillow httpx` and `uv add --dev pytest`.
   Create `tools/__init__.py`, `tests/__init__.py`, `tests/test_smoke.py` (imports work).
4. **Demo client** `clients/_demo-barber/` in `mode: fixture`, every file marked synthetic:
   - `client.yaml` per docs/06 §2: fictional "Demo Fade Co. (fictional)", centred on central Bradford, ON
     (≈ 44.1145, -79.5650), storefront, keywords `["barber bradford", "barber shop near me",
     "fade haircut bradford"]`, grid 7×7 at 0.7 km, `gbp_status: active`, `budget_cad_month: 0`.
   - `facts.yaml`: 6 verified facts (name, phone 555-0100, website https://demo-fade.example.test, hours,
     2 services), 1 proposed fact ("Award-winning", no evidence), 1 rejected fact.
   - `questions.md`, `access.md`, `log.md`, `intake/questionnaire.md` (filled, fictional),
     `intake/notes.md`, empty folders per docs/06 §1 with `.gitkeep`.
5. Create `budget/ledger.csv` with the header row only (docs/06 §9).
6. `git init` (if not already), first commit `B00: bootstrap`.
7. Optional, only if the operator says so: create a **private** GitHub repo with `gh repo create
   maps-rank-studio --private --source . --push`.

Do not build tools beyond the smoke test.

## Verify

```bash
uv run pytest -q
git log --oneline -1
```

## Done when

Tests pass, commit exists, `.claude/settings.json` installed (or the operator declined — note it),
`DECISIONS.md` lists verified doc links with today's date.
