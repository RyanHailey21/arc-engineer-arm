# ARC S2 Engineer Arm: donut + pipe tasks

Adapted from Wang et al., *Lightweight Robotic Arm Based on a Load-Adaptive Hoisting Mechanism*, Actuators 2025, 14, 71.
Task requirements come from the ARC Championship Events Manual S2 v1.0, §3.2.4 (Objectives B and C) and §3.2.4.5 (Controlling Objectives).

## Current state (2026-11-18)

- **Gripper.** The design gripper is the lightweight **gear-synchronised parallel four-bar** (`GRIP=FOURBAR`). Head: 352 g (C-frame jaws held by the linkage at top and bottom) vs 836 g for rev A.
  - All checks pass: interference, hole walls, thread engagement, FEA, envelopes, BOM.
  - Open items: the servo back-drive bench test and the pipe-holding servo duty.
  - **Compliance report** (gripper holds the objects, motors hold the arm, the arm actuates): [cad/docs/compliance_report.md](cad/docs/compliance_report.md).
  - Status and evidence: [cad/docs/fourbar_status.md](cad/docs/fourbar_status.md).
- **Rev A.** The **released rev A package** (TDP, 46 drawings, fab STEP/DXF, FEA) documents the lead-screw gripper (`GRIP=SCREW`).
- **Simulation models.** MuJoCo (MJCF) and Gazebo (URDF with `<mimic>`) models of the four-bar arm are in [sim/](sim/README.md). Both are generated from the CAD and validated against it.
- **Where to start.** `cad/MAP.md` indexes every module, parameter, interface, envelope and part. `CLAUDE.md` holds the working conventions.

## What the arm does

| Task | Requirement (manual) | How the arm does it |
|---|---|---|
| **Donut** (Obj C) | Ø100/Ø50×25 ring sits around the base of a 456 mm zig-zag pole on the 210 mm lower tier. Score it lying flat on the 300×300×50 Scoring Area. | Jaws close on the 100 mm OD with the fingers forward. Lift it up the pole by following the zig-zag (arm Z plus chassis strafe for Y) until it clears the pole top at 666 mm. Then place it flat. |
| **Pipe** (Obj B) | 500 mm × Ø26.7 PVC pipe in a Ø200×250 bucket. Turn it in through a Ø52.5 chute 600 mm up. | Grip the pipe nearest the robot by its top end (fingers forward) and lift it clear of the rim (TCP at 740). Pitch the wrist 90° so the pipe points forward. The chassis then drives it ~300 mm into the chute. |
| **Fail-safe** (§3.2.4.5) | Within 1 s of being defeated, stop controlling objectives; a defeated Engineer's mechanisms are powered off, so the claw must release on its own. | A constant-torque spiral spring on the lead screw always turns it towards OPEN. The Tr8x8 screw is free-running, so with the M2006 unpowered the spring spins the screw (and back-drives the gearbox) and the jaws open. **Bench-test the release time** (see risks). |

## Kept from the paper vs changed

- **Kept:**
  - Palletizer topology: shoulder and elbow motors coaxial at the base, forearm driven through a crank/rod parallelogram.
  - Level-keeping, so the wrist stays level. Stage 1 keeps the paper's parallelogram (ground lever → rod → rocker). Stage 2 (rocker to wrist) is a parallelogram linkage (rod 2, 43 mm levers at 72.7°) since 2026-11-17; the rev A package used a 1:1 GT2 belt there. See [cad/docs/fourbar_status.md](cad/docs/fourbar_status.md).
  - The paper's 1 N·m / 416 rpm gripper motor class: a DJI M2006 P36 (with C610 ESC, CAN, current control = grip-force control).
