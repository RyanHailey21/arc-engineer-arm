# -*- coding: utf-8 -*-
"""
Build guide for the printed prototype of the ACTIVE variant (the servo-driven FOURBAR arm), generated from the model:

    python -I cad/tools/run.py cad/tools/build_guide.py                         (freecadcmd, about 2 min)
    tools/blender-5.3.0-windows-x64/blender.exe -b -P cad/render/build_steps.py   (step pictures, about 1 min)
    python -I cad/docs/paper/make_paper.py                                       (the PDF; the guide is its appendix)

Every part of the model is assigned to exactly one build step (STEPS); a part left over, or matched twice, fails the
run, so the guide cannot forget a screw. For each step it writes:
  - the parts and how many, with what each is made of in the prototype (printed / bought / cut);
  - the stack along each joint axis the step closes: every part within the probe radius of the axis, in order along
    it, from the model at STOW (so washers, shims, bearings and spacers are listed in the order they go on);
  - meshes for the step picture: the step's new parts, the sub-assemblies mounted in it, and what is already built.
Outputs:
  cad/docs/paper/build/steps.tex          one subsection body per step (\\input by paper.tex, wording stays there)
  cad/docs/paper/build/proto_bom.tex      the prototype BOM summary table
  cad/out/<variant>/print/BOM_prototype.csv   the prototype bill of materials (differs from BOM.csv: custom parts
                                          are printed, the pads get neoprene, plus glue, taps and tools)
  cad/out/<variant>/build/steps.json + meshes/*.obj   input of cad/render/build_steps.py
"""
import csv
import json
import os
import re
import sys
import tomllib

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
import FreeCAD as App   # noqa: E402
import Part             # noqa: E402
import MeshPart         # noqa: E402
import params           # noqa: E402
import arm_model as M   # noqa: E402

V = App.Vector
PAPER = os.path.join(CAD, "docs", "paper", "build")
OUT = params.out_dir("build")
MESH = os.path.join(OUT, "meshes")
POSE = "STOW"
FASTENERS = {"BHCS", "SHCS", "CSK", "PAN-M2x12", "INSERT", "NYLOC", "WASHER"}

