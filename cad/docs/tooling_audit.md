# CAD tooling and workflow audit (2026-11-15)

Scope: the freecad-mcp server (`C:\Users\ryanh\tools\freecad-mcp`, branch `feat/techdraw-asme-layout`,
commit cf88122, not pushed) and the drawing tooling that still lives in this repo (`cad/drawings/*`,
`cad/tools/*`, `cad/fea/*`, `cad/fab/*`).

## 1. Where things stand

| Area | freecad-mcp (prebuilt) | Arm repo (scratch) | Verdict |
|---|---|---|---|
| Interference, motion poses | `interference_check` (cached, parallel, 14 poses in ~40 s) | provider only | Works. Has a cache bug (see 3.1). |
| Hole edge distance | `hole_edge_check` | `tools/check_holes.py` (D-bore vs breakout test) | Duplicated. The arm version is better. |
| FEA | `run_fem_analysis` | `fea/run_fea.py`, `render_fea.py` | The arm runner has the mesh fallbacks and zero-response guard. Move it into the MCP. |
| TechDraw sheets | `techdraw_part_drawing`, `techdraw_annotate`, `techdraw_lint`, ASME rules, layout engine, skill | `batch_drawings.py` (1012 lines), `layout.py`, `make_drawings.py`, `check_datums.py`, `lint_pdf.py` | Diverged. The MCP port is a snapshot from 07:21 today; three review rounds of fixes since then are only in the arm repo. |
| Projected heights, procurement, TDP | none | `projected_heights.py`, `make_procurement.py`, `make_tdp.py` | Project-specific. Keep them here, but read data through MCP tools. |

The MCP work succeeded where it was used: the cached interference checks, headless FEA, the McMaster lookups and
the ASME rules port all held up. Ported back from the MCP: frame-inclusive balloon boxes, which caught
leader clips that the arm checker missed. The gap is that every drawing fix since the port went into the
arm repo, so the MCP tool is now behind the project.

## 2. Arm-repo drawing features missing from the MCP port

These were found by three independent reviews (DEFECT count 46, then 38, then 10, then 19 after the
regressions). Each one is a real Y14.5 or shop issue.

### 2.1 Feature recognition (pure Part, headless-testable)

- **Hole sides:** near and far side by probing where a feature opens. Counterbores and countersinks are probed in the ring between the hole and the outer diameter, not on the axis, which is open space inside a through hole.
- **Hole types:** countersinks with the included angle taken from the cone geometry; blind holes from each face (EACH SIDE); coaxial side holes split by their extent along the axis.
- **Side holes:** which end is open (`open_dir`), so FAR SIDE can be decided per view.
- **Stray chords:** a D-bore flat must be at least 0.1 mm deep, so seam slivers are not called D-bores.
- **Hole/feature flags:** shaft grooves are counted, drive flats are taken relative to the shaft axis, and hex drives are noted.

### 2.2 TechDraw robustness (GUI)

- Set Scale and ScaleType on every projection-group item, and `touch()` the items on each scale change, because the items do not recompute when only the scale changes.
- Turn on HardHidden before the first compute; otherwise `getHiddenEdges()` returns nothing.
- `getVisible/HiddenEdges` return page units (multiplied by scale, y flipped). Derive the factor from the data rather than trusting `view.Scale`.
- **Stale-geometry guard:** a view's extent must equal the part's true extent. Stable stale geometry passes "unchanged for 3 polls".
- Before the frame fit, refresh every view the same way export does.
- **Vertex renumbering:** dimensions record their target coordinates (`RefPts`), and `rebind_dims()` re-resolves them before export.
- Datum anchors are in model units (k-normalised); never snap them to edge coordinates.

### 2.3 Callout and ASME semantics