- **Changed:**
  - Links scaled about 2.4×: l1/l2/l3 go from 60/140/205 to 80/340/350 mm.
  - Wrist-pitch servo added (J3): a DS3225, mounted on the level member so the pitch angle is absolute.
  - Wrist-roll stage added (J4): a second DS3225 mounted axially in a printed roll housing between the clevis plates. Its output carries the gripper head on an aluminium hub running in a 6805 thin-section bearing, so the servo doesn't take the pipe's bending moment. The roll axis is 15 mm above the TCP, so a 30° roll shifts the TCP about 4 mm sideways (handled by the IK). Roll lets the arm grip sideways-leaning pipes and tilt the donut through the zig-zag bends.
  - **No rope drive.** The paper's LAHM reel and rope are replaced by a linear drive on the gripper itself:
    - a Tr8x8 (4-start) **bidirectional lead screw** (RH half drives the left jaw, LH half the right) running in 688ZZ bearings in two 6061 end blocks;
    - the M2006 clamped under a CF bridge that closes the end blocks into a stiff frame, driving the screw through an m1 20T/32T reduction (1.6:1; 8 mm per screw turn, about 35 mm/s per jaw at full speed, with 2.6× finer grip-force control than the earlier 32T/20T step-up);
    - a constant-torque spiral spring motor on the screw end for the power-off release;
    - jaws on 2× MGN9 rails, synchronised by the screw itself.
  - **Curved, more robust jaws:** each jaw is a machined 6061 bracket (on the MGN9H block, carrying the flange nut) with two 3 mm CF finger plates, top and bottom, tied by D6 standoffs. A TPU pad between the plates has an R50 arc that wraps the donut OD and a 90° V-notch in the middle that self-centres the Ø26.7 pipe on four lines. The `jaw` value is now the gap between the pad arcs at the TCP: 100 for the donut, 13.8 for the pipe (the pipe sits in the notches).
  - Joint motors are DM-J4340-2EC (9 N·m rated) instead of the paper's 7 N·m-peak motor.

## Model structure

The full model is generated from code, so it can be rebuilt after any parameter change.

| File | What it holds |
|---|---|
| `cad/arm/` | The model, one module per subassembly (see `cad/arm/__init__.py`): `core.py` (parameters `K`, layer stack `Y`, motor interface `DM`, catalogue `CAT`, helpers), `base.py`, `upper_arm.py`, `forearm.py`, `wrist.py` (pitch and roll stage, shared roll hub), `grippers/screw.py` (rev A) and `grippers/fourbar.py`, `bodies.py` (body registry and gripper variants), `kinematics.py` (joints, IK, placements, torques, poses). |
| `cad/arm_model.py` | Compatibility facade: re-exports the whole `cad/arm` namespace so `import arm_model as M` works everywhere. In a long-running FreeCAD session, call `arm.reload_all()` to pick up edits. |
| `cad/hardware.py` | Purchased-part geometry (see below). |
| `cad/vendor/` | The original vendor STEP files and drawings (official downloads). |
| `cad/field.py` | ARC Battlefield items (tier, pole placeholder, bucket, pipes, scoring area, chute). |

Purchased parts in `hardware.py` come from three sources:

