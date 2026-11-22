# -*- coding: utf-8 -*-
"""Negative test: check_interfaces must flag a part whose holes no longer sit on its interface's bolt pattern, the
defect class CLAUDE.md warns about (a standoff moved through a parameter left its plate holes behind).  For every
bolt-pattern interface, the first built part of its first side is moved 3 mm perpendicular to the pattern normal,
in memory only.  Each moved part must turn its PASS rows to FAIL, and rows of parts not moved must not change.
interfaces.json is not written.  Exit 1 on FAIL.
    python -I cad/tools/run.py cad/tests/test_interfaces_moved_part.py      (BASE_DRIVE=DIRECT for the other base)
"""
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
import FreeCAD as App            # noqa: E402
import arm_model as M            # noqa: E402
import iface                     # noqa: E402
import check_interfaces as C     # noqa: E402


def rows(report):
    return {(r["interface"], r["side"], r["part"]): r["status"] for r in report}


bodies = M.build_bodies()
parts = {(bn, p.name): p for bn, ps in bodies.items() for p in ps}
C.main(bodies, write=False)
before = rows(C.main.report)

moved = set()
for I in iface.all_interfaces():
    if "pattern" not in I and "stations" not in I:
        continue
    if I["interface"].get("base_drive", M.BASE_DRIVE) != M.BASE_DRIVE:
        continue
    n = App.Vector(*I["frame"]["normal"])
    side = n.cross(App.Vector(0, 0, 1)) if abs(n.z) < 0.9 else n.cross(App.Vector(1, 0, 0))
    side.normalize()
    for _sk, _side, bps in I.sides():
        hit = [(b, pn) for b, pn in bps if (b, pn) in parts and pn not in moved]
        if hit:
            p = parts[hit[0]]
            if before.get((I.name, _sk, p.name)) != "PASS":
                continue
            for sh in (p.vis, p.chk):
                sh.translate(side * 3.0)
            moved.add(p.name)
            break

C.main(bodies, write=False)
after = rows(C.main.report)
fails = []
if not moved:
    fails.append("fixture: no PASSing interface part found to move in %s/%s" % (M.GRIP, M.BASE_DRIVE))
missed = sorted(k for k, st in after.items() if k[2] in moved and before.get(k) == "PASS" and st != "FAIL")
if missed:
    fails.append("moved but still PASS: " + ", ".join("%s/%s/%s" % k for k in missed[:5]))
changed = sorted(k for k, st in after.items() if k[2] not in moved and before.get(k) != st)
if changed:
    fails.append("rows of unmoved parts changed: " + ", ".join("%s/%s/%s" % k for k in changed[:5]))
flagged = {k[2] for k, st in after.items() if k[2] in moved and st == "FAIL"}
print("TEST %s: %s/%s moved %d interface parts 3 mm, %d flagged; %d rows%s" % (
    "FAIL" if fails else "PASS", M.GRIP, M.BASE_DRIVE, len(moved), len(flagged), len(after),
    "".join("\n  " + f for f in fails)))
sys.stdout.flush()
if fails:
    sys.exit(1)
