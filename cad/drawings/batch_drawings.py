# -*- coding: utf-8 -*-
"""
Batch manufacturing drawings for every custom part (ASME Y14.5-2018, reduced-dimension
model-based drawings: critical sizes, hole callouts with position FCFs, datum reference
frame, all-around profile; undimensioned geometry is BASIC from the STEP model / DXF).
Run inside the FreeCAD GUI after make_drawings.py has been exec'd into the same dict:
    g = {}; exec(open(r"<repo>/cad/drawings/make_drawings.py", encoding="utf-8").read(), g)
    exec(open(r"<repo>/cad/drawings/batch_drawings.py", encoding="utf-8").read(), g)
    g["batch"](start=0, count=5)          # chunks keep each GUI call short
Only native TechDraw objects: DrawProjGroup (third angle), DrawViewPart (iso),
DrawViewDimension, DrawViewBalloon (datums, FCFs, hole callouts), DrawRichAnno (notes),
and the project template ANSIB_Landscape_Y14.svg (title + tolerance block fields).
"""
import json
import math
import re
import os
import sys
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part

V = App.Vector
CSK = "⌵"                                         # countersink symbol
if os.path.join(HERE, 'drawings') not in sys.path:
    sys.path.insert(0, os.path.join(HERE, 'drawings'))
import importlib, asme_rules as R
importlib.reload(R)
SCALES = [5, 4, 3, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.3, 0.25, 0.2]
LOG = os.path.join(OUT, "batch_log.txt")
DENS = {"AL": 2.70, "CF": 1.55, "PRINT": 1.30, "TPU": 1.20, "STEEL": 7.85, "SHIM": 7.9, "PTFE": 2.2, "BRASS": 8.5}
PROCESS = {
    "CF": dict(title2="3 mm CARBON FIBER PLATE", title3="CNC ROUTED / WATERJET FROM DXF",
               pos="0.1", prof="0.2", tol={"TOL_LIN1": "LINEAR ±0.2", "TOL_LIN2": "HOLE ⌀ +0.1/0",
                                            "TOL_FINISH": "EDGES: DEBURR, SEAL WITH CA"},
               notes=["MATERIAL: 3 mm CARBON FIBER PLATE, 3K TWILL, QUASI-ISOTROPIC LAYUP.",
                      "CUT PROFILE AND THRU HOLES FROM DXF {dxf} (1:1, mm); HOLES MARKED REAM/BORE: CUT 0.3 UNDERSIZE ON DIA, THEN FINISH TO THE CALLOUT.",
                      "HOLE ⌀ +0.1/0 (TOLERANCE BLOCK). NO DELAMINATION OR FRAYING AT EDGES OR HOLES.",
                      "@CSK"]),
    "AL": dict(title2="6061-T6 ALUMINUM", title3="CLEAR ANODIZE (MIL-A-8625 TYPE II)",
               pos="0.05", prof="0.1", tol={},
               notes=["MATERIAL: 6061-T6 ALUMINUM.",
                      "@MASK",
                      "BREAK ALL SHARP EDGES 0.2-0.4.",
                      "@THREADS"]),
    "PRINT": dict(title2="PETG-CF (FDM)", title3="FDM PRINT - SEE NOTES",
                  pos="0.2", prof="0.3", tol={"TOL_LIN1": "LINEAR ±0.2", "TOL_LIN2": "HOLE ⌀ ±0.15",
                                               "TOL_FINISH": "SURFACE: AS PRINTED"},
                  notes=["MATERIAL: PETG-CF, FDM. PRINT FROM STEP {step}; HOLES MARKED REAM/BORE: PRINT 0.3 UNDERSIZE ON DIA, THEN FINISH TO THE CALLOUT.",
                         "0.2 mm LAYERS, 4 PERIMETERS, 5 TOP/BOTTOM, 40% GYROID INFILL.",
                         "@INSERT",
                         "PRINT WITH THE DATUM A FACE ON THE BED."]),
    "STEEL": dict(title2="1055 STEEL, CASE HARDENED HRC 59", title3="FROM D10 h6 GROUND ROD",
                  pos="0.05", prof="0.05", tol={"TOL_LIN1": "LINEAR ±0.1", "TOL_LIN2": "DIA: AS ROD (h6)",
                                                "TOL_FINISH": "GROUND FEATURES Ra 0.8"},
                  notes=["MATERIAL: McMASTER-CARR 6112K47, 1055 STEEL D10 h6 x 500, CASE HARDENED HRC 59.",
                         "@SHAFT",
                         "BREAK SHARP EDGES 0.2. D10 h6 ROD SURFACE AS SUPPLIED - DO NOT GRIND IT."]),
    "SHIM": dict(title2="301 STAINLESS SHIM STOCK", title3="LASER CUT / ETCHED",
                 pos="0.05", prof="0.1", tol={"TOL_LIN1": "LINEAR ±0.05 (EXCEPT THICKNESS)", "TOL_LIN2": "THICKNESS: STOCK ±0.01",
                                              "TOL_FINISH": "EDGES BURR-FREE"},
                 notes=["@SHIMMAT",
                        "NO BURRS. FLATNESS PER FCF ON THE SIDE VIEW."]),
    "BRASS": dict(title2="BRASS CW614N (C36000)", title3="TURNED + THREAD-MILLED",
                  pos="0.05", prof="0.1", tol={"TOL_LIN1": "LINEAR ±0.1", "TOL_LIN2": "HOLE ⌀ +0.1/0",
                                               "TOL_FINISH": "Ra 1.6 THREAD FLANKS"},
                  notes=["MATERIAL: FREE-CUTTING BRASS CW614N / C36000.",
                         "INTERNAL THREAD Tr8x8(P2) LEFT-HAND, 4-START, PER ISO 2904 / ISO 2903 CLASS 7H, THREAD-MILLED (MATES THE LH SCREW SECTION); CHECK: SCREW RUNS FREE BY HAND.",
                         "BREAK SHARP EDGES 0.2."]),
    "PTFE": dict(title2="PTFE (VIRGIN)", title3="TURNED FROM D13 ROD",
                 pos="0.1", prof="0.1", tol={"TOL_LIN1": "LINEAR ±0.1", "TOL_LIN2": "BORE ⌀ +0.1/0",
                                             "TOL_FINISH": "AS TURNED"},
                 notes=["MATERIAL: VIRGIN PTFE ROD D13.", "TURN FROM STEP {step}.",
                        "BORE SLIP FIT ON D10 h6 SHAFT."]),
    "TPU": dict(title2="TPU 95A (FDM)", title3="GRIP PAD", pos="0.3", prof="0.4",
                tol={"TOL_LIN1": "LINEAR ±0.3", "TOL_LIN2": "HOLE ⌀ ±0.2", "TOL_FINISH": "SURFACE: AS PRINTED"},
                notes=["MATERIAL: TPU 95A, FDM. PRINT FROM STEP {step}.",
                       "0.2 mm LAYERS, 3 PERIMETERS, 30% INFILL.",
                       "BOND TO FINGER PLATES AFTER ASSEMBLY ON STANDOFFS (OPTIONAL)."]),
}


# Sheet revisions.  A sheet whose part still matches its STEP export in the previous package (PREV_STEP, a copy of
# fab/step taken before export_fab.py rewrites it) keeps its letter; a changed part steps to REV with REV_NOTE.
# New parts start at "A".  REV_REASON adds a specific line for known changes.
REV, REV_DATE = "B", "2026-11-19"
PREV_STEP = os.environ.get("PREV_STEP", "")
REV_NOTE = "GEOMETRY CHANGED SINCE REV A (STS3215 DRIVES, LEVEL-KEEPING LINKAGE); SUPERSEDES REV A"
REV_REASON = {
    "J1_Output_Hub": "MOTOR FLANGE REPLACED BY A STUB: " + "\u2300" + "24 COLLAR, 19 AF HEX FOR THE 54T GEAR, " + "\u2300" + "20 JOURNAL IN A 6804, M5 END.",
    "J2_Output_Hub_Journal": "MOTOR FLANGE REPLACED BY A STUB: " + "\u2300" + "24 COLLAR, 19 AF HEX FOR THE 54T GEAR, " + "\u2300" + "20 JOURNAL IN A 6804, M5 END.",
    "Tower_L_CF3": "MOTOR BOLT PATTERN REPLACED BY 3X " + "\u2300" + "3.3 FOR THE DRIVE FRAME LEGS; OUTLINE GROWN TO THE LEGS.",
    "Tower_R_CF3": "MOTOR BOLT PATTERN REPLACED BY 3X " + "\u2300" + "3.3 FOR THE DRIVE FRAME LEGS; OUTLINE GROWN TO THE LEGS.",
    "Wrist_Level_Member_CF3": "SERVO HOLES MOVED TO THE STS3215 CRADLE PILLARS.",
    "Roll_Housing": "STS3215 POCKET AND FLOOR REPLACE THE DS3225 EAR BULKHEAD.",
}


def sheet_rev(p, shape):
    """-> (letter, note or None).  Compares volume, area and bounding box with the previous package's STEP."""
    f = os.path.join(PREV_STEP, p.name + ".step") if PREV_STEP else ""
    if not f or not os.path.exists(f):
        return ("A", None)
    try:
        old = Part.read(f)
        a, b = old, p.vis
        same = (abs(a.Volume - b.Volume) < 0.5 and abs(a.Area - b.Area) < 0.5
                and all(abs(x - y) < 0.05 for x, y in zip(sorted((a.BoundBox.XLength, a.BoundBox.YLength, a.BoundBox.ZLength)),
                                                         sorted((b.BoundBox.XLength, b.BoundBox.YLength, b.BoundBox.ZLength)))))
    except Exception:
        same = False
    if same:
        return ("A", None)
    return (REV, "REV %s (%s): %s" % (REV, REV_DATE, REV_REASON.get(p.name, REV_NOTE)))


