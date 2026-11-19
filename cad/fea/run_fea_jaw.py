# -*- coding: utf-8 -*-
"""
Jaw pad-support stiffness (four-bar gripper), multi-material FEA (headless):
    set GRIP=FOURBAR & freecadcmd cad/fea/run_fea_jaw.py
-> cad/out/fourbar/fea/jaw_stiffness.md / .json and a `fea_jaw` evidence record.

Why: grip force low on the pad (the donut contact is at the TCP height, z -20) bends the jaw if the four-bar holds it
only at the top. History (cad/out/fourbar/fea): baseline = pad on D6 posts under a top-only jaw (pad bottom 1.35 mm
off its top, FAIL). The design now has a C-frame wall behind the pad AND a bottom link layer, so the linkage holds
the jaw at top and bottom. This measures how much the pad's bottom moves relative to its top.

Model: the jaw block, the standoffs (split at z -13 so the load can go on their lower part) and the bottom finger are
bonded into one CompSolid (BooleanFragments; touching faces shared), each with its own material: PETG-CF 3.5 GPa,
6061 69 GPa, CF 50 GPa. The TPU pad and screws are left out (the pad only transmits the grip into the posts).
  fixed: every coupler-pin bore (top bores in the block; lower bores in the block and the bottom finger);
  load:  the servo-stall grip reaction x 1.25 (run_fea_fourbar basis) in +y (pushing the jaw open), on the posts'
         lower segments (z -26 .. -13), i.e. at the donut contact height - the worst case for the pad bottom.
Reports the pad-plane displacement (y) at the top finger (z 20..23) and the bottom finger (z -29..-26) near the
posts, the pad tilt, and the peak von Mises per material.
"""
import json
import math
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "fea"))
os.environ["GRIP"] = "FOURBAR"
import params  # noqa: E402
OUT = params.out_dir("fea")
os.environ["FEA_LIB"] = "1"
os.environ["FEA_OUT"] = OUT
import FreeCAD as App  # noqa: E402
import Part  # noqa: E402
import ObjectsFem  # noqa: E402
from femmesh.gmshtools import GmshTools  # noqa: E402
from femtools import ccxtools  # noqa: E402
import run_fea as RF  # noqa: E402
import arm_model as M  # noqa: E402

V = App.Vector
FB = M.FB
DF_ACT = 1.25
Z_SPLIT = -13.0
TILT_LIMIT_DEG = 0.5        # acceptance: pad face tilt under the stall grip
BOTTOM_LIMIT_MM = 0.25      # acceptance: pad bottom moves no more than this relative to the top


def grip_stall():
    th = math.radians(M.FB_TREF)
    t_spring = M.SPRING["rate_Nm_per_deg"] * (M.SPRING["preload_deg"] + M.fb_theta(112.0) - M.FB_TREF)
    return (M.SERVO["stall_Nm"] - t_spring) / (2 * (FB["L"] / 1000.0) * math.cos(th))


def jaw_solids(tag="L"):
    """{name: (solid, material key)} for the left jaw as built (JAW_L body frame)."""
    B = M.build_bodies()["JAW_L"]
    get = {p.name: p for p in B}
    out = {"block": (get["Jaw_Block_%s" % tag].chk, "PETG_CF"),
           "finger_bot": (get["Finger_%s_bot_CF3" % tag].chk, "CF_QI")}
    for p in B:
        if p.name.startswith("Standoff_D6_%s" % tag):
            s = p.chk
            lo = s.common(Part.makeBox(400, 400, Z_SPLIT - (-60), V(-200, -200, -60)))
            hi = s.common(Part.makeBox(400, 400, 60 - Z_SPLIT, V(-200, -200, Z_SPLIT)))
            out[p.name + "_lo"] = (lo, "AL6061")
            out[p.name + "_hi"] = (hi, "AL6061")
    for k, (s, _m) in out.items():
        if s.isNull() or s.Volume < 1e-3:
            raise RuntimeError("empty solid %s" % k)
    return out


