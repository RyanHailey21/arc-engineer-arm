# -*- coding: utf-8 -*-
"""Negative test: check_level_keeping.closure_margins() (quick_check's level-keeping step) must flag each of its
three defect classes, injected in memory only:
  1. closure: the level member placed 0.5 mm off rod 2's far pin (placements() and the linkage disagree);
  2. dead-point margin: V2_ANG moved onto a task pose's elbow angle (th2 at a dead point);
  3. limit margin: V2_ANG moved onto the lower elbow limit.
The unmodified model must PASS all three lines first, and each defect must turn only its own line to FAIL where the
check can tell them apart (1 leaves 2 and 3 alone).  Pure kinematics, no shape booleans.  Exit 1 on FAIL.
    python -I cad/tools/run.py cad/tests/test_level_keeping_defects.py      (BASE_DRIVE=DIRECT for the other base)
"""
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
import FreeCAD as App            # noqa: E402
import arm_model as M            # noqa: E402
import check_level_keeping as L  # noqa: E402


def status():
    ok, lines, _d = L.closure_margins()
    return ok, [ln.rstrip().endswith("PASS") for ln in lines], lines


fails = []
ok, st, lines = status()
if not ok or st != [True, True, True]:
    fails.append("fixture: unmodified model does not PASS: " + " | ".join(lines))

# 1. closure: shift the level member 0.5 mm along x in every placement
real_placements = M.placements


def shifted(*a, **kw):
    plc = real_placements(*a, **kw)
    lv = plc["LEVEL"]
    plc["LEVEL"] = App.Placement(lv.Base + App.Vector(0.5, 0, 0), lv.Rotation)
    return plc


M.placements = shifted
try:
    ok, st, lines = status()
finally:
    M.placements = real_placements
if ok or st != [False, True, True]:
    fails.append("closure defect: expected [FAIL, PASS, PASS], got " + " | ".join(lines))

# 2 + 3. dead points: V2_ANG moved onto a task pose's elbow angle, then onto the lower elbow limit
v2_ang = M.K["V2_ANG"]
pose = next(iter(M.POSES))
for label, ang, idx in (("task-pose dead point (%s)" % pose, M.pose_q(pose)[0][1], 1),
                        ("elbow-limit dead point", L.ELBOW_LIMITS[0], 2)):
    M.K["V2_ANG"] = ang
    try:
        ok, st, lines = status()
    finally:
        M.K["V2_ANG"] = v2_ang
    if ok or st[idx]:
        fails.append("%s: line %d still PASS: %s" % (label, idx + 1, " | ".join(lines)))

ok, st, _lines = status()
if st != [True, True, True]:
    fails.append("model not restored after the test")

print("TEST %s: %s/%s level-keeping closure + dead-point margins, 3 defects injected%s" % (
    "FAIL" if fails else "PASS", M.GRIP, M.BASE_DRIVE, "".join("\n  " + f for f in fails)))
sys.stdout.flush()
if fails:
    sys.exit(1)