EXTRA_NOTES = {                                    # features the hole/fit logic cannot recognise
    "J1_Output_Hub": "HEX DRIVES THE 54T DRIVE GEAR (PRINTED); " + "\u2300" + "20 JOURNAL RUNS IN A 6804 IN THE DRIVE FRAME; "
                     "M5 x 10 END SCREW + WASHER CLAMP THE INNER RACE (interfaces/base_hub__drive.toml).",
    "J2_Output_Hub": "HEX DRIVES THE 54T DRIVE GEAR (PRINTED); " + "\u2300" + "20 JOURNAL RUNS IN A 6804 IN THE DRIVE FRAME; "
                     "M5 x 10 END SCREW + WASHER CLAMP THE INNER RACE (interfaces/base_hub__drive.toml).",
    "Drive_Frame": "CARRIES THE 6804 (PRESS FIT IN THE BORE, LIP OUTBOARD) AND THE STS3215 (POCKET + 4 BOTTOM-CAP SCREWS); "
                   "3 LEGS WITH M3 HEAT-SET INSERTS BOLT TO THE TOWER (interfaces/drive_frame__tower.toml).",
    "Wrist_Servo_Cradle": "HOLDS THE J3 STS3215 (POCKET + 4 BOTTOM-CAP SCREWS); 4 PILLARS WITH M3 HEAT-SET INSERTS "
                          "(interfaces/level_member__j3_cradle.toml).",
    "GT2_Pulley": "HEX BOSS MATES THE ARC-121/ARC-127 HEX HOLE.",
    "Level_Rocker": "HEX HOLE: SHARP CORNERS AS MODELLED; DOG-BONE RELIEF OUTSIDE THE FLATS PERMITTED. MATES THE ARC-104 HEX BOSS.",
    "Wrist_Level_Member": "HEX HOLE: SHARP CORNERS AS MODELLED; DOG-BONE RELIEF OUTSIDE THE FLATS PERMITTED. MATES THE ARC-104 HEX BOSS.",
}


def log(msg):
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


# ------------------------------------------------------------- part list / grouping
def custom_parts():
    import arm
    import params
    params.use_release_variant('batch_drawings.py')   # drawings are the released package
    arm.reload_all()                       # hardware, iface, arm.* and the arm_model facade, in order
    import arm_model as M
    M._BODIES.clear()
    bodies = M.build_bodies()
    groups = {}
    for bname, parts in bodies.items():
        for p in parts:
            if p.kind == "CAT" or p.vis.isNull():
                continue
            if p.name == "J1_Output_Hub":             # pilot sheet number ARC-101, drawn by the same generator
                _CACHE["j1"] = [p]
                continue
            s = p.vis
            bb = s.BoundBox
            key = (p.kind, round(s.Volume, 0), round(s.Area, 0), tuple(sorted(round(x, 1) for x in (bb.XLength, bb.YLength, bb.ZLength))))
            groups.setdefault(key, []).append(p)
    out = []
    for key, ps in groups.items():
        out.append(ps)
    out.sort(key=lambda ps: (["AL", "CF", "PRINT", "TPU", "STEEL", "SHIM", "PTFE", "BRASS"].index(ps[0].kind) if ps[0].kind in DENS else 9, ps[0].name))
    try:                                   # stable ARC numbers: a group keeps its previous slot, new groups append
        prev = json.load(open(os.path.join(OUT, "batch_index.json")))
    except Exception:
        prev = []
    pos = {names[0]: i for i, names in enumerate(prev)}
    old = sorted([g for g in out if g[0].name in pos], key=lambda g: pos[g[0].name])
    new = [g for g in out if g[0].name not in pos]
    out = old + new
    nums = [pos[g[0].name] for g in old] + [len(prev) + k for k in range(len(new))]
    index = [list(n) for n in prev] + [[q.name for q in g] for g in new]      # removed groups keep their slot
    _CACHE["nums"], _CACHE["index"] = nums, index
    return out


def _hole_axis_counts(shape):
    cnt = [set(), set(), set()]
    for f in shape.Faces:
        srf = f.Surface
        if srf.__class__.__name__ != "Cylinder" or not (0.9 <= srf.Radius <= 12.5):
            continue
        u0, u1, v0, v1 = f.ParameterRange
        p_ = f.valueAt((u0 + u1) / 2, (v0 + v1) / 2)
        n = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        ax, c = V(srf.Axis), V(srf.Center)
        radial = (p_ - c) - ax * ((p_ - c).dot(ax))
        if radial.Length < 1e-9 or n.dot(radial) > 0:
            continue
        for i, comp in enumerate((ax.x, ax.y, ax.z)):
            if abs(abs(comp) - 1) < 1e-3:
                cnt[i].add((round(c.x, 1), round(c.y, 1), round(c.z, 1), round(srf.Radius, 2)))
    return [sum(k[3] for k in c) for c in cnt]      # weighted by radius: the main bore sets the view axis


def oriented(shape):
    """Copy re-axed for drawing: Z = the axis most holes run along (else the thinnest),
    X = longest remaining extent; centred in XY, Z from 0."""
    s = shape.copy()
    bb = s.BoundBox
    L = [bb.XLength, bb.YLength, bb.ZLength]
    hc = _hole_axis_counts(s)
    zax = max(range(3), key=lambda i: (hc[i], -L[i])) if max(hc) > 0 else min(range(3), key=lambda i: L[i])
    rest = sorted([i for i in range(3) if i != zax], key=lambda i: -L[i])
    order = [rest[0], rest[1], zax]
    cols = [V(*[1.0 if k == i else 0.0 for k in range(3)]) for i in order]
    m = App.Matrix(cols[0].x, cols[0].y, cols[0].z, 0, cols[1].x, cols[1].y, cols[1].z, 0,
                   cols[2].x, cols[2].y, cols[2].z, 0, 0, 0, 0, 1)
    if m.determinant() < 0:                       # keep right-handed: flip the view axis
        m.A31, m.A32, m.A33 = -m.A31, -m.A32, -m.A33
    s.transformShape(m)
    c = s.BoundBox.Center
    tv = V(-c.x, -c.y, -s.BoundBox.ZMin)
    s.translate(tv)
    _XF["m"], _XF["t"] = m, tv                      # part frame -> drawing frame (projected-height lookup)
    return s


_XF = {}
_PH_DETAIL = {}


def group_proj_height(part, thread, hs):
    """Projected-zone height for THIS hole group: the thickest mating stack measured at these holes
    (tools/projected_heights.py detail, mapped into the drawing frame). None = no mating part."""
    if not _PH_DETAIL:
        try:
            _PH_DETAIL["d"] = json.load(open(os.path.join(HERE, "fab", "projected_heights.json")))["detail"]
        except Exception:
            _PH_DETAIL["d"] = []
    m, tv = _XF.get("m"), _XF.get("t")
    if m is None:
        return R.proj_height(part, thread)
    best = None
    for row in _PH_DETAIL["d"]:
        if len(row) < 5 or row[0] != "%s|%s" % (part, thread) or row[4] is None:
            continue
        P = m.multVec(V(*row[3][:3])) + tv
        for h in hs:
            c, ax = h["c"], h["ax"]
            d_ = (P - c) - ax * (P - c).dot(ax)
            if d_.Length < 0.3:
                best = max(best or 0.0, row[4])
    return best


