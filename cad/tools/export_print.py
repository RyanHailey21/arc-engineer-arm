# -*- coding: utf-8 -*-
"""
Fully printed fit-and-motion prototype of the ACTIVE variant: one STL per custom part, written under
cad/out/<variant>/print/ (the released package and the model are untouched; geometry is the model's, unchanged).

    python -I cad/tools/run.py cad/tools/export_print.py

Every custom part (CF plates, aluminium, steel shafts, shims, PTFE washers and the printed parts) is printed at its
modelled size. Purchased parts (servos, bearings, fasteners, pins, inserts, collars, e-clips, the spring) are bought.
TARGET is the printer the pack is cut for (the UTA ERB 335 Ender-3 S1 Pros, PLA or PETG). A part that does not fit it,
flat or diagonally, is split in two with a glued dovetail in the plate's own plane, at the station nearest mid-length
where the dovetail has WALL mm of solid material all round; both halves must then fit. One centred tail is
preferred (in solid material, else with the plate's lightening slot filled locally); a mirrored pair is the last resort.
The socket wall each split achieved is measured and listed (print 1, 2026-11-26: 2 mm socket cheeks broke at fitting). The outline and every hole stay
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
FONT = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "arial.ttf")   # test-piece labels (skipped if missing)
# test pieces, printed before the arm: the dovetail at four clearances (pick the one that slides in with glue room,
# then set CLEAR), and every bore the arm uses at its modelled size plus oversize steps (how much to drill or ream)
DOVETAIL_CLEARS = (0.10, 0.15, 0.20, 0.25)
FIT_SMALL = (("MR105", 10.0), ("6700", 15.0), ("6701", 18.0), ("pin", 4.0), ("", 4.1), ("", 4.2), ("", 4.3),
             ("insert", 4.0), ("M3", 3.3), ("SB5", 5.0), ("D10", 10.0), ("", 10.2))
FIT_LARGE = (("6804", 32.0), ("6805", 37.0))
STL = "%s.stl"                                              # file name per part (and _A / _B halves)
# dovetail sizes (mm), largest first; glued, clearance per side. Each split takes the largest that fits with WALL.
TAILS = (dict(length=8.0, neck=8.0, head=12.0), dict(length=7.0, neck=5.0, head=8.0),
         dict(length=6.0, neck=4.0, head=6.0))
CLEAR = 0.15
WALL = 4.0          # solid material round the socket; 2.0 broke the socket cheeks of the first PLA print
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


def solid_at(shape, x0, tail, zs, wall=WALL):
    """The dovetail(s) plus wall lie wholly in material (no hole, pocket or edge within wall)."""
    bb = shape.BoundBox
    for z in zs:                                        # one probe per tail, cheapest first
        pr = dovetail(x0, bb.YMin + 0.01, bb.YMax - 0.01, tail, wall, (z,))
        pr = pr.common(Part.makeBox(pr.BoundBox.XLength, bb.YLength - 0.02, pr.BoundBox.ZLength,
                                    App.Vector(pr.BoundBox.XMin, bb.YMin + 0.01, pr.BoundBox.ZMin)))
        if abs(shape.common(pr).Volume - pr.Volume) > 1e-3 * pr.Volume:
            return False
    return True


def wall_at(shape, x0, tail, zs, step=0.25, top=10.0):
    """The solid material actually left round the socket (mm, to step): the largest wall solid_at accepts."""
    w = 0.0
    while w + step <= top and solid_at(shape, x0, tail, zs, w + step):
        w += step
    return w


def cut_at(shape, x0, tail, zs, clear=CLEAR):
    """(A, B) halves at x0 with the dovetail(s) at zs, or None."""
    if not solid_at(shape, x0, tail, zs):
        return None
    bb = shape.BoundBox
    big = 1000.0
    lo = Part.makeBox(x0 - bb.XMin + 1, big, big, App.Vector(bb.XMin - 1, -big / 2, -big / 2))
    hi = Part.makeBox(bb.XMax - x0 + 1, big, big, App.Vector(x0, -big / 2, -big / 2))
    a = shape.common(lo).cut(dovetail(x0, bb.YMin, bb.YMax, tail, clear, zs))
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
    """Dovetail split nearest mid-length (x in the body frame) with both halves on TARGET: (x0, n, (A, B), wall), n the
    tail count (0: one tail with the lightening slot filled locally), wall the material measured round the socket.
    Preference: one centred tail in solid material, then one centred tail with the slot filled, then a mirrored pair
    above and below a hole on the centre line (the smallest tail)."""
    bb = shape.BoundBox
    mid = (bb.XMin + bb.XMax) / 2
    zc = (bb.ZMin + bb.ZMax) / 2
    tails = [t_ for t_ in TAILS if t_["head"] + 2 * (CLEAR + WALL) <= bb.ZLength]

    def stations(frac):
        for k in range(0, int(bb.XLength * frac)):
            for x0 in (mid + k, mid - k) if k else (mid,):
                yield x0

    def ok(sh, x0, tail, zs):
        r = cut_at(sh, x0, tail, zs)
        return r if r and all(fit(dims_of(s), TARGET) for s in r) else None

    for x0 in stations(0.5):                            # 1. one centred tail, solid
        for tail in tails:
            r = ok(shape, x0, tail, (zc,))
            if r:
                return x0, 1, r, wall_at(shape, x0, tail, (zc,))
    for x0 in stations(0.25):                           # 2. one centred tail, slot filled locally
        for tail in tails:
            sh = filled(shape, x0 - tail["length"] / 2, tail["length"] + WALL + 6)
            r = ok(sh, x0, tail, (zc,))
            if r:
                return x0, 0, r, wall_at(sh, x0, tail, (zc,))
    small = TAILS[-1]                                   # 3. mirrored pair
    for x0 in stations(0.5):
        for d in [x / 2.0 for x in range(8, int(bb.ZLength))]:
            r = ok(shape, x0, small, (zc - d, zc + d))
            if r:
                return x0, 2, r, wall_at(shape, x0, small, (zc - d, zc + d))
    raise RuntimeError("no dovetail station with %g mm wall fits %s" % (WALL, TARGET[0]))


def label(shape, text, x, y, z_top, size=3.5, depth=0.5):
    """Engrave text into the top face (z = z_top) at (x, y); returns shape unchanged without the font."""
    if not os.path.exists(FONT) or not text:
        return shape
    wires = Part.makeWireString(text, FONT, size, 0)
    faces = []
    for ch in wires:
        for w in ch:
            if w.isClosed():
                faces.append(Part.Face(w))
    if not faces:
        return shape
    f = faces[0].fuse(faces[1:]) if len(faces) > 1 else faces[0]
    f = Part.makeCompound([x_ for x_ in f.Faces])
    bb = f.BoundBox
    f.translate(App.Vector(x - bb.XLength / 2 - bb.XMin, y - bb.YMin, z_top - depth))
    tool = Part.makeCompound([fc.extrude(App.Vector(0, 0, depth + 1)) for fc in f.Faces])
    return shape.cut(tool)


def dovetail_test():
    """Four 30 x 17 x 3 plate pairs, laid flat (z up), the middle tail at DOVETAIL_CLEARS; the clearance is engraved
    on half A. (Its 4.3 mm cheeks are just above WALL; it tests the clearance, which carries to every tail size.)"""
    tail = TAILS[1]
    pieces = []
    for i, c in enumerate(DOVETAIL_CLEARS):
        blank = Part.makeBox(30, 3, 17, App.Vector(-15, -1.5, -8.5))
        a, b = cut_at(blank, 0.0, tail, (0.0,), clear=c)
        for s in (a, b):
            s.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)        # plate normal y -> z, thickness 0..3
            s.translate(App.Vector(0, i * 22.0, 1.5))
        a = label(a, "%.2f" % c, -12.0, i * 22.0 - 1.25, 3.0, size=2.5, depth=0.4)
        pieces += [a, b.translate(App.Vector(14, 0, 0))]           # printed apart: tail tip 7 mm clear of A
    return Part.makeCompound(pieces)


def fit_test(bores, t, pitch_pad=5.0):
    """A plate t thick with one through bore per (name, D) in a row, labelled with name and size."""
    xs, x = [], 0.0
    for _n, d in bores:
        x += d / 2
        xs.append(x)
        x += d / 2 + pitch_pad
    width = max(d for _n, d in bores) + 14
    plate_ = Part.makeBox(x + pitch_pad, width, t, App.Vector(-pitch_pad, -width / 2 + 4, 0))
    for (n, d), xc in zip(bores, xs):
        plate_ = plate_.cut(Part.makeCylinder(d / 2, t + 2, App.Vector(xc, 4, -1)))
        plate_ = label(plate_, "%g" % d, xc, -width / 2 + 5.0, t, size=3.0)
        plate_ = label(plate_, n, xc, 4 + d / 2 + 1.5, t, size=3.0)
    return plate_


def test_pieces(sd):
    """Write the test-piece STLs; return their print_list rows."""
    rows = []
    for name, s, what in (("Test_Dovetail", dovetail_test(),
                           "dovetail at %s mm clearance per side; pick the pair that slides together with room for "
                           "glue, then set CLEAR in export_print.py" % ", ".join("%g" % c for c in DOVETAIL_CLEARS)),
                          ("Test_Fit_Small", fit_test(FIT_SMALL, 4.0),
                           "bores at modelled size (bearing seats, pin 4.0 with +0.1..+0.3 steps, insert, M3 clearance, "
                           "shoulder screw, D10 with a +0.2 step): note how much each needs drilling or reaming"),
                          ("Test_Fit_Large", fit_test(FIT_LARGE, 7.0), "6804 and 6805 bearing seats at modelled size")):
        fn = STL % name
        MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.2).write(os.path.join(sd, fn))
        d = dims_of(s)
        rows.append([fn, name, "TEST", "the filament you will print the arm in", "%.0f x %.0f x %.1f" % tuple(d),
                     round(s.Volume / 1000.0, 1), fit(d, TARGET), "", "test piece", what])
    return rows


def main():
    out = params.out_dir("print")
    sd = os.path.join(out, "stl")
    os.makedirs(sd, exist_ok=True)
    for f in os.listdir(sd):
        if f.endswith(".stl"):
            os.remove(os.path.join(sd, f))
    rows, unfit, cuts, walls = [], [], [], []
    for bn, parts in M.build_bodies().items():
        for p in parts:
            if p.kind == "CAT":
                continue
            if fit(dims_of(p.vis), TARGET):
                pieces, note = [("", p.vis)], p.note
            else:
                try:
                    x0, n, (a, b), wall = split(p.vis)
                except RuntimeError as e:
                    raise RuntimeError("%s: %s" % (p.name, e))
                pieces = [("_A", a), ("_B", b)]
                note = "glue the %s to the other half (CA or epoxy); joint at x %.0f" % (
                    "dovetail" if n == 1 else "%d dovetails" % n if n else "dovetail (lightening slot filled locally)", x0)
                note += "; socket wall %.2f mm" % wall
                cuts.append(p.name)
                walls.append(wall)
                if wall < WALL:
                    unfit.append("%s (socket wall %.2f < %g mm)" % (p.name, wall, WALL))
            for suf, s in pieces:
                fn = STL % (p.name + suf)
                n_sh = sum(len(x.Shells) for x in s.Solids)
                if n_sh != 1:                   # a piece in mid-air prints as string (Level_Hub_*, 2026-11-27)
                    unfit.append("%s (%d disconnected shells)" % (fn, n_sh))
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
    rows = test_pieces(sd) + rows
    with open(os.path.join(out, "print_list.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["file", "part", "body", "print in", "size_mm", "volume_cm3", TARGET[0], "also fits",
                    "production part", "note"])
        w.writerows(rows)
    st = "FAIL" if unfit else "PASS"
    note = "%d STL (%d parts; split for %s: %s; socket wall >= %.2f mm), %.0f cm3; failed: %s" % (
        len(rows), len({r[1] for r in rows}), TARGET[0], ", ".join(cuts) or "none", min(walls or [0]),
        sum(r[5] for r in rows), ", ".join(unfit) or "none")
    params.record("export_print", st, [os.path.join(out, "print_list.csv")], note)
    print("PRINT %s: %s %s -> %s" % (M.VARIANT, st, note, out))
    return 1 if unfit else 0


sys.exit(main())
