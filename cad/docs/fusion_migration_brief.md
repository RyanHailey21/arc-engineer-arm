# Brief: ARC S2 Engineer arm as a parametric Autodesk Fusion project (rev A and rev B)

Given to Codex (gpt-6.2-astra) on 2026-11-20. It works through the Autodesk Fusion MCP server (`autodesk-fusion`, `http://127.0.0.1:27183/mcp`)
in the Fusion session that is open on this machine.

## Goal
The team works in Autodesk Fusion. Put the arm into the team's Fusion project, in the folder the user has open in
Fusion (expected project: **UTA Robomasters**), so that teammates can see it and edit it. Both revisions are needed:

| Revision | Source of truth (FreeCAD code-CAD, read-only) | What differs |
|---|---|---|
| **Rev A, direct drive** (no gears) | `C:\Users\ryanh\tools\_agent\codex-fusion\arm-revA` (commit `46a7227`) | J1/J2 Damiao DM-J4340-2EC direct drive on the output hubs; J3/J4 DS3225MG servos; screw gripper (DJI M2006 drive) |
| **Rev B, geared drive** | `C:\Users\ryanh\tools\_agent\codex-fusion\arm-revB` (current `main`) | Feetech STS3215 on every joint. J1/J2 through a printed m2 18T/54T spur stage (3:1) on a drive frame per tower, with a 6804 bearing and a hex hub stub. J3/J4 in printed cradles. Four-bar gripper |

The files must be **parametric and organised properly**: a teammate must be able to change a key dimension in
Fusion and have the part, and its mates, follow.

## Hard rules
1. **Never modify, move, rename, overwrite or delete anything that already exists in Fusion.** This covers other
   projects, folders, documents and versions. Create only new folders and new documents. Never save over an
   existing file, and never "Save As" onto an existing name.
2. Before creating anything, determine the folder the user has open (`app.data.activeProject` /
   `app.data.activeFolder` via a read-only script), and record it in PROGRESS.md.
   - If that is not readable, use the root folder of project "UTA Robomasters".
   - Create one new folder there, `ARC S2 Engineer Arm`, and put everything inside it.
   - If a folder of that name already exists, do not touch it: use `ARC S2 Engineer Arm (Codex)`.
