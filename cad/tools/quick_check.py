# -*- coding: utf-8 -*-
"""
Quick check (target < 30 s incl. the ~14 s model build): run after every design edit; the full checks
(check_interference.py, FEA) are for milestones.

    set GRIP=FOURBAR (or SCREW)
    "%LOCALAPPDATA%\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad/tools/quick_check.py

Checks, in fail-fast order of usefulness:
  1. envelopes   - every cad/envelopes/*.toml keep-out box vs the arm's check solids at its poses
  2. interfaces  - both sides of every cad/interfaces/*.toml really have the specified holes
  3. self-hit    - gripper bodies against each other over the jaw stroke, roll 0 and 90
  4. mass/torque - gripper and arm mass, static joint torques at every task pose vs actuator ratings
  5. catalogue   - purchased-part mass per catalogue key == units x catalogue mass; every src is a key
                   (tools/catalogue_mass.py; a missing key weighs 0 g, a split motor counted twice doubles)
  6. level-keep  - parallelogram stage 2 closes at every task pose / lift sample and stays clear of its dead
                   points there and at the elbow limits (tools/check_level_keeping.py checks 1+2; its sweep
                   clearance, check 3, is a milestone check)
  7. seating     - every screw, pin and washer sits in a coaxial hole and its head / faces bear on a part
                   (tools/check_seated.py; catches floating fasteners, e.g. a pattern offset applied twice)
  8. bloat       - informational: counts from tools/bloat_report.py (dead code, orphan params/catalogue keys,
                   scratch files); never fails the check.  The full report: python -I cad/tools/bloat_report.py
  9. fingerprint - geometry vs cad/tests/fingerprints/<variant>.json (CHANGED is expected after a real edit)
-> cad/out/<variant>/quick.json, a manifest entry, one summary line per check, and the FRESH/STALE status of
   every recorded check (full interference, holes, engagement ...) against the current design inputs.
"""
import itertools
import json
import os
import sys
import time
import tomllib

T0 = time.time()
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
import FreeCAD as App      # noqa: E402
import Part                # noqa: E402
import arm_model as M      # noqa: E402
import catalogue_mass      # noqa: E402
import check_interfaces    # noqa: E402
import check_level_keeping  # noqa: E402
os.environ["QC_IMPORT"] = "1"   # import the seating check without running its main()
import check_seated        # noqa: E402
import field               # noqa: E402
import fingerprint        # noqa: E402
import params              # noqa: E402

V = App.Vector
VARIANT = M.VARIANT.lower()
GRIPPER_BODIES = {"GRIPPER", "HEAD", "JAW_L", "JAW_R", "SCREW", "MGEAR", "LK_LD", "LK_LI", "LK_RD", "LK_RI"}
# static holding limit per joint (N*m): every STS3215 joint is held to hold_frac of stall (params/actuators.toml,
# report R4); J1/J2: GEARED through the 3:1 spur stage, DIRECT the DM-J4340 at hold_frac of its rated torque
_HOLD = M.STS_R["hold_frac"] * M.STS_R["stall_Nm"]
_BASE = M.BASE_R["ratio"] * M.BASE_R["efficiency"]
_J12 = M.DM_R["hold_frac"] * M.DM_R["rated_Nm"] if M.BASE_DRIVE == "DIRECT" else _HOLD * _BASE
RATED = {"J1": round(_J12, 2), "J2": round(_J12, 2), "J3": round(_HOLD, 2), "J4": round(_HOLD, 2)}
TOL = 0.5                                     # mm^3, same threshold as check_interference.py


def placed(bodies, plc, which, rel=None):
    out = []
    for bn, ps in bodies.items():
        if which == "gripper" and bn not in GRIPPER_BODIES:
            continue
        P_ = plc[bn] if rel is None else rel.multiply(plc[bn])
        for p in ps:
            if not getattr(p, "check", True) or p.chk.isNull():
                continue
            s = p.chk.copy()
            s.Placement = P_.multiply(s.Placement)
            out.append((bn, p.name, s))
    return out


def envelopes(bodies):
    res, ok = [], True
    d = os.path.join(CAD, "envelopes")
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".toml"):
            continue
        for kz in tomllib.load(open(os.path.join(d, fn), "rb"))["keepout"]:
            mn, mx = kz["min"], kz["max"]
            bx = Part.makeBox(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2], V(*mn))
            bb = bx.BoundBox
            for pose in kz["poses"]:
                q, jaw = M.pose_q(pose)
                jaw = kz.get("jaw", jaw)
                plc = M.placements(*q, jaw=jaw)
                rel = None
                if kz["frame"] == "gripper":
                    plc = M.placements(q[0], q[1], q[2], 0.0, jaw=jaw)
                    rel = plc["GRIPPER"].inverse()
                hits = []
                for bn, nm, s in placed(bodies, plc, kz["bodies"], rel):
                    if not s.BoundBox.intersect(bb):
                        continue
                    v = s.common(bx).Volume
                    if v > TOL:
                        hits.append(dict(body=bn, part=nm, mm3=round(v, 1)))
                ok &= not hits
                res.append(dict(envelope=kz["name"], pose=pose, ok=not hits, hits=hits))
                if hits:
                    print("  ENVELOPE %s @ %s: %s" % (kz["name"], pose, ", ".join("%s %.0f" % (h["part"], h["mm3"]) for h in hits[:6])))
    return ok, res


