# -*- coding: utf-8 -*-
"""Negative test (TI-016): check_seated must flag a fastener moved off its hole, the defect class of the upper-arm
standoffs (UA_CLIP_X moved them; the plate holes stayed put; check_interference passed because they sat over a
lightening pocket).  Every UA standoff screw is moved 6 mm sideways (perpendicular to its axis), in memory only.
Each moved screw must FAIL; screws seated before the move must not start failing elsewhere.  Exit 1 on FAIL.
    python -I cad/tools/run.py --grip FOURBAR cad/tests/test_seated_moved_screw.py
"""
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
import FreeCAD as App            # noqa: E402
import arm_model as M            # noqa: E402
import check_seated as S         # noqa: E402

bodies = M.build_bodies()
_n, _p, before, _s = S.run(bodies)
moved = []
for bn, ps in bodies.items():
    for p in ps:
        if p.kind == "CAT" and p.src in S.SCREW_SRC and "_UA_st_" in p.name:
            pts, ax = S.fastener_points(p, p.vis)
            side = ax.cross(App.Vector(0, 0, 1)) if abs(ax.z) < 0.9 else ax.cross(App.Vector(1, 0, 0))
            side.normalize()
            for sh in (p.vis, p.chk):
                sh.translate(side * 6.0)
            moved.append(p.name)
_n, _p, after, _s = S.run(bodies)
flagged = {r.split()[1] for r in after}
fails = []
if not moved:
    fails.append("fixture: no *_UA_st_* screws found in %s" % M.GRIP)
missed = [m for m in moved if m not in flagged]
if missed:
    fails.append("moved but not flagged: " + ", ".join(missed))
new_other = [r for r in after if r.split()[1] not in moved and r not in before]
if new_other:
    fails.append("unrelated new FAILs: " + "; ".join(new_other[:3]))
print("TEST %s: %s moved %d UA standoff screws 6 mm, %d flagged; %d baseline FAILs unchanged%s" % (
    "FAIL" if fails else "PASS", M.GRIP, len(moved), len([m for m in moved if m in flagged]), len(before),
    "".join("\n  " + f for f in fails)))
sys.stdout.flush()
if fails:
    sys.exit(1)