3. Only save the new documents you created.
4. The FreeCAD repos are references.
   - Do not edit them and do not commit or push anything from them.
   - Scratch work goes in `C:\Users\ryanh\tools\_agent\codex-fusion\work\`.
5. Keep `C:\Users\ryanh\tools\_agent\codex-fusion\PROGRESS.md` as a **short ledger**. A later session resumes
   from it. It holds:
   - the folder path, the folder ids and the parameter method, once;
   - a table with one row per document: folder, name, cloud id, version, `verified` / `WIP` / `failed`, and a few
     words if something is odd;
   - a `Next:` line and an `Open issues` list.

   Update a part's row when its state changes.
   - Do not paste raw verification output, measurements or script dumps into the ledger. Verification scripts
     write their own numbers to `work/verify/<part>.json`.
   - A row points to that file only when a check failed.
   - Keep the file under about 150 lines.

   The full history up to 2026-11-20 is in `work/PROGRESS_full_2026-11-20.md`. Read it only to settle a specific
   question.
6. **Never launch, restart or kill Fusion yourself.** Fusion supports only one running instance. On 2026-11-20 a
   second launch from the Codex sandbox account left a stray process that blocked the user's Fusion.
   - Recovery belongs to `fusion_watchdog.ps1`, which runs as the desktop user. It relaunches Fusion after a
     crash and writes `UP`, `RECOVERING` or `DOWN` to `work/fusion_state.txt`.
   - If a Fusion MCP call fails at the transport level, follow **Crash recovery** below. Do not end the run.

## Crash recovery
Fusion crashed three times on 2026-11-20. Each time it was a native exception inside an MCP-executed Python
script (`Ns::MCP::executeScript` → `PyEval` → `_core registerTypeInfo`), in a call that did several things at
once: build, import STEP, `saveAs`, an `adsk.doEvents()`/`time.sleep` polling loop, and `close`.

To avoid it, follow these **script rules**:
- **One Fusion operation per MCP call:** build and measure; import a reference STEP and close it; `saveAs`;
  check the cloud; close the document. Each is its own call.
- **No waiting inside Fusion.** Never call `adsk.doEvents()`, `time.sleep()` or a polling loop inside a Fusion
  script. To wait for a save, make short read-only calls from outside, a few seconds apart.
- **Hold nothing across calls.** Re-fetch documents, folders and data files by id at the start of every call.
  Never reuse an object from a document that was closed.
- **Keep at most two designs open:** the part, plus its parameter master if needed.

**The cloud data API is the main crash trigger.** On 2026-11-20 there were 709 Fusion calls:
- 398 touched `dataFiles`, `dataFolders`, `findFolderById`, `isComplete`, `documents.open` or `saveAs`, and
  18 of them crashed Fusion (4.5 %);
- 311 did only modelling, measuring or closing, and 2 of them crashed (0.6 %).

Several crashes came seconds after a save, while Fusion was still handling cloud push notifications. So:
- **Gate every data-API touch through `work/fusion_guard.py`.**
  - Call `G.data_api(label)` first in every helper that lists folders, reads data files, opens a cloud document
    or saves. Pass `heavy=True` for `saveAs` and `documents.open`.
  - After a confirmed save, call `G.saved(name, id, version)`.
  - The guard allows one data-API call per 20 s and none for 45 s after a save or open. A call that comes too
    soon raises `RetryLater` at once. Wait outside Fusion for the seconds it gives, then send the call again.
- **Do not list folders to check something you already know.**
  - Confirm a save from the document's own `doc.dataFile`, not by listing its folder.
  - Use `G.cached(name)` and the ledger for existence checks.
  - List a folder only once per part, just before its `saveAs`, and when reconciling after a crash.
- **Never run two Fusion calls at once.** Never call the data API from a modelling step.

To recover after a crash:
1. Wait for `work/fusion_state.txt` to read `UP`: check every 30 s.
   - `DOWN` means the watchdog has paused after 10 relaunches in an hour. It is not final: it goes back to `UP`
     once Fusion runs again.
   - Keep waiting for up to 30 min in total. Only then update the ledger and end the run with a note that the
     user must restart Fusion.
2. Reconcile before doing anything else. Read the target folder read-only.
   - If the part you were working on now exists in the cloud, open it, verify it, record it, and do not build it
     again.
   - If it does not exist, rebuild it from scratch. Its earlier in-memory state is gone.
3. Mark the crash in the ledger's `Open issues` with one line: time, part and step. Then continue the work.

## Organisation (target)
```
ARC S2 Engineer Arm/
  00 Parameters/        ARC_Params_RevA, ARC_Params_RevB: user parameters only (see below)
  10 Common/            parts identical in both revisions (check against both STEP sets before sharing)
  20 Rev A/             Rev A-only parts + "ARC Arm Rev A" top assembly
  30 Rev B/             Rev B-only parts + "ARC Arm Rev B" top assembly
  90 Purchased/         vendor and catalogue parts (STEP imports are fine here: motors, servos, bearings, fasteners)
  README                (a Fusion-readable note or the folder description: what is where, how to change a parameter)
