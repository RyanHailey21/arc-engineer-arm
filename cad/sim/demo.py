"""Task-sequence demo on either simulator: plays the CAD task sequences (sim/arc_arm_<variant>/task_poses.json)
through the joint command interface (cad/sim/joint_command.py).

  host: task pose sequence -> minimum-jerk move per pose pair, timed by the joint speed limits
        -> position setpoints streamed at a fixed rate (default 100 Hz), clamped to the joint limits
  backend:
    mujoco  native viewer on Windows/Linux/macOS; position actuators (kp/kv = the DM-J4340 MIT-mode law)
    gazebo  Gazebo Harmonic over gz-transport (start the world first, see sim/README.md)
No planner beyond the CAD-verified task poses, no collision avoidance, no grasping.

    python cad/sim/demo.py --backend mujoco [--seq donut|pipe|both] [--loops N] [--rate 100] [--speed 0.5]
    python cad/sim/demo.py --backend gazebo ...
MuJoCo needs: pip install mujoco. Gazebo needs gz-transport13-python + gz-msgs10-python in the gz-sim environment.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joint_command import ACT, REPO, stream_move  # noqa: E402


def main(default_backend="mujoco"):
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", nargs="?", default="fourbar")
    ap.add_argument("--backend", default=default_backend, choices=("mujoco", "gazebo"))
    ap.add_argument("--scene", default="free", choices=("free", "pick"),
                    help="MuJoCo only: free = no field station (whole sequences); pick = donut-pick station")
    ap.add_argument("--seq", default="both", choices=("donut", "pipe", "both"))
    ap.add_argument("--loops", type=int, default=1)
    ap.add_argument("--rate", type=float, default=100.0, help="setpoint streaming rate (Hz)")
    ap.add_argument("--speed", type=float, default=0.5, help="fraction of each joint's speed limit")
    ap.add_argument("--hold-s", type=float, default=0.5, help="pause at each task pose")
    ap.add_argument("--exit", action="store_true", help="MuJoCo: close the viewer when done (default: leave it open)")
    a = ap.parse_args()
    tp = json.load(open(os.path.join(REPO, "sim", "arc_arm_%s" % a.variant, "task_poses.json"), encoding="utf-8"))
    if a.backend == "mujoco":
        from joint_command import MujocoCommander
        cmd = MujocoCommander(a.variant, scene=a.scene)
    else:
        from joint_command import GazeboCommander
        cmd = GazeboCommander(a.variant)
    t_wait = time.time()
    while len(cmd.state_deg()) < len(ACT):
        if time.time() - t_wait > 10:
            sys.exit("no joint state from %s" % a.backend)
        time.sleep(0.1)
    cur = cmd.state_deg()
    seqs = ["donut", "pipe"] if a.seq == "both" else [a.seq]
    plan = ["STOW"] + [p for _ in range(a.loops) for s in seqs for p in tp["sequences"][s]]
    t_all = time.perf_counter()
    for name in plan:
        if hasattr(cmd, "running") and not cmd.running():
            print("viewer closed")
            break
        tgt = tp["poses"][name]["joints_deg"]
        T, hz = stream_move(cmd, cur, tgt, rate_hz=a.rate, speed_frac=a.speed)
        time.sleep(a.hold_s)
        q = cmd.state_deg()
        err = max(abs(q[j] - cmd.clamp(tgt)[j]) for j in ACT)
        print("%-18s jaw %5.1f mm  move %4.2f s at %5.1f Hz  max tracking error after hold %.2f deg"
              % (name, tp["poses"][name]["jaw_mm"], T, hz, err), flush=True)
        cur = dict(tgt)
    print("done: %d moves in %.1f s (%s)" % (len(plan), time.perf_counter() - t_all, a.backend), flush=True)
    if a.backend == "mujoco" and not a.exit:
        print("viewer stays open; close it to exit", flush=True)
        while cmd.running():
            time.sleep(0.2)
    cmd.close()


if __name__ == "__main__":
    main()
