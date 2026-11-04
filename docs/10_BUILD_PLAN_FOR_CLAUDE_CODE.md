# Build plan — moved to `build/`

The work packages B00–B11 now live as one file each in [`../build/`](../build/README.md), so you can run
them directly:

- Claude Code: `/build B00` (then B01, B02, …)
- Codex: `Follow prompts/build.md with ARGS = B00`

`build/README.md` holds the step table, the universal rules every step follows, which steps can run in a
Claude cloud session, and the dependency order. The acceptance tests (A01–A17) are in
`build/B11_independent_audit.md`.
