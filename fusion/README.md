# Fusion as the design master: snapshots and checks (pilot)

The team designs in Autodesk Fusion. This folder keeps the design observable as code: each revision's Fusion state
is exported as **diffable text**, and checks run on that snapshot instead of on the FreeCAD builders.

## Take a snapshot

Run `snapshot_export.py` in Fusion. A teammate runs it as a Fusion script; an agent loads it by path from a Fusion MCP script (`importlib`, see its docstring), never by pasting the text, so the scripts find the repo from their own location.
It **only reads**: it changes no design and saves nothing.

It makes one cloud open of the top assembly. Every part comes in through the assembly's references, so masses,
materials, placements and joints are read locally. One more open reads the parameter master. Rev B takes about 50 s.

| File in `snapshot/<rev>/` | What it holds | In git |
|---|---|---|
| `snapshot.json` | every occurrence: path, part, source document and version, world transform, bounding box, mass, centre of mass, volume, bodies and materials; every joint with its value and limits | yes |
| `params.toml` | the revision's master user parameters: value, unit, expression, comment | yes |
| `bom.csv` | unique parts: quantity, material, mass, source document and version | yes |
| `summary.json` | document version, counts, total mass, time | yes |
| `view_iso.png` | the assembly at STOW, isometric, Z up (taken with the snapshot) | yes |
| `assembly.step` | the assembly at its saved pose, read by the checks | no (35 MB; regenerated) |

A commit of a new snapshot is the design diff: parameters, masses, versions and joint limits as text.

## Checks on a snapshot

| Check | Command | What it does |
|---|---|---|
| Mass and torque | `python -I cad/tools/run.py fusion/checks/mass_torque.py` | mass and COM per moving body vs the code-CAD; static J1-J3 torque at all 14 task poses by virtual work |
| Interference | `python -I cad/tools/run.py --timeout 1800 fusion/checks/interference.py` | every pair of solids in `assembly.step` at STOW, on the full Fusion geometry; volumes above 0.5 mm³ |

Results go to `checks/out/<rev>_*.json`. Set `SNAP_REV=rev_a` to check the other revision.

## Fixes applied (2026-11-21, after the pilot)