def hole_table(shape):
    """Round holes from concave cylinders, grouped by (axis, diameter, depth/thru, cbore)."""
    zmin, zmax = shape.BoundBox.ZMin, shape.BoundBox.ZMax
    holes = {}
    for f in shape.Faces:
        srf = f.Surface
        if srf.__class__.__name__ != "Cylinder" or not (0.9 <= srf.Radius <= 20.0):
            continue
        u0, u1, v0, v1 = f.ParameterRange
        p = f.valueAt((u0 + u1) / 2, (v0 + v1) / 2)
        n = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        ax, c = V(srf.Axis), V(srf.Center)
        radial = (p - c) - ax * ((p - c).dot(ax))
        if radial.Length < 1e-9 or n.dot(radial) > 0:
            continue
        az = abs(ax.z) > 0.999
        bb = f.BoundBox
        if az:
            zr = (round(bb.ZMin, 1), round(bb.ZMax, 1))     # coaxial holes at different depths stay separate
        else:                                                # side holes: also split by extent ALONG the axis
            ts_ = [(vx.Point - c).dot(ax) for vx in f.Vertexes] or [0.0]
            zr = (round(c.z, 2), round(min(ts_), 0), round(max(ts_), 0))
        key = (round(c.x, 2), round(c.y, 2), zr, az, round(srf.Radius, 2))
        h = holes.setdefault(key, dict(r=srf.Radius, x=c.x, y=c.y, axial=az, z0=1e9, z1=-1e9, span=0.0,
                                        ax=ax, c=c, t0=1e9, t1=-1e9))
        h["z0"], h["z1"] = min(h["z0"], bb.ZMin), max(h["z1"], bb.ZMax)
        for vx in f.Vertexes:                       # extent ALONG the hole axis (side holes: not the z box)
            tt = (vx.Point - h["c"]).dot(h["ax"])
            h["t0"], h["t1"] = min(h["t0"], tt), max(h["t1"], tt)
        h["span"] += math.degrees(u1 - u0)
    full = []
    for h in holes.values():
        if h["span"] >= 359.0:
            full.append(h)
        elif h["span"] >= 270.0:                 # D-bore: chord flat at r*cos(half the missing arc)
            df = h["r"] * math.cos(math.radians((360.0 - h["span"]) / 2.0))
            if h["r"] - df > 0.1:                  # a real flat; a 0.0x chord is a slit/seam artefact
                h["dflat"] = df
            full.append(h)
    # attach coaxial counterbores to their through hole
    res = []
    for h in sorted(full, key=lambda h: h["r"]):
        if h["axial"]:
            h["thru"] = h["z0"] <= zmin + 0.01 and h["z1"] >= zmax - 0.01
            h["depth"] = h["z1"] - h["z0"]
        else:
            h["depth"] = h["t1"] - h["t0"]
            e0, e1 = h["c"] + h["ax"] * (h["t0"] - 0.3), h["c"] + h["ax"] * (h["t1"] + 0.3)
            try:
                o0, o1 = (not shape.isInside(e0, 1e-4, True)), (not shape.isInside(e1, 1e-4, True))
            except Exception:
                o0 = o1 = False
            h["thru"] = o0 and o1
            h["open_dir"] = (h["ax"] * -1.0) if (o0 and not o1) else (h["ax"] if (o1 and not o0) else None)
        res.append(h)
    by_xy = {}
    for h in res:
        if h["axial"]:
            by_xy.setdefault((round(h["x"], 1), round(h["y"], 1)), []).append(h)
    def _open(x, y, z):
        try:
            return not shape.isInside(V(x, y, z), 1e-4, True)
        except Exception:
            return False
    cones = {}
    for f in shape.Faces:                           # countersinks: concave cones on a z axis
        srf = f.Surface
        if srf.__class__.__name__ != "Cone" or abs(abs(V(srf.Axis).z) - 1) > 1e-3:
            continue
        es = [e for e in f.Edges if e.Curve.__class__.__name__ == "Circle"]
        if not es:
            continue
        big = max(es, key=lambda e: e.Curve.Radius)
        sml = min(es, key=lambda e: e.Curve.Radius)
        c_ = big.Curve.Center
        hgt = abs(big.Curve.Center.z - sml.Curve.Center.z)
        if hgt < 1e-6 or big.Curve.Radius - sml.Curve.Radius < 1e-6:
            continue
        inc = 2 * math.degrees(math.atan((big.Curve.Radius - sml.Curve.Radius) / hgt))   # included angle from geometry
        cones[(round(c_.x, 1), round(c_.y, 1))] = (2 * big.Curve.Radius, inc, None, c_.z)
    final = []
    for k, hs in by_xy.items():
        hs.sort(key=lambda h: (h["r"], h["z0"]))
        base = hs[0]
        base["cbore"] = None
        apart = [h_ for h_ in hs[1:] if h_["r"] > base["r"] + 0.05 and
                 (h_["z0"] > base["z1"] + 0.1 or h_["z1"] < base["z0"] - 0.1)]
        for h_ in apart:                            # coaxial but separated by material (e.g. tapped holes from both
            h_["cbore"], h_["csk"] = None, None     # ends of a shaft): its own hole, not a counterbore of the base
            h_["far"] = not _open(h_["x"], h_["y"], h_["z1"] + 0.3) and _open(h_["x"], h_["y"], h_["z0"] - 0.3)
            final.append(h_)
        hs = [h_ for h_ in hs if h_ not in apart]
        for big in hs[1:]:
            if big["r"] > base["r"] + 0.05 and not big["thru"]:
                base["cbore"] = (2 * big["r"], big["depth"])
                rx_ = base["x"] + (base["r"] + big["r"]) / 2.0      # probe in the counterbore RING (the axis is the
                base["cb_far"] = not _open(rx_, base["y"], big["z1"] + 0.3)   # through hole's void): material above = far
        same = [h_ for h_ in hs if abs(h_["r"] - base["r"]) < 0.02]
        mid_void = False
        if len(same) == 2:
            mid_void = _open(base["x"], base["y"], (same[0]["z1"] + same[1]["z0"]) / 2.0)
        if len(same) == 2 and not mid_void and not any(h_["thru"] for h_ in same) and                 same[0]["z0"] <= zmin + 0.01 and same[1]["z1"] >= zmax - 0.01 and same[0]["z1"] < same[1]["z0"] - 0.1:
            base["each_side"] = True                    # two blind holes, one from each face, material between
            base["depth"] = max(same[0]["depth"], same[1]["depth"])
        elif len(same) >= 2 and not mid_void and not any(h_["thru"] for h_ in same) and                 any(same[i_]["z1"] < same[i_ + 1]["z0"] - 0.1 for i_ in range(len(same) - 1)):
            # coaxial blind holes opening on DIFFERENT faces (e.g. a step): separate holes, each with its own side
            same.sort(key=lambda h_: h_["z0"])
            base = same[-1]
            base.setdefault("cbore", None)
            hs = [base] + [h_ for h_ in hs if abs(h_["r"] - base["r"]) >= 0.02]
            for extra in same[:-1]:
                extra["cbore"], extra["csk"] = None, None
                extra["far"] = not _open(extra["x"], extra["y"], extra["z1"] + 0.3) and _open(extra["x"], extra["y"], extra["z0"] - 0.3)
                final.append(extra)
        lo = min(h_["z0"] for h_ in hs)
        hi = max(h_["z1"] for h_ in hs)
        if not base.get("each_side") and _open(base["x"], base["y"], lo - 0.3) and _open(base["x"], base["y"], hi + 0.3):
            base["thru"] = True                         # column (bore + counterbore) open at both ends
        base["far"] = (not base["thru"]) and not base.get("each_side") and             not _open(base["x"], base["y"], base["z1"] + 0.3) and _open(base["x"], base["y"], base["z0"] - 0.3)
        cs_ = cones.get(k)
        if cs_:                                     # side by where the cone's big end opens (probe in the cone ring)
            rx_ = base["x"] + cs_[0] / 2.0 + 0.3    # just OUTSIDE the big diameter: inside the ring is the cone's
            up_open = _open(rx_, base["y"], cs_[3] + 0.3)   # own void when it opens downward (fix from freecad-mcp tests)
            cs_ = (cs_[0], cs_[1], not up_open)
        base["csk"] = cs_
        final.append(base)
    side = [h for h in res if not h["axial"]]
    return final, side, zmax - zmin


def hole_text(h, kind, t):
    d = 2 * h["r"]
    if kind == "STANDOFF" and abs(d - 2.54) < 0.1:      # S9: never tap a long rod through
        return DIA + "2.5 THRU; M3x0.5-6H %s%s BOTH ENDS" % (DEPTH, R.mm(min(8.0, max(t / 2 - 2.0, 4.0)), 1))
    if kind == "BRASS" and abs(d - 8.1) < 0.15:
        return "Tr8x8(P2) LH-7H THRU, MINOR %s6-6.236 (ISO 2903)" % DIA   # the model bore is not the thread
    tapped = {1.25: "M3x0.5-6H", 1.4: "M3x0.5-6H", 1.7: "M4x0.7-6H", 2.1: "M5x0.8-6H"}
    if kind == "AL" and round(h["r"], 2) in tapped:
        if h["thru"]:
            return "%s THRU" % tapped[round(h["r"], 2)]
        return "%s %s%s%s" % (tapped[round(h["r"], 2)], DEPTH, R.mm(max(h["depth"] - 1.5, 1.0), 1),   # >= 3P tap runout
                              " EACH SIDE" if h.get("each_side") else "")
    if h.get("dflat"):                              # D-bore on a D-shaft: clearance LIMITS (low-high, single line)
        s = "%s%s-%s D-BORE, FLAT %s-%s FROM %s" % (DIA, R.mm(d - 0.05, 2), R.mm(d + 0.05, 2),      # the model is cut at
                                                    R.mm(h["dflat"] - 0.05, 2), R.mm(h["dflat"] + 0.05, 2), "℄")  # mid-limit: +/-0.05
        s += " THRU" if h["thru"] else " %s%s" % (DEPTH, R.mm(h["depth"], 1))
        return s
    s = DIA + R.mm(d, 2)
    cb_seat = bool(h.get("cbore")) and kind in ("AL", "CF", "PRINT") and R.bearing_seat(h["cbore"][0], True)
    if kind == "AL" and not cb_seat and (R.bearing_seat(d, True) or R.dowel_hole(d)):
        s += " " + R.fit_text(d, True)
    elif kind in ("CF", "PRINT") and not cb_seat and R.bearing_seat(d, True):
        if h.get("dflat"):                          # a reamer cannot finish a D-bore: the general hole tolerance
            pass                                    # (cut by the stated process) applies
        else:
            s += " " + R.fit_text(d, True) + (" REAM" if d <= 20 else " BORE")   # finished after cut/print (note)
    if kind == "PRINT" and abs(d - 4.0) < 0.05:
        s += " INSERT"
    if h.get("dflat"):
        s += " D-BORE, FLAT %s FROM %s" % (R.mm(h["dflat"], 2), "℄")
    s += " THRU" if h["thru"] else " %s%s%s" % (DEPTH, R.mm(h["depth"], 1), " EACH SIDE" if h.get("each_side") else "")
    if h.get("cbore"):
        s += "  %s%s%s%s %s%s%s" % (CBORE, DIA, R.mm(h["cbore"][0], 1),
                                 (" " + R.fit_text(h["cbore"][0], True)) if cb_seat else "", DEPTH, R.mm(h["cbore"][1], 1),
                                 " FAR SIDE" if h.get("cb_far") else "")
    if h.get("csk"):                                    # Y14.5 4.5.12: diameter and included angle in the callout
        cd, ang, far = h["csk"]
        s += "  %s%s%s X %s°%s" % (CSK, DIA, R.mm(cd, 1), R.mm(round(ang), 0), " FAR SIDE" if far else "")
    return s


def pick_scale(w, h, max_w=205.0, max_h=150.0):
    for sc in SCALES:
        if w * sc <= max_w and h * sc <= max_h:
            return sc
    return SCALES[-1]


def scale_txt(sc):
    from fractions import Fraction
    f = Fraction(sc).limit_denominator(10)
    return "%d:%d" % (f.numerator, f.denominator)


