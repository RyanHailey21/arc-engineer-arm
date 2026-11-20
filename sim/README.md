# ARC S2 Engineer arm: simulation models

`arc_arm_fourbar/` holds the arm with the four-bar gripper, generated from the CAD model. It contains a **MuJoCo** model (MJCF) and a **Gazebo** model (Gazebo Harmonic; URDF with `<mimic>` joints).

The geometry, masses and inertias come straight from `cad/` (the `arm_model` package). Both files reproduce the CAD forward kinematics to **0.0004 mm** at seven task poses.

## Files

| File | For |
|---|---|
| `arc_arm.xml` | MuJoCo robot: actuators, the gripper's opening spring, keyframes for every task pose |
| `scene.xml` | MuJoCo scene: robot + floor + chassis-deck placeholder + ARC lower tier + donut + pipe |
| `arc_arm.urdf` | Plain URDF (relative mesh paths): ROS tools, MuJoCo's URDF importer, yourdfpy, Isaac, … |
| `model.config`, `model.urdf` | Gazebo model (`model://` mesh URIs, gz-sim joint position controllers + joint state publisher) |
| `worlds/arc_arm.sdf` | Gazebo world, donut-pick station: ground, chassis-deck placeholder, lower tier, the arm; bullet-featherstone physics |
| `worlds/arc_arm_free.sdf` | Gazebo world without field items, for playing whole task sequences |
| `task_poses.json` | the 14 CAD task poses (joint targets) and the donut and pipe sequences |
| `meshes/visual/*.stl` | Per-link, per-material visual meshes (mm, scaled 0.001 in the models) |
| `meshes/collision/*.stl` | Per-part collision meshes (the simulators take their convex hulls) |
| `robot_spec.json` | Link frames, masses, inertias, joints, limits, actuators, spring (input to the generator) |
| `fk_reference.json` | CAD body placements at the task poses (validation reference) |
| `validation.json` / `.md` | Results of the checks below |
| `preview.png` | MuJoCo render at DONUT_APPROACH, PIPE_CHUTE and STOW |

## Use

MuJoCo (`pip install mujoco`):

```bash
python -m mujoco.viewer --mjcf=sim/arc_arm_fourbar/scene.xml
```

In the viewer, pick a keyframe (`stow`, `donut_approach`, `donut_lift`, `pipe_grasp`, `pipe_chute`, …) and drive the five position actuators.

### Full tasks in MuJoCo (`tasks.xml`, `cad/sim/tasks.py`)

```bash
python cad/sim/tasks.py --task both
```

Add `--no-viewer` to run headless, faster than real time. The run writes `arc_arm_fourbar/task_run.json`.

Add `--video sim/media/arc_arm_tasks.mp4` to render the run: 1280×720, 30 fps, H.264, captions per phase, drives at 2×. It needs `imageio-ffmpeg`. A rendered copy is in [`media/arc_arm_tasks.mp4`](media/arc_arm_tasks.mp4) (51 s, 3.1 MB).

- **Scene** (`tasks.xml`, built by `cad/sim/build_tasks.py` from `task_field.json`):
  - The arm rides on a chassis with x/y slide joints, an abstraction of the drivetrain.
  - The four CAD field stations sit side by side: donut pick (lower tier, zigzag pole, donut), scoring platform, pipe bucket, and wall with chute. All are built from primitives, so contacts are exact.
- **Donut task:**
  1. Approach from behind the pole and slide in, jaws open.
  2. Descend and close the jaws.
  3. Lift up and off the zigzag pole along the CAD lift path (chassis strafe up to ±44 mm, wrist roll up to 47°).
  4. Drive to the scoring platform, lower, release, retreat, stow.
- **Pipe task:**
  1. Reach in and grip the pipe.
  2. Lift it straight out of the bucket.
  3. Back away and swing to the chute pose.
  4. Drive to the chute and push the pipe 300 mm in.
  5. Release, back off, stow.