| Finding | Fix in Fusion | Code-CAD |
|---|---|---|
| Purchased masses wrong | `fix_purchased_mass.py`: each 90 Purchased document gets a copy of its material whose density gives the catalogue mass (19 fixed, e.g. STS3215 153.7 to 60 g, DM-J4340 918.6 to 330 g, 6804ZZ 6 to 19 g). Fasteners and parts without a catalogue mass keep their solid-model mass | none |
| Duplicate horn | the five `HORN-25T (placeholder)` occurrences are deleted (Rev B, Rev A, shared gripper): the STS3215 vendor model has its horn | none |
| STS3215 vs palm | `Gripper_Palm` gets `servo_seat_z` (19.0) and `palm_y_out` (76.5): the floor sits under the real case (32.9 below the horn seat), and the pocket is sized from the vendor case with a 2.7 mm end wall. The jaw servo moves 0.55 mm down, so its 4.53 mm horn sits under the drive link | `gripper_fourbar.toml` `SEAT_Z`, `Y_OUT`; the gripper uses `hardware.sts3215` and the real horn; fingerprints re-recorded (palm, jaw servo, horn) |
| J2 gear mesh | `Pinion_m2_18T_J2` gets `mesh_phase` (half a tooth, 10°); the horn screw holes keep their angle | the code-CAD gears are check shapes, no teeth |
| Spring vs palm | 9271K56 placed natively in HEAD, turned 200° about its coil and raised 0.2 mm (best of 65 placements, checked at jaw 13.8, 30 and 112; Codex, gripper v3). Its legs point away from the mount plate and web. Residual: 0.6 mm³ against the palm and 0.54 mm³ against `Link_RI_lo` at full open. The rigid vendor legs are bent and cut at assembly | legs are not modelled |
| Base shrink (code-CAD 06cb9a0) | `Base_Plate_AL5` (shared): named parameters for the 150 x 160 outline, 4x M4 chassis holes at SX -/+68, +/-70 and the 70 x 56 R8 harness window (volume equals the code-CAD to 0.1 mm³). C610 removed. M4 chassis screws and two cable clips moved (Codex, rev B and rev A v21) | none |
| Rev A motor masses | the DM-J4340-2EC configured design (Stator and Rotor configurations, used by rev A) gets effective densities: stator 231 g, rotor 99 g, full motor 330 g (Codex, rev A v22) | `actuators.toml` `rotor_share` 0.30 |
| Leftover joints | `fusion/cleanup_joints.py` deletes the nine as-built joints the top assemblies kept from before the gripper became a shared document: the old "J4 roll" and the eight four-bar joints (Ground/Coupler LD, LI, RD, RI), whose live copies sit in the gripper. No occurrence moved, masses and torques unchanged (rev B v23, rev A v24) | none |
| Drive frames not printable flat (2026-11-26) | `fusion/drive_frame_spacers.py`: Drive_Frame_L/R v3 lose the three "Tower leg" features; "Insert bore" becomes "Spacer bolt hole" (D3.3 through the 7 mm wall), so the inboard face is flat and the frame prints face down without supports (78.8 g each, 105.1 cm³ = code-CAD). Codex, rev B v25: new Spacer_DF (D10 / 3.3 x 12, 30 Rev B) and BHCS_M3x30 (90 Purchased); 6 spacers, 6 M3x30 and 6 Nyloc_M3 placed in GROUND, the 6 frame inserts and M3x6 removed. Snapshot: 18 added, 12 removed, nothing moved, joints unchanged, GROUND +4.6 g | `drive_frame__tower.toml` spacer + M3x30/nyloc; `base.py drive_frame`; fingerprint re-recorded |
| Level hubs in two bodies (2026-11-27) | `fusion/level_hub_shoulder.py`: in Level_Hub_Elbow and Level_Hub_Wrist (v3) the D15 6700 seat ran up to y -35, where the D14 "Relieved sleeve" started, so each hub was two bodies with no material between them (the printed necks strung in mid-air). New "Neck shoulder" (D15.2 / D10.6 x 0.6 from the -35 datum, toward the neck), "Join neck to seat" (one body) and "Inner race relief" (D12.6 x 0.3). 1.1442 cm³ each, equal to the code-CAD; 2.4 mm clear of rod 2 at every task pose. References updated in rev B v26 and rev A v27: nothing moved, joints unchanged, +0.015 g per hub | `forearm.py level_hub`; fingerprints re-recorded; `export_print.py` now fails a piece with more than one shell |
| Pads rigid under rubber (2026-11-27) | The lab does not print TPU. Codex (brief 13): Pad_L_TPU / Pad_R_TPU renamed Pad_L / Pad_R (v3, same cloud IDs), user parameter RUBBER_T 1.6 mm drives the R50 arc to R51.6 and moves the V 1.6 x sqrt2 along its bisector; material PETG-CF print like the jaw blocks. New Grip_Rubber_L/R (v1, 30 Rev B: old pad minus new pad, rubber copy at 1.30 g/cm³) placed in JAW_L/JAW_R at the pad transform. 18079.1 + 3721.0 mm³ per jaw = old pad, equal to the code-CAD. Gripper v4, rev B v27, rev A v28: nothing moved, joints unchanged, -2.4 g per arm. The skins are solids, not driven by RUBBER_T: regenerate them if the thickness changes | `pads.toml RUBBER_T`, `fourbar.py _pad_shape(t)`; fingerprints re-recorded |
| Six stale references (2026-11-22) | Rev A and rev B each kept 21 Component Insert steps from their old local gripper groups, from before the shared gripper replaced them. Those steps held Gripper_Palm, the D4 pins and WASHER-D4 at version 2, so Get Latest couldn't clear them. Codex rolled each timeline back to before RemoveInstance-HEAD:1, ran getLatestVersion() on the six references, then returned the timeline to the end. No occurrence moved, joints unchanged, mass unchanged: the live parts already came through the gripper at version 3 (rev A v26, rev B v24; gripper not saved) | none |

