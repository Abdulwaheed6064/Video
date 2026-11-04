# Build one step

ARGS: $ARGUMENTS   (e.g. `B03`)

1. Open `build/` and find the file whose name starts with the step id in ARGS. Read `build/README.md`
   (universal rules) and that file completely.
2. Do the session-start protocol from AGENTS.md.
3. Execute ONLY that step's instructions. Do not start the next step.
4. Run the step's "Verify" commands and paste real output into SESSION_LOG.md.
5. Update PROJECT_STATUS.md (implemented / stubbed / blocked) and commit `Bxx: <summary>`.
6. Print: what was built, what is stubbed, the exact next step.