- **Kinematic grasp:** when the jaws close at a grasp pose and the object is within 8 mm of the TCP, a weld locks it to the head. Opening the jaws releases it. Held objects don't collide with the arm, but they do collide with the field and the chassis.
- **Result:**

  | | |
  |---|---|
  | Run time | 74 s simulated |
  | Grasp error | donut 1.3 mm, pipe 0.5 mm |
  | Robot-to-field contacts | none |
  | Donut-to-pole contacts during the lift | none (the CAD lift planner holds up under physics) |
  | End state | donut on the platform; pipe 298 mm past the wall face |

- **Found by this sim:** a straight joint-space move from STOW to DONUT_APPROACH sweeps the left jaw about 11 mm through the pole, measured on the real mesh. CAD checks the task poses, not the moves between them. The task uses the slide-in approach instead. The pose-playback demos below don't have the pole, so they don't show this.
- **Actuation and grasp loads** (written to `task_run.json` → `actuation`, used by `cad/docs/compliance_report.md`): per joint the peak torque (and the phase it is in), RMS torque and peak speed; per object the weld's wrench at the TCP in the gripper frame while the object is carried free (contact events reported apart). `cad/tools/grip_hold.py` turns these into the clamp the gripper needs.
  - The joints run MIT-style (position + velocity feed-forward), and each 10 ms setpoint is ramped across the physics substeps, as a drive interpolates its command stream. Stepping the setpoint instead kicked the stiff servos at 100 Hz and tripled the torque and grasp-load peaks.
  - Each mesh collides as its convex hull, so the jaw block's collision mesh is split at the top-finger plane: one hull over the whole block filled its stepped pole keep-out and grazed the pole during the lift.
- **Not modelled:** grip friction and slip (the grasp is kinematic); the real drivetrain (the slides are ideal position servos, with no yaw); the zigzag pole is the CAD placeholder (the manual's pole details are TBA).

### Pose playback (no field)

To play the task sequences in MuJoCo (native on Windows; the viewer stays open at the end):

```bash
python cad/sim/demo.py --backend mujoco --seq both
```

`--scene free` (the default) removes the donut-pick station (lower tier and donut), so whole sequences run; `--scene pick` keeps it. Measured here: 20 moves in 25 s at 100 Hz. Poses settle 0.3–0.6° off target. That's the finite-stiffness motor law sagging under gravity (the joint PD law's kp/kv), which Gazebo's ideal velocity motors don't show.

Gazebo Harmonic (gz-sim 8):

```bash
GZ_SIM_RESOURCE_PATH=$PWD/sim gz sim sim/arc_arm_fourbar/worlds/arc_arm.sdf
```

To command a joint:

```bash
gz topic -t /arc_arm/shoulder/cmd_pos -m gz.msgs.Double -p "data: 1.2"
```

Two worlds, same topics:
- `worlds/arc_arm.sdf`: the **donut-pick station** (lower tier in front of the arm).
- `worlds/arc_arm_free.sdf`: floor and chassis only, for **whole task sequences**. The field is per station: the robot drives to the scoring platform for DONUT_PLACE and to the bucket and chute for the pipe moves, so DONUT_PLACE would hit the lower tier in the pick-station world.

To play the CAD task sequences (donut, then pipe) in the free world:

```bash
GZ_SIM_RESOURCE_PATH=$PWD/sim gz sim -r sim/arc_arm_fourbar/worlds/arc_arm_free.sdf
```

```bash
python cad/sim/gz_demo.py fourbar --seq both --rate 100 --speed 0.5
```

The demo needs the gz-transport Python bindings (`gz-transport13-python`, `gz-msgs10-python`). Measured here: 20 moves in 27 s, setpoints at 100 Hz, every pose reached within 0.01°.

