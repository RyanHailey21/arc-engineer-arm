# Four-bar gripper: design status (2026-11-18)

The arm's gripper is now the **gear-synchronised parallel four-bar** (`GRIP=FOURBAR`, the default in `params/variant.toml`). It replaces the rev A lead-screw gripper (`GRIP=SCREW`), which remains the released rev A package.

Evidence for every claim below is in `cad/out/fourbar/`. Each `*.evidence.json` is a `cad-evidence/1` report. `manifest.json` records whether each check is FRESH or STALE against the current design inputs; `cad/tools/quick_check.py` prints that table.

## Design

- **Linkage:** each jaw rides a 47 mm drive link and an idler link on D4 dowel pins (McMaster 91595A158/167/179). Each link has three 3 mm CF layers: two above the pad and, since 2026-11-18, one low down behind the pad, so the linkage holds the jaw at its top **and** bottom.
- **Jaws (2026-11-18):** a C-frame. The printed jaw block is one extrusion of the jaw outline (finger plate + rounded pin ears) with the pad's footprint, the link slots and the pole keep-out step cut from it: top finger, a wall behind the pad, and a lower pin plate. The CF bottom finger has the same outline and screws to the wall through three M3 heat-set inserts; the lower coupler pins press into it (double shear). The rear D6 post is gone. Why: with the jaw held only at the top, a grip low on the pad moved the pad bottom 1.35 mm off its top and overstressed the top finger (see `docs/compliance_report.md`).
- **Synchronisation:** m1 77-tooth acetal sector gears on the two drive links mesh on the centreline, so the jaws centre.
- **Drive:** a Feetech STS3215 12 V servo turns the left drive link directly.
- **Release:** a torsion spring (McMaster 9271K56, right-hand, 22° preload) on the right drive pivot biases the jaws open, so they release when power is lost.
- **Pads:** unchanged from rev A (R50 donut arc + 90° pipe V-notch).
- **Grip symmetry:** the pipe grip (13.8 mm pad gap) and donut grip (100 mm) sit symmetrically about mid-stroke, so both share the same TCP. Full open is 112 mm.
- **Pole clearance:** everything above the pads stays behind x = 135.5. That's the pole keep-out from `envelopes/field.toml`, with 3.5 mm margin.
- **Mass:**

| | Rev A | Four-bar |
|---|---|---|
| Past the wrist | 1,040 g | 558 g (484 before the C-frame jaws and bottom links) |
| Jaw head | 836 g | 352 g (279 before) |
| Arm total | 3.42 kg | 2.92 kg (2.87 with the belt) |

- **Peak static joint torque:**

| Joint | Rev A (N·m) | Four-bar (N·m) |
|---|---|---|
| J1 | 4.63 | 3.34 |
| J2 | 4.36 | 2.84 |
| J3 | 1.24 | 0.87 (pipe now at its centre of mass) |

## Level keeping: linkage instead of the belt (2026-11-17)

The forearm's GT2 belt (stage 2 of level keeping, elbow to wrist) is replaced by a **parallelogram linkage**, for stiffness (no belt stretch at the wrist) and reliability (no tension, idler or tooth skip).

- **Parts:**
  - **Rod 2:** 4 × 16 mm CF plate rod, pins 350 mm apart, MR105 in each eye, in the plane the belt used (y −35…−31).
  - **Levers:** 43 mm at 72.7°, on the CF rocker and on the CF level member. Both pins are SB5×8 shoulder screws with a nyloc on the plate's outboard face.
  - **Hubs:** two turned hubs replace the pulleys, with the same axial stack.
  - **Removed:** the belt, both pulleys and the idler.
- **Why one rod, not two:** a double parallelogram would need one rod to pass a pivot axis, but the elbow shaft fills every layer and the J3 servo sits outboard at the wrist.
- **Dead points:** at elbow +72.7° and −107.3°. The task elbow range is −82.6…+48.0°, so the margin is 24.7° or more, and rod force is at most 2.4× its mid-range value.
- **Pose changes this required:**

  | Pose | Was | Now | Elbow angle (was → now) |
  |---|---|---|---|
  | DONUT_PLACE | TCP x 210 | TCP x 300 | −97.3° → −82.6° |
  | PIPE_LIFT | TCP z 790 | TCP z 740 (pipe still 37 mm over the bucket rim) | 55.7° → 48.0° |

  Elbow limits become −86…+51° (was −110…+70°).
- **Lever direction:** up, not down. Down levers put the level member into the scoring platform at DONUT_PLACE.
- **Clearing the gripper at PIPE_CHUTE (wrist pitch 90°):**
  - a 43 mm lever (not 50);
  - a notch in rod 2's top edge near the wrist;
  - two 2 mm-rounded reliefs in the palm mount plate's top. The −y side is a narrow slot, to keep the palm FEA at SF 2.0; a full corner cut dropped it to 1.5.
