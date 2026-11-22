# -*- coding: utf-8 -*-
"""
Fully printed fit-and-motion prototype of the ACTIVE variant: one STL per custom part, written under
cad/out/<variant>/print/ (the released package and the model are untouched; geometry is the model's, unchanged).

    python -I cad/tools/run.py cad/tools/export_print.py

Every custom part (CF plates, aluminium, steel shafts, shims, PTFE washers and the printed parts) is printed at its
modelled size. Purchased parts (servos, bearings, fasteners, pins, inserts, collars, e-clips, the spring) are bought.
TARGET is the printer the pack is cut for (the UTA ERB 335 Ender-3 S1 Pros, PLA or PETG). A part that does not fit it,
flat or diagonally, is split in two with a glued dovetail in the plate's own plane, at the station nearest mid-length
where the dovetail has WALL mm of solid material all round; both halves must then fit. The outline and every hole stay
where the model has them, so nothing new can collide.

cad/out/<variant>/print/
  stl/<part>.stl, stl/<part>_A.stl + _B.stl   body frame, mm
  print_list.csv                              file, part, material, size, the beds it fits (flat or diagonal)
"""
import csv
import math
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
import FreeCAD as App   # noqa: E402
import Part             # noqa: E402
import MeshPart         # noqa: E402
import params           # noqa: E402
import arm_model as M   # noqa: E402

# beds (name, x, y, z) mm. TARGET decides the splits; the others are listed for information.
TARGET = ("Ender-3 S1 Pro", 220, 220, 270)
OTHERS = (("P1S", 256, 256, 256), ("K2 Pro", 300, 300, 300), ("H2D", 325, 320, 325))
REVIEW = "split_joints.png"                                 # every split joint, for review
STL = "%s.stl"                                              # file name per part (and _A / _B halves)
# dovetail sizes (mm) by plate height at the joint; glued, clearance per side
TAILS = ((24.0, dict(length=8.0, neck=8.0, head=12.0)), (0.0, dict(length=7.0, neck=5.0, head=8.0)))
CLEAR = 0.15
WALL = 2.0                                                  # solid material round the dovetail
MATERIAL = {"PRINT": "PETG (or PLA)", "CF": "PETG (or PLA); print flat", "AL": "PETG (or PLA)",
            "STEEL": "PETG (or PLA), or cut from the D10 rod", "SHIM": "PETG (or PLA); 0.5 mm = 3 layers at 0.16",
            "PTFE": "PETG (or PLA)", "TPU": "TPU 95A (PETG if the lab has no TPU: less grip)"}


def fit(dims, bed):
    """'flat' / 'diagonal' / '' for a part of sorted dims (L, w, t) lying on its largest face."""
    L, w, t = dims
    _n, A, B, H = bed
    if t > H:
        return ""
    if (L <= A and w <= B) or (L <= B and w <= A):
        return "flat"
    for i in range(1, 900):
        a = math.radians(i / 10.0)
        if L * math.cos(a) + w * math.sin(a) <= A and L * math.sin(a) + w * math.cos(a) <= B:
            return "diagonal"
    return ""


def dims_of(s):
    bb = s.BoundBox
    return sorted((bb.XLength, bb.YLength, bb.ZLength), reverse=True)


def dovetail(x0, y0, y1, tail, c, zs=(0.0,)):
    """Tail region(s) of the +x piece, protruding into -x: neck at x0, head at x0 - length, centred at each z in zs;
    grown by c (mm)."""
    L, n, h = tail["length"], tail["neck"] / 2 + c, tail["head"] / 2 + c
    out = None
    for z in zs:
        pts = [App.Vector(x0 + 1.0 + c, 0, z - n), App.Vector(x0, 0, z - n), App.Vector(x0 - L - c, 0, z - h),
               App.Vector(x0 - L - c, 0, z + h), App.Vector(x0, 0, z + n), App.Vector(x0 + 1.0 + c, 0, z + n)]
        s = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(App.Vector(0, y1 - y0 + 2, 0))
        s.translate(App.Vector(0, y0 - 1, 0))
        out = s if out is None else out.fuse(s)
    return out