Re-check (rev B v19): 577 solids, 142 overlaps above 0.5 mm³, 15 min. None of the five findings remain. What is left is intended contacts (fasteners, pins, inserts), overlaps inside the STS3215 vendor model (motor, output gear and case screws against its own case) and the servos' bottom caps touching the cradle floors (1.7 mm³ each).

Afterwards the moving bodies match the code-CAD within a few percent. The static torques agree within 5 % at all 14 poses (rev B and rev A). Totals: rev B 2,024 g (code-CAD 2,049 g), rev A 2,169 g (2,215 g); GROUND within 1 %. Still open: the jaw servo's spline touches the D4x20 drive-link pin (2.1 mm³).

**Fusion API notes, learned the hard way:**
- `Document.updateAllReferences()` crashes Fusion when the document was opened invisibly. Open it visibly (`documents.open(f, True)`).
- Out-of-date references nested inside a shared sub-assembly (the gripper's palm and pins seen from rev A or B) can't be updated through the API: `updateAllReferences()` leaves them, and `getLatestVersion()` or setting `version` raises InternalValidationError. `update_references.py` handles direct references and saves only what it updated. When even Get Latest in the UI leaves a reference stale, look for old Component Insert steps earlier in the timeline. Roll the timeline back to before them, call `getLatestVersion()`, then roll it forward to the end and save (see "Six stale references" above).
- Several saves in a row can leave Fusion busy for more than 20 minutes on the next cloud-data call (`findFileById`, `dataFiles`).
- Positions of occurrences inside sub-components are root-level overrides. Set `transform2` on the root proxy (built with `setWithCoordinateSystem`), then `snapshots.add()`. `MoveFeature` doesn't accept occurrences. In an assembly with joints (rev B), those overrides on GROUND's children revert on `computeAll()`. `addExistingComponent` adds its matrix on top of the component's first occurrence, and deleting a referenced component's last occurrence removes the component from the design. Codex placed the base parts with its own tooling (tools/_agent/codex-fusion).

## Pilot findings (rev B, 2026-11-21)

- The custom parts' masses match the code-CAD within a few percent (forearm, upper arm, rods, links, jaws).
- The **purchased parts are wrong in Fusion.** The STS3215 vendor model's internal bodies (motor, case halves) were
  given *Steel*, so each servo weighs about 150 g instead of about 60 g. There is one each on the wrist (LEVEL),
  the gripper head and the base. That makes the J1/J2 static torques about 20-25 % higher than reality, and the
  bearings carry *Aluminum 6061*. Fix: set each purchased part's mass to its catalogue mass in Fusion, using a
  per-part material density.
- **Interference** (`checks/out/rev_b_interference.json`): 582 solids, 1,902 pairs; the run took **24 min**, which
  is the baseline for the faster checks. 151 overlaps above 0.5 mm³:
  - **85 are intended contacts:** 61 fasteners and pins in their holes, 24 heat-set inserts. These belong in an
    intended-contacts list.
  - **4 are real findings** that the code-CAD's simplified check shapes don't show:
    - **J2 gear mesh, 165 mm³:** `Drive_Gear_m2_54T_J2` vs `Pinion_m2_18T_J2`. The teeth are clocked into each
      other.
    - **The STS3215 vendor model overlaps the gripper palm,** up to 162 mm³, across 60 pairs. The real servo
      case is bigger than the pocket that was designed around the simplified servo.
    - **Duplicate horn, 554 mm³:** the `HORN-25T (placeholder)` sits inside the horn that the STS3215 vendor model
      already includes. Drop the placeholder.
    - **Opening spring 9271K56 vs `Gripper_Palm`, 32 mm³.**