# Build steps, in order. parts: regexes on part names (first matching step wins; every part must match one).
# bench: built on the bench and mounted later by the step whose `mount` lists it. axes: stacks to list
# (name, reference part, axis, probe radius mm, half-length mm along the axis from the reference part's ends).
# view: direction from the target to the camera (world frame: x forward, y left, z up).
STEPS = [
    dict(key="base", title="Base frame", parts=[r"^Base_Plate", r"^Tower_Bracket", r"^BHCS_M3x8_bracketbase", r"^Tower_[LR]_CF3",
                                                 r"^BHCS_M3x10_bracket", r"^Nyloc_M3_bracket", r"^Cable_Clip"], view=(1.0, -1.1, 0.8)),
    dict(key="drive_frames", title="Drive frames with the J1 and J2 servos", bench=True,
         parts=[r"^Drive_Frame", r"^Brg_6804", r"^J[12]_Servo", r"^PAN_M2x12_J[12]_", r"^Servo_Horn_STS_J[12]", r"^Pinion_",
                r"^BHCS_M3x8_pinion"], view=(0.6, -1.4, 0.7)),
    dict(key="upper_arm", title="Upper arm", bench=True,
         parts=[r"^Upper_Arm_", r"^Brg_6700_Elbow_UA", r"^Brg_6701", r"^UA_Standoff", r"^BHCS_M3x\d+_UA_st", r"^PClip_UA"],
         view=(0.5, -1.3, 1.1)),
    dict(key="shoulder", title="Shoulder: upper arm, J1 hub, J2 journal and crank", mount=["upper_arm"],
         parts=[r"^J1_Output_Hub", r"^BHCS_M3x6_UA_hub", r"^J2_Output_Hub_Journal", r"^Crank_CF3", r"^Washer_M4_crank", r"^SHCS_M4x8_crank"],
         view=(0.9, -1.2, 0.9)),
    dict(key="base_drive", title="Base drive: gears, drive frames and end screws", mount=["drive_frames"],
         parts=[r"^Drive_Gear_m2_54T", r"^Spacer_DF", r"^BHCS_M3x30_frame", r"^Nyloc_M3_frame", r"^Washer_M5_hub", r"^SHCS_M5x10_hub"],
         axes=[("shoulder", "Brg_6804_J1", "y", 24.0, 150.0)], view=(0.7, -1.3, 0.6)),
    dict(key="forearm", title="Forearm", bench=True,
         parts=[r"^Forearm_[LR]", r"^FA_Standoff", r"^BHCS_M3x6_FA_st", r"^Brg_6700_Wrist_FA"], view=(0.5, -1.3, 1.1)),
    dict(key="rods", title="Rods", bench=True, parts=[r"^Rod_", r"^Brg_MR105"], view=(0.4, -1.3, 1.0)),
    dict(key="elbow", title="Elbow: shaft, forearm and level rocker", mount=["forearm"],
         parts=[r"^Elbow_Shaft", r"^Elbow_Clamp_Collar", r"^Eclip_D10_elbow", r"^Level_Rocker", r"^Level_Hub_Elbow", r"^Sleeve_E_outer",
                r"^Washer_PTFE_E$"], axes=[("elbow", "Elbow_Shaft_D10x101", "y", 16.0, 2.0)], view=(-0.6, -1.3, 0.8)),
    dict(key="linkage", title="Crank rod and level-keeping rods", mount=["rods"],
         parts=[r"^Shim_A$", r"^SB5x8_A$", r"^Nyloc_M4_A$", r"^Spacer_B$", r"^SB5x12_B$", r"^Nyloc_M4_B$", r"^Spacer_G1$", r"^SB5x10_G1$",
                r"^Nyloc_M4_G1$", r"^Shim_Ev1$", r"^SB5x4_Ev1$", r"^Nyloc_M4_Ev1$", r"^Washer_Ev2_head$", r"^Washer_PTFE_Ev2$", r"^SB5x8_Ev2$",
                r"^Nyloc_M4_Ev2$"],
         axes=[("pivot A (crank, rod AB)", "SB5x8_A", "y", 6.0, 3.0), ("pivot B (forearm, rod AB)", "SB5x12_B", "y", 6.0, 3.0),
               ("G1 (tower, rod 1)", "SB5x10_G1", "y", 6.0, 3.0), ("Ev1 (rocker, rod 1)", "SB5x4_Ev1", "y", 6.0, 3.0),
               ("Ev2 (rocker, rod 2)", "SB5x8_Ev2", "y", 6.0, 3.0)], view=(0.3, -1.4, 0.7)),
    dict(key="roll_housing", title="Clevises, roll housing and the J4 roll servo", bench=True,
         parts=[r"^Clevis_", r"^CSK_M3x6_clevis", r"^Insert_M3_clevis", r"^BHCS_M3x6_clevis", r"^Roll_Housing", r"^J4_Roll_Servo",
                r"^PAN_M2x12_J4", r"^Brg_6805"], view=(1.0, -1.0, 0.8)),
    dict(key="level_member", title="Wrist level member and the J3 pitch servo", bench=True,
         parts=[r"^Wrist_Level_Member", r"^Level_Hub_Wrist", r"^Wrist_Servo_Cradle", r"^J3_Wrist_Servo", r"^PAN_M2x12_J3",
                r"^Insert_M3_j3cradle", r"^CSK_M3x6_level", r"^Servo_Horn_25T_pitch", r"^Wrist_Shaft_Coupler", r"^BHCS_M3x5_horn"],
         view=(0.7, 1.3, 0.8)),
    dict(key="wrist", title="Wrist: shaft, pitch drive and rod 2", mount=["roll_housing", "level_member"],
         parts=[r"^Wrist_Shaft_D10", r"^Eclip_D10_wrist", r"^Washer_Dv2_head", r"^Washer_PTFE_Dv2", r"^SB5x8_Dv2", r"^Nyloc_M4_Dv2"],
         axes=[("wrist", "Wrist_Shaft_D10x70", "y", 11.0, 6.0), ("Dv2 (level member, rod 2)", "SB5x8_Dv2", "y", 6.0, 3.0)],
         view=(0.6, 1.3, 0.9)),
    dict(key="jaws", title="Jaws and pads", bench=True,
         parts=[r"^Jaw_Block", r"^Finger_", r"^Insert_M3_wall", r"^BHCS_M3x6_wall", r"^Pad_", r"^Grip_Rubber", r"^Standoff_D6",
                r"^BHCS_M3x6_fing", r"^Pin_D4x14_coupler"], view=(1.0, -0.9, 1.0)),
    dict(key="head", title="Gripper head: palm, servo, links, spring", bench=True, mount=["jaws"],
         parts=[r"^Gripper_Palm", r"^Grip_Servo", r"^Pin_D4x14_ground", r"^Pin_D4x30", r"^Pin_D4x8", r"^Pin_D4x20", r"^Torsion_Spring",
                r"^Link_", r"^Sector_", r"^Washer_[LR]D$", r"^Servo_Horn_STS_disc"],
         axes=[("left drive pivot", "Pin_D4x20_ground_LD", "z", 5.0, 3.0), ("right drive pivot", "Pin_D4x30_ground_RD", "z", 5.0, 3.0)],
         view=(0.9, -0.9, 1.2)),
    dict(key="roll", title="Roll: hub and gripper head", mount=["head"],
         parts=[r"^Servo_Horn_25T_roll", r"^Roll_Hub", r"^BHCS_M3x5_rollhorn", r"^BHCS_M3x8_palmhub"],
         axes=[("roll", "Roll_Hub", "x", 20.0, 40.0)], view=(1.0, -1.1, 0.7)),
    dict(key="chassis", title="Mounting on the chassis", parts=[r"^SHCS_M4x12_base"], view=(1.2, -1.0, 0.7)),
]

