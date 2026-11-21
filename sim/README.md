# ARC S2 Engineer arm: MuJoCo simulation

`arc_arm_fourbar/` holds a **MuJoCo** model of the arm with the four-bar gripper, generated from the CAD model.
Geometry, masses and inertias come straight from `cad/` (the `arm_model` package). The model reproduces the CAD
forward kinematics to **0.0004 mm** at seven task poses. Gazebo is not used; it was dropped as a requirement.

**Video:** [`media/arc_arm_tasks_realtime.mp4`](media/arc_arm_tasks_realtime.mp4) shows both tasks at the
**real servo speed**: every joint moves at its full rated speed, and the video plays in real time. It is
80.7 s long (4.7 MB).

## Files

| File | For |
|---|---|
| `arc_arm.xml` | Robot: actuators (force-limited to each servo's stall torque), the gripper's opening spring, keyframes for every task pose |
| `scene.xml` | Robot, floor, chassis-deck placeholder, ARC lower tier, donut and pipe |
| `tasks.xml` | Full-task scene: the arm on an x/y chassis, and the four CAD field stations |
| `arc_arm.urdf` | Plain URDF (relative mesh paths), for ROS tools, yourdfpy and MuJoCo's URDF importer; it also supplies the joint speed limits |
| `task_poses.json`, `task_field.json` | The 14 CAD task poses with the donut and pipe sequences, and the field stations |
| `meshes/visual/*.stl`, `meshes/collision/*.stl` | Per-link visual meshes, and per-part collision meshes (MuJoCo uses their convex hulls) |
| `robot_spec.json`, `fk_reference.json` | The generator's input (frames, masses, inertias, joints, limits, actuators, spring), and the CAD body placements used for validation |
| `validation.json` / `.md` | Results of the checks below |
| `task_run.json`, `task_log.npz` | The last full task run: actuation (peak and RMS torque, speed), grasp loads, end states, and a per-tick log for the plots |

## Run

```bash
python -m mujoco.viewer --mjcf=sim/arc_arm_fourbar/scene.xml       # pick a keyframe and drive the 5 actuators
python cad/sim/tasks.py --task both                                 # both tasks in the viewer
python cad/sim/tasks.py --task both --no-viewer                     # headless; writes task_run.json
python cad/sim/tasks.py --task both --no-viewer --speed 1.0 --video sim/media/arc_arm_tasks_realtime.mp4 --realtime
```

- `--speed` is the fraction of each joint's speed limit. The default is 0.5; it is what the verification runs use,
  and `cad/docs/paper` and `cad/tools/grip_hold.py` read its results.
- `--speed 1.0` runs every joint at the servo's full rated speed. The pipe swing to the chute pose is always done at
  a quarter of that. The 500 mm pipe's inertia otherwise pushes the wrist servo near stall, so a real program would
  slow that move too.
- `--video` writes an MP4: 1280×720, 30 fps, captions per phase. It needs `imageio-ffmpeg`. Add `--realtime` to play
  the chassis drives at 1× too; without it they play at 2×.
- `cad/sim/demo.py` plays the CAD pose sequences in the viewer, with no field.

**The tasks:**
- **Donut:** slide in behind the pole, close the jaws, and lift up and off the zig-zag pole along the CAD lift path
  (chassis strafe up to ±44 mm, wrist roll up to 47°). Then drive to the scoring platform, lower the donut, release
  it, retreat and stow.
- **Pipe:** grip the pipe and lift it out of the bucket. Swing it to the chute pose, drive it 300 mm into the chute,
  release it and stow.

**The grasp is kinematic.** When the jaws close at a grasp pose with the object within 8 mm of the TCP, a weld locks
the object to the head. The weld's constraint force is the wrench the jaws must supply, which `grip_hold.py` uses.

**Last run** (default speed): 85.6 s simulated. The donut lands on the platform and the pipe ends 297 mm past the wall
face. Grasp error is 1.6 mm for the donut and 0.6 mm for the pipe. There are no robot-to-field contacts, and tracking
stays within 0.65°.

## Joints

Joint values are the CAD angles: radians in MuJoCo, degrees in `cad/`.

| Joint | Actuator | Limits (deg) | Meaning |
|---|---|---|---|
| `shoulder` | STS3215 + 3:1 spur stage, 8.4 N·m stall | 0 … 180 | upper-arm angle th1 |
| `elbow` | STS3215 + 3:1 spur stage, 8.4 N·m stall | −86 … 51 | absolute forearm angle th2, driven through the crank and rod AB |
| `wrist_pitch` | STS3215, 2.94 N·m stall | −30 … 120 | gripper pitch (absolute: the level member stays level) |
| `wrist_roll` | STS3215, 2.94 N·m stall | −95 … 95 | roll about the gripper axis |
| `gripper` | STS3215, 2.94 N·m stall | 0 … 63.2 | drive-link angle from the pipe grip (0 = 13.8 mm, 54.6 = donut 100 mm, 63.2 = open 112 mm) |

Twelve passive joints follow the actuated ones as MuJoCo joint-equality constraints:
- the rods, rocker and crank;
- the level member;
- the idler links;
- the sector-gear mirror;
- the parallel jaws.

The opening torsion spring (McMaster 9271K56) is a joint spring on `gripper`.

## Validation (`validation.json`)

| Check | Result |
|---|---|
| URDF and MJCF forward kinematics vs CAD (7 poses, every link and the TCP) | max 0.0004 mm / 0.000°; equality residual 0 |
| Hold STOW under gravity for 3 s | tracking 0.48° max; no NaN |
| Power-off release (gripper actuator off at the pipe grip) | jaws open 10 mm in 0.04 s, 90 % in 0.14 s (ARC rule: within 1 s) |
| Scene and URDF import | both compile |

**Limits of the model:**
- **No self-collision.** Self-interference is verified in CAD (`cad/check_interference.py`).
- **The servo back-drive is an estimate** (0.05 N·m friction) until it is bench-measured, and the release time
  depends on it.
- **Estimated dynamics.** Rotor armatures, damping and controller gains are estimates.
- **No mechanical stops.** The software joint limits cover the task poses.
- **Placeholder field items.** The zig-zag pole is the CAD placeholder.
- **Ideal drivetrain.** The chassis slides are ideal position servos.

## Regenerate

From the repo root, in this order:
1. `python -I cad/tools/run.py --grip FOURBAR cad/sim/export_robot.py`: the CAD export.
2. `python cad/sim/build_robot.py fourbar`: build and validate.
3. `python cad/sim/build_tasks.py fourbar`: the task scene.
4. `python cad/sim/tasks.py --task both --no-viewer --log sim/arc_arm_fourbar/task_log.npz --snap cad/docs/paper/fig`:
   the task run, plus the paper's snapshots.

Steps 2 to 4 need a Python with `mujoco`, `yourdfpy`, `trimesh`, `fast_simplification` and `imageio-ffmpeg`.
