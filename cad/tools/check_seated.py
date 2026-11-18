# -*- coding: utf-8 -*-
"""
Fastener seating check (TI-016): every purchased screw and pin must sit in a coaxial hole where it bears.
    python -I cad/tools/run.py --grip FOURBAR cad/tools/check_seated.py   (writes cad/out/<variant>/seated_report.txt)

Why: the upper-arm standoffs were moved through a parameter (UA_CLIP_X) while the plate holes stayed hard-coded.
The standoffs and their screws ended up over lightening pockets, and check_interference passed: no overlap,
because there was no material. An interface file per mate would have caught it (interfaces/ua_plate__ua_standoff
.toml now does); this check catches the same defect for mates nobody formalised.

Rule (assembled STOW pose, vis shapes):
  screw (SHCS, BHCS, CSK, SB5)  under-head point: 0.5 mm past the head bearing face, on the axis
                                (the tip is not judged: tips legitimately stick out of through-tapped holes and
                                nuts, vendor models lack tapped bores; check_engagement covers tapped holes)
  pin   (PIN-*, DOWEL)          both end points:  1 mm in from each end
Each point must lie inside a coaxial hole of ANOTHER part: a concave cylindrical face, axis parallel within 1 deg
and within 0.3 mm of the fastener axis, radius >= the fastener's local radius - 0.15 mm, the point within the
face's axial extent (+-0.3 mm).  Clearance, tapped, insert, nut, washer and bearing bores all count.
  FAIL  a point is in no coaxial hole: the fastener bears on air (a pocket, nothing) or on solid with no hole.
Set screws are not judged (their seat is a tapped hole across a shaft).  Exit 1 on any FAIL.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else \
    r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, HERE)
import FreeCAD as App  # noqa: E402
import arm_model as M  # noqa: E402
import params          # noqa: E402

V = App.Vector
SCREW_SRC = {"SHCS", "BHCS", "CSK", "SB5"}
PIN_PREFIX = ("PIN-", "DOWEL")
AX_TOL, RAD_TOL, T_TOL, ANG_TOL = 0.3, 0.15, 0.3, math.radians(1.0)


def _mid(f):
    u0, u1, v0, v1 = f.ParameterRange
    return (u0 + u1) / 2, (v0 + v1) / 2


def cylinders(shape, concave):
    """[(centre, unit axis, radius, t0, t1)] for cylindrical faces; concave=True -> holes, False -> shafts."""
    out = []
    for f in shape.Faces:
        s = f.Surface
        if type(s).__name__ != "Cylinder":
            continue
        ax, c = V(s.Axis).normalize(), V(s.Center)
        u, v = _mid(f)
        p, n = f.valueAt(u, v), f.normalAt(u, v)
        rad = (p - c) - ax * (p - c).dot(ax)
        if rad.Length < 1e-9 or (n.dot(rad) < 0) != concave:
            continue
        ts = [(x.Point - c).dot(ax) for x in f.Vertexes] or [0.0]
        out.append((c, ax, s.Radius, min(ts), max(ts)))
    return out


def fastener_points(p, s):
    """Seat points [(label, point, local radius)] and the axis, or (None, reason)."""
    shafts = cylinders(s, concave=False)
    if not shafts:
        return None, "no cylindrical face"
    c, ax = shafts[min(range(len(shafts)), key=lambda i: shafts[i][2])][:2]     # thinnest = shank / pin axis
    coax = []
    for (hc, hax, hr, h0, h1) in shafts:          # re-express each face's axial range from the common origin c
        if abs(abs(hax.dot(ax)) - 1) > 1e-6 or ((hc - c) - ax * (hc - c).dot(ax)).Length > 0.05:
            continue
        off, sg = (hc - c).dot(ax), (1.0 if hax.dot(ax) > 0 else -1.0)
        a_, b_ = off + sg * h0, off + sg * h1
        coax.append((hc, ax, hr, min(a_, b_), max(a_, b_)))
    tv = [(x.Point - c).dot(ax) for x in s.Vertexes]
    t0, t1 = min(tv), max(tv)

    def at(t):
        return c + ax * t

    def r_at(t):
        rs = [h[2] for h in coax if min(h[3], h[4]) - 0.05 <= t <= max(h[3], h[4]) + 0.05]
        return max(rs) if rs else min(h[2] for h in coax)

    if p.src.startswith(PIN_PREFIX):
        return [("end A", at(t0 + 1.0), r_at(t0 + 1.0)), ("end B", at(t1 - 1.0), r_at(t1 - 1.0))], ax
    shank_r = min(h[2] for h in coax)
    head = [h for h in coax if h[2] > shank_r * 1.3]
    cones = [f for f in s.Faces if type(f.Surface).__name__ == "Cone"]
    if head:
        hz = [min(h[3], h[4]) for h in head] + [max(h[3], h[4]) for h in head]
    elif cones:
        hz = [(x.Point - c).dot(ax) for f in cones for x in f.Vertexes]
    else:
        return None, "no head found"
    ha, hb = min(hz), max(hz)
    if abs(ha - t0) < abs(t1 - hb):            # head at the t0 end: shank runs towards t1
        under, d = hb, 1.0
    else:
        under, d = ha, -1.0
    tu = under + 0.5 * d
    return [("under head", at(tu), r_at(tu))], ax


def seated(point, ax, r, holes):
    for (c, hax, hr, h0, h1) in holes:
        if abs(hax.dot(ax)) < math.cos(ANG_TOL) or hr < r - RAD_TOL:
            continue
        w = point - c
        t = w.dot(hax)
        if (w - hax * t).Length <= AX_TOL and h0 - T_TOL <= t <= h1 + T_TOL:
            return True
    return False


def run(bodies=None, pose="STOW"):
    bodies = bodies or M.build_bodies()
    q, jaw = M.pose_q(pose)
    placed = list(M.placed(bodies, *q, jaw=jaw, which="vis"))
    holes = []
    for i, (_b, _p, s) in enumerate(placed):
        if s.isNull() or not s.Faces:
            continue
        bb = s.BoundBox
        bb.enlarge(0.5)
        holes.append((i, bb, cylinders(s, concave=True)))
    rows, n_f, n_pts, skipped = [], 0, 0, []
    for i, (bn, p, s) in enumerate(placed):
        if p.kind != "CAT" or not (p.src in SCREW_SRC or p.src.startswith(PIN_PREFIX)) or s.isNull():
            continue
        pts, ax = fastener_points(p, s)
        if pts is None:
            skipped.append("%s/%s (%s)" % (bn, p.name, ax))
            continue
        n_f += 1
        for label, pt, r in pts:
            n_pts += 1
            cand = [h for j, bb, h in holes if j != i and bb.isInside(pt)]
            if not any(seated(pt, ax, r, h) for h in cand):
                where = [placed[j][1].name for j, bb, _h in holes if j != i and bb.isInside(pt)
                         and placed[j][2].isInside(pt, 1e-3, True)]
                rows.append("FAIL %-32s %-10s at (%.1f, %.1f, %.1f)  %s" % (
                    p.name, label, pt.x, pt.y, pt.z,
                    ("inside solid " + ", ".join(where[:3]) + ", no coaxial hole") if where
                    else "no coaxial hole and no material (pocket, gap or off-axis hole)"))
    return n_f, n_pts, rows, skipped


def main():
    n_f, n_pts, rows, skipped = run()
    head = "Fastener seating (%s, STOW): %d screws/pins, %d seat points -> %d FAIL%s" % (
        M.GRIP, n_f, n_pts, len(rows), ("; %d not judged" % len(skipped)) if skipped else "")
    txt = "\n".join([head] + rows + ["not judged: " + s for s in skipped])
    out = os.path.join(params.out_dir(), "seated_report.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    print(txt)
    params.record("seated", "FAIL" if rows else "PASS", [out], head)
    return 1 if rows else 0


if not os.environ.get("QC_IMPORT"):
    sys.exit(main())
