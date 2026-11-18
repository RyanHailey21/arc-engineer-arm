"""Run-test the Gazebo (gz-sim 8 / Harmonic) package: load the world headless, command every FK reference pose
through the JointPositionController topics, read /joint_state back and check
  - each actuated joint reaches its command (tracking),
  - each passive joint follows its <mimic> leader (multiplier * leader),
  - the gripper TCP (from the head link pose) matches the CAD forward kinematics (fk_reference.json),
  - no NaN / runaway state,
  - power-off release: with the gripper controller removed, the spring opens the jaws (release_test).
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
MIMIC_TOL_DEG = 1.0      # follower vs multiplier * leader (bullet gear constraints are slightly soft under load)
TCP_TOL_MM = 3.0         # gripper TCP vs CAD forward kinematics (fk_reference.json)
SETTLE_S = 25.0          # wall-clock limit per pose

ENV = dict(os.environ, GZ_SIM_RESOURCE_PATH=SIM)


def gz(*args, timeout=20):
    return subprocess.run(("gz",) + args, env=ENV, capture_output=True, text=True, timeout=timeout).stdout


def joint_state():
    """-> {joint: position rad} from one /joint_state message (protobuf text format)."""
    txt = gz("topic", "-e", "-n", "1", "-t", JS_TOPIC)
    txt = txt.split("\nheader {")[0] if txt.count("header {") > 1 else txt   # gz may print >1 message
    return parse_js(txt)


def parse_js(txt):
    """-> {joint: position rad} from the text of ONE joint_state message."""
    out = {}
    for blk in re.split(r"\njoint \{", "\n" + txt)[1:]:
        name = re.search(r'name: "([^"]+)"', blk)
        a = blk.find("axis1 {")   # axis1 holds nested xyz {...}, so search for position after it, not within [^}]
        pos = re.search(r"\n\s*position: ([-\d.eE+naif]+)", blk[a:]) if a >= 0 else None
        if name:
            out[name.group(1)] = float(pos.group(1)) if pos else 0.0
    return out


def link_pose(name):
    """-> (position m, quaternion xyzw) of a link from /world/arc_arm/pose/info (world = robot frame: model at origin)."""
    txt = gz("topic", "-e", "-n", "1", "-t", "/world/arc_arm/pose/info")
    i = txt.find('name: "%s"' % name)
    blk = txt[i:txt.find("\npose {", i)]

    def g(sec, k):   # protobuf text omits zero-valued fields, so a missing field is 0
        b = re.search(r"%s \{([^}]*)\}" % sec, blk)
        m = re.search(r"(?:^|\s)%s: ([-\d.eE+]+)" % k, b.group(1)) if b else None
        return float(m.group(1)) if m else 0.0
    return [g("position", k) for k in "xyz"], [g("orientation", k) for k in "xyzw"]


def qrot(q, v):
    x, y, z, w = q
    u = (x, y, z)
    cross = lambda a, b: (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    t = [2 * c for c in cross(u, v)]
    c2 = cross(u, t)
    return [v[k] + w * t[k] + c2[k] for k in range(3)]


def command(q_deg):
    for j in ACT:
        gz("topic", "-t", "/arc_arm/%s/cmd_pos" % j, "-m", "gz.msgs.Double", "-p", "data: %.6f" % math.radians(q_deg[j]))


def release_test(spec):
    """Power-off release in Gazebo (free world): a temporary copy of the model WITHOUT the gripper position controller
    (the servo unpowered), jaws starting at the pipe grip (gripper q = 0). The world starts paused; joint_state is streamed with
    sim-time stamps while it runs, and the torsion spring alone must open the jaws.
    Caveat: bullet-featherstone applies joint spring and (viscous) damping but not joint friction or rotor armature,
    so here the unpowered servo's back-drive is the URDF damping 0.05 N*m*s/rad; MuJoCo uses 0.05 N*m Coulomb
    friction + 0.002 kg*m^2 armature. Both are estimates until the servo is bench-measured."""
    import shutil
    import tempfile
    fb, th_ref = spec["fb"], math.radians(spec["theta_ref_deg"])
    q_open = math.radians(spec["limits_deg"]["gripper"][1])

    def gap(q):                                  # pad-arc gap (mm) for a gripper joint value (as build_robot.py)
        return 2 * (fb["YG"] + fb["L"] * math.sin(th_ref + q) - fb["E"])
    tmp = tempfile.mkdtemp(prefix="gzrel_")
    md = os.path.join(tmp, MODEL)
    os.makedirs(md)
    os.symlink(os.path.join(ROOT, "meshes"), os.path.join(md, "meshes"))
    shutil.copy(os.path.join(ROOT, "model.config"), md)
    t = ET.parse(os.path.join(ROOT, "model.urdf"))
    removed = 0
    for g in t.getroot().iter("gazebo"):
        for p in list(g.findall("plugin")):
            jn = p.find("joint_name")
            if jn is not None and jn.text == "gripper":
                g.remove(p)
                removed += 1
    assert removed == 1, "gripper controller not found"
    t.write(os.path.join(md, "model.urdf"), encoding="utf-8", xml_declaration=True)
    env = dict(ENV, GZ_SIM_RESOURCE_PATH=tmp)
    # free world (no field): the joints start at 0, which leaves the arm stretched forward with the TCP at z 195 -
    # below the lower tier's top (210) in the pick-station world, so the jaws would open against the tier
    free = os.path.join(ROOT, "worlds", "arc_arm_free.sdf")
    srv = subprocess.Popen(["gz", "sim", "-s", "-v", "2", free], env=env,           # no -r: starts paused
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        t0 = time.time()
        while JS_TOPIC not in gz("topic", "-l"):
            if time.time() - t0 > 60 or srv.poll() is not None:
                raise RuntimeError("release test: joint_state topic never appeared")
            time.sleep(0.5)
        echo = subprocess.Popen(["gz", "topic", "-e", "-t", JS_TOPIC, "-n", "4000"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        time.sleep(1.0)
        gz("service", "-s", "/world/arc_arm/control", "--reqtype", "gz.msgs.WorldControl", "--reptype",
           "gz.msgs.Boolean", "--timeout", "3000", "--req", "pause: false")
        out, _ = echo.communicate(timeout=180)
    finally:
        srv.terminate()
        try:
            srv.wait(10)
        except subprocess.TimeoutExpired:
            srv.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    series = []
    for msg in re.split(r"(?m)^header \{", out)[1:]:
        st = re.search(r"stamp \{([^}]*)\}", msg)
        sec = re.search(r"(?:^|\s)sec: (\d+)", st.group(1)) if st else None   # not the tail of "nsec:"
        nsec = re.search(r"nsec: (\d+)", st.group(1)) if st else None
        ts = (int(sec.group(1)) if sec else 0) + (int(nsec.group(1)) if nsec else 0) * 1e-9
        series.append((ts, parse_js(msg).get("gripper", 0.0)))
    series.sort()
    if not series:
        return dict(ok=False, note="no joint_state messages captured")
    ts0, q0 = series[0]
    t10 = next((ts - ts0 for ts, q in series if gap(q) >= gap(q0) + 10.0), None)
    t90 = next((ts - ts0 for ts, q in series if q - q0 >= 0.9 * (q_open - q0)), None)
    curve, nxt = [], 0.0                        # pad gap every 0.25 s of sim time
    for ts, q in series:
        if ts - ts0 >= nxt:
            curve.append((round(ts - ts0, 2), round(gap(q), 1)))
            nxt += 0.25
    return dict(start_gap_mm=round(gap(q0), 1), end_gap_mm=round(gap(series[-1][1]), 1),
                full_open_gap_mm=round(gap(q_open), 1), sim_span_s=round(series[-1][0] - ts0, 3), samples=len(series),
                t_open_10mm_s=None if t10 is None else round(t10, 3), t_90pct_open_s=None if t90 is None else round(t90, 3),
                gap_curve_s_mm=curve,
                ok=t10 is not None and t10 < 1.0,   # same criterion as MuJoCo's power-off release (ARC: within 1 s)
                note="gripper controller removed (servo unpowered); torsion spring against the URDF joint damping "
                     "(0.05 N*m*s/rad, viscous). MuJoCo models the same unmeasured servo back-drive as 0.05 N*m "
                     "Coulomb friction + rotor armature instead; neither is bench-measured. ARC rule: release within 1 s.")


def main():
    mimic = {}
    for J in ET.parse(os.path.join(ROOT, "model.urdf")).getroot().iter("joint"):
        m = J.find("mimic")
        if m is not None:
            mimic[J.get("name")] = (m.get("joint"), float(m.get("multiplier", 1)), float(m.get("offset", 0)))
    poses = json.load(open(os.path.join(ROOT, "fk_reference.json"), encoding="utf-8"))
    spec = json.load(open(os.path.join(ROOT, "robot_spec.json"), encoding="utf-8"))
    F = next(l for l in spec["links"] if l["name"] == "head")["frame_in_cad_mm"]
    tcp_head_m = [(spec["tcp_in_gripper_frame_mm"][k] - F[k]) / 1000.0 for k in range(3)]   # TCP in the head link frame

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
    import hashlib
    urdf_sha = hashlib.sha256(open(os.path.join(ROOT, "model.urdf"), "rb").read().replace(b"\r\n", b"\n")).hexdigest()   # EOL-neutral
    res = dict(variant=VAR, model_urdf_sha256=urdf_sha, gz_version=gz("sim", "--versions").strip(), world="ground only" if EMPTY else os.path.relpath(WORLD, REPO), poses=[])
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
            hp, hq = link_pose("head")
            tcp = [1000.0 * (hp[k] + qrot(hq, tcp_head_m)[k]) for k in range(3)]
            tcp_err = math.dist(tcp, p["tcp_mm"])
            finite = all(math.isfinite(v) for v in js.values())
            ok = finite and all(abs(e) < TRACK_TOL_DEG for e in trk.values()) and \
                all(abs(e) < MIMIC_TOL_DEG for e in mim.values()) and len(mim) == len(mimic) and tcp_err < TCP_TOL_MM
            res["poses"].append(dict(pose=p["pose"], settle_s=round(time.time() - t1, 1),
                                     track_err_deg={k: round(v, 3) for k, v in trk.items()},
                                     max_mimic_err_deg=round(max((abs(v) for v in mim.values()), default=float("nan")), 4),
                                     worst_mimic=max(mim, key=lambda k: abs(mim[k])) if mim else None,
                                     tcp_mm=[round(v, 2) for v in tcp], tcp_err_mm=round(tcp_err, 3),
                                     finite=finite, ok=ok))
            print("%-20s settle %5.1fs  max track %.3f deg  max mimic %.4f deg  TCP err %.2f mm  %s" % (
                p["pose"], res["poses"][-1]["settle_s"], max(abs(v) for v in trk.values()),
                res["poses"][-1]["max_mimic_err_deg"], tcp_err, "ok" if ok else "FAIL"))
    finally:
        srv.terminate()
        if EMPTY:
            os.remove(world)
        try:
            srv.wait(10)
        except subprocess.TimeoutExpired:
            srv.kill()
    res["power_off_release"] = rel = release_test(spec)
    print("power-off release: start gap %s mm, open 10 mm in %s s, 90%% open in %s s, end gap %s mm  %s" % (
        rel.get("start_gap_mm"), rel.get("t_open_10mm_s"), rel.get("t_90pct_open_s"), rel.get("end_gap_mm"),
        "ok" if rel["ok"] else "FAIL"))
    res["ok"] = bool(res["poses"]) and not res["missing_joints"] and all(p["ok"] for p in res["poses"]) and rel["ok"]
    res["tolerances"] = dict(track_deg=TRACK_TOL_DEG, mimic_deg=MIMIC_TOL_DEG, tcp_mm=TCP_TOL_MM)
    json.dump(res, open(os.path.join(ROOT, "gazebo_validation%s.json" % ("_empty" if EMPTY else "")), "w", encoding="utf-8"), indent=1)
    print("GZ_CHECK %s: %s" % (VAR, "PASS" if res["ok"] else "FAIL"))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