# Prototype-only items (not in the model): consumables and tools. (item, qty, use)
EXTRAS = [
    ("consumable", "CA glue (medium) or 5-minute epoxy", "1", "dovetail halves of the upper arm, forearm and rod plates"),
    ("consumable", "3M 300LSE transfer tape (or CA)", "1 roll", "bonds the neoprene to the pads"),
    ("consumable", "Medium threadlocker (blue)", "1", "metal screws into the aluminium servo horns"),
    ("consumable", "Dry PTFE lubricant", "1", "printed gear meshes (18T/54T, sector gears)"),
    ("tool", "M3, M4 and M5 hand taps with a tap wrench", "1 set", "threads in the printed parts that the production parts have tapped"),
    ("tool", "4.0 and 4.1 mm drills (or a 4 mm H8 reamer)", "1 each", "D4 pin bores, to the size the Test_Fit_Small piece chose"),
    ("tool", "Soldering iron with an M3 heat-set insert tip", "1", "M3 inserts"),
    ("tool", "Hex keys 1.5, 2, 2.5, 3, 4 mm; 5.5 and 7 mm wrenches", "1 set", "button heads (2), M3 cap (2.5), M4 (3), M5 (4); M3 / M4 nylocs"),
    ("tool", "Bench vice with soft jaws (or a hand arbor press)", "1", "bearings and pins"),
    ("tool", "E-clip pliers (or a flat screwdriver)", "1", "DIN 6799 size 7 on the D10 shafts"),
    ("tool", "PC with the Feetech FD software and the FE-URT-1 adapter", "1", "servo IDs, mode and calibration"),
]


def _esc(s):
    return (str(s).replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")
            .replace("#", r"\#").replace("^", r"\^{}").replace("~", r"\~{}").replace("$", r"\$"))


