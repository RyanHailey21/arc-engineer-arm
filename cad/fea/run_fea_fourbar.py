# -*- coding: utf-8 -*-
"""
FEA + hand checks for the four-bar gripper's new load paths (headless):
    set GRIP=FOURBAR & freecadcmd cad/fea/run_fea_fourbar.py
-> cad/out/fourbar/fea/fea_report.md, fea_results.json, per-case .FCStd/.vtu, and an evidence record.
Reuses fea/run_fea.py (gmsh 2nd-order tets + CalculiX, same mesh-fallback strategy) in library mode.

Load basis (params/gripper_fourbar.toml):
  * actuator-bounded loads (servo stall torque, the grip it produces): STALL x 1.25 - the servo cannot exceed its
    stall torque, so the 2.5 dynamic factor used for gravity/impact loads is not applied to them;
  * gravity + pipe moment (external): x 2.5, as in the rev A FEA.
Required SF >= 1.5 on the factored load.  Allowables: CF plate 200 MPa, PETG-CF 40 MPa (rev A basis),
acetal (POM) sector gears 60 MPa (Delrin yield ~65-70 MPa), 52100 dowel pins 1,000 MPa shear (hardened, conservative).
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
import run_fea as RF  # noqa: E402
import arm_model as M  # noqa: E402

FB, SV = M.FB, M.SERVO
G = 9.81
DF_ACT, DF_EXT = 1.25, 2.5
L = FB["L"] / 1000.0
T_STALL = SV["stall_Nm"]


def link_force():
    """Coupler-pin force on the servo-driven link when the servo stalls against blocked jaws (all torque through
    the lower left drive link, which carries the horn)."""
    return T_STALL / L


def grip_stall():
    th = math.radians(M.FB_TREF)
    t_spring = M.SPRING["rate_Nm_per_deg"] * (M.SPRING["preload_deg"] + M.fb_theta(112.0) - M.FB_TREF)
    return (T_STALL - t_spring) / (2 * L * math.cos(th))


def cases():
    C = []
    gd, gi, cd, ci = M.fb_pivots(1)
    # ---- drive link (CF): fixed at the ground pivot bore, stall reaction at the coupler bore, perpendicular to the link
    s = RF.part_shape("Link_LD_lo_CF3")
    ang = math.atan2(cd[1] - gd[1], cd[0] - gd[0])
    Fl = link_force() * DF_ACT
    C.append(dict(name="fb_drive_link", part="Link_LD_lo_CF3", mat="CF_QI", shape=s, h=0.8,
                  fixed=RF.cyl_faces(s, (0, 0, 1), (gd[0], gd[1], 0), r=FB["PIN_R"] + 0.05),
                  loads=[(RF.cyl_faces(s, (0, 0, 1), (cd[0], cd[1], 0), r=FB["PIN_R"] + 0.05),
                          (-math.sin(ang) * Fl, math.cos(ang) * Fl, 0.0))],
                  desc="servo stall %.2f N*m reacted at the coupler pin: %.0f N x %.2f = %.0f N" % (T_STALL, link_force(), DF_ACT, Fl)))
    # ---- jaw block (PETG-CF): fixed at the coupler pin bores, stall grip reaction on the pad-standoff screw holes
    s = RF.part_shape("Jaw_Block_L")
    Fg = grip_stall() * DF_ACT
    XT, o = M.K["GRIP"], M.O_REF
    holes = []
    for (x, y) in [(XT - 12.0, o + 9.0), (XT + 12.0, o + 9.0), (XT + 12.0, o + 18.0)]:
        holes += RF.cyl_faces(s, (0, 0, 1), (x, y, 0), r=1.65)
    C.append(dict(name="fb_jaw_block", part="Jaw_Block_L", mat="PETG_CF", shape=s, h=1.2,
                  fixed=RF.cyl_faces(s, (0, 0, 1), (cd[0], cd[1], 0), r=FB["PIN_R"] + 0.05) +
                  RF.cyl_faces(s, (0, 0, 1), (ci[0], ci[1], 0), r=FB["PIN_R"] + 0.05),
                  loads=[(holes, (0.0, Fg, 0.0))],
                  desc="stall clamp reaction %.1f N x %.2f = %.0f N on the pad standoffs (all on the top finger)" % (grip_stall(), DF_ACT, Fg)))
    # ---- palm (PETG-CF): fixed at the hub-flange screw holes; head + payload + pipe moment as a vertical load on the
    # ground-pivot bores giving the same bending moment at the mount plate (lever 82 - 65 = 17 mm)
    s = RF.part_shape("Gripper_Palm")
    m_head = sum(M.part_mass_g(p) for bn in ("HEAD", "JAW_L", "JAW_R", "LK_LD", "LK_LI", "LK_RD", "LK_RI")
                 for p in M.build_bodies()[bn]) / 1000.0
    lever = (FB["XG"] - M.IF_PALM.frame_x) / 1000.0
    M_mount = (m_head * G * 0.045 + 0.165 * G * (M.K["GRIP"] - M.IF_PALM.frame_x) / 1000.0 + 0.5) * DF_EXT
    Fp = M_mount / lever
    pins = []
    for p in M.fb_pivots(1)[:2] + M.fb_pivots(-1)[:2]:
        pins += RF.cyl_faces(s, (0, 0, 1), (p[0], p[1], 0), r=FB["PIN_R"] + 0.05)
    C.append(dict(name="fb_palm", part="Gripper_Palm", mat="PETG_CF", shape=s, h=2.0,
                  fixed=RF.cyl_faces(s, (1, 0, 0), None, r=M.IF_PALM["side_b"]["clearance_d"] / 2),
                  loads=[(pins, (0.0, 0.0, -Fp))],
                  desc="head %.2f kg + 165 g pipe + 0.5 N*m pipe moment: %.2f N*m x %.1f at the mount -> %.0f N on the pivot bores"
                  % (m_head, M_mount / DF_EXT, DF_EXT, Fp)))
    return C


def hand_checks():
    """Lewis tooth bending for the sector mesh and dowel shear (closed-form, documented as hand calcs)."""
    out = []
    z, mod, b = FB["TEETH"], 1.0, FB["ZSEC"][1] - FB["ZSEC"][0]
    Y = 0.434                                    # Lewis form factor, 20 deg full depth, z ~ 75 (standard table)
    Ft = (T_STALL / 2) / (z * mod / 2 / 1000.0)  # half the servo torque crosses the mesh to drive the right jaw
    s_l = Ft * DF_ACT / (b * mod * Y)
    out.append(dict(case="fb_sector_tooth", part="Sector_m1_%dT" % z, material="Acetal (POM)", method="Lewis bending (hand calc)",
                    load="half stall torque through the mesh: Ft %.1f N x %.2f" % (Ft, DF_ACT),
                    max_stress_MPa=round(s_l, 1), allowable_MPa=60.0, safety_factor=round(60.0 / s_l, 2),
                    verdict="PASS" if 60.0 / s_l >= 1.5 else "FAIL"))
    A = math.pi * (2 * FB["PIN_R"]) ** 2 / 4
    tau = link_force() * DF_ACT / A
    out.append(dict(case="fb_pivot_pin", part="Dowel D4 (91595A158/167/179)", material="52100 steel, HRC 52+",
                    method="single shear (hand calc)", load="coupler/ground pin force %.0f N x %.2f" % (link_force(), DF_ACT),
                    max_stress_MPa=round(tau, 1), allowable_MPa=1000.0, safety_factor=round(1000.0 / tau, 1),
                    verdict="PASS" if 1000.0 / tau >= 1.5 else "FAIL"))
    p_b = link_force() * DF_ACT / (2 * FB["PIN_R"] * 3.0)    # pin bearing on one 3 mm CF link plate
    out.append(dict(case="fb_link_bearing", part="Link CF3 pivot bore", material="CF plate (bearing allowable 200 MPa)",
                    method="projected-area bearing (hand calc)", load="%.0f N on a 4 x 3 mm bore" % (link_force() * DF_ACT),
                    max_stress_MPa=round(p_b, 1), allowable_MPa=200.0, safety_factor=round(200.0 / p_b, 1),
                    verdict="PASS" if 200.0 / p_b >= 1.5 else "FAIL"))
    return out


def main():
    results = []
    for c in cases():
        if not c["fixed"] or not all(l[0] for l in c["loads"]):
            results.append(dict(case=c["name"], verdict="SETUP ERROR", note="face selection empty: fixed %d, loads %s"
                                % (len(c["fixed"]), [len(l[0]) for l in c["loads"]])))
            continue
        h0 = c.get("h", 2.0)
        last = ""
        for opts in (dict(), dict(algo="Delaunay", hoo=True), dict(algo="Frontal", hoo=True), dict(linear2nd=True, h=h0 * 0.75)):
            cc = dict(c)
            cc.update(opts)
            try:
                r_ = RF.run_case(cc)
                r_["method"] = "FEA (gmsh 2nd-order tets + CalculiX)" + (" %s" % opts if opts else "")
                results.append(r_)
                break
            except Exception:
                import traceback
                last = traceback.format_exc()[-500:]
        else:
            results.append(dict(case=c["name"], verdict="ERROR", note=last))
    results += hand_checks()
    json.dump(results, open(os.path.join(OUT, "fea_results.json"), "w"), indent=1)
    lines = ["# Four-bar gripper - FEA and hand checks", "",
             "Actuator-bounded loads x %.2f (servo stall %.2f N*m is a hard ceiling); gravity + pipe moment x %.1f. "
             "Required SF >= 1.5." % (DF_ACT, T_STALL, DF_EXT), "",
             "| Case | Part | Material | Method | Load | Max stress (MPa) | Allowable (MPa) | SF | Max disp (mm) | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        if "safety_factor" in r:
            lines.append("| %s | %s | %s | %s | %s | %.1f | %.0f | %.1f | %s | %s |" % (
                r["case"], r["part"], r["material"], r.get("method", "FEA"), r["load"],
                r.get("max_von_mises_MPa", r.get("max_stress_MPa")), r["allowable_MPa"], r["safety_factor"],
                ("%.3f" % r["max_disp_mm"]) if "max_disp_mm" in r else "-", r["verdict"]))
        else:
            lines.append("| %s | - | - | - | - | - | - | - | - | %s: %s |" % (r["case"], r["verdict"], r.get("note", "")[:150].replace("|", "/").replace("\n", " ")))
    rep = os.path.join(OUT, "fea_report.md")
    open(rep, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    bad = [r for r in results if r.get("verdict") != "PASS"]
    params.record("fea_fourbar", "FAIL" if bad else "PASS", [rep, os.path.join(OUT, "fea_results.json")],
                  "%d cases, min SF %.1f" % (len(results), min(r.get("safety_factor", 0) for r in results)))
    return 0


main()
