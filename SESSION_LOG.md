# Session log

Append one entry per AI session. Newest at the bottom.

Template:

```text
## YYYY-MM-DD HH:MM · <Claude Code | Codex | Claude cloud> · <model> · <task e.g. B03 or sprint kings-barbers day 2>
- Files changed:
- Commands run (with real results):
- Stubbed / not working:
- Next:
```

---

## 2026-11-03 · Claude Code (desktop) · Opus 5.5 · planning

- Files changed: moved draft pack 00–12 into `docs/`; added README, AGENTS.md, CLAUDE.md, PROJECT_STATUS,
  DECISIONS, this log, `docs/13`, `docs/14`, `build/B00–B11`, `agents/*` (14), `.claude/agents/*`,
  `.claude/commands/*`, `prompts/*`, `knowledge/ranking-rules.md`, `.claude/settings.json`,
  `.gitignore`, `.env.example`.
- Commands run: none beyond file moves. No code, no tests yet.
- Stubbed: all of `tools/`, `schemas/`, `templates/`, `tests/`.
- Next: B00.

## 2026-11-04 · Claude cloud · Claude Code · B00 bootstrap

- Files changed: `DECISIONS.md` (verified doc links, settings decision, `synthetic` key),
  `PROJECT_STATUS.md`, `.claude/settings.json` (new), `templates/claude/settings.json` (`$schema`
  added, `git push` deny removed), `pyproject.toml`, `uv.lock`, `.python-version`, `tools/__init__.py`,
  `tests/__init__.py`, `tests/test_smoke.py`, `budget/ledger.csv`, `clients/_demo-barber/**`
  (client.yaml, facts.yaml, questions.md, access.md, log.md, intake/questionnaire.md, intake/notes.md,
  `.gitkeep` folders per docs/06 §1).
- Commands run (with real results):
  - WebFetch code.claude.com docs (sub-agents, slash-commands, memory, settings, permissions): OK, findings in DECISIONS.
  - WebFetch developers.openai.com: failed (`getaddrinfo ENOTFOUND`; host not allowed by the session network).
  - `uv init --bare --python 3.12 --name maps-rank-studio`: initialized. `uv add pyyaml jsonschema pydantic matplotlib qrcode pillow httpx`: OK. `uv add --dev pytest`: OK (pytest 9.2.0).
  - `uv run python --version`: Python 3.12.3.
  - `uv run pytest -q`: `11 passed in 1.55s`.
  - `git log --oneline -1`: the `B00: bootstrap` commit, made right after this entry.
- Stubbed / not working: Codex formats not verified (network). `tools/validate.py` doesn't exist yet
  (B01). Step 7 (`gh repo create`) skipped: the repo already exists on GitHub (abdulwaheed6064/seo).
- Next: B01. Its schemas must accept `synthetic: true` on client.yaml/facts.yaml.
