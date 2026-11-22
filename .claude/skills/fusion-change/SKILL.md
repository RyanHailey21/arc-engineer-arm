---
name: fusion-change
description: Make, check and record a change in the Autodesk Fusion design master (ARC Arm Rev A/B, the shared four-bar gripper, purchased parts) through the Fusion MCP. Use for any Fusion edit, a Fusion snapshot, or comparing Fusion with the code-CAD.
---

# Change the Fusion design master

Fusion is the design master; the code-CAD is the reference the checks run on. `fusion/README.md` has the
snapshot and check commands, the record of fixes applied, and the Fusion API notes. Read it first.

## Rules
- One Fusion writer at a time: you, or Codex (see the `codex-fusion` skill), never both.
- Never modify, move, rename or delete Fusion items this project did not create, unless the user asks.
- Edit a shared document (the four-bar gripper, `Base_Plate_AL5`, purchased parts) in its own document, then
  update the references in both assemblies. Both revisions use it.
- Fusion MCP calls time out on the client but finish inside Fusion. Write every result to a file under
  `fusion/checks/out/` as each step finishes, then wait for the file. Never re-send a call that timed out.
- Open documents visibly (`documents.open(f, True)`): `updateAllReferences` on an invisibly opened document
  crashes Fusion.
- Keep a change as a script in `fusion/` (with a `MODE = "list"` dry run) so it is recorded and repeatable.
- Fusion hung for more than about 25 minutes: the watchdog (`C:\Users\ryanh\tools\_agent\codex-fusion\fusion_watchdog.ps1`)
  relaunches it. Never launch Fusion yourself.

## Steps
1. Dry run: list what the script would change and check it against the snapshot (`fusion/snapshot/<rev>/snapshot.json`).
2. Apply it and save with a version description that says what changed.
3. Re-snapshot both revisions: `fusion/snapshot_export.py` `export(rev)` in a read-only MCP script.
4. Compare with the previous snapshot (git diff of `snapshot.json`): no occurrence moved unless intended, masses as
   expected.
5. Checks: `fusion/checks/mass_torque.py` for both revisions, and `fusion/checks/interference.py` (about 15 min,
   in the background) when geometry changed.
6. Record it: add a row to the "Fixes applied" table in `fusion/README.md` and update "Still open". Then rebuild
   the paper (`cad/docs/paper/make_paper.py`); it reads the Fusion versions from the check results.
7. Run the `verify` skill and commit.
