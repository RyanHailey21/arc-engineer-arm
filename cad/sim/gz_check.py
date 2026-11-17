"""Run-test the Gazebo (gz-sim 8 / Harmonic) package: load the world headless, command every FK reference pose
through the JointPositionController topics, read /joint_state back and check
  - each actuated joint reaches its command (tracking),
  - each passive joint follows its <mimic> leader (multiplier * leader),
  - no NaN / runaway state.
Writes sim/arc_arm_<variant>/gazebo_validation.json.

Runs inside an environment that has gz-sim 8 (here: WSL + micromamba conda-forge env ~/mm/gz):
    micromamba run -p ~/mm/gz python cad/sim/gz_check.py [variant]
Only the gz CLI is used (no gz python bindings needed).
"""
import json
import math
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
VAR = (ARGS[0] if ARGS else "fourbar").lower()
EMPTY = "--empty" in sys.argv   # ground plane + arm only: tests the model without field contact
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SIM = os.path.join(REPO, "sim")
ROOT = os.path.join(SIM, "arc_arm_%s" % VAR)
MODEL = "arc_arm_%s" % VAR
WORLD = os.path.join(ROOT, "worlds", "arc_arm.sdf")
JS_TOPIC = "/world/arc_arm/model/%s/joint_state" % MODEL
ACT = ("shoulder", "elbow", "wrist_pitch", "wrist_roll", "gripper")
TRACK_TOL_DEG = 1.5      # actuated joint vs command at steady state
MIMIC_TOL_DEG = 0.5      # follower vs multiplier * leader
SETTLE_S = 25.0          # wall-clock limit per pose

ENV = dict(os.environ, GZ_SIM_RESOURCE_PATH=SIM)


def gz(*args, timeout=20):
    return subprocess.run(("gz",) + args, env=ENV, capture_output=True, text=True, timeout=timeout).stdout


def joint_state():
    """-> {joint: position rad} from one /joint_state message (protobuf text format)."""
    txt = gz("topic", "-e", "-n", "1", "-t", JS_TOPIC)
    out = {}
    txt = txt.split("\nheader {")[0] if txt.count("header {") > 1 else txt   # gz may print >1 message
    for blk in re.split(r"\njoint \{", "\n" + txt)[1:]:
        name = re.search(r'name: "([^"]+)"', blk)
        a = blk.find("axis1 {")   # axis1 holds nested xyz {...}, so search for position after it, not within [^}]
        pos = re.search(r"\n\s*position: ([-\d.eE+naif]+)", blk[a:]) if a >= 0 else None
        if name:
            out[name.group(1)] = float(pos.group(1)) if pos else 0.0
    return out


def command(q_deg):
    for j in ACT:
        gz("topic", "-t", "/arc_arm/%s/cmd_pos" % j, "-m", "gz.msgs.Double", "-p", "data: %.6f" % math.radians(q_deg[j]))


def main():
    mimic = {}
    for J in ET.parse(os.path.join(ROOT, "model.urdf")).getroot().iter("joint"):
        m = J.find("mimic")
        if m is not None:
            mimic[J.get("name")] = (m.get("joint"), float(m.get("multiplier", 1)), float(m.get("offset", 0)))
    poses = json.load(open(os.path.join(ROOT, "fk_reference.json"), encoding="utf-8"))

    world = WORLD
    if EMPTY:
        w = open(WORLD, encoding="utf-8").read()
        w = re.sub(r"\s*<!--[^>]*-->\s*<model name=\"chassis_placeholder\">.*?</model>", "", w, flags=re.S)
        w = re.sub(r"\s*<!--[^>]*-->\s*<model name=\"lower_tier\">.*?</model>", "", w, flags=re.S)
        assert "lower_tier" not in w and "chassis_placeholder" not in w
        world = os.path.join(ROOT, "worlds", "_empty_check.sdf")
        open(world, "w", encoding="utf-8").write(w)
    srv = subprocess.Popen(["gz", "sim", "-s", "-r", "-v", "2", world], env=ENV,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    res = dict(variant=VAR, gz_version=gz("sim", "--versions").strip(), world="ground only" if EMPTY else os.path.relpath(WORLD, REPO), poses=[])
    try:
        t0 = time.time()
        while JS_TOPIC not in gz("topic", "-l"):
            if time.time() - t0 > 60 or srv.poll() is not None:
                raise RuntimeError("joint_state topic never appeared; server exited=%s" % srv.poll())
            time.sleep(0.5)
        res["load_s"] = round(time.time() - t0, 1)
        js = joint_state()
        res["joints_reported"] = sorted(js)
        res["missing_joints"] = sorted((set(ACT) | set(mimic)) - set(js))
        for p in poses:
            q = p["joints_deg"]
            t1 = time.time()
            # re-publish until the arm settles: the CLI publisher can race the subscriber on the first message
            while True:
                command(q)
                time.sleep(1.0)
                js = joint_state()
                trk = {j: math.degrees(js.get(j, float("nan"))) - q[j] for j in ACT}
                if all(abs(e) < TRACK_TOL_DEG for e in trk.values()) or time.time() - t1 > SETTLE_S:
                    break
            mim = {}
            for f, (lead, mult, off) in mimic.items():
                if f in js and lead in js:
                    mim[f] = math.degrees(js[f] - (mult * js[lead] + off))
            finite = all(math.isfinite(v) for v in js.values())
            ok = finite and all(abs(e) < TRACK_TOL_DEG for e in trk.values()) and \
                all(abs(e) < MIMIC_TOL_DEG for e in mim.values()) and len(mim) == len(mimic)
            res["poses"].append(dict(pose=p["pose"], settle_s=round(time.time() - t1, 1),
                                     track_err_deg={k: round(v, 3) for k, v in trk.items()},
                                     max_mimic_err_deg=round(max((abs(v) for v in mim.values()), default=float("nan")), 4),
                                     worst_mimic=max(mim, key=lambda k: abs(mim[k])) if mim else None,
                                     finite=finite, ok=ok))
            print("%-20s settle %5.1fs  max track %.3f deg  max mimic %.4f deg  %s" % (
                p["pose"], res["poses"][-1]["settle_s"], max(abs(v) for v in trk.values()),
                res["poses"][-1]["max_mimic_err_deg"], "ok" if ok else "FAIL"))
    finally:
        srv.terminate()
        if EMPTY:
            os.remove(world)
        try:
            srv.wait(10)
        except subprocess.TimeoutExpired:
            srv.kill()
    res["ok"] = bool(res["poses"]) and not res["missing_joints"] and all(p["ok"] for p in res["poses"])
    res["tolerances_deg"] = dict(track=TRACK_TOL_DEG, mimic=MIMIC_TOL_DEG)
    json.dump(res, open(os.path.join(ROOT, "gazebo_validation%s.json" % ("_empty" if EMPTY else "")), "w", encoding="utf-8"), indent=1)
    print("GZ_CHECK %s: %s" % (VAR, "PASS" if res["ok"] else "FAIL"))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
