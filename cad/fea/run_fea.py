# -*- coding: utf-8 -*-
"""
Linear-static FEA of the load-critical custom parts with FreeCAD's own FEM stack
(ObjectsFem + gmsh + CalculiX, all bundled with FreeCAD 1.1).  Headless:
    freecadcmd cad/fea/run_fea.py            (writes cad/fea/out/fea_report.md + .json + per-case .FCStd)
Load basis: worst static joint torques / reactions from check_interference.py [4] (3.25 kg arm,
300 g donut) times a 2.5 dynamic/impact factor.  Allowables: 6061-T6 yield 276 MPa;
quasi-isotropic 3 mm CF plate 200 MPa (bearing/notch knock-down from ~550 MPa UTS);
PETG-CF 40 MPa.  Required safety factor on the factored load: >= 1.5.
"""
import json
import math
import os
import sys
import time
import traceback

import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, HERE)
LIB = bool(os.environ.get("FEA_LIB"))          # imported as a library (e.g. fea/run_fea_fourbar.py): no guard, no main()
OUT = os.environ.get("FEA_OUT") if LIB else os.path.join(HERE, "fea", "out")
os.makedirs(OUT, exist_ok=True)
import params   # noqa: E402
if not LIB:
    params.use_release_variant('run_fea.py')   # writes the released package
import arm_model as M          # noqa: E402
import ObjectsFem              # noqa: E402
from femmesh.gmshtools import GmshTools   # noqa: E402
from femtools import ccxtools  # noqa: E402

V = App.Vector
DF = 2.5
MAT = {
    "AL6061": dict(name="Aluminium-6061-T6", E="69000 MPa", nu=0.33, rho="2700 kg/m^3", allow=276.0),
    "CF_QI": dict(name="CF plate quasi-isotropic", E="50000 MPa", nu=0.30, rho="1550 kg/m^3", allow=200.0),
    "PETG_CF": dict(name="PETG-CF (FDM)", E="3500 MPa", nu=0.38, rho="1300 kg/m^3", allow=40.0),
}


def part_shape(name):
    for parts in M.build_bodies().values():
        for p in parts:
            if p.name == name:
                return p.vis.copy()
    raise KeyError(name)


def cyl_faces(shape, axis, centre=None, r=None, near=None, tol=0.3):
    """Concave cylindrical faces with the given axis direction, radius and centre-line position."""
    out = []
    for i, f in enumerate(shape.Faces):
        s = f.Surface
        if s.__class__.__name__ != "Cylinder":
            continue
        if abs(abs(V(s.Axis).dot(V(*axis))) - 1) > 1e-3:
            continue
        if r is not None and abs(s.Radius - r) > tol:
            continue
        c = V(s.Center)
        if centre is not None:
            d = (c - V(*centre))
            d = d - V(*axis) * d.dot(V(*axis))
            if d.Length > (near if near is not None else 0.5):
                continue
        out.append("Face%d" % (i + 1))
    return out


def shoulder_faces(shape, normal, centre_xz, r, tol=0.3):
    """Planar faces normal to `normal` with a circular edge of radius r about the given axis: bearing shoulders."""
    n0 = V(*normal)
    out = []
    for i, f in enumerate(shape.Faces):
        if f.Surface.__class__.__name__ != "Plane":
            continue
        try:
            n = f.normalAt(*f.ParameterRange[0::2])
        except Exception:
            continue
        if abs(abs(n.dot(n0)) - 1) > 1e-3:
            continue
        for e in f.Edges:
            c = getattr(e.Curve, "Radius", None)
            if c is not None and abs(c - r) < tol and abs(e.Curve.Center.x - centre_xz[0]) < tol and abs(e.Curve.Center.z - centre_xz[1]) < tol:
                out.append("Face%d" % (i + 1))
                break
    return out