```
- **Assemblies.** Each top assembly holds one external component per part (distributed design), arranged in
  sub-assemblies per moving body: base/ground, upper arm, crank, forearm, level member, wrist, gripper. Use
  **joints** between bodies, with the joint limits from the params, so the arm can be posed. Default pose is
  **STOW**.
- **Naming.** Component and document names follow the FreeCAD part names (e.g. `Drive_Frame_L`,
  `J1_Output_Hub`). Look them up in `cad/MAP.md` of the matching revision.
- **Units.** Millimetres. The world frame is the robot frame: x forward from the bumper, y left, z up from the
  floor (see `CLAUDE.md`).

## Parametric rules
- **Built, not imported.** Every custom part (plates, hubs, frames, cradles, gears, brackets, gripper parts) is
  built from sketches and features in Fusion. It is not an imported STEP body. Imported STEP is allowed only for
  purchased parts.

## Purchased parts: found and imported, never built
Purchased and vendor parts include motors, servos, ESCs, bearings, screws, nuts, washers, dowels, inserts,
standoffs, collars, clips, rails, carriages, lead screws, springs and catalogue gears. These parts are **never
built** in Fusion. They are also **never exported from the FreeCAD model**: the FreeCAD repo models most of them
itself, as approximations. For each one:

1. **One document per part number.** Use the part numbers in `cad/data/catalogue.toml` and `cad/fab/BOM.csv`,
   e.g. one `BHCS M3x6` document. Do not make one per instance. The assemblies insert that one document as many
   times as needed.
2. **Find the manufacturer's or distributor's CAD, and import it.** Look in this order:
   - the repo's `cad/vendor/`, which already has the DJI M2006 and C610 and the Feetech STS3215;
   - McMaster-Carr through the `mcmaster-carr` MCP server: `mcmaster_search`, then `mcmaster_download_cad`;
   - the manufacturer's own site, for example Damiao, Hiwin, NSK or SKF.
3. **Check that the CAD fits the design.** Its key dimensions must match what the arm was designed around:
   bore, OD and width for bearings; thread, length and head for screws; the mounting pattern for motors and
   servos. A mismatch is an open issue, not something to adjust.
4. **Record the source** in the ledger row: the vendor and part number, or the URL.
5. **No vendor CAD found?** Only then import the FreeCAD-exported shape, name it `<part> (placeholder)`, and list
   it in the ledger's `Open issues` and in the README. Never build one with sketches.

The per-instance STEP files in `work/assembly_inputs_rev*/purchased/` were exported from the FreeCAD model.
Use them only for STOW positions, or as a last-resort placeholder.
- **Key dimensions are user parameters.** Name them after the TOML keys in that revision's `cad/params/*.toml`
  and `cad/interfaces/*.toml`, e.g. `GEAR_module`, `stub_hex_af`, `pocket_clearance`. Give each its unit and the
  TOML comment as its Fusion comment. Sketch dimensions and feature inputs reference these parameters, not
  literals.
- **One parameter set per revision.** Fusion parameters are per document. Put the authoritative set in
  `ARC_Params_RevA` / `ARC_Params_RevB`. Then, in order of preference:
  - drive each part from them (derived parameters, or an add-in/script that pushes values into the part
    documents);
  - or, if neither is reliable through the API, put the same named parameters in each part document. In that
    case add a script (saved in the work folder and described in the README) that syncs them from the
    revision's TOML files.
  Record the method you chose and why.
- **Mates follow the interfaces.** Both mating parts take their hole patterns, pocket sizes and so on from the
  same parameters (the repo's `cad/interfaces/*.toml` exists for exactly this). Moving a part must not leave its
  mate's holes behind.
- **Model tree.** Keep it readable: named sketches and features, no stray construction bodies, and fillets as
  in the source.

## Verification (per part, before moving on)
- Compare each Fusion part with the revision's exported STEP in `cad/fab/step/<part>.step`:
  - volume within 0.5 %;
  - bounding box within 0.1 mm;
  - the same hole count and diameters.
  Use a read-only Fusion script, or import the STEP into a scratch document that you then close without saving.
- Record the result as the part's ledger status in PROGRESS.md; the numbers go in `work/verify/<part>.json`. A
  part that does not match is not done.
- Parametric check: change one key parameter (e.g. a hole PCD or a plate thickness), confirm the part updates
  and its mate follows, then restore the value. Log it.
- At assembly level: screenshot each top assembly at STOW (front and iso) into the work folder, and check that
  no two bodies overlap at STOW (Fusion interference analysis).

## Order of work
1. Read the reference material:
   - `CLAUDE.md` and `cad/MAP.md` in both repos;
   - the params, interfaces and envelopes;
   - the part list and BOM, in `cad/fab/BOM.csv` of each revision.
2. Create the folder structure and the two parameter documents.
3. Build the parts that differ least first, to settle the method (e.g. a carbon plate such as `Upper_Arm_L_CF3`).
   Verify it and record the method in PROGRESS.md.
4. Build the Common parts.
5. Build the Rev B-specific parts: drive frame, 54T gear, 18T pinion, hub stub, cradles, four-bar gripper.
6. Build the Rev A-specific parts: DM-J4340 hub/tower interfaces, DS3225 mounts, screw gripper.
7. Import the purchased parts.
8. Build both assemblies with joints.
9. Verify the assemblies.
10. Write the README.

If the work cannot finish in one session, stop at a clean point (every saved document verified or marked WIP in
PROGRESS.md) and summarise what is left.

## Report at the end
- The Fusion folder path, and the documents created (name and id).
- Per part: verification results.
- The parameter method chosen.
- Anything you could not make parametric, and why.
- Open issues for the team.
