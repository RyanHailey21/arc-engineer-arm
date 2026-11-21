# -*- coding: utf-8 -*-
"""
Projected tolerance zone heights for tapped holes, measured in the assembly (ASME Y14.5 10.4.1 /
App. B-4: projected height = maximum thickness of the mating part clamped by the screw).
    freecadcmd cad/tools/projected_heights.py   -> cad/fab/projected_heights.json  {"<part>|M3": height_mm}
For every tapped hole of a custom part (thread pilot radius 1.25 / 1.7 / 2.1), a line along the hole axis
is intersected with all other custom parts at the STOW pose; the contiguous stack of parts touching the
tapped part's face is the mating stack (gaps < 0.5 mm count as contact). Height = stack thickness, rounded
up to 0.5 mm. Holes with nothing mating (spare holes) are reported but give no height.
"""
import json
import math
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
import FreeCAD as App  # noqa: E402
import Part  # noqa: E402
import arm_model as M  # noqa: E402
import params  # noqa: E402

V = App.Vector
TAP = {1.25: "M3", 1.27: "M3", 1.7: "M4", 2.1: "M5"}   # 1.27: standoff through-tap


def tapped_holes(shape):
    out = {}
    for f in shape.Faces:
        s = f.Surface
        if s.__class__.__name__ != "Cylinder":
            continue
        r = round(s.Radius, 2)
        if r not in TAP:
            continue
        u0, u1, v0, v1 = f.ParameterRange
        p = f.valueAt((u0 + u1) / 2, (v0 + v1) / 2)
        n = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        ax, c = V(s.Axis), V(s.Center)
        rad = (p - c) - ax * ((p - c).dot(ax))
        if rad.Length < 1e-9 or n.dot(rad) > 0:
            continue                                   # convex -> not a hole
        c0 = c + ax * ((f.CenterOfMass - c).dot(ax))
        key = (round(c0.x, 1), round(c0.y, 1), round(c0.z, 1), r)
        out[key] = (c0, ax, TAP[r], r)
    return list(out.values())


def main():
    q, jaw = M.pose_q("STOW")
    plc = M.placements(*q, jaw=jaw)
    world, P2B = [], {}
    for bname, parts in M.build_bodies().items():
        for p in parts:
            if p.vis is None or p.vis.isNull():
                continue
            s = p.vis.copy()
            s.Placement = plc[bname].multiply(s.Placement)
            world.append((p, s))
            P2B[p.name] = plc[bname]
    custom = [(p, s) for p, s in world if p.kind != "CAT"]
    res, detail = {}, []
    for p, s in custom:
        if not p.src.startswith("custom: 5 mm 6061") and "6061" not in p.src:
            continue                                   # only machined aluminium parts are tapped
        holes = tapped_holes(s)
        if not holes:
            continue
        fast = ("SHCS", "BHCS", "CSK", "SB", "SetScrew", "Dowel", "Nyloc", "Insert")
        fasteners = [(q_, t) for q_, t in world if q_.name.startswith(("SHCS", "BHCS", "CSK", "SB"))]
        others = [(q_, t) for q_, t in world if q_.name != p.name and not q_.name.startswith(fast)]   # mating stack incl. washers / motors
        for c0, ax, th, rt in holes:
            best = None
            # rays through MATERIAL just outside the hole (the axis itself runs through the empty bore and the
            # mating clearance hole); 4 angles, the smallest consistent stack wins
            perp = ax.cross(V(1, 0, 0)) if abs(ax.x) < 0.9 else ax.cross(V(0, 1, 0))
            perp.normalize()
            perp2 = ax.cross(perp)
            offs = [perp * (rt + 1.2), perp * -(rt + 1.2), perp2 * (rt + 1.2), perp2 * -(rt + 1.2)]
            # the screw in this hole decides the side: its head (farthest point) is on the mating side
            axl = Part.makeLine(c0 - ax * 80, c0 + ax * 80)
            far = 0.0
            for q_, t in fasteners:
                if not t.BoundBox.intersect(axl.BoundBox):
                    continue
                try:
                    cm = t.common(axl)
                except Exception:
                    continue
                for e in cm.Edges:
                    for v in e.Vertexes:
                        tt = (v.Point - c0).dot(ax)
                        if abs(tt) > abs(far):
                            far = tt
            sides = [1 if far > 0 else -1] if abs(far) > 0.5 else [1, -1]   # through-tapped standoffs: both ends
            for sgn in sides:                          # only the screw-head side
              d = ax * sgn
              hs_ = []
              for off in offs:
                o0 = c0 + off
                line = Part.makeLine(o0, o0 + d * 60)
                own = s.common(Part.makeLine(o0 - d * 60, o0 + d * 60))
                ts = [(v.Point - c0).dot(d) for e in own.Edges for v in e.Vertexes]
                exit_t = max(ts) if ts else 0.0
                segs = []
                for q_, t in others:
                    if not t.BoundBox.intersect(line.BoundBox):
                        continue
                    try:
                        cm = t.common(line)
                    except Exception:
                        continue
                    for e in cm.Edges:
                        a_, b_ = sorted((v.Point - c0).dot(d) for v in e.Vertexes)
                        if b_ - a_ > 0.05:
                            segs.append((a_, b_, q_.name))
                segs.sort()
                stack, edge = [], exit_t
                for a_, b_, nm in segs:
                    if b_ <= exit_t + 0.05:
                        continue
                    if a_ - edge > 0.5:
                        break
                    stack.append(nm)
                    edge = max(edge, b_)
                if stack:
                    hs_.append((edge - exit_t, stack))
              if len(hs_) >= 2:                        # mating material on at least two sides of the hole
                h = min(x[0] for x in hs_)
                if best is None or h > best[0]:
                    best = (h, [n for x in hs_ for n in x[1]])
            k = "%s|%s" % (p.name, th)
            inv = P2B[p.name].inverse()                 # hole in the PART frame (p.vis), for per-group lookup
            cb, ab = inv.multVec(c0), inv.Rotation.multVec(ax)
            loc = [round(cb.x, 3), round(cb.y, 3), round(cb.z, 3), round(ab.x, 4), round(ab.y, 4), round(ab.z, 4)]
            if best:
                hh = math.ceil(best[0] * 2) / 2.0
                res[k] = max(res.get(k, 0.0), hh)
                detail.append((k, round(best[0], 2), sorted(set(best[1])), loc, hh))
            else:
                detail.append((k, None, "no mating part (spare hole)", loc, None))
    outs = [os.path.join(params.out_dir(), "projected_heights.json")]
    if params.grip() == params.release_variant() and params.base_drive() == params.release_base_drive():
        outs.append(os.path.join(CAD, "fab", "projected_heights.json"))     # read by the rev A drawings
    for out in outs:
        json.dump(dict(heights=res, detail=detail), open(out, "w"), indent=1)
    params.record("projected_heights", "PASS", outs, "%d tapped-hole groups" % len(res))
    for k, v in sorted(res.items()):
        print("%-34s %.1f mm" % (k, v))
    print("spare:", sorted({d[0] for d in detail if d[1] is None} - set(res)))


main()