def plane_faces(shape, normal, at, tol=0.05):
    n0 = V(*normal)
    out = []
    for i, f in enumerate(shape.Faces):
        if f.Surface.__class__.__name__ != "Plane":
            continue
        try:
            n = f.normalAt(*f.ParameterRange[0::2])
        except Exception:
            continue
        if abs(abs(n.dot(n0)) - 1) > 1e-3:
            continue
        if abs(f.CenterOfMass.dot(n0) - at) < tol:
            out.append("Face%d" % (i + 1))
    return out


def run_case(case):
    t0 = time.time()
    name = case["name"]
    doc = App.newDocument("FEA_" + name)
    shape = case["shape"]
    part = doc.addObject("Part::Feature", "Part")
    part.Shape = shape
    ana = ObjectsFem.makeAnalysis(doc, "Analysis")
    mk = getattr(ObjectsFem, "makeSolverCalculiXCcxTools", None) or ObjectsFem.makeSolverCalculixCcxTools
    solver = mk(doc, "Solver")
    ana.addObject(solver)
    m = MAT[case["mat"]]
    mat = ObjectsFem.makeMaterialSolid(doc, "Material")
    mat.Material = {"Name": m["name"], "YoungsModulus": m["E"], "PoissonRatio": str(m["nu"]), "Density": m["rho"]}
    mat.References = [(part, "Solid1")]
    ana.addObject(mat)
    fix = ObjectsFem.makeConstraintFixed(doc, "Fixed")
    fix.References = [(part, f) for f in case["fixed"]]
    ana.addObject(fix)
    total = 0.0
    for k, (faces, vec) in enumerate(case["loads"]):
        line = doc.addObject("Part::Feature", "Dir%d" % k)
        u = V(*vec)
        line.Shape = Part.makeLine(V(0, 0, 0), u.normalize() * 10)
        fo = ObjectsFem.makeConstraintForce(doc, "Force%d" % k)
        fo.References = [(part, f) for f in faces]
        fo.Force = "%.3f N" % V(*vec).Length
        fo.Direction = (line, ["Edge1"])
        fo.Reversed = False
        ana.addObject(fo)
        total += V(*vec).Length
    mesh = ObjectsFem.makeMeshGmsh(doc, "Mesh")
    mesh.Shape = part
    mesh.CharacteristicLengthMax = "%.2f mm" % case.get("h", 2.0)
    mesh.CharacteristicLengthMin = "%.2f mm" % (case.get("h", 2.0) / 3)
    mesh.ElementOrder = case.get("order", "2nd")
    if case.get("algo"):
        mesh.Algorithm3D = case["algo"]
    if case.get("hoo") or case.get("linear2nd"):
        mesh.HighOrderOptimize = "Elastic+Optimization"   # gmsh untangles curved quadratic tets (negative Jacobians)
    if case.get("linear2nd"):
        mesh.SecondOrderLinear = True
    ana.addObject(mesh)
    doc.recompute()
    err = GmshTools(mesh).create_mesh()
    if err:
        raise RuntimeError("gmsh: %s" % err)
    doc.recompute()
    wd = os.path.join(OUT, "ccx_" + name)
    os.makedirs(wd, exist_ok=True)
    solver.WorkingDir = wd
    fea = ccxtools.FemToolsCcx(ana, solver)
    fea.update_objects()
    fea.setup_working_dir(wd)
    fea.setup_ccx()
    msg = fea.check_prerequisites()
    if msg:
        raise RuntimeError("prerequisites: %s" % msg)
    fea.purge_results()
    fea.write_inp_file()
    fea.ccx_run()
    fea.load_results()
    res = [o for o in ana.Group if o.isDerivedFrom("Fem::FemResultObject")]
    if not res:
        raise RuntimeError("no results (see %s)" % wd)
    r = res[0]
    vm = max(r.vonMises)
    disp = max(r.DisplacementLengths)
    nodes = len(r.NodeNumbers)
    if vm <= 1e-6 or disp <= 1e-9:
        raise RuntimeError("zero response: load not applied (check load face selection)")
    sf = m["allow"] / vm
    try:
        import feminout.importVTKResults as vtk
        vtk.export([r], os.path.join(OUT, name + ".vtu"))
    except Exception:
        pass
    doc.saveAs(os.path.join(OUT, "FEA_" + name + ".FCStd"))
    App.closeDocument(doc.Name)
    return dict(case=name, part=case["part"], material=m["name"], load=case["desc"], total_force_N=round(total, 1),
                max_von_mises_MPa=round(vm, 2), max_disp_mm=round(disp, 4), allowable_MPa=m["allow"],
                safety_factor=round(sf, 2), nodes=nodes, mesh_h_mm=case.get("h", 2.0),
                verdict="PASS" if sf >= 1.5 else "FAIL", seconds=round(time.time() - t0, 1))