def _world(p, plc):
    s = p.vis.copy()
    s.Placement = plc.multiply(s.Placement)
    return s


def _group_key(p):
    """What a builder picks up: a printed / cut part by name, a purchased part by catalogue key and size."""
    if p.kind != "CAT":
        return re.sub(r"_$", "", re.sub(r"(_[LR]?)\d$", r"\1", p.name))   # Spacer_DF_L0..2 -> Spacer_DF_L x3
    m = re.search(r"(M\d+x\d+|D4x\d+|SB5x\d+|PA2\.0)", p.name)
    size = m.group(1) if m else ""
    if p.src in ("BHCS", "SHCS", "CSK"):
        return "%s %s" % (p.src, size)
    if p.src in ("NYLOC", "INSERT", "WASHER"):
        mm = re.search(r"_M(\d)", p.name)
        return "%s M%s" % (p.src.title() if p.src != "INSERT" else "Insert", mm.group(1) if mm else "")
    if p.src == "SB5":
        return "Shoulder screw %s" % size
    return p.src


def main():
    bodies = M.build_bodies()
    q, jaw = M.pose_q(POSE)
    plc = M.placements(*q, jaw=jaw)
    parts = [(b, p) for b, ps in bodies.items() for p in ps]
    by_name = {p.name: (b, p) for b, p in parts}
    world = {p.name: _world(p, plc[b]) for b, p in parts}

    # ---- assign every part to one step
    owner, problems = {}, []
    for b, p in parts:
        hits = [s["key"] for s in STEPS if any(re.search(rx, p.name) for rx in s["parts"])]
        if not hits:
            problems.append("no step for %s (%s)" % (p.name, b))
        else:
            owner[p.name] = hits[0]
    steps = {s["key"]: s for s in STEPS}
    for s in STEPS:
        s["names"] = [n for n, k in owner.items() if k == s["key"]]
        if not s["names"]:
            problems.append("step %s has no parts" % s["key"])
        for m in s.get("mount", []):
            if m not in steps or not steps[m].get("bench"):
                problems.append("step %s mounts %s, which is not a bench step" % (s["key"], m))
    mounted = {m for s in STEPS for m in s.get("mount", [])}
    for s in STEPS:
        if s.get("bench") and s["key"] not in mounted:
            problems.append("bench step %s is never mounted" % s["key"])

    # ---- printed parts: which STL files (halves) and the print material, from export_print.py's list
    plist = {}
    pl_path = os.path.join(params.out_dir("print"), "print_list.csv")
    if os.path.exists(pl_path):
        for r in csv.DictReader(open(pl_path, encoding="utf-8")):
            plist.setdefault(r["part"], []).append(r)
    else:
        problems.append("missing %s: run cad/tools/export_print.py first" % pl_path)
    cat = tomllib.load(open(os.path.join(CAD, "data", "catalogue.toml"), "rb"))

    def proto_of(p):
        if p.kind == "CAT":
            return "buy"
        if p.kind == "RUBBER":
            return "cut from neoprene sheet"
        rows = plist.get(p.name, [])
        if not rows:
            problems.append("custom part %s is not in print_list.csv" % p.name)
            return "?"
        return "print, 2 halves (glue)" if len(rows) > 1 else "print"

    # ---- stacks along joint axes
    def stack(ref, axis, r, half):
        bb = world[ref].BoundBox
        c = bb.Center
        i = "xyz".index(axis)
        lo = (bb.XMin, bb.YMin, bb.ZMin)[i] - half
        hi = (bb.XMax, bb.YMax, bb.ZMax)[i] + half
        a, e = V(c), V(c)
        setattr(a, axis, lo)
        setattr(e, axis, hi)
        seg = Part.LineSegment(a, e).toShape()
        out = []
        for n, s in world.items():
            sb = s.BoundBox
            mn, mx = (sb.XMin, sb.YMin, sb.ZMin)[i], (sb.XMax, sb.YMax, sb.ZMax)[i]
            if mx < lo or mn > hi:
                continue
            o = [k for k in range(3) if k != i]
            near = all((sb.XMin, sb.YMin, sb.ZMin)[k] - r <= c[k] <= (sb.XMax, sb.YMax, sb.ZMax)[k] + r for k in o)
            if not near:
                continue
            if mx - mn > 1.2 * (hi - lo):
                continue                    # a long plate the probe only grazes (the forearm on the roll axis)
            p_ = by_name[n][1]
            if p_.kind == "CAT" and p_.src in FASTENERS:
                ctr = ((sb.XMin + sb.XMax) / 2, (sb.YMin + sb.YMax) / 2, (sb.ZMin + sb.ZMax) / 2)
                if max(abs(ctr[k] - c[k]) for k in o) > 1.5:
                    continue                # bolt circles and servo screws: in the parts table, not on the axis
            try:
                d = s.distToShape(seg)[0]
            except Exception:
                d = 0.0
            if d <= r:
                out.append((round(mn, 1), round(mx, 1), n))
        return sorted(out)

    # ---- per-step tables, stacks and meshes
    os.makedirs(PAPER, exist_ok=True)
    os.makedirs(MESH, exist_ok=True)
    installed = []          # names built into the arm so far
    jsteps, tex = [], []
    for idx, s in enumerate(STEPS, 1):
        new = s["names"]
        mount = []
        stackm = list(s.get("mount", []))
        while stackm:                       # mounted sub-assemblies, and the ones they carry
            k = stackm.pop()
            mount += steps[k]["names"]
            stackm += steps[k].get("mount", [])
        context = [] if s.get("bench") else list(installed)
        if not s.get("bench"):
            installed += mount + new
        # meshes
        files = {}
        for role, names in (("new", new), ("mount", mount), ("context", context)):
            if not names:
                continue
            comp = Part.makeCompound([world[n] for n in names])
            f = os.path.join(MESH, "%02d_%s_%s.obj" % (idx, s["key"], role))
            MeshPart.meshFromShape(Shape=comp, LinearDeflection=0.25, AngularDeflection=0.5, Relative=False).write(f)
            files[role] = os.path.relpath(f, OUT).replace("\\", "/")
        fb = Part.makeCompound([world[n] for n in new + mount]).BoundBox
        jsteps.append(dict(idx=idx, key=s["key"], title=s["title"], view=s["view"], files=files,
                           frame=[fb.XMin, fb.YMin, fb.ZMin, fb.XMax, fb.YMax, fb.ZMax],
                           png="build_%02d_%s.jpg" % (idx, s["key"])))
        # parts table: group by what the builder picks up
        groups = {}
        for n in new:
            b, p = by_name[n]
            g = _group_key(p)
            e = groups.setdefault(g, dict(qty=0, kind=p.kind, src=p.src, proto=proto_of(p), names=[]))
            e["qty"] += 1
            e["names"].append(n)
        rows = []
        for g in sorted(groups, key=lambda g: (groups[g]["kind"] == "CAT", g)):
            e = groups[g]
            if e["kind"] == "CAT":
                desc = cat.get(e["src"], {}).get("desc", e["src"])
                desc = re.split(r"[,:(]", desc)[0].strip() if len(desc) > 60 else desc
            else:
                b, p = by_name[e["names"][0]]
                desc = "%s; production: %s" % (e["proto"], re.sub(r"^custom: ", "", p.src))
            rows.append(r"%s & %d & %s \\" % (_esc(g), e["qty"], _esc(desc[:110])))
        mt = [steps[m]["title"].split(":")[0] for m in s.get("mount", [])]
        t = [r"\begin{center}\render{%s}{0.62\linewidth}\\[-2pt]{\footnotesize Step %d: %s. Orange: added in this step; blue: "
             r"bench sub-assembly mounted; grey: already built.}\end{center}" % (jsteps[-1]["png"], idx, _esc(s["title"])),
             r"\paragraph{Parts.}" + (r" Built on the bench." if s.get("bench") else "")
             + (r" Mounts: %s." % ", ".join(_esc(x[0].lower() + x[1:]) for x in mt) if mt else ""),
             r"\begin{center}\footnotesize\begin{tabular}{@{}p{0.30\linewidth}rp{0.58\linewidth}@{}}\toprule",
             r"Part & Qty & Prototype / description \\ \midrule"] + rows + [r"\bottomrule\end{tabular}\end{center}"]
        for (an, ref, axis, r, half) in s.get("axes", []):
            st = stack(ref, axis, r, half)
            side = {"y": r"from the \_L side ($-y$) to the \_R side ($+y$)", "x": "from the rear ($-x$) forward",
                    "z": "from the bottom up"}[axis]
            items, seen = [], {}
            for mn, mx, n in st:
                seen.setdefault((re.sub(r"_\d+$", "", n), mn, mx), []).append(n)
            for (base, mn, mx), ns in sorted(seen.items(), key=lambda kv: (kv[0][1], kv[0][2])):
                lbl = ns[0] if len(ns) == 1 else "%d x %s" % (len(ns), base)
                items.append(r"\texttt{%s} {\scriptsize(%s %.1f\,..\,%.1f)}" % (_esc(lbl), axis, mn, mx))
            t.append(r"\paragraph{Stack on the %s axis,} %s: %s." % (_esc(an), side, "; ".join(items)))
        tex.append((s["key"], "\n".join(t)))

    with open(os.path.join(PAPER, "steps.tex"), "w", encoding="utf-8", newline="\n") as f:
        f.write("% generated by cad/tools/build_guide.py: one \\buildstep{key} body per step; do not edit\n")
        for k, body in tex:
            f.write("\\expandafter\\def\\csname buildstep@%s\\endcsname{%%\n%s}\n" % (k, body))
        f.write("\\newcommand{\\buildstep}[1]{\\csname buildstep@#1\\endcsname}\n")
    json.dump(dict(variant=params.variant(), pose=POSE, steps=jsteps), open(os.path.join(OUT, "steps.json"), "w"), indent=1)

    # ---- prototype BOM: what differs from BOM.csv (custom parts printed, rubber cut, extras)
    bom_rows, counts = [], {}
    for b, p in parts:
        if p.kind == "CAT":
            g = _group_key(p)
            counts[g] = counts.get(g, 0) + 1
    for b, p in parts:
        if p.kind == "CAT":
            continue
        rows_ = plist.get(p.name, [])
        files = " + ".join(r["file"] for r in rows_)
        mat = rows_[0]["print in"] if rows_ else ("neoprene 1/16 in" if p.kind == "RUBBER" else "")
        bom_rows.append(["printed" if rows_ else "cut", p.name, 1, b, mat, files, re.sub(r"^custom: ", "", p.src),
                         "printed in place of the production part" if rows_ and p.kind != "PRINT" else ""])
    for g in sorted(counts):
        bom_rows.append(["purchased", g, counts[g], "", "", "", "same as BOM.csv", "see amazon_buy_list.csv (prototype column)"])
    for kind, item, qty, use in EXTRAS:
        bom_rows.append([kind, item, qty, "", "", "", "prototype only", use])
    bom_path = os.path.join(params.out_dir("print"), "BOM_prototype.csv")
    with open(bom_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["type", "item", "qty", "body", "prototype material", "print files", "production part", "note"])
        w.writerows(bom_rows)
    n_print = sum(1 for r in bom_rows if r[0] == "printed")
    n_sub = sum(1 for r in bom_rows if r[0] == "printed" and r[7])
    n_halves = sum(1 for r in bom_rows if r[0] == "printed" and " + " in r[5])
    n_buy = sum(r[2] for r in bom_rows if r[0] == "purchased")
    with open(os.path.join(PAPER, "proto_bom.tex"), "w", encoding="utf-8", newline="\n") as f:
        f.write("% generated by cad/tools/build_guide.py; do not edit\n")
        f.write("\\newcommand{\\ProtoPrinted}{%d}\\newcommand{\\ProtoSubst}{%d}\\newcommand{\\ProtoHalves}{%d}"
                "\\newcommand{\\ProtoBought}{%d}\\newcommand{\\ProtoBoughtLines}{%d}\\newcommand{\\BuildSteps}{%d}\n"
                % (n_print, n_sub, n_halves, n_buy, len(counts), len(STEPS)))
        f.write("\\newcommand{\\ProtoExtras}{%\n\\begin{center}\\footnotesize\\begin{tabular}{@{}lp{0.40\\linewidth}lp{0.36\\linewidth}@{}}\\toprule\n"
                "& Item & Qty & Use \\\\ \\midrule\n")
        for kind, item, qty, use in EXTRAS:
            f.write("%s & %s & %s & %s \\\\\n" % (kind, _esc(item), _esc(qty), _esc(use)))
        f.write("\\bottomrule\\end{tabular}\\end{center}}\n")
        bus = params.load("actuators")["BUS"]
        f.write("\\newcommand{\\BusBaud}{%g\\,kbit/s}\n" % (bus["baud"] / 1000.0))
        f.write("\\newcommand{\\BusTable}{%\n\\begin{center}\\footnotesize\\begin{tabular}{@{}llrrrrp{0.25\\linewidth}@{}}\\toprule\n"
                "Joint & Servo & ID & Task range (joint) & Ratio & At the servo & Single-turn reach, centred \\\\ \\midrule\n")
        tp = json.load(open(os.path.join(os.path.dirname(CAD), "sim", "arc_arm_fourbar", "task_poses.json")))["poses"]
        ratio = params.load("actuators")["BASE"]["ratio"]
        mids = {}
        for jk, jn, servo, rt in (("J1", "shoulder", "left drive frame", ratio), ("J2", "elbow", "right drive frame", ratio),
                                  ("J3", "wrist_pitch", "level member cradle", 1.0), ("J4", "wrist_roll", "roll housing", 1.0),
                                  ("GRIP", "gripper", "palm", 1.0)):
            v = [tp[k]["joints_deg"][jn] for k in tp]
            span = (max(v) - min(v)) * rt
            mid = (max(v) + min(v)) / 2
            mids[jk] = mid
            out_ = sorted(k for k in tp if abs(tp[k]["joints_deg"][jn] - mid) * rt > 180.0)
            reach = ("%.1f\\,..\\,%.1f$^\\circ$" % (mid - 180.0 / rt, mid + 180.0 / rt)) if span > 360 else "the whole range"
            if out_:
                reach += "; misses " + ", ".join(_esc(k) for k in out_)
            f.write("%s (%s) & %s & %d & %.1f\\,..\\,%.1f$^\\circ$ & %g:1 & %.0f$^\\circ$ & %s \\\\\n"
                    % (jk, jn.replace("_", " "), servo, bus[jk], min(v), max(v), rt, span, reach))
        f.write("\\bottomrule\\end{tabular}\\end{center}}\n")

        f.write("\\newcommand{\\MidJOne}{%.1f}\\newcommand{\\MidJTwo}{%.1f}\n" % (mids["J1"], mids["J2"]))

    status = "FAIL" if problems else "PASS"
    for pr in problems:
        print("BUILD_GUIDE problem:", pr)
    print("BUILD_GUIDE %s: %d steps, %d parts assigned, %d printed (%d in place of metal/CF), %d purchased pieces"
          % (status, len(STEPS), len(owner), n_print, n_sub, n_buy))
    params.record("build_guide", status, files=[bom_path, os.path.join(PAPER, "steps.tex"), os.path.join(OUT, "steps.json")],
                  note="%d steps; %d problems" % (len(STEPS), len(problems)))
    return 0 if not problems else 1


sys.exit(main())