def self_hit(bodies):
    """Gripper bodies against each other over the jaw stroke at roll 0/90.  A pair whose relative placement
    has not changed since it was last computed is not recomputed (most pairs only move with the jaw or roll)."""
    hits, ok = [], True
    q = M.pose_q("DONUT_LIFT")[0]
    parts = [(bn, p) for bn, ps in bodies.items() if bn in GRIPPER_BODIES for p in ps
             if getattr(p, "check", True) and not p.chk.isNull()]
    cache = {}
    for jaw in sorted({M.PIPE_JAW, 40.0, 70.0, 100.0, 112.0}):
        for roll in (0.0, 90.0):
            plc = M.placements(q[0], q[1], q[2], roll, jaw=jaw)
            rels = {}
            for b1, b2 in itertools.combinations(sorted(GRIPPER_BODIES & set(bodies)), 2):
                m = plc[b1].inverse().multiply(plc[b2]).toMatrix()
                rels[(b1, b2)] = tuple(round(x, 6) for x in (m.A11, m.A12, m.A13, m.A14, m.A21, m.A22, m.A23, m.A24,
                                                             m.A31, m.A32, m.A33, m.A34))
            sh = {}
            for (b1, p1), (b2, p2) in itertools.combinations(parts, 2):
                if b1 == b2:
                    continue
                if b1 > b2:
                    (b1, p1), (b2, p2) = (b2, p2), (b1, p1)
                key = (p1.name, p2.name, rels[(b1, b2)])
                if key not in cache:
                    for bn, p in ((b1, p1), (b2, p2)):
                        if (bn, p.name) not in sh:
                            s_ = p.chk.copy()
                            s_.Placement = plc[bn].multiply(s_.Placement)
                            sh[(bn, p.name)] = s_
                    s1, s2 = sh[(b1, p1.name)], sh[(b2, p2.name)]
                    cache[key] = s1.common(s2).Volume if s1.BoundBox.intersect(s2.BoundBox) else 0.0
                v = cache[key]
                if v > TOL:
                    ok = False
                    hits.append(dict(jaw=jaw, roll=roll, a=p1.name, b=p2.name, mm3=round(v, 1)))
    for h in hits[:8]:
        print("  SELF-HIT jaw %.1f roll %.0f: %s / %s %.1f mm3" % (h["jaw"], h["roll"], h["a"], h["b"], h["mm3"]))
    return ok, hits


def mass_torque(bodies):
    mass = {bn: sum(M.part_mass_g(p) for p in ps) for bn, ps in bodies.items()}
    grip = sum(v for k, v in mass.items() if k in GRIPPER_BODIES)
    head = sum(v for k, v in mass.items() if k in GRIPPER_BODIES and k != "GRIPPER")
    rows, worst = [], {}
    for pose in M.POSES:
        q, jaw = M.pose_q(pose)
        pay = 300.0 if pose.startswith(("DONUT_LIFT", "DONUT_PLACE")) else (165.0 if pose.startswith(("PIPE_LIFT", "PIPE_CHUTE")) else 0.0)
        # the donut's centre is at the TCP; the 500 mm pipe hangs from it, so put its mass at its COM (203 mm down
        # the gripper z): that is what loads the wrist pitch once the pipe is swung horizontal for the chute
        arm = field.PIPE_COM_BELOW_TCP if pose.startswith(("PIPE_LIFT", "PIPE_CHUTE")) else None
        tau = M.static_torques(bodies, *q, payload_g=pay, payload_arm=arm, jaw=jaw)
        rows.append(dict(pose=pose, payload_g=pay, tau=[round(t, 2) for t in tau]))
        for j, t in zip(("J1", "J2", "J3", "J4"), tau):
            worst[j] = max(worst.get(j, 0.0), abs(t))
    util = {j: round(worst[j] / RATED[j], 3) for j in RATED}
    ok = all(u <= 1.0 for u in util.values())
    return ok, dict(arm_g=round(sum(v for k, v in mass.items() if k != "GROUND"), 1), past_wrist_g=round(grip, 1),
                    head_g=round(head, 1), worst_static_Nm={k: round(v, 2) for k, v in worst.items()},
                    rated_utilisation=util, poses=rows)


