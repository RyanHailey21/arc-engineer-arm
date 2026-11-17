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
| `worlds/arc_arm.sdf` | Gazebo world: ground, chassis-deck placeholder, lower tier, the arm; bullet-featherstone physics |
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

Gazebo Harmonic (gz-sim 8):

```bash
GZ_SIM_RESOURCE_PATH=$PWD/sim gz sim sim/arc_arm_fourbar/worlds/arc_arm.sdf
```

To command a joint:

```bash
gz topic -t /arc_arm/shoulder/cmd_pos -m gz.msgs.Double -p "data: 1.2"
```

## Joints

Joint values are the CAD model's own angles. The CAD convention is **radians in the simulators and degrees in `cad/`**.

| Joint | Actuator | Limits (deg) | Meaning |
|---|---|---|---|
| `shoulder` | DM-J4340-2EC, 27 N·m peak | 0 … 180 | upper-arm angle th1 |
| `elbow` | DM-J4340-2EC, 27 N·m peak | −110 … 70 | **absolute** forearm angle th2 (J2 drives it through the crank and rod AB) |
| `wrist_pitch` | DS3225, 2.4 N·m | −30 … 120 | gripper pitch (absolute: the level member stays level) |
| `wrist_roll` | DS3225, 2.4 N·m | −95 … 95 | roll about the gripper axis |
| `gripper` | STS3215, 2.94 N·m stall | 0 … 63.2 | drive-link angle from the pipe grip (0 = 13.8 mm pad gap, 54.6 = donut 100 mm, 63.2 = fully open 112 mm) |

The 11 passive joints each follow one actuated joint exactly:
- rods, rocker and crank;
- level member (GT2 belt);
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
| Gazebo run test (`gazebo_validation.json`, gz-sim 8.10, bullet-featherstone, full field world) | each of the 7 poses commanded over the `cmd_pos` topics: settles in ~7 s; actuated joints within 0.005°; all 11 mimic followers within 0.41°; gripper TCP within 2.4 mm of CAD. Power-off release (gripper controller removed): open 10 mm in 0.12 s, fully open by 2.0 s |

## Limits of these models (read before relying on them)

- **Gazebo needs Harmonic (gz-sim 8) with bullet-featherstone**, which the world selects. DART in gz-physics 7 has no mimic constraints, so the passive links would not follow there.
  - The Gazebo controllers run in **velocity mode** (`use_velocity_commands`): the joint motor's torque is capped at the actuator's peak torque (URDF `effort`), and its speed at `cmd_max`. Force-mode PID with the MuJoCo gains was unstable on the light gripper links.
  - Bullet's mimic constraints are slightly soft under load (up to 0.4°), which puts the TCP up to ~2.4 mm off CAD. MuJoCo matches CAD exactly.
  - The massless `crank_pin` helper link carries 3 g / 1e-5 kg·m² in `model.urdf` (the crank-pin hardware, counted twice: 0.1 % of the arm mass). With ~0 inertia, Bullet's constraint solve jams the elbow.
  - The joints start at 0 and drive to the first command; there is no initial-pose setting in the URDF.
  - Power-off release in Gazebo: run on a copy of the model without the gripper controller (servo unpowered). The jaws open 10 mm in 0.12 s and fully (112 mm) by 2.0 s. It's slower than MuJoCo because the two engines stand in for the unmeasured servo back-drive differently: Gazebo uses viscous joint damping (0.05 N·m·s/rad; Bullet has no joint friction), MuJoCo uses 0.05 N·m friction plus rotor inertia. Both meet the 1 s release rule.
- **No self-collision in MuJoCo.** Arm geoms collide with the world and objects (`contype 2 / conaffinity 1`) but not with each other. Self-interference is verified in CAD (`cad/check_interference.py`).
- **Servo back-drive is a guess.** The gripper servo's unpowered back-drive is modelled as 0.05 N·m friction. The real value is not yet bench-measured, and the release time above depends on it.
- **Estimated actuator dynamics.** Rotor armatures, joint damping and controller gains are estimates (`build_robot.py`: ARMATURE, KP).
- **Software joint limits.** The limits cover the task poses with margin; mechanical stops are not modelled.
- **Placeholder field items.** The chassis deck and field items are placeholders; the zig-zag pole is not in the scene.

## Regenerate

From the repo root:
1. CAD export: `freecadcmd cad/sim/export_robot.py`, with `GRIP=FOURBAR`.
2. Build URDF/MJCF/Gazebo files and validate. This needs a Python with `mujoco`, `yourdfpy`, `trimesh` and `fast_simplification`:

```bash
python cad/sim/build_robot.py fourbar
```

3. Gazebo run test, in an environment with gz-sim 8 (here: WSL Ubuntu + a conda-forge env, `micromamba create -p ~/mm/gz -c conda-forge gz-sim8 ruby`). Then rerun step 2 so `validation.json` picks up the result; it is FRESH only if it ran on the current `model.urdf`:

```bash
micromamba run -p ~/mm/gz python cad/sim/gz_check.py fourbar
```
