# -*- coding: utf-8 -*-
"""
Interface agreement check (quick tier): for every cad/interfaces/*.toml with a bolt pattern, confirm that both
mating parts, as actually built, have a hole on each pattern axis with the size the interface specifies.

    set GRIP=FOURBAR (or SCREW)
    "%LOCALAPPDATA%\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe" cad/tools/check_interfaces.py
-> cad/out/<variant>/interfaces.json and a PASS/FAIL line per interface side.
"""
import json
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
import FreeCAD as App      # noqa: E402
import arm_model as M      # noqa: E402
import iface               # noqa: E402

VARIANT = M.GRIP.lower()


def expected_r(side):
    if side["hole"] == "tapped" and "drill_d" in side:
        return side["drill_d"] / 2.0
    if side["hole"] == "clearance":
        return side["clearance_d"] / 2.0
    return None                                   # catalogue part: any coaxial hole up to the thread size


def holes_on_axis(shape, p, n, r_exp, tol=0.01):
    """Radii of cylindrical faces whose axis is parallel to n and passes through p."""
    found = []
    for f in shape.Faces:
        srf = f.Surface
        if "Cylinder" not in srf.TypeId:
            continue
        ax = srf.Axis
        if abs(abs(ax.dot(n)) - 1.0) > 1e-6:
            continue
        d = (p - srf.Center).cross(ax).Length
        if d < tol:
            found.append(round(srf.Radius, 4))
    return found


def main():
    bodies = M.build_bodies()
    parts = {(bn, p.name): p for bn, ps in bodies.items() for p in ps}
    report, ok_all = [], True
    for I in iface.all_interfaces():
        if "pattern" not in I:
            continue
        n = App.Vector(*I["frame"]["normal"])
        x0 = I.frame_x
        for sk in ("side_a", "side_b"):
            side = I[sk]
            p = parts.get((side["body"], side["part"]))
            if p is None:
                report.append(dict(interface=I.name, side=sk, part=side["part"], status="MISSING"))
                ok_all = False
                continue
            r_exp = expected_r(side)
            res = []
            for (y, z) in I.points_yz():
                got = holes_on_axis(p.chk, App.Vector(x0, y, z), n, r_exp)
                good = bool(got) and (r_exp is None and min(got) <= 1.7 or r_exp is not None and any(abs(g - r_exp) < 0.01 for g in got))
                res.append(dict(y=round(y, 3), z=round(z, 3), radii=got, ok=good))
            st = "PASS" if all(h["ok"] for h in res) else "FAIL"
            ok_all &= st == "PASS"
            report.append(dict(interface=I.name, side=sk, part=side["part"], expected_r=r_exp, status=st, holes=res))
            print("INTERFACE %-24s %-6s %-22s %s" % (I.name, sk, side["part"], st))
    out = os.path.join(CAD, "out", VARIANT)
    os.makedirs(out, exist_ok=True)
    json.dump(dict(variant=VARIANT, ok=ok_all, report=report), open(os.path.join(out, "interfaces.json"), "w"), indent=1)
    print("INTERFACES %s: %s" % (VARIANT, "PASS" if ok_all else "FAIL"))
    return 0 if ok_all else 1


if not os.environ.get("QC_IMPORT"):          # imported by tools/quick_check.py -> functions only
    rc = main()
    if os.environ.get("FP_EXIT"):
        sys.exit(rc)