def cases():
    L2, L3 = M.K["L2"], M.K["L3"]
    g = 9.81
    C = []
    # ---- upper arm L (CF): fixed on the J1 hub interface, elbow reaction at the elbow bore
    s = part_shape("Upper_Arm_L_CF3")
    F = (1.9 * g * DF) / 2                              # forearm+head+payload ~1.9 kg, split over 2 plates
    C.append(dict(name="upper_arm", part="Upper_Arm_L_CF3", mat="CF_QI", shape=s, h=2.0,
                  fixed=cyl_faces(s, (0, 1, 0), (0, 0, 0), near=11.0),
                  loads=[(cyl_faces(s, (0, 1, 0), (L2, 0, 0), r=7.5), (0, 0, -F))],
                  desc="elbow reaction %.1f N per plate (1.9 kg distal mass x g x %.1f)" % (F, DF)))
    # ---- forearm L (CF): fixed at the elbow bore + pivot B, wrist load at the wrist bore
    s = part_shape("Forearm_L_CF3")
    F = (1.2 * g * DF) / 2
    C.append(dict(name="forearm", part="Forearm_L_CF3", mat="CF_QI", shape=s, h=2.0,
                  fixed=cyl_faces(s, (0, 1, 0), (0, 0, 0), r=5.0) + cyl_faces(s, (0, 1, 0), (-M.K["L1"], 0, 0), near=3.0),
                  loads=[(cyl_faces(s, (0, 1, 0), (L3, 0, 0), r=7.5), (0, 0, -F))],
                  desc="wrist load %.1f N per plate (1.2 kg head+payload x g x %.1f)" % (F, DF)))
    # ---- clevis L (CF): fixed on the wrist-shaft D-bore, head weight at the roll-housing screws
    s = part_shape("Clevis_L_CF3")
    F = (1.0 * g * DF) / 2
    C.append(dict(name="clevis", part="Clevis_L_CF3", mat="CF_QI", shape=s, h=1.5,
                  fixed=cyl_faces(s, (0, 1, 0), (0, 0, 0), r=5.0),
                  loads=[(cyl_faces(s, (0, 1, 0), (48, 0, M.ROLL_Z - 15), r=1.65) + cyl_faces(s, (0, 1, 0), (48, 0, M.ROLL_Z + 30), r=1.65),
                          (0, 0, -F))],
                  desc="head weight %.1f N per plate at the roll-housing screws (1.0 kg x g x %.1f)" % (F, DF)))
    # ---- J2 hub journal (6061): driven through its hex by the 54T gear (interfaces/base_hub__drive.toml), crank
    #      reaction on the D12 journal.  Fixed on the six hex flats (the gear holds them; the 6804 on the D20 journal
    #      takes the radial load just outboard).
    s = part_shape("J2_Output_Hub_Journal")
    T = 4.0 * DF
    F = T / (M.K["L1"] / 1000.0) / 2.0                 # crank pin reaction shared by the journal
    af = M.IF_HUB_DRIVE["stub"]["hex_af"]
    flats = [f for k in range(6) for f in plane_faces(
             s, (math.cos(math.radians(60 * k)), 0, math.sin(math.radians(60 * k))), af / 2.0, tol=0.05)]
    C.append(dict(name="j2_hub", part="J2_Output_Hub_Journal", mat="AL6061", shape=s, h=1.2,
                  fixed=flats,
                  loads=[(cyl_faces(s, (0, 1, 0), (0, 0, 0), r=6.0), (0, 0, -F))],
                  desc="crank reaction %.0f N on the D12 journal (J2 %.1f N*m incl. x%.1f)" % (F, T, DF)))
    # ---- roll housing (PETG-CF): fixed at the clevis screw holes, roll-servo + pipe moment as force at the bearing seat
    s = part_shape("Roll_Housing")
    C.append(dict(name="roll_housing", part="Roll_Housing", mat="PETG_CF", shape=s, h=2.0,
                  fixed=cyl_faces(s, (0, 1, 0), None, r=2.0),
                  loads=[(cyl_faces(s, (1, 0, 0), (0, 0, M.ROLL_Z), r=18.5), (0, 0, -(1.0 * g * DF)))],
                  desc="head + payload %.1f N through the 6805 seat (1.0 kg x g x %.1f)" % (1.0 * g * DF, DF)))
    return C


