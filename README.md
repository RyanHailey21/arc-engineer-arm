# ARC S2 Engineer Arm: donut + pipe tasks

Adapted from Wang et al., *Lightweight Robotic Arm Based on a Load-Adaptive Hoisting Mechanism*, Actuators 2025, 14, 71.
Task requirements come from the ARC Championship Events Manual S2 v1.0, §3.2.4 (Objectives B and C) and §3.2.4.5 (Controlling Objectives).

The whole arm is code-CAD (FreeCAD 1.1 Python). **Start with [`cad/MAP.md`](cad/MAP.md)** (generated: every module, parameter, interface, envelope and part, with the line that builds it) and [`CLAUDE.md`](CLAUDE.md) (working conventions, frames, check workflow, guard rails).

## Current state

- **Design (rev B, released 2026-11-19, `GRIP=FOURBAR`).** Gear-synchronised parallel four-bar gripper on a palletizer arm with parallelogram level keeping, Feetech STS3215 servos on every joint (J1/J2 through a printed 3:1 spur stage). Head 352 g, past the wrist 564 g; worst static torque J1 3.39, J2 2.90, J3 0.88 N·m.
  - **Product summary and requirements verification:** [cad/docs/ARC_S2_Engineer_Arm.pdf](cad/docs/ARC_S2_Engineer_Arm.pdf), rebuilt from the check results by `cad/docs/paper/make_paper.py`.
- **Base-drive variant (`BASE_DRIVE=DIRECT`).** Damiao DM-J4340-2EC direct drive on J1/J2 (the Fusion "Rev A"), kept to compare base motors. Outputs in `cad/out/fourbar_direct/`; its STEP set and BOM for the Fusion migration come from `cad/tools/export_variant.py` → `cad/out/fourbar_direct/fab/`.
- **Released package.** `cad/fab/` (STEP, DXF, BOM, procurement), `cad/fea/out` and the renders in `cad/render/out` are rev B. There are no drawings: they are not a project requirement.
- **Simulation.** A MuJoCo model of the four-bar arm, generated from the CAD and validated against it, that runs both tasks end to end; video at the real servo speed: [sim/README.md](sim/README.md).

## What the arm does

| Task | Requirement (manual) | How the arm does it |
|---|---|---|
| **Donut** (Obj C) | Ø100/Ø50×25 ring around the base of a 456 mm zig-zag pole on the 210 mm lower tier; score it lying flat on the 300×300×50 Scoring Area. | Jaws close on the 100 mm OD, fingers forward. Lift it up the pole following the zig-zag (arm Z, wrist roll, chassis strafe for Y) until it clears the top at 666 mm, then place it flat. |
| **Pipe** (Obj B) | 500 mm × Ø26.7 PVC pipe in a Ø200×250 bucket; turn it in through a Ø52.5 chute 600 mm up. | Grip the nearest pipe by its top end in the pad V-notches, lift it clear of the rim (TCP at 740), pitch the wrist 90° so it points forward; the chassis drives it ~300 mm into the chute. |
| **Fail-safe** (§3.2.4.5) | Within 1 s of being defeated, stop controlling objectives; the claw must release unpowered. | A torsion spring on the right drive pivot biases the jaws open and back-drives the unpowered gripper servo. **Bench-test the back-drive torque and the release time** (open item 1). |

## Layout

| Path | What it holds |
|---|---|
| `cad/arm/` | The model, one module per subassembly; `cad/arm_model.py` re-exports it (`import arm_model as M`). |
| `cad/params/`, `cad/interfaces/`, `cad/envelopes/`, `cad/data/catalogue.toml` | Design inputs, mating interfaces, field keep-out boxes, purchased parts. Edit these, not literals in code. |
| `cad/hardware.py`, `cad/vendor/` | Purchased-part geometry: vendor STEP (STS3215, DM-J4340, C610 ESC), ISO/DIN hardware, catalogue-modelled parts. |
| `cad/field.py` | ARC Battlefield items (tier, placeholder pole, bucket, pipes, scoring area, chute). |
| `cad/tools/`, `cad/check_interference.py`, `cad/tests/` | Checks (quick check, interfaces, seating, engagement, holes, level keeping, grip hold, fingerprint, bloat report) and their tests. |
| `cad/out/<variant>/` | Check results, `manifest.json` (status + inputs hash: FRESH/STALE), the maintained FreeCAD working document. |
| `cad/sim/`, `sim/` | MuJoCo model generators, the generated model, task runs and the task video. |
| `cad/fab/`, `cad/fea/` | Release fabrication export and FEA. |
| `cad/docs/` | The product summary PDF and its generator (`paper/`). |
| `cad/render/` | Blender renders (release generator). |

## Checks

| When | Run | Covers |
|---|---|---|
| After every edit (~30 s + build) | `python -I cad/tools/run.py cad/tools/quick_check.py` | envelopes, interfaces, gripper self-interference over the jaw stroke, mass/torque, catalogue masses, level keeping, fastener seating, bloat, fingerprint; prints FRESH/STALE evidence |
| Refactors | `cad/tools/fingerprint.py` with `FP_MODE=check` | MATCH for `GRIP=FOURBAR` and `BASE_DRIVE=DIRECT` (`fourbar_direct`) |
| Milestones (~4 min, cached) | `python -I cad/tools/run.py --timeout 900 cad/check_interference.py` | every part pair at STOW, the 14 task poses (`FULL=1`: interpolated sweep), field clearance, donut lift along the pole, static torques |
| Milestones | `tools/check_holes.py`, `tools/check_engagement.py`, `tools/check_level_keeping.py`, `tools/grip_hold.py`, `tools/bom.py` | hole edge distance, thread engagement, parallelogram closure and dead points, grip margins from the sim loads, BOM |

`cad/tools/run.py` launches freecadcmd so the output, traceback and exit code are never lost. Interference results are cached in `cad/.cache/` (`NOCACHE=1` forces a full recompute).

## Open items / risks (in priority order)

1. **Servo back-drive bench test.** The opening spring gives 0.124 N·m at full open; the STS3215's unpowered back-drive torque is unknown (0.1–0.5 N·m estimated). The 1 s power-off release depends on it.
2. **Pipe holding torque.** Held within the servo's continuous rating with margin 1.13 (target 1.5; 5.6 at stall). Pick the spring after the back-drive test; log servo temperature on a 30 s horizontal pipe hold.
3. **Zig-zag pole geometry is TBA in the manual.** The pole is a placeholder (Ø24, analytic ±50 mm S-curve); the donut-lift path is generated from it, so re-run `check_interference.py` when the official drawing lands.
4. **Robot Building Specifications not reviewed.** No size or weight limits applied yet; the stowed arm top is about 420 mm (central limbo bar 420, side bar 300).
5. **STS3215 bottom-cap screws.** The cradles hold each servo by its four bottom-cap screws (12 mm). Check on a real servo that they take the length and the floor bosses meet the case.
6. **The arm falls when the robot is defeated** (allowed by the rules): add a soft landing stop or gas spring.
7. **The chassis isn't designed.** Assumptions: deck at 120 mm, shoulder 160 mm behind the bumper.
