# -*- coding: utf-8 -*-
"""
Geometry fingerprint: a regression guard for refactors (moving parameters/interfaces must not move geometry).

    set GRIP=FOURBAR (or SCREW) and FP_MODE=record | check, then
    "%LOCALAPPDATA%\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad/tools/fingerprint.py

record -> cad/tests/fingerprints/<variant>.json (the baseline)
check  -> cad/out/<variant>/fingerprint.json, compared with the baseline; exit code 1 and a diff on any change.

Per part (chk and vis shapes): volume, centre of mass (from the solids), bounding box, face/edge counts,
a face digest (surface type, area and centroid of every face, so a moved hole is caught), mass (g), kind, src.
Per pose (STOW, DONUT_LIFT, PIPE_CHUTE at two jaw openings): every body placement and the TCP.
"""
import hashlib
import json
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
if os.environ.get("FP_MODEL_DIR"):          # fingerprint an older copy of arm_model.py (e.g. a pre-refactor snapshot)
    sys.path.insert(0, os.environ["FP_MODEL_DIR"])
import FreeCAD as App      # noqa: E402
import arm_model as M      # noqa: E402

VARIANT = getattr(M, "VARIANT", getattr(M, "GRIP", "screw")).lower()
MODE = os.environ.get("FP_MODE", "check")
BASE = os.path.join(CAD, "tests", "fingerprints", VARIANT + ".json")
OUT = os.path.join(CAD, "out", VARIANT, "fingerprint.json")
TOL_LEN, TOL_VOL = 1e-3, 1e-2          # mm, mm^3 (well above OCC run-to-run noise, far below any real edit)


def r(x, n=4):
    return round(float(x), n)


def centre_of_mass(s):
    """Volume-weighted centre of the solids. Generic Shapes (makeFillet, compounds) have no
    CenterOfMass; the old bounding-box fallback hid holes moved inside the outline (TI-009)."""
    if hasattr(s, "CenterOfMass"):
        return s.CenterOfMass
    sol = [x for x in s.Solids if x.Volume > 1e-9]
    if sol:
        v = sum(x.Volume for x in sol)
        c = App.Vector()
        for x in sol:
            c += x.CenterOfMass * (x.Volume / v)
        return c
    return s.BoundBox.Center


def face_digest(s):
    """Order-independent digest of every face (surface type, area, centroid). Moving a hole moves its
    cylinder face's centroid even when volume, mass centre and bounding box barely change."""
    sig = []
    for f in s.Faces:
        try:
            c = f.CenterOfMass
            sig.append("%s:%.2f:%.2f,%.2f,%.2f" % (type(f.Surface).__name__, f.Area, c.x, c.y, c.z))
        except Exception:
            sig.append("%s:%.2f" % (type(f.Surface).__name__, f.Area))
    sig.sort()
    return hashlib.sha1("|".join(sig).encode()).hexdigest()[:12]


def shape_fp(s):
    if s.isNull():
        return dict(null=True)
    bb = s.BoundBox
    try:
        com = centre_of_mass(s)
    except Exception:
        com = bb.Center
    try:
        vol = r(s.Volume, 3)
    except Exception:                       # e.g. open shells in vendor STEP visuals: area instead
        vol = "area:%.2f" % s.Area
    return dict(vol=vol, com=[r(com.x), r(com.y), r(com.z)],
                bb=[r(bb.XMin), r(bb.YMin), r(bb.ZMin), r(bb.XMax), r(bb.YMax), r(bb.ZMax)],
                faces=len(s.Faces), edges=len(s.Edges), fdig=face_digest(s))


def plc_fp(p):
    m = p.toMatrix()
    return [r(v, 5) for v in (m.A11, m.A12, m.A13, m.A14, m.A21, m.A22, m.A23, m.A24, m.A31, m.A32, m.A33, m.A34)]


def build():
    bodies = M.build_bodies()
    parts = {}
    for bn, ps in bodies.items():
        for p in ps:
            key = "%s/%s" % (bn, p.name)
            try:
                mg = r(M.part_mass_g(p), 3)
            except Exception:
                mg = None
            parts[key] = dict(kind=p.kind, src=p.src, mass_g=mg,
                              chk=shape_fp(p.chk), vis=shape_fp(p.vis))
    poses = {}
    for nm in ("STOW", "DONUT_LIFT", "PIPE_CHUTE"):
        q, jaw = M.pose_q(nm)
        for j in (jaw, 112.0):
            plc = M.placements(*q, jaw=j)
            tcp = plc["HEAD"].multVec(App.Vector(M.K["GRIP"], 0, -M.K["DROP"]))
            poses["%s@jaw%.1f" % (nm, j)] = dict(tcp=[r(tcp.x), r(tcp.y), r(tcp.z)],
                                                 bodies={k: plc_fp(v) for k, v in sorted(plc.items())})
    return dict(variant=VARIANT, parts=parts, poses=poses,
                totals=dict(n_parts=len(parts), mass_g=r(sum(v["mass_g"] or 0 for v in parts.values()), 2)))


def diff(a, b, path=""):
    """List of human-readable differences between two fingerprint trees."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append("+ %s/%s (new)" % (path, k))
            elif k not in b:
                out.append("- %s/%s (removed)" % (path, k))
            else:
                out += diff(a[k], b[k], "%s/%s" % (path, k))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, "%s[%d]" % (path, i))
    elif isinstance(a, float) or isinstance(b, float):
        tol = TOL_VOL if path.endswith("vol") or "mass" in path else TOL_LEN
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))) or abs(a - b) > tol:
            out.append("~ %s: %s -> %s" % (path, a, b))
    elif a != b:
        out.append("~ %s: %s -> %s" % (path, a, b))
    return out


def main():
    fp = build()
    if MODE == "record":
        os.makedirs(os.path.dirname(BASE), exist_ok=True)
        json.dump(fp, open(BASE, "w"), indent=0, sort_keys=True)
        print("FINGERPRINT recorded %s: %d parts, %.1f g" % (BASE, fp["totals"]["n_parts"], fp["totals"]["mass_g"]))
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(fp, open(OUT, "w"), indent=0, sort_keys=True)
    if not os.path.exists(BASE):
        print("FINGERPRINT no baseline at %s (run with FP_MODE=record)" % BASE)
        return 1
    d = diff(json.load(open(BASE)), fp)
    for line in d[:60]:
        print(line)
    print("FINGERPRINT %s: %s (%d differences, %d parts)" % (VARIANT, "MATCH" if not d else "CHANGED", len(d), fp["totals"]["n_parts"]))
    return 1 if d else 0


if not os.environ.get("QC_IMPORT"):          # imported by tools/quick_check.py -> functions only
    rc = main()
    if os.environ.get("FP_EXIT"):
        sys.exit(rc)