- **Upper-arm standoffs:** moved from x 113/227 to 85/150 mm, because rod 2 sweeps the old 227 mm station when the arm folds (STOW, DONUT_PICK).
- **Rod 2 strength:** buckling 344 N for the plain rod and **313 N with the notch** (finite-difference column, E 50 GPa, pinned-pinned). Worst load is 134 N (J3 stall 2.4 N·m through a 43 mm lever at 24.7° from the dead point): **SF 2.35**. Shear-out at the eyes is about 2.4 kN.
- **Check:** `tools/check_level_keeping.py` verifies parallelogram closure, the dead-point margins (task poses, lift path, joint limits), an elbow sweep at reachable shoulder angles, and the wrist-pitch range each task pose needs.
- **SCREW (rev A) gripper:** its `Gripper_Bridge_CF3` hits rod 2 at PIPE_CHUTE. Rev A is frozen, so this is left as a known limit of the SCREW variant with the linkage.

## Verification

| Check | Result |
|---|---|
| Full interference (`check_interference.py`) | 0 overlaps at STOW, across the 14 task poses and the moves between them; field clearance clear; donut lift up the pole clear |
| Level keeping (`tools/check_level_keeping.py`) | closure exact; dead-point margin ≥ 24.7° (21.3° at the joint limits); elbow sweep clean; wrist pitch clear to 96° / 95° at PIPE_CHUTE / PIPE_CHUTE_ROLL90 |
| Quick check | envelopes, interfaces, self-interference over the jaw stroke at roll 0/90°, mass/torque, fingerprint: PASS |
| Hole edge distance | 0 broken out, 0 fail; new WARNs (below the 0.5d plate rule): rod-2 eyes (3 mm wall; shear-out about 2.4 kN against 134 N) and the turned level hubs |
| Thread engagement | 0 FAIL; the only WARNs are the three known J1 hub screws from rev A |
| FEA (`fea/run_fea_fourbar.py`) | drive link SF 1.8; jaw block 16 (4.1 before the bottom links); palm 2.1 |
| Jaw stiffness FEA (`fea/run_fea_jaw.py`) | pad bottom 0.0006 mm off its top under 1.25 × stall grip (1.35 mm with the old top-held jaw); tilt 0.001° |
| Grip hold (`tools/grip_hold.py`, sim loads) | donut margin 1.65 at rated / 5.6 at stall; pipe 1.13 / 5.6 (WARN: below the 1.5 target at rated) |
| Hand checks (in the same report) | sector tooth (Lewis) 2.7; pivot pins 161; link bore bearing 31 |
| BOM (`tools/bom.py`) | 26 purchased line items, all with a source; 69 custom parts |
| Simulation export | MuJoCo + Gazebo models in `sim/arc_arm_fourbar/`; forward kinematics within 0.0004 mm of CAD |
| Gazebo run test (`cad/sim/gz_check.py`, informational since 2026-11-18) | gz-sim 8.10: all 7 task poses commanded and reached; joints within 0.005°, mimic followers within 0.41°, TCP within 2.4 mm |

## Open items (in priority order)

1. **Servo back-drive bench test.**
   - The spring gives 0.124 N·m to open the jaws at full open.
   - The STS3215's unpowered back-drive torque is unknown; the estimate is 0.1–0.5 N·m.
   - Measure it, then keep 9271K56 or change spring: the weaker 9271K52, or a stronger one on the same arbor.
   - The 1 s power-off release depends on this. The MuJoCo release test (0.04 s to open 10 mm) uses an assumed 0.05 N·m.
2. **Pipe holding torque.**
   - The sim-based grip check (`tools/grip_hold.py`, which replaced the hand-estimate grip budget and also checks the opening spring) shows the pipe held within the servo's continuous rating, margin 1.13 (5.6 at stall). The opening spring takes 0.48 of the 0.98 N·m at the pipe grip.
   - After the back-drive test, pick a weaker or less-preloaded spring to raise the margin (options in `docs/compliance_report.md` §1.3). Log servo temperature on a 30 s horizontal pipe hold.
3. **Drawings and renders.** The four-bar parts have no drawings or renders yet; these were dropped during the redesign.
   - The rev A drawing package covers the SCREW variant only.
   - Run the release generators once the four-bar is promoted: set `release = "FOURBAR"` in `params/variant.toml`.
4. **Unchanged from rev A:**
   - drawing sign-off (Checked/Approved PENDING);
   - the J1 hub thread-engagement decision.