# ------------------------------------------------------------- one drawing
def full_circles(view, hidden_ok=False):
    """Holes as TechDraw draws them: arcs grouped by (centre, radius) whose spans add up to a full
    circle (circles are often split in two at a seam). Slot-end half-arcs are excluded."""
    acc = {}
    for i, e in _edges(view):
        c = e.Curve
        if c.__class__.__name__ != "Circle":
            continue
        k = (round(c.Center.x, 3), round(c.Center.y, 3), round(c.Radius, 3))
        a = acc.setdefault(k, [i, c, 0.0])
        a[2] += abs(e.LastParameter - e.FirstParameter)
    out = [(i, c) for (i, c, span) in acc.values() if span >= 1.5 * math.pi]    # full circles + D-bores (slot ends are 180 deg)
    if hidden_ok:                                   # getEdgeByIndex has no hidden edges: add them, converted from
        try:                                        # page units (x scale, y flipped) to the view's model units
            ve_ = view.getVisibleEdges() or []
            ie_ = [e for _i, e in _edges(view)]
            if ve_ and ie_:                         # factor from the data itself (hidden/visible edges are in the
                wv = max(e.BoundBox.XMax for e in ve_) - min(e.BoundBox.XMin for e in ve_)   # scale they were
                wi = max(e.BoundBox.XMax for e in ie_) - min(e.BoundBox.XMin for e in ie_)   # computed at)
                sc_ = wv / wi if wi > 1e-9 else float(view.Scale)
            else:
                sc_ = float(getattr(view, "Scale", 1.0)) or 1.0
            seen_ = {(round(c.Center.x, 2), round(c.Center.y, 2), round(c.Radius, 2)) for _i, c in out}
            hacc = {}                                   # hidden circles are often split: merge arcs first
            for e in view.getHiddenEdges() or []:
                c = e.Curve
                if c.__class__.__name__ != "Circle":
                    continue
                k_ = (round(c.Center.x / sc_, 2), round(-c.Center.y / sc_, 2), round(c.Radius / sc_, 2))
                hacc[k_] = hacc.get(k_, 0.0) + abs(e.LastParameter - e.FirstParameter)
            for k_, span in hacc.items():
                if span >= 1.5 * math.pi and k_ not in seen_:
                    seen_.add(k_)
                    out.append((-1, Part.Circle(V(k_[0], k_[1], 0), V(0, 0, 1), k_[2])))
        except Exception:
            pass
        return out
    return [ic for ic in out if not _hidden_circle(view, ic[1])]   # never point a leader at a hidden line


def _circle_keys(edges, sc=1.0):
    """getVisibleEdges/getHiddenEdges are in page units (x view scale, y flipped); getEdgeByIndex is not."""
    ks = set()
    for e in edges or []:
        c = getattr(e, "Curve", None)
        if c is not None and c.__class__.__name__ == "Circle":
            for sy in (1, -1):
                ks.add((round(c.Center.x / sc, 1), round(sy * c.Center.y / sc, 1), round(c.Radius / sc, 1)))
    return ks


def _hidden_circle(view, c):
    """True if this circle is drawn only as a hidden line (far-face hole seen through the part)."""
    try:
        ve_, ie_ = view.getVisibleEdges() or [], [e for _i, e in _edges(view)]
        sc_ = float(getattr(view, "Scale", 1.0)) or 1.0
        if ve_ and ie_:
            wi = max(e.BoundBox.XMax for e in ie_) - min(e.BoundBox.XMin for e in ie_)
            if wi > 1e-9:
                sc_ = (max(e.BoundBox.XMax for e in ve_) - min(e.BoundBox.XMin for e in ve_)) / wi
        vis, hid = _circle_keys(ve_, sc_), _circle_keys(view.getHiddenEdges(), sc_)
    except Exception:
        return False
    if not vis and not hid:
        return False
    k = (round(c.Center.x, 1), round(c.Center.y, 1), round(c.Radius, 1))
    return k in hid and k not in vis


def _anchors(b, centres, r):
    """Every instance of the callout's feature: the layout attaches the leader to the best one."""
    try:
        b.addProperty("App::PropertyString", "Anchors", "Layout")
        b.addProperty("App::PropertyFloat", "AnchorR", "Layout")
        b.Anchors = ";".join("%.4f,%.4f" % (x, y) for x, y in centres)
        b.AnchorR = float(r)
    except Exception:
        pass
    return b


def features(shape):
    """Feature flags for note selection (A7: no boilerplate for absent features)."""
    out = dict(csk=[], groove=False, flat=False, step=False, ins=False)
    cyl_r = set()
    for f_ in shape.Faces:
        sn = f_.Surface.__class__.__name__
        if sn == "Cone":
            es = [e for e in f_.Edges if e.Curve.__class__.__name__ == "Circle"]
            if es:
                out["csk"].append(round(2 * max(e.Curve.Radius for e in es), 1))
        elif sn == "Cylinder":
            cyl_r.add(round(f_.Surface.Radius, 2))
    out["csk"] = sorted(set(out["csk"]))
    out["groove"] = 3.5 in cyl_r                           # DIN 6799 size 7 groove on D10
    out["step"] = any(r < 4.9 and r != 3.5 for r in cyl_r)
    cyls = [f_ for f_ in shape.Faces if f_.Surface.__class__.__name__ == "Cylinder"]
    out["grooves"] = 0
    if cyls:
        main = max(cyls, key=lambda f_: f_.Surface.Radius)
        ax_, c0 = V(main.Surface.Axis), V(main.Surface.Center)
        gpos = {round((f_.CenterOfMass - c0).dot(ax_), 0) for f_ in cyls if abs(f_.Surface.Radius - 3.5) < 0.01}
        out["grooves"] = len(gpos)
        for f_ in shape.Faces:                   # drive flat: a plane PARALLEL to the shaft axis, off the axis
            if f_.Surface.__class__.__name__ == "Plane":
                n_ = f_.normalAt(*f_.ParameterRange[0::2])
                if abs(n_.dot(ax_)) < 1e-3 and abs((f_.CenterOfMass - c0).dot(n_)) > 0.5:
                    out["flat"] = True
    return out


def symmetric(shape):
    """True if the part is its own mirror image about a mid-plane (then L/R hands are identical)."""
    c = shape.BoundBox.Center
    for n_ in (V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)):
        try:
            m = shape.mirror(c, n_)
            if shape.common(m).Volume > 0.995 * shape.Volume:
                return True
        except Exception:
            pass
    return False


def find_hexes(shape):
    """Hex drives (boss or hole) on the Z axis: 3 pairs of opposite flats, 60 deg apart, common centre.
    Returns [dict(cx, cy, af, hole, z0, z1, nx, ny)] (n = outward normal of one flat, for the leader)."""
    fl = []
    for f_ in shape.Faces:
        if f_.Surface.__class__.__name__ != "Plane":
            continue
        n_ = f_.normalAt(*f_.ParameterRange[0::2])
        if abs(n_.z) > 1e-3:
            continue
        fl.append((f_, V(n_.x, n_.y, 0).normalize(), f_.CenterOfMass, f_.BoundBox))
    pairs = []
    for i, (fa, na, ca, ba) in enumerate(fl):
        for fb, nb, cb, bb in fl[i + 1:]:
            if na.dot(nb) > -0.999:
                continue
            af = abs((cb - ca).dot(na))
            if af < 3.0:
                continue
            mid = (ca + cb) * 0.5
            hole = (mid - ca).dot(na) > 0             # normal points to the centre = face of a HOLE
            pairs.append(dict(c=mid, af=af, n=na if not hole else na * -1, hole=hole,
                              z0=min(ba.ZMin, bb.ZMin), z1=max(ba.ZMax, bb.ZMax)))
    out = []
    used = set()
    for i, p in enumerate(pairs):
        if i in used:
            continue
        grp = [i]
        for j, q in enumerate(pairs):              # 3 DISTINCT flat directions, 60 deg apart (|cos| = 0.5)
            if j == i or j in used or q["hole"] != p["hole"] or abs(q["af"] - p["af"]) > 0.02 or (q["c"] - p["c"]).Length > 0.1:
                continue
            if all(abs(abs(q["n"].dot(pairs[k]["n"])) - 0.5) < 0.01 for k in grp):
                grp.append(j)
        if len(grp) == 3:
            used.update(grp)
            out.append(dict(cx=p["c"].x, cy=p["c"].y, af=p["af"], hole=p["hole"], z0=p["z0"], z1=p["z1"],
                            nx=p["n"].x, ny=p["n"].y))
    return out


