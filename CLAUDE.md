# ARC S2 Engineer arm — working conventions

Code-CAD robot arm in FreeCAD 1.1 Python (`%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecadcmd.exe`; pin this version).
Start with `cad/MAP.md` (generated): every module, parameter file, interface, keep-out zone, and every part with the file:line that builds it.

## Design inputs and variants
- Design inputs live in `cad/params/*.toml`, `cad/interfaces/*.toml` (mates; both parts build from the file through `cad/iface.py`), `cad/envelopes/*.toml` (field keep-outs) and `cad/data/catalogue.toml` (purchased parts). **Edit these, not literals in code.** New mates or limits go there first; when you move a part, check its mate is in `interfaces/` (a standoff moved through a parameter once left its plate holes behind).
- `cad/params/variant.toml` sets the gripper (`GRIP`, only `FOURBAR`) and the J1/J2 base drive (`BASE_DRIVE`: `GEARED` = rev B STS3215 + 3:1 spur stage; `DIRECT` = DM-J4340 direct drive, Fusion "Rev A", outputs and fingerprint `fourbar_direct`). Env vars override it.
- `import arm_model as M` (`cad/arm_model.py`) is the compatibility facade over `cad/arm/`.
- New gripper: `cad/arm/grippers/<name>.py` with a bodies function and a `placements(Hd, jaw)` function (names are free: FOURBAR's are `fourbar_bodies`, `fb_placements`), paired in `cad/arm/bodies.py` GRIPPERS, mounted on `cad/interfaces/roll_hub__gripper_palm.toml`.
- Autodesk Fusion is the design master; the team edits there. Fusion work follows the `fusion-change` skill, one Fusion writer at a time (you or Codex, see `codex-fusion`).

## Frames
- World/robot frame: x forward from the bumper, y left, z up from the floor.
- Gripper frame: x along the roll axis, TCP at (151, 0, −20), roll axis at z = −5.
- `jaw` = gap between the pad arcs at the TCP: pipe 13.8, donut 100, open 112.

## Checks (run from the repo root; `cad/tools/run.py` keeps freecadcmd's output and exit code)
- After a change: `python -I cad/tools/run.py cad/tools/quick_check.py` (about 90 s). PASS and fingerprint MATCH; add `BASE_DRIVE=DIRECT` when the base or a shared module changed. After an *intended* geometry change, re-record with `FP_MODE=record` and say which parts changed. The `verify` skill picks the checks for a given diff.
- Milestones: `python -I cad/tools/run.py --timeout 900 cad/check_interference.py` (about 4 min, ground truth). FEA and renders only on request.
- `cad/out/<variant>/manifest.json` records each check's status and inputs hash (FRESH/STALE).
- The FreeCAD working document `cad/out/<variant>/ARC_Arm_<Variant>.FCStd` (Git LFS) is rebuilt by `cad/tools/working_doc.py`. A headless rebuild leaves a copy open in the GUI stale: rebuild in the GUI before showing the model, then run `import check_working_doc as W; W.main()` there.

## Guard rails
- The released package (rev B since 2026-11-19) in `cad/fab/`, `cad/fea/out/` and `cad/render/out/` changes only on request; a hook asks before hand edits there. Its generators (`cad/export_fab.py`, `cad/fea/run_fea.py`, `cad/render/export_render.py`) refuse non-release variants; a non-release STEP/BOM comes from `cad/tools/export_variant.py`.
- Documentation is one PDF, `cad/docs/ARC_S2_Engineer_Arm.pdf`, rebuilt from the check results by `python -I cad/docs/paper/make_paper.py` (MiKTeX). Wording goes in `cad/docs/paper/paper.tex`; `numbers.tex` is generated. No drawings, and no parallel docs: README.md only points to the PDF, `fusion/README.md` and `sim/README.md`. Deliverables live in this GitHub repo (not OneDrive).
- In a running FreeCAD GUI, call `arm.reload_all()` to pick up edits. Don't drive the GUI from `execute_code_async`.
- Run long jobs (full interference, FEA, renders) in the background.

## Agent tooling
- Project skills in `.claude/skills/`: `verify`, `fusion-change`, `codex-fusion`, `repo-upkeep` (the daily scheduled upkeep).
- Docs MCP servers: `claude-code-docs`, `claude-platform-docs`, `openai-docs`. Check features there, not from memory.
- Tooling friction goes in `cad/docs/tooling_issues.md`, one TI row each; upkeep runs in its "Upkeep runs" table.
- Bash: use absolute paths instead of a leading `cd`; wait on long jobs with `run_in_background` or Monitor, never `sleep`.