def patch_material_sets(inp, solids):
    """Reassign every C3D10 element to the material of the source part that contains its centroid, rewriting the
    *ELSET ...Solid blocks FreeCAD wrote (its element-to-solid mapping drops pieces of a multi-solid compound)."""
    L = open(inp).read().splitlines()
    nodes, k = {}, next(i for i, l in enumerate(L) if l.replace(" ", "").upper().startswith("*NODE,NSET"))
    for l in L[k + 1:]:
        if l.startswith("**") or not l.strip():
            continue
        if l.startswith("*"):
            break
        a = l.split(",")
        nodes[int(a[0])] = V(float(a[1]), float(a[2]), float(a[3]))
    elems, k = [], next(i for i, l in enumerate(L) if l.upper().startswith("*ELEMENT, TYPE=C3D10"))
    buf = []
    for l in L[k + 1:]:
        if l.startswith("**") or not l.strip():
            continue
        if l.startswith("*"):
            break
        buf += [int(x) for x in l.split(",") if x.strip()]      # C3D10: id + 10 nodes, may wrap onto 2 lines
        while len(buf) >= 11:
            elems.append((buf[0], buf[1:5]))
            buf = buf[11:]
    keys = list(solids)
    sets = {}
    for eid, corners in elems:
        c = sum((nodes[n] for n in corners), V()) * 0.25
        k_ = next((k for k in keys if solids[k][0].isInside(c, 1e-3, True)), None)
        if k_ is None:
            k_ = min(keys, key=lambda kk: solids[kk][0].distToShape(Part.Vertex(c))[0])
        sets.setdefault(solids[k_][1], []).append(eid)
    out, i = [], 0
    while i < len(L):
        l = L[i]
        m = l.replace(" ", "").upper()
        if m.startswith("*ELSET,ELSET=MAT_") and m.endswith("SOLID"):
            mkey = l.split("=")[1].strip()[len("Mat_"):-len("Solid")]
            out.append(l)
            ids = sets.get(mkey, [])
            for j in range(0, len(ids), 10):
                out.append(",".join(str(x) for x in ids[j:j + 10]) + ",")
            i += 1
            while i < len(L) and not L[i].startswith("*"):
                i += 1
            continue
        out.append(l)
        i += 1
    open(inp, "w").write("\n".join(out) + "\n")
    return {k: len(v) for k, v in sets.items()}, len(elems)


def reuse_solution(wd, inp):
    """JAW_REUSE=1: a CalculiX solve of this exact deck already in wd/reuse (e.g. a long solve run by hand) is
    loaded instead of solving again. The deck must match byte for byte, so the result belongs to this mesh."""
    if os.environ.get("JAW_REUSE") != "1":
        return False
    old = os.path.join(wd, "reuse")
    ref, frd = os.path.join(old, os.path.basename(inp)), os.path.join(old, "Mesh.frd")
    if not (os.path.exists(ref) and os.path.exists(frd)):
        return False
    import filecmp
    import shutil
    if not filecmp.cmp(ref, inp, shallow=False):
        print("JAW_REUSE: the deck differs from wd/reuse; solving")
        return False
    for f in os.listdir(old):
        if f.startswith("Mesh.") and not f.endswith(".inp"):
            shutil.copy2(os.path.join(old, f), os.path.join(wd, f))
    print("JAW_REUSE: identical deck, loading the stored CalculiX result")
    return True