def part_drawing(ps, number):
    p = ps[0]
    kind = p.kind if p.kind in PROCESS else "PRINT"
    proc = dict(PROCESS[kind])
    shape = oriented(p.vis)
    bb = shape.BoundBox
    Lx, Ly, Lz = bb.XLength, bb.YLength, bb.ZLength
    mass = shape.Volume * DENS.get(kind, 1.3) / 1000.0
    three = not (kind == "CF" or Lz < 0.15 * Ly)
    _FORCE_SC = _CACHE.setdefault("force_sc", {})
    if kind == "SHIM" and Lz > 0.5:
        proc["title2"], proc["title3"] = "301 STAINLESS SHEET", "LASER CUT"
        proc["tol"] = dict(proc.get("tol") or {}, TOL_LIN1="LINEAR ±0.05 (EXCEPT THICKNESS)",
                           TOL_LIN2="THICKNESS: SHEET STOCK (EN 10151)")
    sc = pick_scale(Lx + Lz + (40 if three else 25), Ly + (Lz + 30 if three else 0), 215.0, 140.0 if three else 110.0)   # Y14.2 legibility: largest std scale that fits
    if number in _FORCE_SC:
        sc = _FORCE_SC[number]                     # re-draw at a smaller standard scale (notes had no room)
    _CACHE.setdefault("last_sc", {})[number] = sc
    title1 = p.name.replace("_CF3", "").replace("_", " ").upper()
    names = [q.name for q in ps]
    qty = len(ps)
    mirror = any(n.endswith(("_R", "R")) for n in names) and any(n.endswith(("_L", "L")) for n in names)
    if qty > 1:                                       # A8: say how the sharing parts relate
        if mirror and not symmetric(shape):
            _hand = " %s SHOWN; %s IS ITS MIRROR IMAGE." % (names[0], ", ".join(names[1:]))
        else:
            _hand = " ALL IDENTICAL (%s SHOWN)." % names[0]
    else:
        _hand = ""
    stem = "%s_%s" % (number, p.name)
    doc, page = new_sheet("DWG_" + number.replace("-", "_"), title1[:28], proc["title2"], proc["title3"],
                          number, scale_txt(sc), R.mm(mass, 1) + " g", tol=proc.get("tol"), rev=sheet_rev(p, shape)[0])
    part = doc.addObject("Part::Feature", "Part")
    part.Shape = shape
    part.ViewObject.Visibility = False

    pg = doc.addObject("TechDraw::DrawProjGroup", "ProjGroup")
    page.addView(pg)
    pg.Source = [part]
    pg.ProjectionType = "Third angle"
    front = pg.addProjection("Front")
    pg.Anchor.Direction = V(0, 0, 1)
    pg.Anchor.XDirection = V(1, 0, 0)
    side = pg.addProjection("Right")
    thin = Lz < 0.15 * Ly                                 # plate-like: top view would be a sliver
    topv = None if (kind == "CF" or thin) else pg.addProjection("Top")
    def _set_scale(val):                                  # A1: every item at the sheet scale, not just the anchor
        pg.ScaleType = "Custom"
        pg.Scale = val
        for v_ in pg.Views:
            if hasattr(v_, "ScaleType"):
                v_.ScaleType = "Custom"
            v_.Scale = val
            v_.touch()                                    # items do not re-run HLR on a scale change alone
        doc.recompute()
    for v in pg.Views:                                    # hidden lines ON before the first compute
        v.HardHidden = kind != "CF"
    _set_scale(sc)
    for prop, val in (("AutoDistribute", True), ("spacingX", 35.0), ("spacingY", 35.0)):
        if hasattr(pg, prop):
            setattr(pg, prop, val)
    pg.X, pg.Y = (150, 150) if three else (120, 165)   # 3-view: room left of the front view for callouts
    for v in pg.Views:
        v.HardHidden = kind != "CF"
    iso = doc.addObject("TechDraw::DrawViewPart", "Iso")
    iso.Source = [part]
    iso.Direction = V(1, -1, 1.2)
    isc = pick_scale(max(Lx, Ly, Lz) * 1.15, max(Lx, Ly, Lz) * 1.0, 70, 50)   # iso shows all three extents
    add_view(page, iso, 372, 232, isc)
    wait_views(doc, [front, side, iso] + ([topv] if topv else []))
    # any projection-group view outside the frame -> next smaller standard scale
    if os.path.join(HERE, 'drawings') not in sys.path:
        sys.path.insert(0, os.path.join(HERE, 'drawings'))
    import importlib, layout as _lay
    importlib.reload(_lay)
    for _ in range(5):
        for v_ in list(pg.Views) + [iso]:              # the scene is measured: refresh every view first, the
            v_.touch()                                  # same way export() does, or a stale view escapes the fit
        doc.recompute()
        wait_views(doc, [front, side] + ([topv] if topv else []))
        page.ViewObject.doubleClicked()
        _lay._refresh(doc)
        out = [k for k in _lay.views_outside_frame(doc, page) if not k.startswith("Iso")]
        if not out or sc == SCALES[-1]:
            break
        sc = SCALES[SCALES.index(sc) + 1]
        _set_scale(sc)
        wait_views(doc, [front, side] + ([topv] if topv else []))
    et = dict(page.Template.EditableTexts)
    et["scale"] = scale_txt(sc)
    page.Template.EditableTexts = et
    wait_views(doc, [front, side] + ([topv] if topv else []))      # settled geometry before reading vertices
    # stale-geometry guard: a view's x-extent must equal the part's true extent (front/top: Lx, side: Lz);
    # geometry left over from an earlier scale is stable, so polling for "no change" cannot catch it
    def _xext(v):
        bbs = [e.BoundBox for _i, e in _edges(v)]
        return (max(b.XMax for b in bbs) - min(b.XMin for b in bbs)) if bbs else 0.0
    want = [(front, Lx), (side, Lz)] + ([(topv, Lx)] if topv else [])
    for _try in range(6):
        bad_ = [v for v, L in want if abs(_xext(v) - L) > 0.02 * L + 0.05]
        if not bad_:
            break
        for v in bad_:
            v.touch()
        doc.recompute()
        page.ViewObject.doubleClicked()
        wait_views(doc, bad_)
    else:
        log("WARN %s: view geometry did not settle to the part extents" % number)

    # ---------------- overall size dims (front: X and Y extents, side: thickness)
    def extreme(view, axis, lo):
        """Extreme REAL vertex (an edge endpoint) - TechDraw also lists arc/circle centres as vertices."""
        ends = []
        for _j, e_ in _edges(view):
            for q_ in (e_.Vertexes[0].Point, e_.Vertexes[-1].Point):
                ends.append((q_.x, q_.y))
        best, bv = None, None
        i = 0
        while True:
            try:
                q = view.getVertexByIndex(i)
            except Exception:
                break
            if q is None:
                break
            if not any(abs(q.Point.x - ex) < 1e-4 and abs(q.Point.y - ey) < 1e-4 for ex, ey in ends):
                i += 1
                continue
            val = q.Point.x if axis == 0 else q.Point.y
            if best is None or (val < best if lo else val > best):
                best, bv = val, "Vertex%d" % i
            i += 1
        return bv, best
    vxl, xl = extreme(front, 0, True)
    vxh, xh = extreme(front, 0, False)
    vyl, yl = extreme(front, 1, True)
    vyh, yh = extreme(front, 1, False)
    ebb = [e_.BoundBox for _i, e_ in _edges(front)]
    if ebb:                                          # true outline extents (a circle has only seam vertices)
        exl, exh = min(b.XMin for b in ebb), max(b.XMax for b in ebb)
        eyl, eyh = min(b.YMin for b in ebb), max(b.YMax for b in ebb)
        vert_ok = (xh - xl) > 0.9 * (exh - exl) and (yh - yl) > 0.9 * (eyh - eyl)
        xl, xh, yl, yh = exl, exh, eyl, eyh
    else:
        vert_ok = True
    # round outline (turned part): one diameter dimension instead of vertex extents
    big = full_circles(front)                                                            # full circles only, not arcs
    big = max(big, key=lambda ic: ic[1].Radius) if big else None
    round_part = (big is not None and 2 * big[1].Radius >= 0.9 * max(xh - xl, yh - yl, 1e-6)
                  and 2 * big[1].Radius <= 1.05 * max(xh - xl, yh - yl, 1e-6))
    if round_part:
        cx_, cy_, rr = big[1].Center.x, big[1].Center.y, big[1].Radius
        xl, xh, yl, yh = cx_ - rr, cx_ + rr, cy_ - rr, cy_ + rr
        hc_ = [cc for (_i, cc) in full_circles(front, hidden_ok=True) if cc.Radius < rr - 0.05]
        def _clear(th):
            return all(abs(-math.sin(th) * (cc.Center.x - cx_) + math.cos(th) * (cc.Center.y - cy_)) > cc.Radius + 1.0 / sc
                       for cc in hc_)
        ths = sorted((math.radians(a_) for a_ in range(0, 180, 3)), key=lambda th: abs(th - math.radians(45)))
        th_ = next((th for th in ths if _clear(th)), math.radians(45))      # the diameter line crosses no hole
        dd_ = dimv(doc, page, front, ["Edge%d" % big[0]], "Diameter", DIA + R.DIM_FORMAT,
                   at=((cx_ + math.cos(th_) * rr) * sc + math.cos(th_) * 14, (cy_ + math.sin(th_) * rr) * sc + math.sin(th_) * 14),
                   basic=(kind != "STEEL"), name="Dim_D")   # S1: the OD is BASIC -> sized AND located by the profile
    def vpt(nm):
        return front.getVertexByIndex(int(nm[6:])).Point
    skipped = []
    dimw_x = None                                   # model-x of the width/diameter dimension line
    # overall size dims: extension lines on the side where they are shortest; if they would run across
    # most of the part either way, give the envelope as a REF note instead (profile is basic per Y14.41)
    if not round_part and vxl and vxh and vert_ok:
        pa, pb = vpt(vxl), vpt(vxh)
        below, above = max(pa.y - yl, pb.y - yl), max(yh - pa.y, yh - pb.y)   # longest extension line per side
        if min(below, above) > 0.25 * (yh - yl) + 2.0:
            skipped.append("L")
        elif below <= above:
            dimv(doc, page, front, [vxl, vxh], "DistanceX", "(%.1w)", at=(0, -(yh - yl) * sc / 2 - 14), name="Dim_L")
        else:
            dimv(doc, page, front, [vxl, vxh], "DistanceX", "(%.1w)", at=(0, (yh - yl) * sc / 2 + 14), name="Dim_L")
    if not round_part and not vert_ok:
        skipped += ["L", "W"]                        # outline extents not resolvable from vertices -> envelope note
    if vyl and vyh and not round_part and vert_ok:
        pa, pb = vpt(vyl), vpt(vyh)
        right, left = max(xh - pa.x, xh - pb.x), max(pa.x - xl, pb.x - xl)   # longest extension line per side
        if min(right, left) > 0.25 * (xh - xl) + 2.0:
            skipped.append("W")
        else:
            dimw_obj = dimv(doc, page, front, [vyl, vyh], "DistanceY", (DIA + R.DIM_FORMAT + " h6") if kind == "STEEL" else "(%.1w)",
                 at=(((xh - xl) * sc / 2 + 12) if right <= left else (-(xh - xl) * sc / 2 - 14),
                     (-(yh - yl) * sc / 2 - 9.0) if kind == "STEEL" else 0), name="Dim_W")   # shaft: text below
            dimw_x = (xh + 12.0 / sc) if right <= left else (xl - 14.0 / sc)
    sxl, sxlv = extreme(side, 0, True)
    sxh, sxhv = extreme(side, 0, False)
    if sxl and sxh and abs(sxhv - sxlv) > 0.05 and kind != "STEEL":   # shafts: seen end-on -> datum A = axis
        tw_ = abs(sxhv - sxlv) * sc
        dimv(doc, page, side, [sxl, sxh], "DistanceX", R.DIM_FORMAT,
             at=((tw_ / 2 + 7.0) if tw_ < 12.0 else 0, -(yh - yl) * sc / 2 - 12), name="Dim_T")   # narrow: text outside
        cand_ = []
        for _j, e_ in _edges(side):
            p0_, p1_ = e_.Vertexes[0].Point, e_.Vertexes[-1].Point
            if abs(p0_.x - sxhv) < 0.02 and abs(p1_.x - sxhv) < 0.02 and abs(p1_.y - p0_.y) > 0.5:
                cand_.append((abs(p1_.y - p0_.y), (p0_.y + p1_.y) / 2))
        ya_ = max(cand_)[1] if cand_ else 0.0           # midpoint of the longest edge on the datum face
        k_ = abs(sxhv - sxlv) / Lz if Lz > 1e-6 else 1.0  # view-geometry units per model mm (the side view's
        k_ = k_ if k_ > 1e-6 else 1.0                    # x-extent IS the thickness Lz); balloon origins are model mm
        datum(doc, page, side, "A", (sxhv / k_, ya_ / k_), (sxhv / k_ + 10 / sc, ya_ / k_))
        if kind == "SHIM":                          # flatness as an FCF, not a note (S3)
            yf_ = ya_ / k_ + (yh - yl) * 0.3            # same (datum A) face, ABOVE the datum symbol: the
            fl_ = balloon(doc, page, side, "|".join([SYM["flatness"], "0.02"]), (sxhv / k_, yf_),   # thickness
                          (sxhv / k_ + 16.0 / sc, yf_ + 6.0 / sc), end="Filled arrow", name="FCF_flat")  # dim is below
    else:
        # round part seen end-on (shaft, spacer): datum A = axis of the diameter, symbol on the end of the
        # diameter's dimension line (Y14.5: aligned with the dimension line -> feature of size / axis)
        xd = dimw_x if dimw_x is not None else xh + 12.0 / sc     # on the diameter's dimension line
        da = datum(doc, page, front, "A", (xd, yh), (xd, yh + 10.0 / sc))   # on the dimension line (6.3.2)
        if dimw_x is not None:                      # move with the dimension during layout (same group)
            dimw_obj.Label = "Dim_W_g90"
            da.Label = "Datum_A_g90"

    # ---------------- holes: callouts + position FCFs (DRF A|B|C)
    holes, side_holes, t = hole_table(shape)
    side_holes_all = list(side_holes)
    hk = ("STANDOFF" if "Standoff" in p.name else
          "PLAIN" if any(w in p.name for w in ("Spacer", "Sleeve")) else kind)   # spacers / sleeves plain; standoffs tapped through
    groups = {}
    for h in holes:
        groups.setdefault((hole_text(h, hk, t), bool(h.get("far"))), []).append(h)   # near and far pairs apart
    order = sorted(((k_[0], v_) for k_, v_ in groups.items()), key=lambda kv: -kv[1][0]["r"])
    circles = full_circles(front)                    # holes only (split arcs merged), not slot-end arcs
    x_text = (xh - xl) / 2 + 22 / sc
    y_text = (yh - yl) / 2 + 4 / sc
    step = 24.0 / sc
    letters = ["B", "C"]
    # targets first (DRF role by size), then stack callouts in the vertical order of their
    # targets so leaders do not cross; callout + FCF + datum share a group suffix "_g<i>"
    # so the layout pass moves them as one unit
    tg = []
    circles_all = full_circles(front, hidden_ok=True)
    def _own(cs, hs):
        """Circles at THIS group's hole positions (front view: x = X, y = +/-Y)."""
        for sy in (1, -1):
            m_ = [c for c in cs if any(abs(c.Center.x - h_["x"]) < 0.1 and abs(c.Center.y - sy * h_["y"]) < 0.1 for h_ in hs)]
            if m_:
                return m_
        return []
    for gi, (txt, hs) in enumerate(order[:7]):
        r = hs[0]["r"]
        cand = _own([c for (_i, c) in circles if abs(c.Radius - r) < 0.02], hs)
        if not cand and all(h_.get("far") for h_ in hs):  # blind from the far face: shown hidden -> FAR SIDE callout
            cand = _own([c for (_i, c) in circles_all if abs(c.Radius - r) < 0.02], hs)
            if cand:
                txt = txt + " FAR SIDE"
        if not cand:
            continue
        if all(h_.get("far") for h_ in hs) and not txt.endswith("FAR SIDE"):
            txt = txt + " FAR SIDE"                 # opens on the far face (its circle may coincide with a near twin)
        c = max(cand, key=lambda c: c.Center.x + 0.3 * c.Center.y)        # instance nearest the text column
        tg.append((gi, txt, hs, r, c))
    # hole groups with no visible circle in the front view (on the far face, drawn hidden): specified in a
    # note with their position tolerance instead of a leader to a hidden line
    farside = [(t_, h_) for gi_, (t_, h_) in enumerate(order[:7]) if gi_ not in [x[0] for x in tg]]
    # Each callout block sits just above the view, over its own hole (short leader):
    #   row 0: hole callout (leader down to the hole)  /  FCF above it  /  datum symbol left of FCF.
    # Blocks that would overlap move to the next row up.  Units: model mm (x page/sc).
    BW, BH = 56.0 / sc, 21.0 / sc                       # callout + FCF (datum symbol sits LEFT of the FCF)
    rows = []                                            # list of x-intervals per row
    tg.sort(key=lambda t_: (not t_[2][0].get("dflat"), bool(t_[2][0].get("each_side"))))   # a D-bore is datum B: its flat arrests rotation (A|B
    DRF = R.drf(len(tg[0][2]) if tg else 0)              # clocks everything) -> no datum C needed
    if tg and tg[0][2][0].get("dflat"):
        DRF = ["A", "B"]
    if len(tg) < 2:
        DRF = DRF[:2]                                    # no second hole group -> no datum C on this sheet
    for (gi, txt, hs, r, c) in sorted(tg, key=lambda t: t[4].Center.x):
        ox, oy = c.Center.x + r * 0.707, c.Center.y + r * 0.707
        role = [t_[0] for t_ in tg].index(gi)
        cb_part = None
        if (role == 0 or (role == 1 and "C" in DRF)) and ("  " + CBORE) in txt:
            txt, cb_part = txt.split("  " + CBORE, 1)   # S4: the datum is the HOLE; the counterbore gets its own
            cb_part = CBORE + cb_part                    # callout + FCF, so the datum symbol is unambiguous
        label = ("%dX " % len(hs) if len(hs) > 1 else "") + txt
        if topv is None:                               # 2-view sheet: blocks above the front view
            x = min(max(c.Center.x, xl + BW / 2 - 10 / sc), xh - BW / 2 + 10 / sc) if (xh - xl) > BW else (xl + xh) / 2
            row = 0
            while True:
                if row >= len(rows):
                    rows.append([])
                if all(abs(x - q) >= BW for q in rows[row]):
                    rows[row].append(x)
                    break
                row += 1
            y0 = yh + 8.0 / sc + row * BH
        else:                                          # 3-view sheet (top view above): blocks left of the front view
            x = xl - BW / 2 - 12.0 / sc
            y0 = yh - 4.0 / sc - len(rows) * BH
            rows.append([x])
        cb = callout(doc, page, front, label, (ox, oy), (x, y0 + 9.5 / sc), name="Call_g%d" % gi)   # Y14.5 Fig 6-30: FCF below the callout
        _anchors(cb, [(cc.Center.x, cc.Center.y) for cc in
                      _own([cc for (_i, cc) in (circles_all if txt.endswith("FAR SIDE") else circles)
                            if abs(cc.Radius - r) < 0.02], hs)], r)
        d_ = 2 * r
        thr_ = re.search(r"\b(M\d)x", txt)
        tapped_ = thr_ is not None
        if kind == "AL" and R.bearing_seat(d_, True):
            tv, mmc_ = "0.02", False                       # bearing seat: RFS, tight
        elif kind in ("AL", "CF", "BRASS"):
            tv, mmc_ = R.position_tol(d_, kind, tapped=tapped_, floor=float(proc["pos"]),
                                      mate_clear={"M3": 3.3, "M4": 4.5, "M5": 5.5}.get(thr_.group(1)) if tapped_ else None)
        else:
            tv, mmc_ = proc["pos"], False                  # printed parts: process tolerance, RFS
        tcell = DIA + tv + (MMC if mmc_ else "")
        if tapped_ and kind == "AL":                  # Y14.5 App. B-4 / 10.4.1: fixed fastener -> projected zone
            ph = group_proj_height(p.name, thr_.group(1), hs)   # this group's measured mating stack
            if ph is not None:                      # no mating part (set screw / spare): no projected zone
                tcell += " " + R.PROJ + R.mm(ph)
        role = [t_[0] for t_ in tg].index(gi)      # datum role by rank among VISIBLE groups (a hidden
        if role == 0:                               # largest group goes to the notes and defines nothing)
            cells = [SYM["position"], tcell, "A"]
        elif role == 1 and "C" in DRF:
            cells = [SYM["position"], tcell, "A", "B"]          # this group IS datum C: never self-referenced
        else:
            cells = [SYM["position"], tcell] + DRF
        fcf(doc, page, front, cells, (x, y0), name="FCF_g%d" % gi)
        if role == 0 or (role == 1 and "C" in DRF):
            dd = datum(doc, page, front, letters[role], (x, y0 - 3.6 / sc), (x, y0 - 10.0 / sc))
            dd.Label = "Datum_%s_g%d" % (letters[role], gi)
        if cb_part:
            hb_ = hs[0]
            rcb = hb_["cbore"][0] / 2.0
            lab2 = ("%dX " % len(hs) if len(hs) > 1 else "") + cb_part
            cb2 = callout(doc, page, front, lab2, (c.Center.x - rcb * 0.707, c.Center.y - rcb * 0.707),
                          (x, y0 - BH + 9.5 / sc), name="Call_g%d" % (30 + gi))
            pool_ = circles_all if cb_part.endswith("FAR SIDE") else circles
            _anchors(cb2, [(cc.Center.x, cc.Center.y) for (_i, cc) in pool_ if abs(cc.Radius - rcb) < 0.02 and
                           any(abs(cc.Center.x - h_["x"]) < 0.1 and abs(abs(cc.Center.y) - abs(h_["y"])) < 0.1 for h_ in hs)], rcb)
            fcf(doc, page, front, [SYM["position"], DIA + ("0.02" if "H7" in cb_part else proc["pos"]), "A", letters[role]],
                (x, y0 - BH), name="FCF_g%d" % (30 + gi))
    # ---------------- side holes: callout + FCF where they are seen as circles (not note text, S3)
    sgroups, side_called = {}, set()
    for h in side_holes:
        sgroups.setdefault(hole_text(h, hk, t), []).append(h)
    drf_s = DRF[:2] if tg else ["A"]
    for si, (txt, hs) in enumerate(sgroups.items()):
        r = hs[0]["r"]
        ax_ = hs[0]["ax"]
        vw, cand, far_ = None, [], False
        for vw_, along, mp in ((side, 0, lambda q, sx, sy: (sx * (q.z - Lz / 2), sy * q.y)),
                               (topv, 1, lambda q, sx, sy: (sx * q.x, sy * (q.z - Lz / 2)))):
            if vw_ is None or abs((ax_.x, ax_.y)[along]) < 0.99:
                continue                            # this view does not see the group as circles
            vis_c = [c for (_i, c) in full_circles(vw_) if abs(c.Radius - r) < 0.02]
            hid_c = [c for (_i, c) in full_circles(vw_, hidden_ok=True) if abs(c.Radius - r) < 0.02
                     and not any(abs(c.Center.x - w.Center.x) < 0.05 and abs(c.Center.y - w.Center.y) < 0.05 for w in vis_c)]
            def _hits(cs, sx, sy):
                out_ = []
                for h_ in hs:
                    px, py = mp(h_["c"], sx, sy)
                    m_ = [c for c in cs if abs(c.Center.x - px) < 0.1 and abs(c.Center.y - py) < 0.1]
                    if not m_:
                        return None
                    out_.append(m_[0])
                return out_
            for cs, isfar in ((vis_c, False), (hid_c, True)):   # visible match first; hidden -> FAR SIDE
                for sx in (1, -1):
                    for sy in (1, -1):
                        hit = _hits(cs, sx, sy)
                        if hit and not cand:
                            vw, cand, far_ = vw_, hit, isfar
            if cand:
                break
        if vw is None:
            continue
        od_ = hs[0].get("open_dir")
        if od_ is not None:                         # right view looks from +X, top view from +Y (third angle)
            far_ = (od_.x < 0) if vw is side else (od_.y < 0)
        if far_:
            txt = txt + " FAR SIDE"
        c = max(cand, key=lambda c: c.Center.x + 0.3 * c.Center.y)
        gid = 50 + si
        y0 = c.Center.y + r + 10.0 / sc
        x = c.Center.x + r + 24.0 / sc
        label = ("%dX " % len(hs) if len(hs) > 1 else "") + txt
        cb = callout(doc, page, vw, label, (c.Center.x + r * 0.707, c.Center.y + r * 0.707), (x, y0 + 9.5 / sc),
                     name="Call_g%d" % gid)
        _anchors(cb, [(cc.Center.x, cc.Center.y) for cc in cand], r)      # this group's holes only
        tapped_ = txt.startswith("M")
        if kind in ("AL", "CF", "BRASS"):
            tv, mmc_ = R.position_tol(2 * r, kind, tapped=tapped_, floor=float(proc["pos"]),
                                      mate_clear={"M3": 3.3, "M4": 4.5, "M5": 5.5}.get(txt[:2]) if tapped_ else None)
        else:
            tv, mmc_ = proc["pos"], False
        tcell = DIA + tv + (MMC if mmc_ else "")
        if tapped_ and kind == "AL":
            ph = group_proj_height(p.name, txt[:2], hs)
            if ph is not None:
                tcell += " " + R.PROJ + R.mm(ph)
        fcf(doc, page, vw, [SYM["position"], tcell] + drf_s, (x, y0), name="FCF_g%d" % gid)
        side_called.add(txt.replace(" FAR SIDE", ""))
    side_holes = [h for h in side_holes if hole_text(h, hk, t) not in side_called]
    # ---------------- bearing journals (external cylinders on a bearing bore size): fit callout
    hidden_journals = []
    journals_present = False
    if kind == "AL" and hk not in ("STANDOFF", "PLAIN"):   # bearing journals only, never on spacers
        seen = set()
        for f in shape.Faces:
            srf = f.Surface
            if srf.__class__.__name__ != "Cylinder" or abs(abs(V(srf.Axis).z) - 1) > 1e-3:
                continue
            u0, u1, v0, v1 = f.ParameterRange
            p_ = f.valueAt((u0 + u1) / 2, (v0 + v1) / 2)
            n_ = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
            c_ = V(srf.Center)
            rad = (p_ - c_) - V(srf.Axis) * ((p_ - c_).dot(V(srf.Axis)))
            if rad.Length < 1e-9 or n_.dot(rad) < 0 or not R.bearing_seat(2 * srf.Radius, False):
                continue                                   # concave, or not a bearing journal size
            key = round(srf.Radius, 2)
            if key in seen:
                continue
            seen.add(key)
            journals_present = True
            cand = [cc for (_i, cc) in circles if abs(cc.Radius - srf.Radius) < 0.02]
            txt = "%s%s %s  Ra 0.8" % (DIA, R.mm(2 * srf.Radius), R.fit_text(2 * srf.Radius, False))
            if not cand:                                   # journal behind the front face: FAR SIDE callout
                cand = [cc for (_i, cc) in full_circles(front, hidden_ok=True) if abs(cc.Radius - srf.Radius) < 0.02]
                if cand:
                    txt += " FAR SIDE"
            if not cand:
                hidden_journals.append(txt)
                continue
            cc = cand[0]
            gi = 20 + len(seen)
            cb = callout(doc, page, front, txt, (cc.Center.x - srf.Radius * 0.707, cc.Center.y - srf.Radius * 0.707),
                         (xl - 34.0 / sc, yl + 2.0 / sc), name="Call_g%d" % gi)
            _anchors(cb, [(cc.Center.x, cc.Center.y)], srf.Radius)
            fcf(doc, page, front, [SYM["position"], DIA + "0.02"] + (DRF[:2] if tg else ["A"]),
                (xl - 34.0 / sc, yl + 2.0 / sc - 9.5 / sc), name="FCF_g%d" % gi)      # journal location (FCF, not text)
    # ---------------- hex drives: callout + FCF (not note text) - S1
    zmin_, zmax_ = shape.BoundBox.ZMin, shape.BoundBox.ZMax
    for k_, hx in enumerate(find_hexes(shape)):
        far_ = (not hx["hole"]) and hx["z1"] < zmax_ - 0.01          # a boss below the top face is seen from the far side
        txt_ = "HEX AF %s %s%s" % (R.mm(hx["af"], 2), "H9" if hx["hole"] else "h9", " FAR SIDE" if far_ else "")
        pts_ = []
        for sy_ in (1, -1):                         # flat midpoint, in whichever y sense the view uses
            pts_.append((hx["cx"] + hx["nx"] * hx["af"] / 2, sy_ * (hx["cy"] + hx["ny"] * hx["af"] / 2)))
        on_ = [q for q in pts_ if any(e.distToShape(Part.Vertex(V(q[0], q[1], 0)))[0] < 0.05 for _i, e in _edges(front))]
        q_ = (on_ or pts_)[0]
        gid_ = 40 + k_
        cbh = callout(doc, page, front, txt_, q_, (xl - 34.0 / sc, yl - 6.0 / sc), name="Call_g%d" % gid_)
        _anchors(cbh, [q_], 0.0)
        fcf(doc, page, front, [SYM["position"], DIA + "0.05"] + (DRF[:2] if tg else ["A"]),
            (xl - 34.0 / sc, yl - 6.0 / sc - 9.5 / sc), name="FCF_g%d" % gid_)
    drf = DRF if tg else ["A"]
    # all-around profile of the outline
    # profile FCF starts at the end of the part with fewer holes, leaving room for the hole callouts
    ncl = sum(1 for (_i, cc) in circles if cc.Center.x < xl + 0.25 * (xh - xl))
    ncr = sum(1 for (_i, cc) in circles if cc.Center.x > xh - 0.25 * (xh - xl))
    px_ = (xh - 0.04 * (xh - xl)) if ncr < ncl else (xl + 0.04 * (xh - xl))
    prof = balloon(doc, page, front, "|".join([SYM["profile_surface"], proc["prof"]] + drf),
                   (px_, yh), (px_ + (22 / sc if px_ < (xl + xh) / 2 else -22 / sc), yh + 8 / sc), end="Filled arrow", name="FCF_profile")
    prof.Label = "Prof_g99"
    ao = doc.addObject("TechDraw::DrawRichAnno", "AllOver")      # plain text: a balloon draws a line through it
    page.addView(ao)
    ao.AnnoText = '<html><body style="font-family:osifont; font-size:10pt;"><p align="center">ALL OVER</p></body></html>'
    ao.ShowFrame = False
    ao.MaxWidth = 30
    ao.X, ao.Y = float(pg.X) + px_ * sc, float(pg.Y) + yh * sc   # rough; snapped under the FCF before layout
    ao.Label = "AllOver_g99"                      # moves with the profile FCF (same group)
    vpts = []
    for i_ in range(400):
        try:
            q_ = front.getVertexByIndex(i_)
        except Exception:
            break
        if q_ is None:
            break
        vpts.append((q_.Point.x, q_.Point.y))
    hc_all = [cc for (_i, cc) in full_circles(front, hidden_ok=True) if cc.Radius < 0.45 * max(xh - xl, yh - yl)]   # holes, not the OD
    vpts = [q for q in vpts if not any(math.hypot(q[0] - cc.Center.x, q[1] - cc.Center.y) < cc.Radius + 0.2 for cc in hc_all)]
    _anchors(prof, vpts, 0.0)                     # profile: leader to an OUTLINE vertex, never onto a hole
    # ---------------- notes
    has_threads = any(("M3x" in hole_text(h_, hk, t) or "M4x" in hole_text(h_, hk, t) or "M5x" in hole_text(h_, hk, t)
                       or "Tr8" in hole_text(h_, hk, t)) for h_ in holes + side_holes_all)
    step_file = "fab/step/%s.step" % p.name
    dxf_file = "fab/dxf/%s.dxf" % p.name
    lines = ["NOTES:", ("1. DIMS/TOLS PER ASME Y14.5-2018. UNDIMENSIONED GEOMETRY IS BASIC, DEFINED BY THE "
                        "STEP MODEL %s%s. THE PROFILE FCF APPLIES ALL OVER (Y14.5 11.3.1.5), EXCEPT FEATURES THAT CARRY A FIT, "
                        "THEIR OWN FCF, OR A TOLERANCED THICKNESS.%s") % (
                        step_file, (" AND DXF " + dxf_file) if kind == "CF" else "",
                        " THREADED HOLES ARE MODELLED AS PLAIN HOLES: THE THREAD CALLOUT GOVERNS." if has_threads else ""),
             "2. QTY %d PER ROBOT: %s." % (qty, ", ".join(names)) + _hand]
    n = 3
    ft = features(shape)
    for s_ in proc["notes"]:
        if s_ == "@CSK":
            continue                                # countersinks are specified in the hole callouts (4.5.12)
        elif s_ == "@THREADS":
            if not (any(hole_text(h_, hk, t).startswith("M") or "M3x" in hole_text(h_, hk, t) for h_ in holes + side_holes_all)):
                continue
            s_ = "THREADS PER ASME B1.13M, CLASS 6H."
        elif s_ == "@MASK":
            if not any(("H7" in hole_text(h_, hk, t)) for h_ in holes + side_holes_all) and not journals_present:
                s_ = "FINISH: CLEAR ANODIZE PER MIL-A-8625 TYPE II CLASS 1."
                lines.append("%d. %s" % (n, s_))
                n += 1
                continue
            s_ = "FINISH: CLEAR ANODIZE PER MIL-A-8625 TYPE II CLASS 1; MASK ALL TOLERANCED FIT FEATURES."
        elif s_ == "@INSERT":
            if not any(abs(2 * h_["r"] - 4.0) < 0.05 for h_ in holes + side_holes_all):
                continue
            s_ = DIA + "4 HOLES: M3 HEAT-SET INSERTS, LENGTH NOT TO EXCEED WALL/HOLE DEPTH, INSTALL AT 230 °C."
        elif s_ == "@SHAFT":
            ng_ = ft["grooves"]
            ops = ["CUT TO LENGTH"] + (["STEP"] if ft["step"] else []) +                   (["%s PER DIN 6799 SIZE 7 (%s7 x 0.94)" % ("%dX E-CLIP GROOVES" % ng_ if ng_ > 1 else "E-CLIP GROOVE", DIA)] if ng_ else [])                   + (["DRIVE FLATS AS MODELLED (MATE THE D-BORES)"] if ft["flat"] else [])
            s_ = "; ".join(ops) + (". MACHINE THESE FEATURES BY GRINDING (CASE HARDENED STOCK)." if len(ops) > 1 else ".")
        if s_ == "@SHIMMAT":
            s_ = ("MATERIAL: 301 STAINLESS FULL-HARD SHIM STOCK, %s mm THICK. CUT FROM STEP {step} (LASER OR PHOTO-ETCH)." % R.mm(Lz, 2)
                  if Lz <= 0.5 else
                  "MATERIAL: 301 STAINLESS 1/2-HARD SHEET, %s mm THICK. LASER CUT FROM STEP {step}, DEBURR." % R.mm(Lz, 2))
        s_ = s_.replace("@THK", R.mm(Lz, 2) + " mm")
        if "; HOLES MARKED REAM/BORE" in s_ and not any(
                (" REAM" in hole_text(h_, hk, t) or " BORE" in hole_text(h_, hk, t).replace("D-BORE", "")) for h_ in holes + side_holes_all):
            s_ = s_.split("; HOLES MARKED REAM/BORE")[0] + "."       # no finished holes on this part
        lines.append("%d. %s" % (n, s_.format(step=step_file, dxf=dxf_file)))
        n += 1
    if side_holes:
        sg = {}
        for h in side_holes:
            a_ = h["ax"]
            axn = "X" if abs(a_.x) > 0.9 else ("Y" if abs(a_.y) > 0.9 else "Z")
            pos_ = h["c"]
            key_ = "%s, AXIS %s AT %s" % (hole_text(h, hk, t), axn,
                                          ("X%s" % R.mm(pos_.x, 1)) if axn != "X" else ("Y/Z PER MODEL"))
            sg.setdefault(key_, 0)
            sg[key_] += 1
        lines.append("%d. SIDE HOLES (LOCATION PER MODEL, " % n + SYM["position"] + " " + DIA + "%s|%s): " % (proc["pos"], "|".join(DRF[:2] if tg else ["A"])) +
                     "; ".join("%dX %s" % (k_, s_) for s_, k_ in sg.items()))
        n += 1
    if farside:
        parts_ = []
        for t_, h_ in farside:
            tp_ = t_.startswith("M")
            tv_, mm_ = R.position_tol(2 * h_[0]["r"], kind, tapped=tp_, floor=float(proc["pos"]),
                                      mate_clear={"M3": 3.3, "M4": 4.5, "M5": 5.5}.get(t_[:2]) if tp_ else None)
            cell = DIA + tv_ + (MMC if mm_ else "")
            if tp_ and kind == "AL":
                ph_ = R.proj_height(p.name, t_[:2])
                cell += " " + R.PROJ + R.mm(ph_ if ph_ is not None else R.PROJ_H_DEFAULT)
            parts_.append("%dX %s %s %s|%s" % (len(h_), t_, SYM["position"], cell, "|".join(DRF if tg else ["A"])))
        lines.append("%d. FAR-FACE HOLES (HIDDEN IN FRONT VIEW, LOCATION PER MODEL): " % n + "; ".join(parts_))
        n += 1
    if hidden_journals:
        lines.append("%d. JOURNAL / PILOT NOT SEEN AS A CIRCLE IN THE FRONT VIEW (LOCATION PER MODEL, " % n + SYM["position"] + " " + DIA + "0.02|" + "|".join(DRF[:2] if tg else ["A"]) + "): " + "; ".join(hidden_journals) + ".")
        n += 1
    for key_, txt_ in EXTRA_NOTES.items():
        if p.name.startswith(key_):
            lines.append("%d. %s" % (n, txt_))
            n += 1
    if skipped:
        lines.append("%d. ENVELOPE %s x %s x %s (REF)." % (n, R.mm(xh - xl, 1), R.mm(yh - yl, 1), R.mm(Lz, 1)))
        n += 1
    _rv, _note = sheet_rev(p, shape)
    if _note:
        lines.append("%d. %s" % (n, _note))
        n += 1
    lines.append("%d. MASS %s g (REF). MODEL SOURCE: arm_model.py (%s)." % (n, R.mm(mass, 1), p.src.replace("custom: ", "")))
    rich(doc, page, html_lines(lines, 7), 106, 74, 150, name="Notes")   # column ends 14 mm left of the tolerance block
    rich(doc, page, html_lines(["ISOMETRIC (REF)", "SCALE " + scale_txt(isc)], 8), 372, 196, 40, name="Cap_iso")
    pdf = export(doc, page, stem)
    App.closeDocument(doc.Name)
    return pdf


