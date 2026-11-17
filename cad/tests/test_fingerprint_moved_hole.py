# -*- coding: utf-8 -*-
"""Negative test (TI-009): the fingerprint must report a hole moved inside a filleted plate.
makeFillet returns a generic Shape with no CenterOfMass; the old bounding-box fallback hid the move
(Finger_*_bot_CF3 rear standoff hole, 2026-11-16).  Prints TEST PASS / TEST FAIL.  Run (TI-010: a short
script passed to freecadcmd by path printed nothing on this machine, so exec it):
    freecadcmd -c "exec(open(r'cad/tests/test_fingerprint_moved_hole.py').read())"   """
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else \
    r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"              # fingerprint.py: functions only
import FreeCAD as App                      # noqa: E402
import Part                                # noqa: E402
import fingerprint as F                    # noqa: E402

V = App.Vector


def plate(hx, hy):
    b = Part.makeBox(40, 30, 5)
    vert = [e for e in b.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1]
    s = b.makeFillet(3.0, vert)
    return s.cut(Part.makeCylinder(1.6, 5, V(hx, hy, 0)))


fails = []
a, b = plate(16, 20), plate(12, 18)        # the real move: (XT+16, o+20) -> (XT+12, o+18)
fa, fb = F.shape_fp(a), F.shape_fp(b)
d = F.diff(fa, fb)
if not d:
    fails.append("moved hole not reported: %s" % fa)
if abs(fa["vol"] - fb["vol"]) > F.TOL_VOL or fa["bb"] != fb["bb"]:
    fails.append("fixture wrong: volume/bbox should be unchanged by the move")
if not any("fdig" in x for x in d):
    fails.append("face digest did not change: %s" % d)
same = F.diff(F.shape_fp(plate(16, 20)), fa)
if same:
    fails.append("rebuilding the same plate is not stable: %s" % same)
c = F.centre_of_mass(a)
if not hasattr(a, "CenterOfMass") and (c - a.BoundBox.Center).Length < 1e-6:
    fails.append("centre of mass still falls back to the bounding-box centre")
print("TEST %s: %s" % ("FAIL" if fails else "PASS", "; ".join(fails) or "moved hole reported (%s)" % "; ".join(d)))
sys.stdout.flush()
