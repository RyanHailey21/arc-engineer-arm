# -*- coding: utf-8 -*-
"""
Fabrication outputs (headless):  freecadcmd export_fab.py
  fab/BOM.csv                 purchased + custom parts, qty, mass, process, notes
  fab/dxf/<plate>.dxf         2D cut profiles for every 3 mm CF plate (1:1 mm)
  fab/step/<part>.step        every custom part in its body frame
  fab/step/ARC_Arm_STOW.step  full assembly at the stowed pose
"""
import csv
import math
import os
import sys
from collections import OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, HERE)
import FreeCAD as App   # noqa: E402
import Part             # noqa: E402
import params   # noqa: E402
params.use_release_variant('export_fab.py')   # writes the released package
import arm_model as M   # noqa: E402

OUT = os.path.join(HERE, "fab")
for d in (OUT, os.path.join(OUT, "dxf"), os.path.join(OUT, "step")):
    os.makedirs(d, exist_ok=True)

def plate_face(shape):
    """Largest planar face of a plate.  XZ plates (normal Y) are returned as is; XY
    plates (normal Z: bridge, finger plates) are rotated +90 deg about X so the
    DXF writer's (x, z) output is the plate's (x, y)."""
    best, axis = None, None
    for f in shape.Faces:
        try:
            n = f.normalAt(0, 0)
        except Exception:
            continue
        for ax, comp in (("y", n.y), ("z", n.z)):
            if abs(abs(comp) - 1) < 1e-6 and (best is None or f.Area > best.Area + 1e-6):
                best, axis = f, ax
    if best is not None and axis == "z":
        best = best.copy()
        best.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
    return best


def write_dxf(face, path):
    """Minimal R12 DXF of a face lying in an XZ plane (outputs X, Z)."""
    ents = []
    for e in face.Edges:
        c = e.Curve
        if isinstance(c, Part.Line) or e.Curve.TypeId == "Part::GeomLine":
            p1, p2 = e.Vertexes[0].Point, e.Vertexes[-1].Point
            ents.append(("LINE", p1.x, p1.z, p2.x, p2.z))
        elif e.Curve.TypeId == "Part::GeomCircle":
            cx, cz, r = c.Center.x, c.Center.z, c.Radius
            if e.isClosed():
                ents.append(("CIRCLE", cx, cz, r))
            else:
                p1, p2 = e.Vertexes[0].Point, e.Vertexes[-1].Point
                pm = e.valueAt((e.FirstParameter + e.LastParameter) / 2)
                a1 = math.degrees(math.atan2(p1.z - cz, p1.x - cx)) % 360
                a2 = math.degrees(math.atan2(p2.z - cz, p2.x - cx)) % 360
                am = math.degrees(math.atan2(pm.z - cz, pm.x - cx)) % 360
                if not ((a2 - a1) % 360 > (am - a1) % 360):
                    a1, a2 = a2, a1
                ents.append(("ARC", cx, cz, r, a1, a2))
        else:   # fallback: polyline discretisation
            pts = e.discretize(24)
            for p, q in zip(pts[:-1], pts[1:]):
                ents.append(("LINE", p.x, p.z, q.x, q.z))
    with open(path, "w") as f:
        f.write("0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n")
        for e in ents:
            if e[0] == "LINE":
                f.write("0\nLINE\n8\nCUT\n10\n%.4f\n20\n%.4f\n11\n%.4f\n21\n%.4f\n" % e[1:])
            elif e[0] == "CIRCLE":
                f.write("0\nCIRCLE\n8\nCUT\n10\n%.4f\n20\n%.4f\n40\n%.4f\n" % e[1:])
            else:
                f.write("0\nARC\n8\nCUT\n10\n%.4f\n20\n%.4f\n40\n%.4f\n50\n%.4f\n51\n%.4f\n" % e[1:])
        f.write("0\nENDSEC\n0\nEOF\n")
    return len(ents)


def spec_of(p):
    n = p.name
    for pre in ("SHCS_", "BHCS_", "CSK_", "Nyloc_", "Dowel_", "SB5x", "Insert_", "Washer_", "Eclip_", "Shim_",
                "UA_Standoff_", "FA_Standoff_", "Servo_Standoff_", "Finger_Standoff_", "Brg_", "Spacer_",
                "SetScrew_", "Collar_", "Cable_Clip_"):
        if n.startswith(pre):
            tok = n.split("_")
            return "_".join(tok[:2]) if pre not in ("Brg_",) else "Brg_" + p.src
    return p.src


def main():
    bodies = M.build_bodies()
    custom = OrderedDict()
    cat = defaultdict(int)
    for bname, parts in bodies.items():
        for p in parts:
            if "rotor" in p.name:
                continue
            if p.kind == "CAT":
                cat[(p.src, spec_of(p))] += 1
            else:
                custom[p.name] = (bname, p)
    rows = []
    tot = 0.0
    for (key, spec), n in sorted(cat.items()):
        c = M.CAT.get(key, {})
        m = c.get("mass", 0) * n
        tot += m
        rows.append(["PURCHASED", spec, c.get("desc", key), n, "%.0f" % m, "", c.get("verify", c.get("src", ""))])
    for name, (bname, p) in custom.items():
        m = M.part_mass_g(p)
        tot += m
        bb = p.vis.BoundBox
        rows.append(["CUSTOM", name, "%s; body %s; env %.0fx%.0fx%.0f mm" % (p.src, bname, bb.XLength, bb.YLength, bb.ZLength),
                     1, "%.0f" % m, p.kind, p.note])
    with open(os.path.join(OUT, "BOM.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type", "item", "description / process", "qty", "mass_g", "material", "notes / source / VERIFY"])
        w.writerows(rows)
        w.writerow([])
        w.writerow(["TOTAL", "", "modelled mass (motors, gripper drive, all hardware)", "", "%.0f" % tot, "", ""])
    print("BOM rows %d, total %.0f g" % (len(rows), tot))
    ndxf = 0
    for name, (bname, p) in custom.items():
        p.vis.exportStep(os.path.join(OUT, "step", name + ".step"))
        if p.kind == "CF":
            face = plate_face(p.vis)
            if face is None:
                print("  no planar face for", name)
                continue
            write_dxf(face, os.path.join(OUT, "dxf", name + ".dxf"))
            ndxf += 1
    print("DXF files:", ndxf)
    for pose in ("STOW", "DONUT_LIFT", "PIPE_CHUTE_ROLL90"):
        q, jaw = M.pose_q(pose)
        shapes = [s for (_b, _p, s) in M.placed(bodies, *q, jaw=jaw, which="vis")]
        Part.makeCompound(shapes).exportStep(os.path.join(OUT, "step", "ARC_Arm_%s.step" % pose))
    print("STEP done")
    # files the current model no longer produces -> fab/obsolete/ (moved, not deleted) so a shop
    # given fab/step or fab/dxf cannot pick up a superseded part
    import shutil
    keep = {n + ".step" for n in custom} | {"ARC_Arm_%s.step" % p_ for p_ in ("STOW", "DONUT_LIFT", "PIPE_CHUTE_ROLL90")}
    keep_dxf = {n + ".dxf" for n, (_b, p) in custom.items() if p.kind == "CF"}
    moved = 0
    for sub, ok in (("step", keep), ("dxf", keep_dxf)):
        dst = os.path.join(OUT, "obsolete", sub)
        for fn in os.listdir(os.path.join(OUT, sub)):
            if fn not in ok:
                os.makedirs(dst, exist_ok=True)
                shutil.move(os.path.join(OUT, sub, fn), os.path.join(dst, fn))
                moved += 1
    print("obsolete files moved:", moved)


main()