def solid_at(shape, x0, tail, zs):
    """The dovetail(s) plus WALL lie wholly in material (no hole, pocket or edge within WALL)."""
    bb = shape.BoundBox
    for z in zs:                                        # one probe per tail, cheapest first
        pr = dovetail(x0, bb.YMin + 0.01, bb.YMax - 0.01, tail, WALL, (z,))
        pr = pr.common(Part.makeBox(pr.BoundBox.XLength, bb.YLength - 0.02, pr.BoundBox.ZLength,
                                    App.Vector(pr.BoundBox.XMin, bb.YMin + 0.01, pr.BoundBox.ZMin)))
        if abs(shape.common(pr).Volume - pr.Volume) > 1e-3 * pr.Volume:
            return False
    return True


def cut_at(shape, x0, tail, zs):
    """(A, B) halves at x0 with the dovetail(s) at zs, or None."""
    if not solid_at(shape, x0, tail, zs):
        return None
    bb = shape.BoundBox
    big = 1000.0
    lo = Part.makeBox(x0 - bb.XMin + 1, big, big, App.Vector(bb.XMin - 1, -big / 2, -big / 2))
    hi = Part.makeBox(bb.XMax - x0 + 1, big, big, App.Vector(x0, -big / 2, -big / 2))
    a = shape.common(lo).cut(dovetail(x0, bb.YMin, bb.YMax, tail, CLEAR, zs))
    b = shape.common(hi).fuse(shape.common(dovetail(x0, bb.YMin, bb.YMax, tail, 0.0, zs))).removeSplitter()
    if not (a.isValid() and b.isValid()) or a.common(b).Volume > 1e-6:
        return None
    return a, b


def filled(shape, x0, half):
    """shape with its lightening pockets (inner outlines that are not plain circles) filled for |x - x0| <= half: the
    plate's own slots, which nothing else enters, so the outline and every hole stay as modelled."""
    bb = shape.BoundBox
    y = (bb.YMin + bb.YMax) / 2
    wires = shape.slice(App.Vector(0, 1, 0), y)
    outer = max(wires, key=lambda w: w.BoundBox.DiagonalLength)
    box = Part.makeBox(2 * half, bb.YLength + 2, bb.ZLength + 2, App.Vector(x0 - half, bb.YMin - 1, bb.ZMin - 1))
    out = shape
    for w in wires:
        if w is outer or (len(w.Edges) == 1 and w.Edges[0].Curve.TypeId == "Part::GeomCircle"):
            continue
        f = Part.Face(w)
        f.translate(App.Vector(0, bb.YMin - y, 0))
        out = out.fuse(f.extrude(App.Vector(0, bb.YLength, 0)).common(box))
    return out.removeSplitter()


def split(shape):
    """Dovetail split nearest mid-length (x in the body frame) with both halves on TARGET: one centred tail, or a
    mirrored pair above and below a hole on the centre line."""
    bb = shape.BoundBox
    mid = (bb.XMin + bb.XMax) / 2
    zc = (bb.ZMin + bb.ZMax) / 2
    big = next(t for hmin, t in TAILS if bb.ZLength >= hmin)
    small = TAILS[-1][1]                                # pairs share the web with the hole: the small tail
    layouts = [(big, (zc,))] + [(small, (zc - d, zc + d)) for d in [x / 2.0 for x in range(8, int(bb.ZLength))]]
    for k in range(0, int(bb.XLength / 2)):
        for x0 in (mid + k, mid - k) if k else (mid,):
            for tail, zs in layouts:
                r = cut_at(shape, x0, tail, zs)
                if r and all(fit(dims_of(s), TARGET) for s in r):
                    return x0, len(zs), r
    # no solid station (slotted links): fill the slots locally at mid-length and put one centred tail there
    for k in range(0, int(bb.XLength / 4)):
        for x0 in (mid + k, mid - k) if k else (mid,):
            sh = filled(shape, x0 - big["length"] / 2, big["length"] + WALL + 6)
            for tail in (big, small):
                r = cut_at(sh, x0, tail, (zc,))
                if r and all(fit(dims_of(s), TARGET) for s in r):
                    return x0, 0, r
    raise RuntimeError("no dovetail station fits %s" % TARGET[0])