def run(name, solids, h=1.0):
    doc = App.newDocument("FEA_" + name)
    keys = list(solids)
    shapes = [solids[k][0] for k in keys]
    # general fuse: split at contacts so touching faces are SHARED (bonded joints) and keep an exact map from each
    # input part to its output pieces (materials follow the map; centre-of-mass lookups miss hollow/odd shapes)
    res, mp = shapes[0].generalFuse(shapes[1:], 1e-4)
    cs = res                          # compound of solids that share their contact faces (meshed conformally)
    sol = cs.Solids
    mat_of = [None] * len(sol)
    for k, outs, src in zip(keys, mp, shapes):
        for sh in (outs or [src]):          # an untouched input (only touching others) has an empty map entry
            for so in sh.Solids:
                c = so.BoundBox.Center
                idx = min(range(len(sol)), key=lambda i: abs(sol[i].Volume - so.Volume) + (sol[i].BoundBox.Center - c).Length)
                mat_of[idx] = k
    if None in mat_of:
        raise RuntimeError("unmapped solids: %s" % [i for i, k in enumerate(mat_of) if k is None])
    seen, shared = {}, 0
    for i, so in enumerate(sol):
        for f in so.Faces:
            h_ = f.hashCode()
            if h_ in seen and seen[h_] != i:
                shared += 1
            seen.setdefault(h_, i)
    if shared == 0:
        raise RuntimeError("no shared faces between parts: the joints would not be bonded")
    bf = doc.addObject("Part::Feature", "Jaw")
    bf.Shape = cs
    doc.recompute()
    ana = ObjectsFem.makeAnalysis(doc, "Analysis")
    mk = getattr(ObjectsFem, "makeSolverCalculiXCcxTools", None) or ObjectsFem.makeSolverCalculixCcxTools
    solver = mk(doc, "Solver")
    ana.addObject(solver)
    for mkey in sorted(set(solids[k][1] for k in keys)):
        m = RF.MAT[mkey]
        mat = ObjectsFem.makeMaterialSolid(doc, "Mat_" + mkey)
        mat.Material = {"Name": m["name"], "YoungsModulus": m["E"], "PoissonRatio": str(m["nu"]), "Density": m["rho"]}
        mat.References = [(bf, "Solid%d" % (i + 1)) for i, k in enumerate(mat_of) if solids[k][1] == mkey]
        ana.addObject(mat)
    # fixed: every coupler-pin bore on the two coupler axes (the block's top bores; its lower bores and the bottom
    # finger's press-fit bores, where the bottom links hold the jaw)
    _gd, _gi, cd, ci = M.fb_pivots(1)
    fixed = []
    for c_ in (cd, ci):
        for r_ in (FB["PIN_R"] + 0.05, FB["PIN_R"]):
            fixed += [f for f in RF.cyl_faces(cs, (0, 0, 1), (c_[0], c_[1], 0), r=r_, tol=0.01) if f not in fixed]
    if not fixed:
        raise RuntimeError("no coupler-pin bores found to fix")
    fix = ObjectsFem.makeConstraintFixed(doc, "Fixed")
    fix.References = [(bf, f) for f in fixed]
    ana.addObject(fix)
    # load: outer cylinder faces (r 3) of the standoffs' lower segments
    load_faces = []
    for i, f in enumerate(cs.Faces):
        srf = f.Surface
        if "Cylinder" in srf.TypeId and abs(srf.Radius - 3.0) < 0.01 and f.BoundBox.ZMax <= Z_SPLIT + 0.01:
            load_faces.append("Face%d" % (i + 1))
    F = grip_stall() * DF_ACT
    line = doc.addObject("Part::Feature", "Dir")
    line.Shape = Part.makeLine(V(0, 0, 0), V(0, 10, 0))
    fo = ObjectsFem.makeConstraintForce(doc, "Grip")
    fo.References = [(bf, f) for f in load_faces]
    fo.Force = "%.3f N" % F
    fo.Direction = (line, ["Edge1"])
    ana.addObject(fo)
    mesh = ObjectsFem.makeMeshGmsh(doc, "Mesh")
    mesh.Shape = bf
    mesh.CharacteristicLengthMax = "%.2f mm" % h
    mesh.CharacteristicLengthMin = "%.2f mm" % (h / 3)
    mesh.ElementOrder = "2nd"
    mesh.HighOrderOptimize = "Elastic+Optimization"
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
    counts, n_el = patch_material_sets(fea.inp_file_name, solids)
    if sum(counts.values()) != n_el:
        raise RuntimeError("material sets %s do not cover %d elements" % (counts, n_el))
    if not reuse_solution(wd, fea.inp_file_name):
        fea.ccx_run()
    fea.load_results()
    r = [o for o in ana.Group if o.isDerivedFrom("Fem::FemResultObject")][0]
    fm = r.Mesh.FemMesh
    XT, o = M.K["GRIP"], M.O_REF
    posts = [(XT - 12.0, o + 9.0), (XT + 12.0, o + 9.0)]

    def near_posts(p):
        return min(math.hypot(p.x - x, p.y - y) for x, y in posts) < 8.0
    top, bot, recs = [], [], []
    for nid, d, vm in zip(r.NodeNumbers, r.DisplacementVectors, r.vonMises):
        p = fm.getNodeById(nid)
        if near_posts(p):
            if FB["ZFT"][0] - 0.01 <= p.z <= FB["ZFT"][1] + 0.01:
                top.append(d.y)
            elif FB["ZFB"][0] - 0.01 <= p.z <= FB["ZFB"][1] + 0.01:
                bot.append(d.y)
        recs.append((vm, V(p)))
    n_nodes, max_disp = len(r.NodeNumbers), max(r.DisplacementLengths)
    if not top or not bot:
        raise RuntimeError("no nodes found at the finger levels")
    # peak von Mises per material: classify the most-stressed nodes by the part that contains them (stresses differ by
    # material, so the top few hundred nodes cover every material's peak)
    vm_by_mat = {}
    for vm, p in sorted(recs, key=lambda t: -t[0])[:600]:
        k_ = next((k for k in solids if solids[k][0].isInside(p, 0.05, True)), None)
        if k_:
            mk_ = solids[k_][1]
            vm_by_mat[mk_] = max(vm_by_mat.get(mk_, 0.0), vm)
    d_top, d_bot = sum(top) / len(top), sum(bot) / len(bot)
    span = FB["ZFT"][0] - FB["ZFB"][1]
    tilt = math.degrees(math.atan2(d_bot - d_top, span))
    doc.saveAs(os.path.join(OUT, "FEA_" + name + ".FCStd"))
    App.closeDocument(doc.Name)
    sf = {k: round(RF.MAT[k]["allow"] / v, 2) for k, v in vm_by_mat.items() if v > 0}
    return dict(case=name, grip_N=round(F, 1), nodes=n_nodes, load_faces=len(load_faces), shared_faces=shared,
                fixed_faces=len(fixed),
                disp_top_mm=round(d_top, 4), disp_bottom_mm=round(d_bot, 4),
                bottom_rel_top_mm=round(d_bot - d_top, 4), tilt_deg=round(tilt, 3),
                max_disp_mm=round(max_disp, 4),
                vm_max_MPa={k: round(v, 2) for k, v in vm_by_mat.items()}, safety_factor=sf,
                ok=abs(d_bot - d_top) <= BOTTOM_LIMIT_MM and abs(tilt) <= TILT_LIMIT_DEG and min(sf.values()) >= 1.5)