- FAR SIDE callouts to hidden circles, for holes, counterbores, side holes and journals.
- Leaders are matched to the group's own hole positions, not to any circle with the same radius.
- When the datum group is a hole with a counterbore, the callout is split, so the datum is unambiguous.
- Fits are shown as `⌀4 H7` only (5.2.1), with no inline `(+a/b)`.
- "ALL OVER" goes beneath the profile FCF (11.3.1.5(b)). Note 1 states the exception for directly toleranced features (11.3.1.4).
- Side-hole and journal FCFs are real frames, not note text.
- Notes are driven by features: threads, anodize masking, REAM/BORE, inserts, countersinks, shaft steps and grooves, shim material by thickness.
- Shafts take datum A on the diameter dimension line. Reference sizes are shown in parentheses to 1 decimal. Diameter dimensions are placed at an angle that clears the holes. The profile FCF starts at the end of the part with fewer holes.
- Bug in the MCP copy of `asme_rules.mm()`: with `nd=0` it strips trailing zeros from integers ("80" → "8").

### 2.4 Layout

- Leaders must not cross other views or other callout target holes (`_obstacles`, `_leader_hits`).
- The callout shoulder (landing line) is part of the callout's box.
- Leaders that hug an FCF edge are caught (expanded box).
- Callout, FCF and datum of the same group may abut.
- `snap_allover`, run before layout.
- A second-round wide search. It needs a time budget: ARC-119 took 18 minutes.

## 3. MCP defects found this session

1. **The interference cache can be wrong in both directions.** `fcmcp_common.fingerprint()` hashes only
   volume, area, element counts and the bounding box. Moving a hole (Roll_Hub, Clevis) keeps all of
   those, so a stale BREP is reused. This produced false clashes, and it can equally produce **false
   clears**. Fix: include a geometry hash (for example sorted face centroids and normals, or a hash of the
   BREP text) and add a regression test.
2. **`execute_code` timeouts.** The client reports a timeout while the GUI task keeps running. The result
   is lost and later calls queue silently: one batch waited 35 minutes. Needed: a GUI job API (submit,
   status, log, cancel) and visibility of the queue in `get_rpc_status`.
3. **`execute_code_async` can wedge FreeCAD.** Running TechDraw document work from the async thread hung
   FreeCAD and needed a restart. Needed: a guard, such as refusing TechDraw or document mutation outside
   `commit()`, or at least a loud warning.
4. **No parallel TechDraw.** One GUI thread does about one sheet per 30–90 s. Needed: a multi-instance
   batch runner (N FreeCAD GUI processes, each running a sheet slice and exiting).
5. **Version drift between sessions.** `techdraw_lint` exists on the branch but was not loaded in this
   session's server. Needed: a server version and capability check, and a documented restart step.
6. **`execute_code_headless` timeouts kill background `interference_check` jobs** (the job vanished
   with "unknown job").

## 4. Workflow lessons

- The independent subagent review was the most effective check. It found what lint, datum and layout
  checks could not: wrong FAR SIDE, wrong hole counts, impossible processes. The reviewers' STEP probe
  scripts (`scratchpad/review3`, `review4`) are reusable and could become a `techdraw_verify` tool that
  cross-checks callouts against the model.
- Regressions came from editing the generator without fixture tests. Feature recognition is pure Part,
  so it can be unit-tested headless on fixture solids: through hole, blind hole, counterbore on the near
  and far side, countersink, D-bore, holes from both faces, side holes.
- Project specifics (the materials/process table, the hex notes, name-based heuristics such as
  `Standoff`/`Spacer`) belong in a project config passed to the MCP tool, not in the tool itself.

## 5. Proposed expansion (freecad-mcp)

1. Fix the fingerprint (3.1) with a test. Clear caches on upgrade.
2. `fcmcp_features.py` (headless, pure Part): everything in 2.1, plus fixture tests.
3. Bring `techdraw_lib` in line with 2.2, 2.3 and 2.4. Fix `mm()`. Make process profiles and extra notes a
   JSON/py config argument of `techdraw_part_drawing`.
4. `techdraw_batch`: a parallel multi-instance runner with job status, a per-sheet time budget and an
   input fingerprint for skipping unchanged sheets.
5. `techdraw_verify`: model-vs-callout cross-check, covering depth vs. thickness, near/far side, counts,
   countersink angle, thread vs. clearance, and datums defined.
6. A GUI job API for long `execute_code` work, queue visibility, and a guard on async TechDraw use.
7. Update the skill: the workflow ends with an independent review step.

After this, the arm repo keeps only a thin project config, `projected_heights`, procurement and the TDP
build, and calls the MCP for drawings, checks and FEA.
