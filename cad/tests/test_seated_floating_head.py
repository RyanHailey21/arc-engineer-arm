# -*- coding: utf-8 -*-
"""Negative test (TI-017): check_seated must flag screws whose heads float.  Rev B's STS3215 bottom-cap screws
(PAN-M2x12) were once translated twice by their pattern offset (hardware.pan_screw returned one object as vis and
chk), so they hung 13 mm off their holes; the seating check did not judge PAN screws and had no head-contact rule.
In memory only:
  case A  every PAN screw pulled 2 mm back along its axis: the head stands off the cradle floor (shank still in
          its hole, so only rule 2, head bearing, can see it)
  case B  every PAN screw shifted 13.2 mm sideways (the double-translate): rules 1 and 2
Each moved screw must FAIL in both cases; nothing else may start failing.  Exit 1 on FAIL.
    python -I cad/tools/run.py --grip FOURBAR cad/tests/test_seated_floating_head.py
"""
import copy
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
import FreeCAD as App            # noqa: E402
import arm_model as M            # noqa: E402
import check_seated as S         # noqa: E402

base = M.build_bodies()
_n, _p, before, _s = S.run(base)


def moved_bodies(vec_of):
    bodies = {bn: [copy.copy(p) for p in ps] for bn, ps in base.items()}
    names = []
    for ps in bodies.values():
        for p in ps:
            if p.kind == "CAT" and p.src.startswith("PAN-"):
                S.fastener_points.bearing = None
                _pts, ax = S.fastener_points(p, p.vis)
                d = S.fastener_points.bearing[3]
                v = vec_of(ax, d)
                p.vis, p.chk = p.vis.copy(), p.chk.copy()
                p.vis.translate(v)
                p.chk.translate(v)
                names.append(p.name)
    return bodies, names


fails, lines = [], []
for case, vec_of in (("A head 2 mm off", lambda ax, d: ax * (-2.0 * d)),
                     ("B 13.2 mm sideways", lambda ax, d: S._perp(ax)[0] * 13.2)):
    bodies, moved = moved_bodies(vec_of)
    _n, _p, after, _s = S.run(bodies)
    flagged = {r.split()[1] for r in after}
    if not moved:
        fails.append("%s: fixture: no PAN screws in %s" % (case, M.GRIP))
    missed = [m for m in moved if m not in flagged]
    if missed:
        fails.append("%s: moved but not flagged: %s" % (case, ", ".join(missed)))
    other = [r for r in after if r.split()[1] not in moved and r not in before]
    if other:
        fails.append("%s: unrelated new FAILs: %s" % (case, "; ".join(other[:3])))
    lines.append("%s: %d moved, %d flagged" % (case, len(moved), len([m for m in moved if m in flagged])))
print("TEST %s: %s %s; %d baseline FAILs%s" % ("FAIL" if fails else "PASS", M.GRIP, "; ".join(lines), len(before),
                                              "".join("\n  " + f for f in fails)))
sys.stdout.flush()
if fails:
    sys.exit(1)