def main():
    tag = os.environ.get("JAW_CASE", "current")
    res = None
    last = ""
    for h in ([float(os.environ["JAW_H"])] if os.environ.get("JAW_H") else [1.0, 1.4]):
        try:
            res = run("jaw_stiffness_" + tag, jaw_solids(), h=h)
            break
        except Exception:
            import traceback
            last = traceback.format_exc()
            open(os.path.join(OUT, "jaw_stiffness_%s_error.txt" % tag), "w").write(last)
    if res is None:
        print(last[-1500:])
        params.record("fea_jaw", "FAIL", note="jaw stiffness FEA did not run")
        return 1
    fn = os.path.join(OUT, "jaw_stiffness_%s.json" % tag)
    json.dump(res, open(fn, "w"), indent=1)
    md = os.path.join(OUT, "jaw_stiffness_%s.md" % tag)
    open(md, "w", encoding="utf-8").write(
        "# Jaw pad-support stiffness (%s)\n\nGrip %.1f N (servo stall x %.2f) on the standoffs' lower segments (donut contact"
        " height); fixed at every coupler-pin bore (top and bottom links).\n\n| Pad top (y) | Pad bottom (y) | Bottom rel. top | Tilt | Max disp |"
        " SF by material |\n|---|---|---|---|---|---|\n| %.3f mm | %.3f mm | %.3f mm (limit %.2f) | %.2f deg (limit %.1f) |"
        " %.3f mm | %s |\n\n%s\n" % (tag, res["grip_N"], DF_ACT, res["disp_top_mm"], res["disp_bottom_mm"],
                                     res["bottom_rel_top_mm"], BOTTOM_LIMIT_MM, res["tilt_deg"], TILT_LIMIT_DEG,
                                     res["max_disp_mm"], res["safety_factor"], "PASS" if res["ok"] else "FAIL"))
    print(json.dumps(res, indent=1))
    params.record("fea_jaw", "PASS" if res["ok"] else "FAIL", files=[fn, md],
                  note="%s: bottom rel top %.3f mm, tilt %.2f deg" % (tag, res["bottom_rel_top_mm"], res["tilt_deg"]))
    return 0


sys.exit(main())
