# -*- coding: utf-8 -*-
"""
Variant export for CAD migration (Fusion): the STEP set, BOM and STOW placements of the ACTIVE variant, written under
cad/out/<variant>/fab/ so the released package in cad/fab/ (export_fab.py) is never touched.

    python -I cad/tools/run.py --grip FOURBAR --base-drive DIRECT cad/tools/export_variant.py

cad/out/<variant>/fab/
  BOM.csv                      fab/BOM.csv columns + material and density columns: every custom part with its
                               material, every purchased item with its quantity (split motors: stator + rotor = 1)
  step/<part>.step             every custom part, in its body frame (as fab/step/)
  step/ARC_Arm_STOW.step       the whole arm (vis shapes) at STOW, world frame
  purchased/<part>.step        EXPORT_ALL=1 only: every purchased part instance in its body frame (vendor geometry;
                               ~40 MB, not committed: the vendor STEP is in cad/vendor/), and ARC_Arm_DONUT_LIFT /
                               ARC_Arm_PIPE_CHUTE_ROLL90.step (~40 MB each)
  stow.json                    STOW: joint angles, each body's to-world matrix, and per part kind/material/mass/bbox
                               and the STEP path (what the Fusion builder places occurrences from)
"""
import csv
import json
import os
import sys
from collections import OrderedDict, defaultdict

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
import FreeCAD as App   # noqa: E402
import Part             # noqa: E402
import params           # noqa: E402
import arm_model as M   # noqa: E402

ALL = bool(os.environ.get("EXPORT_ALL"))
POSES = ("STOW", "DONUT_LIFT", "PIPE_CHUTE_ROLL90") if ALL else ("STOW",)
MATERIAL = {"CF": "carbon-fibre plate (3K, epoxy)", "AL": "6061-T6 aluminium", "PRINT": "PETG-CF print (gears: PA12 or PETG-CF)",
            "STEEL": "steel", "TPU": "TPU 95A print", "BRASS": "brass", "SHIM": "301 stainless shim stock", "PTFE": "PTFE",
            "RUBBER": "neoprene sheet, bonded"}
HW_PREFIX = ("SHCS_", "BHCS_", "CSK_", "Nyloc_", "Dowel_", "SB5x", "Insert_", "Washer_", "Eclip_", "SetScrew_",
             "Collar_", "Cable_Clip_", "PAN_", "Pin_")


def item_of(p):
    """BOM line key for a purchased part: hardware by its size token (SHCS_M3x6), bearings by catalogue key, the
    rest (motors, servos, horns, springs) by catalogue key."""
    if p.name.startswith("Brg_"):
        return "Brg_" + p.src
    if p.name.startswith(HW_PREFIX):
        return "_".join(p.name.split("_")[:2])
    return p.src


def matrix(pl):
    m = pl.Matrix
    return [[getattr(m, "A%d%d" % (r, c)) for c in range(1, 5)] for r in range(1, 5)]


def main():
    out = params.out_dir("fab")
    for d in ("step", "purchased") if ALL else ("step",):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    bodies = M.build_bodies()
    custom, cat = OrderedDict(), defaultdict(lambda: [0, 0.0])
    for bn, parts in bodies.items():
        for p in parts:
            if p.kind == "CAT":
                e = cat[(item_of(p), p.src)]
                e[0] += 0 if "rotor" in p.name else 1
                e[1] += M.part_mass_g(p)
            else:
                custom[p.name] = (bn, p)
    rows, tot = [], 0.0
    for (item, src), (n, m) in sorted(cat.items()):
        c = M.CAT.get(src, {})
        tot += m
        rows.append(["PURCHASED", item, c.get("desc", src), n, "%.1f" % m, "", "", "", c.get("verify", c.get("src", ""))])
    for name, (bn, p) in custom.items():
        m = M.part_mass_g(p)
        tot += m
        bb = p.vis.BoundBox
        rows.append(["CUSTOM", name, "%s; body %s; env %.0fx%.0fx%.0f mm" % (p.src, bn, bb.XLength, bb.YLength, bb.ZLength),
                     1, "%.1f" % m, p.kind, MATERIAL.get(p.kind, p.kind), M.MAT.get(p.kind, ""), p.note])
    with open(os.path.join(out, "BOM.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type", "item", "description / process", "qty", "mass_g", "material", "material_name",
                    "density_g_cm3", "notes / source / VERIFY"])
        w.writerows(rows)
        w.writerow([])
        w.writerow(["TOTAL", "", "modelled mass, variant %s (motors, gripper drive, all hardware)" % M.VARIANT, "",
                    "%.0f" % tot, "", "", "", ""])
    for name, (bn, p) in custom.items():
        p.vis.exportStep(os.path.join(out, "step", name + ".step"))
    q, jaw = M.pose_q("STOW")
    plc = M.placements(*q, jaw=jaw)
    stow = dict(variant=M.VARIANT, grip=M.GRIP, base_drive=M.BASE_DRIVE, inputs_hash=params.inputs_hash(), pose="STOW",
                q_deg=list(q), jaw_mm=jaw, units="mm", frames="each part's STEP is in its body frame; to_world places it",
                bodies={})
    for bn, parts in bodies.items():
        rec = stow["bodies"].setdefault(bn, dict(to_world=matrix(plc[bn]), parts=[]))
        for p in parts:
            bb = p.vis.BoundBox
            if p.kind == "CAT":
                rel = "purchased/%s.step" % p.name if ALL else None
                if ALL:
                    p.vis.exportStep(os.path.join(out, *rel.split("/")))
            else:
                rel = "step/%s.step" % p.name
            rec["parts"].append(dict(name=p.name, kind=p.kind, src=p.src, material=MATERIAL.get(p.kind, "purchased"),
                                     mass_g=round(M.part_mass_g(p), 2), bbox_body_mm=[round(v, 3) for v in (
                                         bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)], step=rel))
    json.dump(stow, open(os.path.join(out, "stow.json"), "w"), indent=1)
    for pose in POSES:
        q, jaw = M.pose_q(pose)
        shapes = [s for (_b, _p, s) in M.placed(bodies, *q, jaw=jaw, which="vis")]
        Part.makeCompound(shapes).exportStep(os.path.join(out, "step", "ARC_Arm_%s.step" % pose))
    n_cat = sum(len([p for p in ps if p.kind == "CAT"]) for ps in bodies.values())
    files = [os.path.join(out, "BOM.csv"), os.path.join(out, "stow.json")] + \
            [os.path.join(out, "step", "ARC_Arm_%s.step" % p_) for p_ in POSES]
    note = "%d custom STEP, %d purchased instances (%s), %d BOM lines, %.0f g" % (
        len(custom), n_cat, "STEP exported" if ALL else "placements only", len(rows), tot)
    params.record("export_variant", "PASS", files, note)
    print("EXPORT %s: %s -> %s" % (M.VARIANT, note, out))


main()
