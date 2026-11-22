# -*- coding: utf-8 -*-
"""
Fully printed fit-and-motion prototype of the ACTIVE variant: one STL per custom part, written under
cad/out/<variant>/print/ (the released package and the model are untouched; geometry is the model's, unchanged).

    python -I cad/tools/run.py cad/tools/export_print.py

Every custom part (CF plates, aluminium, steel shafts, shims, PTFE washers and the printed parts) is printed at its
modelled size. Purchased parts (servos, bearings, fasteners, pins, inserts, collars, e-clips, the spring) are bought.
Parts longer than a 256 mm bed are split in SPLITS with a glued dovetail in the plate's own plane, so the envelope and
every hole stay where the model has them (nothing new to collide).

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

K = params.load("arm")["K"]
# beds (x, y, z) mm; the team slices for these itself
BEDS = (("Ender 3 V3 / K1 SE", 220, 220, 250), ("P1S", 256, 256, 256), ("K2 Pro", 300, 300, 300),
        ("H2D", 325, 320, 325))
# part -> split station x (body frame) with the dovetail; the solid band there has no hole or pocket
SPLITS = {"Forearm_L_CF3": K["L3"] / 2, "Forearm_R_CF3": K["L3"] / 2}
STL = "%s.stl"                                              # file name per part (and _A / _B halves)
TAIL = dict(length=8.0, neck=8.0, head=12.0, clear=0.15)     # dovetail (mm), glued; clearance per side
MATERIAL = {"PRINT": "PETG or PLA", "CF": "PETG or PLA (plate, print flat)", "AL": "PETG or PLA",
            "STEEL": "PETG or PLA (or cut from the D10 rod)", "SHIM": "PETG or PLA (0.5 mm: 3 layers at 0.16)",
            "PTFE": "PETG or PLA", "TPU": "TPU 95A"}


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


def dovetail(x0, y0, y1, c):
    """Tail region of the +x piece, protruding into -x: neck at x0, head at x0 - length; grown by c."""
    L, n, h = TAIL["length"], TAIL["neck"] / 2 + c, TAIL["head"] / 2 + c
    pts = [App.Vector(x0 + 1.0, 0, -n), App.Vector(x0, 0, -n), App.Vector(x0 - L - c, 0, -h),
           App.Vector(x0 - L - c, 0, h), App.Vector(x0, 0, n), App.Vector(x0 + 1.0, 0, n)]
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return face.extrude(App.Vector(0, y1 - y0 + 2, 0)).translate(App.Vector(0, y0 - 1, 0))


def split(shape, x0):
    bb = shape.BoundBox
    big = 1000.0
    lo = Part.makeBox(x0 - bb.XMin + 1, big, big, App.Vector(bb.XMin - 1, -big / 2, -big / 2))
    hi = Part.makeBox(bb.XMax - x0 + 1, big, big, App.Vector(x0, -big / 2, -big / 2))
    tail = dovetail(x0, bb.YMin, bb.YMax, 0.0)
    a = shape.common(lo).cut(dovetail(x0, bb.YMin, bb.YMax, TAIL["clear"]))
    b = shape.common(hi).fuse(shape.common(tail)).removeSplitter()
    # the joint must stay inside solid material: the tail takes no less than its own area from the plate
    t = bb.YLength
    need = t * TAIL["length"] * (TAIL["neck"] + TAIL["head"]) / 2
    if shape.common(tail).Volume < need - 1.0 or not (a.isValid() and b.isValid()):
        raise RuntimeError("dovetail at x=%.1f leaves solid material or is invalid" % x0)
    return a, b


def main():
    out = params.out_dir("print")
    sd = os.path.join(out, "stl")
    os.makedirs(sd, exist_ok=True)
    for f in os.listdir(sd):
        if f.endswith(".stl"):
            os.remove(os.path.join(sd, f))
    rows, unfit = [], []
    for bn, parts in M.build_bodies().items():
        for p in parts:
            if p.kind == "CAT":
                continue
            pieces = list(zip(("_A", "_B"), split(p.vis, SPLITS[p.name]))) if p.name in SPLITS else [("", p.vis)]
            for suf, s in pieces:
                fn = STL % (p.name + suf)
                mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.2)
                mesh.write(os.path.join(sd, fn))
                bb = s.BoundBox
                dims = sorted((bb.XLength, bb.YLength, bb.ZLength), reverse=True)
                fits = [b[0] + (" (diagonal)" if fit(dims, b) == "diagonal" else "") for b in BEDS if fit(dims, b)]
                if not fits:
                    unfit.append(fn)
                note = "glue the dovetail to the other half (CA or epoxy)" if suf else p.note
                rows.append([fn, p.name, bn, MATERIAL.get(p.kind, p.kind), "%.0f x %.0f x %.1f" % tuple(dims),
                             round(s.Volume / 1000.0, 1), "; ".join(fits), p.src.replace("custom: ", ""), note])
    rows.sort(key=lambda r: (r[2], r[0]))
    with open(os.path.join(out, "print_list.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["file", "part", "body", "print in", "size_mm", "volume_cm3", "fits", "production part", "note"])
        w.writerows(rows)
    st = "FAIL" if unfit else "PASS"
    note = "%d STL (%d parts, %d split), %.0f cm3; no bed fits: %s" % (
        len(rows), len({r[1] for r in rows}), len(SPLITS), sum(r[5] for r in rows), ", ".join(unfit) or "none")
    params.record("export_print", st, [os.path.join(out, "print_list.csv")], note)
    print("PRINT %s: %s %s -> %s" % (M.VARIANT, st, note, out))
    return 1 if unfit else 0


sys.exit(main())