def outline(s):
    """Polylines (x, z) of a plate's mid-thickness section."""
    bb = s.BoundBox
    return [[(v.x, v.z) for v in w.discretize(Deflection=0.05)] for w in s.slice(App.Vector(0, 1, 0), (bb.YMin + bb.YMax) / 2)]


def review(splits, path):
    """One row per split part: the whole plate (half A blue, half B orange) and a close-up of the joint."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(splits), 2, figsize=(15, 1.9 * len(splits)), gridspec_kw=dict(width_ratios=[3.2, 1]))
    for row, (name, x0, a, b) in zip(axs, splits):
        for ax, zoom in zip(row, (False, True)):
            for s, c in ((a, "#2b6cb0"), (b, "#dd6b20")):
                for w in outline(s):
                    xs, zs = zip(*w)
                    ax.plot(xs, zs, color=c, lw=0.9)
            ax.set_aspect("equal")
            ax.tick_params(labelsize=7)
            if zoom:
                ax.set_xlim(x0 - 22, x0 + 12)
                ax.set_title("joint at x %.0f" % x0, fontsize=8)
            else:
                ax.axvline(x0, color="0.6", lw=0.6, ls="--")
                ax.set_title("%s  (A blue, B orange; body frame, mm)" % name, fontsize=8, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    out = params.out_dir("print")
    sd = os.path.join(out, "stl")
    os.makedirs(sd, exist_ok=True)
    for f in os.listdir(sd):
        if f.endswith(".stl"):
            os.remove(os.path.join(sd, f))
    rows, unfit, cuts, splits = [], [], [], []
    for bn, parts in M.build_bodies().items():
        for p in parts:
            if p.kind == "CAT":
                continue
            if fit(dims_of(p.vis), TARGET):
                pieces, note = [("", p.vis)], p.note
            else:
                try:
                    x0, n, (a, b) = split(p.vis)
                except RuntimeError as e:
                    raise RuntimeError("%s: %s" % (p.name, e))
                pieces = [("_A", a), ("_B", b)]
                note = "glue the %s to the other half (CA or epoxy); joint at x %.0f" % (
                    "dovetail" if n == 1 else "%d dovetails" % n if n else "dovetail (lightening slot filled locally)", x0)
                cuts.append(p.name)
                if p.name.endswith(("_L_CF3", "_CF4")) or p.name.startswith("Rod_"):   # one of each mirrored pair
                    splits.append((p.name, x0, a, b))
            for suf, s in pieces:
                fn = STL % (p.name + suf)
                mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.2)
                mesh.write(os.path.join(sd, fn))
                d = dims_of(s)
                on = fit(d, TARGET)
                if not on:
                    unfit.append(fn)
                others = [b[0] + (" (diagonal)" if fit(d, b) == "diagonal" else "") for b in OTHERS if fit(d, b)]
                rows.append([fn, p.name, bn, MATERIAL.get(p.kind, p.kind), "%.0f x %.0f x %.1f" % tuple(d),
                             round(s.Volume / 1000.0, 1), on, "; ".join(others), p.src.replace("custom: ", ""), note])
    rows.sort(key=lambda r: (r[2], r[0]))
    with open(os.path.join(out, "print_list.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["file", "part", "body", "print in", "size_mm", "volume_cm3", TARGET[0], "also fits",
                    "production part", "note"])
        w.writerows(rows)
    st = "FAIL" if unfit else "PASS"
    note = "%d STL (%d parts; split for %s: %s), %.0f cm3; off the %s bed: %s" % (
        len(rows), len({r[1] for r in rows}), TARGET[0], ", ".join(cuts) or "none", sum(r[5] for r in rows),
        TARGET[0], ", ".join(unfit) or "none")
    review(splits, os.path.join(out, REVIEW))
    params.record("export_print", st, [os.path.join(out, "print_list.csv"), os.path.join(out, REVIEW)], note)
    print("PRINT %s: %s %s -> %s" % (M.VARIANT, st, note, out))
    return 1 if unfit else 0


sys.exit(main())