def main():
    bodies = M.build_bodies()
    t_build = time.time() - T0
    summary, data = [], dict(variant=VARIANT)
    t = time.time()
    ok, data["envelopes"] = envelopes(bodies)
    summary.append(("envelopes", ok, "%d pose checks" % len(data["envelopes"]), time.time() - t))
    t = time.time()
    rc = check_interfaces.main()
    data["interfaces"] = json.load(open(os.path.join(CAD, "out", VARIANT, "interfaces.json")))
    summary.append(("interfaces", rc == 0, "%d sides" % len(data["interfaces"]["report"]), time.time() - t))
    t = time.time()
    ok, data["self_hit"] = self_hit(bodies)
    summary.append(("self-hit", ok, "%d overlaps over the jaw stroke" % len(data["self_hit"]), time.time() - t))
    t = time.time()
    ok, data["mass_torque"] = mass_torque(bodies)
    mt = data["mass_torque"]
    summary.append(("mass/torque", ok, "past wrist %.0f g (head %.0f g); worst static J1 %.2f J2 %.2f J3 %.2f N*m" %
                    (mt["past_wrist_g"], mt["head_g"], mt["worst_static_Nm"]["J1"], mt["worst_static_Nm"]["J2"],
                     mt["worst_static_Nm"]["J3"]), time.time() - t))
    t = time.time()
    ok, data["catalogue"] = catalogue_mass.check(bodies, M.CAT, M.part_mass_g)
    cm = data["catalogue"]
    for f in cm["fails"][:8]:
        print("  CATALOGUE %s" % f)
    summary.append(("catalogue", ok, "%d keys, %d purchased units match catalogue mass" % (cm["keys"], cm["units"])
                    if ok else "%d problem(s); first: %s" % (len(cm["fails"]), cm["fails"][0]), time.time() - t))
    t = time.time()
    ok, lk_lines, data["level_keeping"] = check_level_keeping.closure_margins()
    lk = data["level_keeping"]
    for ln in lk_lines:
        if ln.endswith("FAIL"):
            print("  LEVEL-KEEP %s" % ln)
    summary.append(("level-keep", ok, "closure %.0e mm over %d samples; dead-point margin %.1f deg (%s), %.1f at elbow limits"
                    % (lk["closure_mm"], lk["samples"], lk["margin_deg"], lk["margin_at"], lk["limit_margin_deg"]),
                    time.time() - t))
    t = time.time()
    n_f, n_pts, rows, _sk = check_seated.run(bodies)
    for r in rows[:8]:
        print("  SEATING %s" % r)
    summary.append(("seating", not rows, "%d fasteners, %d FAIL%s" % (n_f, len(rows), (": " + rows[0][5:60]) if rows else ""),
                    time.time() - t))
    t = time.time()
    try:
        import bloat_report
        br = bloat_report.scan()
        data["bloat"] = br["counts"]
        note = bloat_report.counts_line(br)[len("BLOAT "):]
    except Exception as e:                    # informational: a broken report must not fail the quick check
        note = "report failed: %s" % e
    summary.append(("bloat", None, note, time.time() - t))
    t = time.time()
    fp = fingerprint.build()
    base = fingerprint.BASE
    if os.path.exists(base):
        d = fingerprint.diff(json.load(open(base)), fp)
        summary.append(("fingerprint", None, "MATCH" if not d else "CHANGED (%d differences; re-record if intended)" % len(d), time.time() - t))
    else:
        summary.append(("fingerprint", None, "no baseline", time.time() - t))
    out = os.path.join(CAD, "out", VARIANT)
    os.makedirs(out, exist_ok=True)
    data["summary"] = [dict(check=a, ok=b, note=c, s=round(e, 1)) for a, b, c, e in summary]
    data["elapsed_s"] = round(time.time() - T0, 1)
    json.dump(data, open(os.path.join(out, "quick.json"), "w"), indent=1)
    allok_ = all(b is not False for _a, b, _c, _e in summary)
    params.record("quick", "PASS" if allok_ else "FAIL", [os.path.join(out, "quick.json")],
                  "; ".join("%s %s" % (a_, c_) for a_, _b, c_, _e in summary))
    print("QUICK CHECK %s  (model build %.1f s)" % (VARIANT, t_build))
    for a, b, c, e in summary:
        print("  %-12s %-5s %s  [%.1f s]" % (a, "-" if b is None else ("PASS" if b else "FAIL"), c, e))
    ev = params.evidence()
    if ev:
        print("  evidence for %s (inputs %s):" % (VARIANT, params.inputs_hash()))
        for chk, st, tm, fr in ev:
            print("    %-18s %-5s %s  %s" % (chk, st, tm, fr))
    allok = all(b is not False for _a, b, _c, _e in summary)
    print("QUICK %s: %s in %.1f s" % (VARIANT, "PASS" if allok else "FAIL", time.time() - T0))
    return 0 if allok else 1


if not os.environ.get("QC_NOMAIN"):        # tests import the check functions without running them
    rc = main()
    if os.environ.get("FP_EXIT"):
        sys.exit(rc)
