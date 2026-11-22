# -*- coding: utf-8 -*-
"""
Hole edge-distance check for every custom (made) part.   ~2-3 min, headless:
    freecadcmd cad/tools/check_holes.py          (writes cad/out/<variant>/hole_report.txt)

A "hole" is a set of concave cylindrical faces sharing one axis and radius
(OCC splits a hole into two half-faces).  For holes 2..12 mm diameter:
  BROKEN  the hole is not a full 360 deg AND it meets a neighbouring face at a
          sharp edge, i.e. it breaks out through the part edge, a pocket or a
          window.  Partial cylinders that blend tangentially into their
          neighbours (slot ends, fillets) are intended and ignored.
  FAIL    wall from a full hole to the nearest side-bounding face < MIN_ABS
  WARN    wall < max(WARN_ABS, WARN_D * d)
Side-bounding faces are faces that do not lie across the hole axis (so plate
faces, counterbore floors and the hole's own counterbore/chamfer are ignored).
Purchased parts (kind CAT) are the vendor's responsibility and are skipped.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else \
    r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, HERE)
import FreeCAD as App      # noqa: E402
import Part                # noqa: E402
import arm_model as M      # noqa: E402
import params              # noqa: E402

MIN_ABS, WARN_ABS, WARN_D, MIN_D, MAX_D = 1.0, 1.5, 0.5, 2.0, 12.0
TANGENT_DEG = 3.0


def _mid_normal(face, pnt):
    u, v = face.Surface.parameter(pnt)
    return face.normalAt(u, v)


def hole_groups(shape):
    """{key: dict(faces, centre, axis, r, span_deg)} for concave cylinders."""
    groups = {}
    for f in shape.Faces:
        s = f.Surface
        if s.__class__.__name__ != "Cylinder":
            continue
        d = 2 * s.Radius
        if not (MIN_D <= d <= MAX_D):
            continue
        u0, u1, v0, v1 = f.ParameterRange
        p = f.valueAt((u0 + u1) / 2, (v0 + v1) / 2)
        n = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        ax, c = App.Vector(s.Axis), App.Vector(s.Center)
        radial = (p - c) - ax * ((p - c).dot(ax))
        if radial.Length < 1e-9 or n.dot(radial) > 0:        # convex: boss / shaft, not a hole
            continue
        if ax.x < -1e-9 or (abs(ax.x) < 1e-9 and (ax.y < -1e-9 or (abs(ax.y) < 1e-9 and ax.z < 0))):
            ax = ax * -1
        foot = c - ax * c.dot(ax)                            # axis line, canonical point
        key = tuple(round(x, 2) for x in (ax.x, ax.y, ax.z, foot.x, foot.y, foot.z, s.Radius))
        g = groups.setdefault(key, dict(faces=[], centre=c, axis=ax, r=s.Radius, span=0.0))
        g["faces"].append(f)
        g["span"] += math.degrees(u1 - u0)
    return groups


def _is_d_flat(nb, pm, g, shape):
    """D-bore chord vs breakout: a planar face parallel to the hole axis, closer than r, with MATERIAL just
    behind it (stepping away from the axis stays inside the part) is the flat of a D-bore.  At a breakout
    through a part edge, stepping away from the axis leaves the part."""
    if nb.Surface.__class__.__name__ != "Plane":
        return False
    ax, c = g["axis"], g["centre"]
    try:
        n = _mid_normal(nb, pm)
    except Exception:
        return False
    if abs(n.dot(ax)) > 1e-3:
        return False
    n = n.normalize()
    d = n.dot(c - pm)                           # signed distance flat-plane -> hole axis
    if abs(d) < 1e-6 or abs(d) >= g["r"] - 1e-6:
        return False
    u = n * (1.0 if d > 0 else -1.0)            # unit normal of the flat pointing towards the axis
    try:
        return shape.isInside(pm - u * 0.3, 1e-4, True) and not shape.isInside(pm + u * 0.3, 1e-4, True)
    except Exception:
        return False


def breaks_out(shape, g):
    """Partial hole: True if any straight boundary edge meets its neighbour sharply."""
    ids = [f.hashCode() for f in g["faces"]]
    for f in g["faces"]:
        for e in f.Edges:
            if e.Curve.__class__.__name__ not in ("Line", "LineSegment"):
                continue
            pm = e.valueAt((e.FirstParameter + e.LastParameter) / 2)
            for nb in shape.ancestorsOfType(e, Part.Face):
                if nb.hashCode() in ids:
                    continue
                if _is_d_flat(nb, pm, g, shape):
                    continue                     # intended D-bore chord (torque flat), not a breakout
                try:
                    a = _mid_normal(f, pm).getAngle(_mid_normal(nb, pm))
                except Exception:
                    continue
                if math.degrees(a) > TANGENT_DEG:
                    return True
    return False


def ligament(shape, g):
    ax, c, r = g["axis"], g["centre"], g["r"]
    ids = {f.hashCode() for f in g["faces"]}
    own_edges = {e.hashCode() for f in g["faces"] for e in f.Edges}
    hole = Part.Shell(g["faces"]) if len(g["faces"]) > 1 else g["faces"][0]
    bb = hole.BoundBox
    bb.enlarge(r + 8.0)
    best = 1e9
    for h in shape.Faces:
        if h.hashCode() in ids or any(e.hashCode() in own_edges for e in h.Edges):
            continue
        if not h.BoundBox.intersect(bb):
            continue
        sn = h.Surface.__class__.__name__
        if sn == "Plane":
            try:
                n = h.normalAt(*h.ParameterRange[0::2])
            except Exception:
                continue
            if abs(n.dot(ax)) > 0.5:
                continue
        elif sn == "Cylinder" and abs(App.Vector(h.Surface.Axis).dot(ax)) > 0.99:
            d = (h.Surface.Center - c) - ax * ((h.Surface.Center - c).dot(ax))
            if d.Length < 1e-3:                               # coaxial counterbore / chamfer
                continue
        try:
            best = min(best, hole.distToShape(h)[0])
        except Exception:
            pass
    return best


def scan_part(p):
    """(rows, holes, broken, fail, warn) for one made part; rows as in hole_report.txt.  quick_check.py runs this
    on the parts the fingerprint says changed (TI-005)."""
    rows, nb, nf, nw, nh = [], 0, 0, 0, 0
    for g in hole_groups(p.vis).values():
        c, d = g["centre"], 2 * g["r"]
        where = "(%.1f, %.1f, %.1f)" % (c.x, c.y, c.z)
        if g["span"] < 359.0:
            if breaks_out(p.vis, g):
                rows.append("BROKEN %-28s D%.1f at %s  breaks out (%.0f deg of rim left)" % (p.name, d, where, g["span"]))
                nb += 1
            continue
        nh += 1
        lig = ligament(p.vis, g)
        if lig < MIN_ABS:
            rows.append("FAIL   %-28s D%.1f at %s  wall %.2f mm" % (p.name, d, where, lig))
            nf += 1
        elif lig < max(WARN_ABS, WARN_D * d):
            rows.append("WARN   %-28s D%.1f at %s  wall %.2f mm" % (p.name, d, where, lig))
            nw += 1
    return rows, nh, nb, nf, nw


def judged(p):
    """Made parts only: purchased (CAT) parts are the vendor's responsibility."""
    return p.kind != "CAT" and not p.vis.isNull()


def main():
    bodies = M.build_bodies()
    rows, nb, nf, nw, nh = [], 0, 0, 0, 0
    for bname, parts in bodies.items():
        for p in parts:
            if not judged(p):
                continue
            r_, h_, b_, f_, w_ = scan_part(p)
            rows += r_
            nh, nb, nf, nw = nh + h_, nb + b_, nf + f_, nw + w_
    head = ["Hole edge-distance check (custom parts): %d holes -> %d broken-out, %d fail (wall < %.1f mm), "
            "%d warn (wall < max(%.1f mm, %.1f d))" % (nh, nb, nf, MIN_ABS, nw, WARN_ABS, WARN_D)]
    txt = "\n".join(head + sorted(rows))
    rep = os.path.join(params.out_dir(), "hole_report.txt")
    with open(rep, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    print(txt)
    params.record("holes", "FAIL" if nb or nf else ("WARN" if nw else "PASS"), [rep], head[0])


if not os.environ.get("QC_IMPORT"):          # tools/quick_check.py imports scan_part without running the check
    main()