_CACHE = {}


def batch(start=0, count=100, only=None):
    if "groups" not in _CACHE:
        _CACHE["groups"] = custom_parts()
    groups = _CACHE["groups"]
    if start == 0:
        open(LOG, "w").close()
        with open(os.path.join(OUT, "batch_index.json"), "w") as fh:
            json.dump(_CACHE["index"], fh)
    done = []
    idx = only if only is not None else range(start, min(start + count, len(groups)))
    for gi in idx:
        ps = _CACHE["j1"] if gi == -1 else groups[gi]
        number = "ARC-%03d" % (101 if gi == -1 else 102 + _CACHE["nums"][gi])
        t0 = time.time()
        try:
            pdf = part_drawing(ps, number)
            log("OK   %s %-28s %5.1fs %s" % (number, ps[0].name, time.time() - t0, os.path.basename(pdf)))
            done.append(pdf)
        except Exception:
            log("FAIL %s %-28s %s" % (number, ps[0].name, traceback.format_exc()[-400:].replace("\n", " | ")))
    return len(groups), done


def draw_one(index):
    """Entry for freecad-mcp gui_batch: draw ONE sheet by its stable batch index (-1 = J1 hub, ARC-101).
    Builds the part list once per FreeCAD instance; never truncates the shared log or index."""
    if "groups" not in _CACHE:
        _CACHE["groups"] = custom_parts()
    ps = _CACHE["j1"] if index == -1 else _CACHE["groups"][index]
    number = "ARC-%03d" % (101 if index == -1 else 102 + _CACHE["nums"][index])
    t0 = time.time()
    pdf = part_drawing(ps, number)
    for _try in range(2):                           # notes found no free spot -> one standard scale smaller
        try:
            lay_ = open(os.path.join(OUT, os.path.basename(pdf)[:-4] + "_layout.txt"), encoding="utf-8").read()
        except Exception:
            break
        if "no free spot for Notes" not in lay_ or "REMAINING 0" in lay_:
            break
        sc_ = _CACHE["last_sc"].get(number)
        if sc_ is None or sc_ == SCALES[-1]:
            break
        _CACHE.setdefault("force_sc", {})[number] = SCALES[SCALES.index(sc_) + 1]
        pdf = part_drawing(ps, number)
    rem = None
    try:
        with open(os.path.join(OUT, os.path.basename(pdf)[:-4] + "_layout.txt"), encoding="utf-8") as fh:
            rem = [l for l in fh.read().splitlines() if l.startswith("REMAINING")]
    except Exception:
        pass
    return {"number": number, "part": ps[0].name, "pdf": pdf, "seconds": round(time.time() - t0, 1),
            "layout": rem[0] if rem else None}
