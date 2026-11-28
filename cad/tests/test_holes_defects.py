# -*- coding: utf-8 -*-
"""Negative test for tools/check_holes.py's three verdicts (TI-043).  test_quick_holes_changed.py only proves a
0.5 mm wall is caught and accepts FAIL or BROKEN for it; nothing proved BROKEN or WARN fire, or that a hole
blending tangentially into a slot (an intended slot end) is left alone.  In memory only, on the first full hole of
Jaw_Block_L (a gripper part, the same in both variants) that the report does not already list:
  1. breakout:  a D13 cutter (above MAX_D, so not a hole itself) bites half the radius into the hole -> BROKEN;
  2. thin wall: a twin hole with a 1.25 mm wall (MIN_ABS <= wall < max(WARN_ABS, WARN_D d))   -> WARN;
  3. no wall:   a twin hole with a 0.5 mm wall (< MIN_ABS)                                     -> FAIL;
  4. slot end:  the hole stretched 2 mm into a slot with flat, tangent walls                   -> no row.
Each case must give exactly its verdict for that hole, and the untouched part must give none.  Exit 1 on FAIL.
    python -I cad/tools/run.py cad/tests/test_holes_defects.py      (then with BASE_DRIVE=DIRECT)
"""
import os
import re
import sys
import types
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
import FreeCAD as App            # noqa: E402
import Part                      # noqa: E402
import arm_model as M            # noqa: E402
import check_holes as H          # noqa: E402

PART = "Jaw_Block_L"
fails = []
part = next(p for ps in M.build_bodies().values() for p in ps if p.name == PART)
base = part.vis


def scan(shape):
    return H.scan_part(types.SimpleNamespace(name=PART, vis=shape))[0]


def on_axis(row, g):
    """True if the row's hole centre lies on hole g's axis (OCC may move the centre along it after a cut)."""
    m = re.search(r"at \(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", row)
    if not m:
        return False
    d = App.Vector(*map(float, m.groups())) - g["centre"]
    return (d - g["axis"] * d.dot(g["axis"])).Length < 0.1 and abs(float(row.split(" D")[1].split()[0]) - 2 * g["r"]) < 0.05


rows0 = scan(base)
cands = [g for g in H.hole_groups(base).values()
         if g["span"] >= 359.0 and not any(on_axis(r, g) for r in rows0)]
if not cands:
    print("TEST FAIL: fixture: %s has no full hole the report leaves alone" % PART)
    sys.exit(1)
g = cands[0]
ax, c, r = g["axis"], g["centre"], g["r"]
L = base.BoundBox.DiagonalLength * 2
mid = base.BoundBox.Center - c
inward = mid - ax * mid.dot(ax)                      # towards the part's middle, across the axis
if inward.Length < 1e-6:
    inward = ax.cross(App.Vector(0, 0, 1) if abs(ax.z) < 0.9 else App.Vector(1, 0, 0))
inward.normalize()
across = ax.cross(inward).normalize()


def cyl(rad, centre):
    return Part.makeCylinder(rad, L, centre - ax * (L / 2), ax)


def slot(length):
    pts = [c + across * s * r + inward * t for s, t in ((-1, 0), (1, 0), (1, length), (-1, length), (-1, 0))]
    bar = Part.Face(Part.makePolygon([p - ax * (L / 2) for p in pts])).extrude(ax * L)
    return bar.fuse(cyl(r, c + inward * length))


CASES = [
    ("breakout", base.cut(cyl(6.5, c - inward * (r + 6.5 - 0.5 * r))), "BROKEN"),
    ("thin wall", base.cut(cyl(r, c + inward * (2 * r + 1.25))), "WARN"),
    ("no wall", base.cut(cyl(r, c + inward * (2 * r + 0.5))), "FAIL"),
    ("slot end", base.cut(slot(2.0)), None),
]
print("  hole: %s D%.1f at (%.1f, %.1f, %.1f), %d rows before" % (PART, 2 * r, c.x, c.y, c.z, len(rows0)))
for case, shape, want in CASES:
    rows = scan(shape)
    mine = sorted({x.split()[0] for x in rows if on_axis(x, g)})
    got = mine or ["none"]
    print("  %-10s -> %s  (want %s)" % (case, ",".join(got), want or "none"))
    if mine != ([want] if want else []):
        fails.append("%s: hole gave %s, want %s" % (case, got, want or "none"))
    if want is None and any(x.startswith("BROKEN") for x in rows if x not in rows0):
        fails.append("%s: the tangent slot end was reported as a breakout" % case)

print("TEST %s: check_holes BROKEN / WARN / FAIL / tangent slot on %s%s"
      % ("FAIL" if fails else "PASS", PART, "".join("\n  " + f for f in fails)))
sys.stdout.flush()
sys.exit(1 if fails else 0)
