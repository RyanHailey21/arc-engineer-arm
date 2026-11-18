"""Demo driver for the Gazebo model: plays the CAD task sequences (sim/arc_arm_<variant>/task_poses.json).

Control stack (cad/sim/joint_command.py), the same shape as on the real arm:
  host: task pose sequence -> minimum-jerk move per pose pair, timed by the joint speed limits
        -> setpoints streamed at a fixed rate (default 100 Hz), clamped to the joint limits
  sim:  per-joint JointPositionControllers (velocity mode, torque capped at each actuator's peak)
No planner beyond the CAD-verified task poses, no collision avoidance, no grasping (the Gazebo world has no donut
or pipe). After each move it prints the tracking error read back from /joint_state.

Start Gazebo first (GUI):
    GZ_SIM_RESOURCE_PATH=<repo>/sim gz sim -r <repo>/sim/arc_arm_fourbar/worlds/arc_arm.sdf
then, in the same gz-sim environment (needs gz-transport13-python + gz-msgs10-python):
    python cad/sim/gz_demo.py [variant] [--seq donut|pipe|both] [--loops N] [--rate 100] [--speed 0.5]
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from joint_command import ACT, REPO, GazeboCommander, stream_move  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", nargs="?", default="fourbar")
    ap.add_argument("--seq", default="both", choices=("donut", "pipe", "both"))
    ap.add_argument("--loops", type=int, default=1)
    ap.add_argument("--rate", type=float, default=100.0, help="setpoint streaming rate (Hz)")
    ap.add_argument("--speed", type=float, default=0.5, help="fraction of each joint's speed limit")
    ap.add_argument("--hold-s", type=float, default=0.5, help="pause at each task pose")
    a = ap.parse_args()
    tp = json.load(open(os.path.join(REPO, "sim", "arc_arm_%s" % a.variant, "task_poses.json"), encoding="utf-8"))
    cmd = GazeboCommander(a.variant)
    t_wait = time.time()
    while len(cmd.state_deg()) < len(ACT):
        if time.time() - t_wait > 10:
            sys.exit("no joint_state from Gazebo - is the world running?")
        time.sleep(0.1)
    cur = cmd.state_deg()
    seqs = ["donut", "pipe"] if a.seq == "both" else [a.seq]
    plan = ["STOW"] + [p for _ in range(a.loops) for s in seqs for p in tp["sequences"][s]]
    t_all = time.perf_counter()
    for name in plan:
        tgt = tp["poses"][name]["joints_deg"]
        T, hz = stream_move(cmd, cur, tgt, rate_hz=a.rate, speed_frac=a.speed)
        time.sleep(a.hold_s)
        q = cmd.state_deg()
        err = max(abs(q[j] - cmd.clamp(tgt)[j]) for j in ACT)
        print("%-18s jaw %5.1f mm  move %4.2f s at %5.1f Hz  max tracking error after hold %.2f deg"
              % (name, tp["poses"][name]["jaw_mm"], T, hz, err), flush=True)
        cur = dict(tgt)
    print("done: %d moves in %.1f s" % (len(plan), time.perf_counter() - t_all))
    cmd.close()


if __name__ == "__main__":
    main()