**Control stack** (`cad/sim/joint_command.py`), shaped like the real arm's:
- **Host side:** task poses (`task_poses.json`, 14 poses and the `donut` / `pipe` sequences, exported from CAD) → a minimum-jerk move between poses, timed so no joint exceeds `--speed` × its speed limit → position setpoints streamed at a fixed rate, clamped to the joint limits.
- **Backend:** `MujocoCommander` sets the MuJoCo position-actuator targets, running the physics in real time with the viewer. `GazeboCommander` publishes on `/arc_arm/<joint>/cmd_pos` and reads `/joint_state`. `cad/sim/demo.py --backend mujoco|gazebo` runs the same sequence on either. A hardware backend (DM-J4340 MIT mode over CAN, servo bus for the wrist and gripper) would implement the same `send()` / `state_deg()`, with no change to the planning code.
- **Not included:** path planning, collision avoidance beyond the CAD-checked poses, grasping (the Gazebo worlds have no donut or pipe; MuJoCo's `scene.xml` does).
- **Discovery:** run only one command source at a time. Gazebo's discovery takes about 1 s, and a second publisher on the same topics will fight the first.

On Windows under WSL, if the Gazebo window opens blank, check that WSL windows show at all. If they don't, run `wsl --shutdown` and relaunch. If only Gazebo is blank, set `LIBGL_ALWAYS_SOFTWARE=1` (the docs' software-rendering fallback).

## Joints

Joint values are the CAD model's own angles. The CAD convention is **radians in the simulators and degrees in `cad/`**.

| Joint | Actuator | Limits (deg) | Meaning |
|---|---|---|---|
| `shoulder` | STS3215 + 3:1 spur stage, 8.4 N·m stall | 0 … 180 | upper-arm angle th1 |
| `elbow` | STS3215 + 3:1 spur stage, 8.4 N·m stall | −86 … 51 | **absolute** forearm angle th2 (J2 drives it through the crank and rod AB). The limits keep the level-keeping parallelogram ≥ 21° from its dead points |
| `wrist_pitch` | STS3215, 2.94 N·m stall | −30 … 120 | gripper pitch (absolute: the level member stays level) |
| `wrist_roll` | STS3215, 2.94 N·m stall | −95 … 95 | roll about the gripper axis |
| `gripper` | STS3215, 2.94 N·m stall | 0 … 63.2 | drive-link angle from the pipe grip (0 = 13.8 mm pad gap, 54.6 = donut 100 mm, 63.2 = fully open 112 mm) |

The 12 passive joints each follow one actuated joint exactly:
- rods, rocker and crank;
- level-keeping rod 2 (replaced the forearm belt; parallel to the forearm);
- level member (rod-2 parallelogram);
- idler links and sector-gear mirror;
- parallel jaws.

They are joint-equality constraints in MuJoCo and `<mimic>` in URDF/Gazebo. The opening torsion spring (McMaster 9271K56) is a joint spring on `gripper`: k 0.324 N·m/rad, unwound at 85.2°.

## Verification (`validation.json`)

| Check | Result |
|---|---|
| URDF forward kinematics vs CAD (7 poses, every link) | max 0.0004 mm / 0.000° |
| MJCF forward kinematics vs CAD (7 poses, every link + TCP) | max 0.0004 mm / 0.000°; equality residual 0 |
| MuJoCo: hold STOW under gravity for 3 s | tracking 0.48° max; constraint drift 1e-4; no NaN |
| Holding torques vs CAD static torques at STOW | shoulder −2.77 vs −2.73 N·m; elbow 2.06 vs 2.01 N·m (masses and inertias carried through) |
| Power-off release (gripper actuator off at the pipe grip) | jaws open 10 mm in 0.04 s, 90 % open in 0.14 s (ARC rule: release within 1 s) |
| Contacts between the arm and the scene at all 7 keyframes | none |
| Scene drop test (1 s) | donut and pipe settle, finite state |
| URDF in MuJoCo's URDF importer | compiles (17 bodies) |
| Gazebo package structure | `model.urdf` parses; all 107 `model://` meshes resolve; 11 mimic joints; 5 controllers; no link/joint name clashes |
| Gazebo run test (`gazebo_validation.json`, gz-sim 8.10, bullet-featherstone, full field world). **Informational since 2026-11-18** (Gazebo dropped as a requirement; it no longer gates `build_robot.py`) | each of the 7 poses commanded over the `cmd_pos` topics: settles in ~8 s; actuated joints within 0.003°; all 12 mimic followers within 0.33°; gripper TCP within 2.0 mm of CAD. Power-off release (gripper controller removed, free world): open 10 mm in 0.59 s, 90 % open in 2.6 s |

