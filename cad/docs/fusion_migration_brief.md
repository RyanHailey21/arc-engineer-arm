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
5. Keep `C:\Users\ryanh\tools\_agent\codex-fusion\PROGRESS.md` current after every part. Record:
   - what exists in Fusion (folder path, document names and ids);
   - what is verified;
   - what is next.

   A later session resumes from it.
6. **Never launch, restart or kill Fusion.** Fusion supports only one running instance; a second launch (which
   a crash recovery from the Codex sandbox account did on 2026-11-20) leaves a stray process that blocks the
   user's Fusion. If the Fusion MCP server stops answering, stop at once: update PROGRESS.md and end the run
   with a note that Fusion needs restarting by the user.

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
- Log the result in PROGRESS.md. A part that does not match is not done.
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
