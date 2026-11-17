# Four-bar gripper: design status (2026-11-17)

The arm's gripper is now the **gear-synchronised parallel four-bar** (`GRIP=FOURBAR`, the default in `params/variant.toml`). It replaces the rev A lead-screw gripper (`GRIP=SCREW`), which remains the released rev A package.

Evidence for every claim below is in `cad/out/fourbar/`. Each `*.evidence.json` is a `cad-evidence/1` report. `manifest.json` records whether each check is FRESH or STALE against the current design inputs; `cad/tools/quick_check.py` prints that table.

## Design

- **Linkage:** each jaw rides a 47 mm drive link and an idler link, each made of two 3 mm CF layers on D4 dowel pins (McMaster 91595A158/167/179).
- **Synchronisation:** m1 77-tooth acetal sector gears on the two drive links mesh on the centreline, so the jaws centre.
- **Drive:** a Feetech STS3215 12 V servo turns the left drive link directly.
- **Release:** a torsion spring (McMaster 9271K56, right-hand, 22° preload) on the right drive pivot biases the jaws open, so they release when power is lost.
- **Pads:** unchanged from rev A (R50 donut arc + 90° pipe V-notch).
- **Grip symmetry:** the pipe grip (13.8 mm pad gap) and donut grip (100 mm) sit symmetrically about mid-stroke, so both share the same TCP. Full open is 112 mm.
- **Pole clearance:** everything above the pads stays behind x = 135.5. That's the pole keep-out from `envelopes/field.toml`, with 3.5 mm margin.
- **Mass:**

| | Rev A | Four-bar |
|---|---|---|
| Past the wrist | 1,040 g | 485 g |
| Jaw head | 836 g | 280 g |
| Arm total | 3.42 kg | 2.87 kg |

- **Peak static joint torque:**

| Joint | Rev A (N·m) | Four-bar (N·m) |
|---|---|---|
| J1 | 4.63 | 3.07 |
| J2 | 4.36 | 2.54 |
| J3 | 1.24 | 0.78 |

## Verification

| Check | Result |
|---|---|
| Full interference (`check_interference.py`) | 0 overlaps at STOW and across 14 task poses; field clearance clear; donut lift up the pole clear |
| Quick check | envelopes, interfaces, self-interference over the jaw stroke at roll 0/90°, mass/torque, fingerprint: PASS |
| Hole edge distance | 0 broken out, 0 fail; no warnings on any four-bar part |
| Thread engagement | 0 FAIL; the only WARNs are the three known J1 hub screws from rev A |
| FEA (`fea/run_fea_fourbar.py`) | drive link SF 1.8; jaw block 4.1; palm 2.0 (after adding the central web; it was 1.3 before) |
| Hand checks (in the same report) | sector tooth (Lewis) 2.7; pivot pins 161; link bore bearing 31 |
| Grip budget (`tools/grip_budget.py`) | WARN: see below |
| BOM (`tools/bom.py`) | 28 purchased line items, all with a source; 66 custom parts |
| Simulation export | MuJoCo + Gazebo models in `sim/arc_arm_fourbar/`; forward kinematics within 0.0004 mm of CAD |
| Gazebo run test (`cad/sim/gz_check.py`) | gz-sim 8.10: all 7 task poses commanded and reached; joints within 0.005°, mimic followers within 0.41°, TCP within 2.4 mm |

## Open items (in priority order)

1. **Servo back-drive bench test.**
   - The spring gives 0.124 N·m to open the jaws at full open.
   - The STS3215's unpowered back-drive torque is unknown; the estimate is 0.1–0.5 N·m.
   - Measure it, then keep 9271K56 or change spring: the weaker 9271K52, or a stronger one on the same arbor.
   - The 1 s power-off release depends on this. The MuJoCo release test (0.04 s to open 10 mm) uses an assumed 0.05 N·m.
2. **Pipe holding torque.**
   - Holding the pipe with the wrist rolled 90° (11 N per jaw) needs 1.40 N·m. That's 143% of the servo's rated 0.98 N·m, but only 48% of its 2.94 N·m stall.
   - It is acceptable for the short pipe transit. Check servo temperature and overload cut-out on the bench.
   - Holding by friction alone (wrist not rolled) needs 87% of stall. Don't do it.
3. **Drawings and renders.** The four-bar parts have no drawings or renders yet; these were dropped during the redesign.
   - The rev A drawing package covers the SCREW variant only.
   - Run the release generators once the four-bar is promoted: set `release = "FOURBAR"` in `params/variant.toml`.
4. **Unchanged from rev A:**
   - drawing sign-off (Checked/Approved PENDING);
   - the J1 hub thread-engagement decision.
