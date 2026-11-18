"""Demo driver for the Gazebo model: plays the CAD task sequences (sim/arc_arm_<variant>/task_poses.json) by
streaming joint targets to the JointPositionController topics /arc_arm/<joint>/cmd_pos.

This is the whole "control policy" today: a scripted pose sequence, linearly interpolated in joint space, on top of
per-joint position controllers (velocity mode: motor torque capped at each actuator's peak). No planner, no
collision avoidance beyond the CAD-verified task poses, no grasp logic (the Gazebo world has no donut/pipe).

Start Gazebo first (GUI):
    GZ_SIM_RESOURCE_PATH=<repo>/sim gz sim -r <repo>/sim/arc_arm_fourbar/worlds/arc_arm.sdf
then, in the same gz-sim environment:
    python cad/sim/gz_demo.py [variant] [--seq donut|pipe|both] [--loops N] [--step-deg 6]
"""
import argparse
import json
import os
import subprocess
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ACT = ("shoulder", "elbow", "wrist_pitch", "wrist_roll", "gripper")


def publish(q_deg):
    """Send all five targets at once (one gz CLI process per joint, in parallel)."""
    ps = [subprocess.Popen(["gz", "topic", "-t", "/arc_arm/%s/cmd_pos" % j, "-m", "gz.msgs.Double",
                            "-p", "data: %.6f" % (q_deg[j] * 3.141592653589793 / 180.0)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for j in ACT]
    for p in ps:
        p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", nargs="?", default="fourbar")
    ap.add_argument("--seq", default="both", choices=("donut", "pipe", "both"))
    ap.add_argument("--loops", type=int, default=1)
    ap.add_argument("--step-deg", type=float, default=6.0, help="largest joint change per interpolation step")
    ap.add_argument("--hold-s", type=float, default=1.0, help="pause at each task pose")
    a = ap.parse_args()
    tp = json.load(open(os.path.join(REPO, "sim", "arc_arm_%s" % a.variant, "task_poses.json"), encoding="utf-8"))
    seqs = ["donut", "pipe"] if a.seq == "both" else [a.seq]
    cur = dict(tp["poses"]["STOW"]["joints_deg"])
    print("moving to STOW")
    publish(cur)
    time.sleep(3.0)
    for _ in range(a.loops):
        for s in seqs:
            print("== sequence", s)
            for name in tp["sequences"][s]:
                tgt = tp["poses"][name]["joints_deg"]
                n = max(1, int(max(abs(tgt[j] - cur[j]) for j in ACT) / a.step_deg + 0.999))
                print("  %-18s jaw %5.1f mm  (%d steps)" % (name, tp["poses"][name]["jaw_mm"], n))
                for k in range(1, n + 1):
                    publish({j: cur[j] + (tgt[j] - cur[j]) * k / n for j in ACT})
                cur = dict(tgt)
                time.sleep(a.hold_s)
    print("done")


if __name__ == "__main__":
    main()