def main():
    results = []
    only = os.environ.get("ONLY")
    for c in cases():
        if only and c["name"] not in only.split(","):
            continue
        if not c["fixed"] or not all(l[0] for l in c["loads"]):
            results.append(dict(case=c["name"], verdict="SETUP ERROR", note="face selection empty: fixed %d, loads %s"
                                % (len(c["fixed"]), [len(l[0]) for l in c["loads"]])))
            continue
        h0 = c.get("h", 2.0)
        # mesh strategies, in order of preference: quadratic tets first; 1st order only as a flagged last resort
        strategies = [
            (dict(), ""),
            (dict(algo="Delaunay", hoo=True), "gmsh Delaunay 3D + elastic high-order optimisation (curved quadratic tets)"),
            (dict(algo="Frontal", hoo=True), "gmsh Frontal 3D + elastic high-order optimisation (curved quadratic tets)"),
            (dict(algo="HXT", hoo=True), "gmsh HXT 3D + elastic high-order optimisation (curved quadratic tets)"),
            (dict(linear2nd=True, h=h0 * 0.75), "straight-sided quadratic tets (SecondOrderLinear)"),
            (dict(order="1st", h=h0 * 0.5), "1st-order tets (h %.2f mm): quadratic meshes had negative Jacobians; stresses may read low" % (h0 * 0.5)),
        ]
        done = False
        for opts, note in strategies:
            cc = dict(c)
            cc.update(opts)
            try:
                r_ = run_case(cc)
                if note:
                    r_["note"] = note
                results.append(r_)
                done = True
                break
            except Exception:
                last = traceback.format_exc()[-600:]
        if not done:
            results.append(dict(case=c["name"], verdict="ERROR", note=last))
    with open(os.path.join(OUT, "fea_results.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    lines = ["# FEA evidence - load-critical custom parts", "",
             "FreeCAD 1.1 FEM: gmsh 2nd-order tets + CalculiX linear static. Load factor %.1f on worst static case. "
             "Required SF >= 1.5 on factored load." % DF, "",
             "| Case | Part | Material | Load | Max von Mises (MPa) | Allowable (MPa) | SF | Max disp (mm) | Nodes | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        if "max_von_mises_MPa" in r:
            lines.append("| %s | %s | %s | %s | %.1f | %.0f | %.1f | %.3f | %d | %s |" % (
                r["case"], r["part"], r["material"], r["load"], r["max_von_mises_MPa"], r["allowable_MPa"],
                r["safety_factor"], r["max_disp_mm"], r["nodes"], r["verdict"]))
        else:
            lines.append("| %s | - | - | - | - | - | - | - | - | %s: %s |" % (r["case"], r["verdict"], r.get("note", "")[:120].replace("|", "/").replace("\n", " ")))
    with open(os.path.join(OUT, "fea_report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if not LIB:
    main()