## Limits of these models (read before relying on them)

- **Gazebo needs Harmonic (gz-sim 8) with bullet-featherstone**, which the world selects. DART in gz-physics 7 has no mimic constraints, so the passive links would not follow there.
  - The Gazebo controllers run in **velocity mode** (`use_velocity_commands`): the joint motor's torque is capped at the actuator's peak torque (URDF `effort`), and its speed at `cmd_max`. Force-mode PID with the MuJoCo gains was unstable on the light gripper links.
  - Bullet's mimic constraints are slightly soft under load (up to 0.4°), which puts the TCP up to ~2.4 mm off CAD. MuJoCo matches CAD exactly.
  - The massless `crank_pin` helper link carries 3 g / 1e-5 kg·m² in `model.urdf` (the crank-pin hardware, counted twice: 0.1 % of the arm mass). With ~0 inertia, Bullet's constraint solve jams the elbow.
  - The joints start at 0 and drive to the first command; there is no initial-pose setting in the URDF.
  - Power-off release in Gazebo: run on a copy of the model without the gripper controller (servo unpowered), in the free world. The jaws open 10 mm in 0.59 s and 90 % in 2.6 s. An earlier figure of 0.12 s came from the field world, where the stretched-out start pose can rest the jaws on the lower tier, so it isn't trustworthy. It's slower than MuJoCo because the two engines stand in for the unmeasured servo back-drive differently: Gazebo uses viscous joint damping (0.05 N·m·s/rad; Bullet has no joint friction), MuJoCo uses 0.05 N·m friction plus rotor inertia. Both meet the 1 s release rule, Gazebo with less margin; the bench test of the servo back-drive settles the real figure.
- **No self-collision in MuJoCo.** Arm geoms collide with the world and objects (`contype 2 / conaffinity 1`) but not with each other. Self-interference is verified in CAD (`cad/check_interference.py`).
- **Servo back-drive is a guess.** The gripper servo's unpowered back-drive is modelled as 0.05 N·m friction. The real value is not yet bench-measured, and the release time above depends on it.
- **Estimated actuator dynamics.** Rotor armatures, joint damping and controller gains are estimates (`build_robot.py`: ARMATURE, KP).
- **Software joint limits.** The limits cover the task poses with margin; mechanical stops are not modelled.
- **Placeholder field items.** The chassis deck and field items are placeholders; the zig-zag pole is not in the scene.

## Regenerate

From the repo root:
1. CAD export: `freecadcmd cad/sim/export_robot.py`, with `GRIP=FOURBAR`. It also writes `task_poses.json` and `task_field.json`. Set `EXPORT_ONLY=poses` to write just those two, without meshes.
2. Build URDF/MJCF/Gazebo files and validate, then build the MuJoCo task scene. This needs a Python with `mujoco`, `yourdfpy`, `trimesh` and `fast_simplification`:

```bash
python cad/sim/build_robot.py fourbar
```

```bash
python cad/sim/build_tasks.py fourbar
```

3. Gazebo run test, in an environment with gz-sim 8 (here: WSL Ubuntu + a conda-forge env, `micromamba create -p ~/mm/gz -c conda-forge gz-sim8 ruby`). Then rerun step 2 so `validation.json` picks up the result; it is FRESH only if it ran on the current `model.urdf`:

```bash
micromamba run -p ~/mm/gz python cad/sim/gz_check.py fourbar
```