- **Vendor CAD:**
  - Damiao DM-J4340-2EC: STEP model and 2D drawing from [dmBots/DM-J4340-2EC](https://github.com/dmBots/DM-J4340-2EC). The hubs, towers and dowels follow the real interfaces: output 6×M3 on PCD 27 plus 3×Ø4 dowels on PCD 24; housing 6×M3 on PCD 50 plus 2×Ø3 dowels.
  - DJI M2006 P36 and C610: STEP files from robomaster.com. The M2006 output shaft is Ø6 × 16.5 mm with a flat (overall length 64.8 mm); the motor is clamped by its body and the shaft runs through the 20T gear (full 5 mm engagement, set screw on the flat).
- **ISO/DIN hardware at standard dimensions:** ISO 4762, 7380 and 10642 screws; ISO 7379 shoulder screws; ISO 10511 nylocs; DIN 6799 e-clips; ISO 8734 dowels; bearings; standoffs. These are generated the same way the FreeCAD Fasteners workbench generates them.
- **Modelled from catalog data (no public CAD):** HIWIN MGN9R rail and MGN9H block, GT2 30T pulleys and belt, DS3225 servo envelope, Tr8x8 bidirectional screw and flange nuts, m1 spur gears, shaft collars, spring-motor cassette, P-clips and cable-tie mounts.

Every pivot has a stated stack-up: bearing, shoulder screw, spacer or shim, and nyloc nut. Every bolted interface has its screws modelled.

### Gripper variants, interfaces and regression guards

- **Gripper variant:** `cad/params/variant.toml` selects the gripper. Setting the `GRIP` environment variable overrides it for one run.
  - `GRIP=FOURBAR` (the default) is the lightweight gear-synchronised parallel four-bar gripper. It is a concept under evaluation.
  - `GRIP=SCREW` is the rev A lead-screw gripper. The rev A drawings, FEA jaw case and fabrication exports assume this variant.
- **Parameter files:** `cad/params/*.toml` hold the named design inputs, one file per subsystem. Each value has its unit and the reason it has that value:
  - `arm.toml`: kinematics `K`, layer stack `Y`, plate thickness, level-keeping, J1 hub, harness;
  - `pads.toml`: jaw pads shared by every gripper;
  - `wrist.toml`;
  - `gripper_screw.toml` and `gripper_fourbar.toml`;
  - `materials.toml`;
  - `variant.toml`.

  The purchased-part catalogue (descriptions, masses, sources) is in `cad/data/catalogue.toml`. Values derived from these stay in code next to the parts that use them. Edit the TOML, run the quick check, then re-record the fingerprint if the change was intended. `cad/tests/test_params_flow.py` confirms a parameter edit reaches the geometry.
- **Outputs and evidence:** checks write to `cad/out/<variant>/`:
  - `check_interference.py`, `tools/check_holes.py`, `tools/check_engagement.py`, `tools/projected_heights.py`;
  - the quick check, interface check and fingerprint.

  Each run is logged in `cad/out/<variant>/manifest.json` with its status and a hash of the design inputs (model code, parameters, interfaces, envelopes, vendor CAD). The quick check lists every logged check as FRESH or STALE against the current inputs. The hash covers both variants' code, so an edit to either marks both STALE.
- **Release guard:** the release generators (`export_fab.py`, `fea/run_fea.py`, `drawings/*`, `build_assembly.py`, `render/export_render.py`) build the release variant set in `params/variant.toml` (`SCREW`, rev A). They refuse any other `GRIP`, so a concept can't overwrite `fab/`, `drawings/out`, `fea/out` or `render/`. For the release variant, the engagement report and projected heights are also written to `cad/fab/`, because the rev A TDP and drawings read them from there.
- **Model map:** `cad/MAP.md` is generated by `cad/tools/make_map.py`; run it once per variant. It indexes every module, parameter file, interface and envelope, and every part with its kind, source, mass and a link to the line that builds it. `CLAUDE.md` at the repo root holds the working conventions.
- **Interface files:** `cad/interfaces/*.toml` holds one file per mating interface: frame, bolt pattern, hole type and size on each side, and fastener. Both mating parts build from the file through `cad/iface.py`. Look here first for "what bolts to what". Current files:
  - `dm_j4340__hub_tower.toml` (J1/J2 motor bolt and dowel patterns; not probed by the check yet)
  - `roll_horn__roll_hub.toml`
  - `roll_hub__gripper_palm.toml` (every gripper variant mounts here)
- **Interface check:** `cad/tools/check_interfaces.py` probes the built geometry to confirm both sides of each interface have a hole on every pattern axis at the specified size. Output goes to `cad/out/<variant>/interfaces.json`.
- **Geometry fingerprint:** `cad/tools/fingerprint.py` records volume, centre of mass, bounding box, face and edge counts and mass for every part, plus every body placement and the TCP at three poses.
  - `FP_MODE=check` compares against `cad/tests/fingerprints/<variant>.json`. Run it after any refactor; a pure refactor must report MATCH.
  - After an *intended* geometry change, re-record with `FP_MODE=record`.

```bash
"$LOCALAPPDATA/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/tools/fingerprint.py
```
```bash
"$LOCALAPPDATA/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/tools/check_interfaces.py
```

- **Field envelopes:** `cad/envelopes/field.toml` lists keep-out boxes the arm must stay out of at given task poses. Each entry gives its reason and its source in `field.py` or the manual. Current entries:
  - the pole base plate and the lower tier at the donut pick;
  - the pole above and below the fingers during the lift (nothing above the pads within 14 mm of the TCP x);
  - the perimeter wall at the chute;
  - the scoring platform.
- **Quick check:** `cad/tools/quick_check.py` (about 25–30 s, including the 15 s model build) is the check to run after every design edit. It covers:
  - envelopes;
  - interface agreement;
  - gripper self-interference over the jaw stroke at roll 0° and 90°;
  - mass and static joint torque against actuator ratings;
  - the fingerprint.

  Output goes to `cad/out/<variant>/quick.json`. The full `check_interference.py`, FEA and drawings are for milestones.
- `cad/tests/test_envelope_catches_pole.py` is a negative test. It rebuilds the first four-bar head, whose jaw blocks reached x 165, and confirms the envelope flags the pole clash.

```bash
"$LOCALAPPDATA/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/tools/quick_check.py
```

## Mated assembly

`cad/ARC_Engineer_Arm.FCStd` is a FreeCAD 1.x **Assembly-workbench** document:

- Each rigid body is an `App::Part`: GROUND, UPPER, CRANK, ROD_AB, ROD1, FOREARM, ROCKER, LEVEL, GRIPPER, HEAD, SCREW, MGEAR, JAW_L, JAW_R.
- 20 joints connect the bodies:
  - grounded base;
  - 13 revolutes: S ×2, A, B, E, G1, E+v1, E (rocker), D ×2, roll J4 (GRIPPER to HEAD), the lead screw and the motor gear;
  - 1 Belt joint: the 1:1 GT2 30T, 9 mm belt from the rocker pulley to the wrist pulley (stage-2 level keeping). Through the whole simulation the level member stays within 0.0000° of level;
  - 2 sliders, one per jaw on its MGN9 rail;
  - 2 Screw joints (pitch +8 / −8 mm) between the lead screw and each jaw;
  - 1 Gears joint (r 10 / r 16) between the screw gear and the motor gear.
- The Ondsel solver drops the redundant constraints that closed planar loops create, then solves the assembly.
- At every task pose the solved placements match the analytic kinematics with **0.000 mm drift** (`cad/assembly_solve_report.txt`).
- Each body carries a hidden `Datum_<body>` feature at its origin, and all joint frames reference these datums.
- `cad/scenes/ARC_Arm_<POSE>.FCStd` holds the same assembly solved at each task pose, with the field items and the pose-specific cable harness.
- After opening a file in the GUI, run `cad/color_assembly.py` to apply colours and visibility. Headless-saved objects open hidden until it runs. It also re-attaches the joints' view providers in files built headless (`freecadcmd`), which otherwise make every GUI solve fail (`'ViewProviderJoint' object has no attribute 'switch_JCS1'`), so dragging works in any build. Only the GUI build adds the simulation, and a headless run overwrites `ARC_Engineer_Arm.FCStd`.
- **To see it actuate**, build it inside the FreeCAD GUI so the joints get their view providers (a headless build solves, but FreeCAD's drag and simulation tools need them): in the FreeCAD Python console set `os.environ["KEEP_OPEN"] = "1"` and `exec` `cad/build_assembly.py`. The GUI build also adds **`Simulation_demo_cycle`** (Assembly ▸ Simulations): angular motions on J1, J2, wrist pitch, roll and the lead screw. The jaws, motor gear, level-keeping linkage and belt all follow through the mates (driving the motor gear itself stalls the solver). Double-click it, press *Run*, then play. The Assembly solver's formula parser only accepts sin/cos/polynomials, so each motion is a 16-harmonic Fourier series through the keyframes. You can also drag any part in the GUI and the linkage follows.

## Iterating

**Interference results are cached.** `cad/.cache/interference_cache.json` stores each pair's result, keyed by a geometry fingerprint of both parts plus their relative placement. A re-run only re-booleans pairs whose geometry or relative pose actually changed: a warm re-run with no geometry changes takes about 85 s and does 0 booleans, against about 290 s cold. Set `NOCACHE=1` to force a full recompute.

**Quick loop (about 2 min warm), run this after every change:**

```bash
"%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecadcmd.exe" cad/tools/quick_static.py
```
Takes about 30 s: builds all parts and checks every part pair at the stowed pose.

After a local change, `cad/tools/quick_pairs.py` with `FILTER=<regex of changed part names>` checks only those parts against everything else at all 14 task poses (about 1 min), instead of the full sweep.

```bash
"%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecadcmd.exe" cad/tools/check_holes.py
```
Takes about 1–3 min: **hole edge-distance (manufacturability) check** on every custom part, written to `cad/hole_report.txt`.
- BROKEN: a hole that breaks out through an edge, pocket or window. Partial cylinders that blend tangentially (slot ends, fillets) are ignored.
- FAIL: wall from a hole to the nearest side face < 1.0 mm.
- WARN: wall < max(1.5 mm, 0.5 × hole d). The remaining warnings are walls set by fixed interfaces (servo-horn PCD16 against the D10 shaft, motor PCDs) or deliberately thin 2–4 mm parts.

Purchased parts are skipped. The first run found and fixed real issues:
- 20T GT2 pulleys whose 10.6 mm bore left 0.1 mm under the tooth roots (now 30T);
- 0.25 mm walls at the J1/J2 hub counterbores (hub Ø39 now);
- 0.3 mm between the UA-L hub screws and the pilot (now 3×M3 on PCD20);
- a standoff hole breaking into a lightening pocket (pockets now keep a web around every hole);
- end-block tapped holes breaking into the window, roll-hub tapped holes cutting the journal;
- a sign error in the tangent-line construction of tapered plates (`_hull2`).

```bash
"%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecadcmd.exe" cad/check_interference.py
```
Takes about 2 min. Checks:
- self-interference and field clearance at all 14 task poses, including the roll poses;
- static torques J1–J4.

**Release loop (about 15 min), run only at milestones:**

```bash
set FULL=1
```
With `FULL=1` set:
- `check_interference.py` sweeps about 90 interpolated poses through both task sequences, including roll moves;
- `build_assembly.py` also writes the 9 posed scene assemblies.

Then run `export_fab.py` for the BOM, DXFs and STEP files.

`analysis/arm_sizing.py` is the first-pass 2-D hand calc. It is superseded by the model's own torque output.

## Renders and animation

Renders use Blender 5.3 (the portable build in `tools/blender-5.3.0-windows-x64/`, SHA-256 verified) through its own Python API. Nothing custom does the rendering itself. The pipeline:

1. `cad/render/export_render.py` (FreeCAD) meshes each rigid body by material and writes `anim.json`: per-frame body transforms for the donut and pipe clips, computed from the same kinematics the mated assembly solves to.
2. `cad/render/blender_render.py` (Blender) imports the meshes, applies PBR materials (clear-coated CF, PETG-CF, anodised aluminium, black-oxide hardware, TPU), lights a studio scene, keyframes the bodies, and renders.

```bash
cd cad/render
```
```bash
../../tools/blender-5.3.0-windows-x64/blender.exe -b -P blender_render.py -- --stills
```
```bash
../../tools/blender-5.3.0-windows-x64/blender.exe -b -P blender_render.py -- --anim
```

Outputs go to `cad/render/out/`:
- `hero_*.png`: Cycles, 1920×1080, 128 samples, OIDN denoising;
- `arc_engineer_arm_cycle.mp4`: EEVEE, 1280×720, 24 fps.
  - Donut clip: approach, pick, then a Cartesian lift **along the pole**. The chassis strafes to keep the pole inside the donut hole, J4 rolls the donut to follow the pole's slope (up to 50° on the placeholder pole), and the strafe is biased within the hole's play so the pole clears the fingers at the tight bends (`field.donut_lift_path`). Then ±25° roll above the pole.
  - Pipe clip: the robot (not the field) moves. Grasp at the bucket, lift, strafe 500 mm to line up with the chute, pitch to horizontal 50 mm short of the wall, drive 350 mm in, then 90° roll.
- `detail_gripper_pipe.png`, `detail_gripper_donut.png`: Cycles close-ups of the jaws.
- Materials use the CC0 ambientCG / Poly Haven maps (carbon twill, brushed aluminium, black-oxide steel, PETG-CF, TPU, plywood) through tri-planar projection, with the studio image as reflection environment.
- `arc_engineer_arm.blend`: the scene, which you can open and re-render.

Environment variables `SAMPLES`, `RESPCT`, `ONLY=<still>`, `TESTFRAMES=a,b` and `EEVEE_RT=1` make quick previews.

### FreeCAD-native renders (textured)

`cad/render/fc_render.py` renders inside FreeCAD's own Coin3D/OpenGL viewer. It applies real texture maps through Coin's texture nodes, the same mechanism as FreeCAD's `Std_TextureMapping` command:

- the colour map, plane-mapped on carbon-fibre plates so the weave keeps a constant ~30 mm tile, and cube-mapped elsewhere;
- a studio reflection on a second texture unit for the metals and the clear-coated carbon fibre.

Assets are prebuilt and CC0, stored in `cad/render/assets/`:

| Use | Asset |
|---|---|
| Carbon fibre | ambientCG Fabric004 |
| Brushed aluminium | ambientCG Metal012 |
| Steel and anodised parts | ambientCG Metal032 |
| PETG-CF prints | ambientCG Plastic011 |
| Pads | ambientCG Rubber004 |
| Field tier | Poly Haven plywood |
| Metal reflections | Poly Haven studio_small_03 |

Two preparation steps adapt these assets for Coin:

- `equirect_to_spheremap.py` converts the studio image to the sphere-map format Coin needs.
- The plastic, rubber and metal colour maps are level-normalised so they tint parts instead of darkening them.

Frames are captured with `saveImage` at 2× resolution and downsampled for anti-aliasing. The PNG frames are then encoded to MP4 with Blender's bundled FFmpeg (`encode_frames.py`, encoding only, no rendering).

To render, run this inside the FreeCAD GUI:

```python
exec(open(r"<repo>/cad/render/fc_render.py").read())
setup()
still("hero_donut_lift")
frames(0, 10000)
```

Outputs go to `cad/render/out_fc/`:
- stills: `hero_donut_lift`, `hero_pipe_chute`, `hero_stow`, `detail_wrist`, `detail_base`;
- `frames/` (the animation frames);
- `arc_engineer_arm_freecad.mp4`.

**Blender MCP** (optional, for driving Blender interactively from Claude) is not installed yet. Run these yourself, then restart the Claude app:

```bash
uvx mcp-for-blender install-addon
```
```bash
claude mcp add blender uvx mcp-for-blender
```

## Status (2026-11-14)

- The model is complete: about 320 parts across 14 rigid bodies, 4 arm DOF (J1 shoulder, J2 elbow, J3 wrist pitch, J4 wrist roll) plus the lead-screw gripper, with vendor motors and ESC, and every fastener, set screw, bearing, collar, spacer and cable clip.
- The cable harness is modelled per pose. It is visual only and not included in the interference check.
- Static joint torques are J1 ≤ 3.9, J2 ≤ 4.0, J3 ≤ 1.2, J4 ≤ 0.13 N·m against ratings of 9 / 9 / ~2.4 / ~2.4 N·m (the gripper drive moved about 300 g to the wrist).
- Modelled arm mass is 3.18 kg.
- The donut lift along the (placeholder) pole is checked as a Cartesian path with roll and strafe: clear.
- Not done: dynamics, the chassis (a placeholder in the manual-derived scenes), and wiring to a controller.

## Technical data package

`cad/tdp/ARC_Engineer_Arm_TDP.pdf` is a single PDF built from the project's outputs, with no hand-entered numbers. Rebuild it with `python -I cad/tdp/make_tdp.py`. It contains:

- **Verification summary.** Interference (static and 14 task poses), field and pole-path clearance, hole edge distance, assembly solve.
- **Structural FEA.** Built by `cad/fea/run_fea.py`, headless, using FreeCAD FEM with gmsh and CalculiX. Loads are the worst static reaction × 2.5, with SF ≥ 1.5 required. Contour plots come from `cad/fea/render_fea.py`. Any case with zero stress or displacement is rejected rather than passed.
- **Procurement.** `cad/fab/make_procurement.py` writes `procurement.csv`. Each line has one of four statuses:
  - VERIFIED: spec confirmed through the McMaster MCP or the vendor page.
  - SOURCED: a vendor product page matches. This covers the bearings, KHK gears, Ruland collar, Gates belt, servo horn, and the bidirectional Tr8x8 screw with its nuts from an Alibaba listing.
  - CATALOGUE: an exact standard designation, but no supplier part number yet.
  - SPECIAL: needs a quote or a design decision. That's the two non-standard shoulder lengths and the spring motor.
- **Projected tolerance zones.** `cad/tools/projected_heights.py` measures each tapped hole's projected height in the assembly, as the mating stack on the screw-head side, and writes `cad/fab/projected_heights.json` for the drawings.
- **Drawings.** Appendix A holds 45 ASME drawing sheets, ARC-101 to ARC-145. Existing parts keep their numbers; new parts are appended.
  - `cad/drawings/batch_drawings.py` generates them, `asme_rules.py` holds the rules (verified against Y14.5-2018 §4.3.1, §4.4.4 and App. B), and `layout.py` handles placement.
  - `cad/drawings/check_datums.py` checks that every datum referenced in an FCF is defined on its sheet.
  - Torque interfaces are modelled as D-flats with mating D-bores: the wrist shaft to the clevis plates and coupler, and the J2 journal to the crank. `cad/tools/check_holes.py` recognises D-bores and doesn't report them as breakouts.

The layout is checked on TechDraw's own rendered scene. A sheet passes only with:

- no overlapping labels;
- no leader running through a label;
- no leader crossing a dimension line, an extension line or another leader.

Leaders attach to whichever instance of a hole pattern, and whichever rim point, gives the shortest clean, inclined, radial leader.

## Open items / risks (in priority order)

1. **Zig-zag pole geometry is TBA in the manual.** The pole is a placeholder: a single continuous swept tube, Ø24, along an analytic ±50 mm S-curve in Y (min bend radius about 39 mm, steepest 50° from vertical). The donut-lift path (roll + strafe) is generated from it, so re-run `check_interference.py` when the official drawing lands.
2. **Robot Building Specifications not reviewed.** No size or weight limits are applied yet. The stowed arm top is about 420 mm, which equals the central limbo bar (420) and won't fit under the side bar (300).
3. **Fail-safe release.** The spring motor must back-drive the unpowered M2006 (36:1) through the 20/32 reduction. Measure the real back-drive torque at the M2006 output, then pick a spring of at least 2× that × 32/20 (about 0.2 N·m assumed), and bench-test release < 1 s.
4. **M2006 gear retention.** The 20T gear sits on the Ø6 × 16.5 mm output shaft with a set screw on the flat (add Loctite 638); check the shaft flat orientation on a real motor before drilling the set-screw hole.
5. **DS3225 envelope.** There's no vendor CAD for this servo. Caliper-check the ear-hole grid (49.5 × 10) before cutting the level member.
6. **The arm falls when the robot is defeated** (motors unpowered). This is allowed by the rules, but add a soft landing stop or gas spring so it doesn't slam.
7. **(Rev A only) Stage-2 belt load.** The J3 servo's reaction torque (up to about 1.2 N·m) runs through the belt: about 125 N on the 30T pulleys, so the belt is now 9 mm GT2 (rocker/level plates, rod 1 and the J3 servo stack moved 3 mm outboard to fit it). Use a fibreglass- or steel-cord 2GT-9 belt and set the idler tension to at least the expected load.
8. **(Rev A only) GT2 pulleys are custom parts** (30T, hex-keyed into the rocker and level member, with a 6700 bearing inside). Hob them in 6061, or buy 30T bore-10 pulleys and machine the hex. The belt is clamp-spliced and tensioned by the idler on the forearm.
9. **The chassis isn't designed.** Assumptions: deck at 120 mm, shoulder 160 mm behind the bumper.

## Next steps

1. Fetch the Robot Building Specs and the pole drawing, then update `K` and `field.py`.
2. Print and cut a v0: CF plates from the DXFs, PETG-CF prints, the 6061 jaw brackets and end blocks. Bench-test the spring release and grip force on a pipe and a donut.
3. Add the control stack: paper eq. 6–9 IK (already implemented in `ik()`), CAN for the DM motors, and C610 for the M2006.
