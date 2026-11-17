# -*- coding: utf-8 -*-
"""Forearm: FOREARM, ROCKER and the GT2 level-keeping pulley.
"""
from arm.core import *  # noqa: F401,F403
from arm.base import *  # noqa: F401,F403
from arm.upper_arm import *  # noqa: F401,F403

from arm.core import _hull2  # noqa: F401

def gt2_level_pulley(name):
    """Custom GT2 30T pulley keyed to its plate by a hex (af19), bearing inside."""
    body, chk, pd = H.gt2_pulley(GT2_T, -36.0, -25.5, 10.6, flange_t=0.75)
    hexk = H._hexprism(19, -39.0, -36.0)
    pul = body.fuse(hexk).cut(ycyl(0, 0, -39.1, -35.0, 7.5)).cut(ycyl(0, 0, -43, -20, 5.3))
    odr = (pd - 0.508) / 2
    fr = odr + 1.5
    chk = hexk.fuse(ycyl(0, 0, -36.0, -35.25, fr)).fuse(ycyl(0, 0, -35.25, -26.25, odr)).fuse(ycyl(0, 0, -26.25, -25.5, fr))
    chk = chk.cut(ycyl(0, 0, -39.1, -35.0, 7.5)).cut(ycyl(0, 0, -43, -20, 5.3))
    return [Part_(name, pul, chk, "AL", "custom: 6061 GT2 %dT hobbed, hex key af19" % GT2_T, "alu"),
            P(name + "_Brg_6700", H.bearing(10, 15, 4, -39.0, 1), "CAT", "6700ZZ", "alu")], pd


def body_forearm():
    L1, L3 = K["L1"], K["L3"]
    out = []
    xs = [-L1, 0, L3 / 3, L3 / 2, 2 * L3 / 3, L3]
    pd30 = GT2_T * 2.0 / math.pi
    IZ = pd30 / 2 - 0.254 + 1.38 + 7.0                 # idler (r7) rides on the belt back
    pk = [((22, 0, 6), (L3 / 3 - 15, 0, 6)), ((L3 / 3 + 15, 0, 6), (L3 / 2 - 15, 0, 6)),
          ((L3 / 2 + 15, 0, 6), (2 * L3 / 3 - 15, 0, 6)), ((2 * L3 / 3 + 15, 0, 6), (L3 - 28, 0, 5))]
    for side, yc in (("L", Y["FL"]), ("R", -Y["FL"])):
        holes = [(0, 0, 5.0), (L3, 0, 7.5), (L3 / 3, 0, 1.65), (2 * L3 / 3, 0, 1.65), (-L1, 0, 2.1)]
        lobes = [(-L1, 0, 9), (0, 0, 14), (L3, 0, 12)] + ([(L3 / 2, IZ, 6.5)] if side == "L" else [])
        pl = plate(lobes, yc, holes, pockets=pk)
        if side == "L":   # idler slot (tension adjust)
            pl = pl.cut(_hull2(L3 / 2, IZ - 1.5, 2.1, L3 / 2, IZ + 1.5, 2.1, yc - T / 2 - 1, T + 2))
        out.append(Part_("Forearm_%s_CF3" % side, pl, pl, "CF", "custom: 3 mm CF plate (DXF)", "cf"))
    out.append(P("Brg_6700_Wrist_FA_L", at(H.bearing(10, 15, 4, -19.5, 1), L3, 0), "CAT", "6700ZZ", "alu"))
    out.append(P("Brg_6700_Wrist_FA_R", at(H.bearing(10, 15, 4, 19.5, -1), L3, 0), "CAT", "6700ZZ", "alu"))
    sh = ycyl(0, 0, -50.5, 50.5, 5.0)                                   # 1.56 mm land outboard of each groove
    for y0_ in (48.0, -48.94):                                            # e-clip grooves D7 x 0.94 (DIN 6799 size 7)
        sh = sh.cut(ycyl(0, 0, y0_, y0_ + 0.94, 6.0).cut(ycyl(0, 0, y0_ - 0.1, y0_ + 1.04, 3.5)))
    out.append(Part_("Elbow_Shaft_D10x101", sh, sh, "STEEL", "custom: cut from McMaster 6112K47 D10 h6 rod, ground e-clip grooves", "steel"))
    for sgn in (-1, 1):
        nmc = "L" if sgn < 0 else "R"
        # Stafford 1LM010 one-piece clamp collar, 10 mm bore, OD 24 x 9, M3x10 clamp screw included;
        # sits inboard against the forearm plate (y 7.5 .. 16.5)
        col = ring(0, 0, sgn * 16.5, sgn * 7.5, 12.0, 5.0)
        out.append(Part_("Elbow_Clamp_Collar_%s" % nmc, col, col, "CAT", "COLLAR10", "steel", "Stafford 1LM010 clamp collar"))
        out.append(P("Eclip_D10_elbow_%s" % ("L" if sgn < 0 else "R"), H.eclip(10, sgn * 48.0, sgn), "CAT", "ECLIP", "steel"))
    for i, x in enumerate((L3 / 3, 2 * L3 / 3)):
        out.append(P("FA_Standoff_D8_%d" % i, at(H.standoff_round(8, 33, -16.5, 1), x, 0), "AL", "custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer)", "alu"))
        for sgn in (-1, 1):
            out.append(P("BHCS_M3x6_FA_st_%d%s" % (i, "L" if sgn < 0 else "R"),
                         at(H.screw("BHCS", 3, 6, sgn * 19.5, -sgn), x, 0), "CAT", "BHCS", "steel"))
    # pivot B (rod AB): spacer, shoulder screw, nyloc in the forearm gap
    out.append(P("Spacer_B", at((ring(0, 0, 19.5, 27.5, 4.5, 2.6),) * 2, -L1, 0), "AL", "custom: D9/D5.2 x 8 alu", "alu"))
    out.append(P("SB5x12_B", at(H.shoulder(5, 12, 4, 8, 31.5, -1), -L1, 0), "CAT", "SB5", "steel"))
    out.append(P("Nyloc_M4_B", at(H.nyloc(4, 16.5, -1), -L1, 0), "CAT", "NYLOC", "steel"))
    # belt idler (tensioner) on forearm L, in the belt plane
    ix, iz = L3 / 2, IZ
    out.append(Part_("Belt_Idler_Roller", ring(ix, iz, -36, -26, 7.0, 5.0), ring(ix, iz, -36, -26, 7.0, 5.0),
                     "PRINT", "custom: printed roller", "pla"))
    out.append(P("Belt_Idler_Brg_MR104", at(H.bearing(4, 10, 4, -35.0, 1), ix, iz), "CAT", "MR104ZZ", "alu"))
    out.append(P("Belt_Idler_Brg_MR104_b", at(H.bearing(4, 10, 4, -27.0, -1), ix, iz), "CAT", "MR104ZZ", "alu"))
    out.append(P("Belt_Idler_Spacer", at((ring(0, 0, -26.0, -19.5, 4.0, 2.1),) * 2, ix, iz), "AL", "custom: D8/D4.2 x 6.5", "alu"))
    out.append(P("SHCS_M4x30_idler", at(H.screw("SHCS", 4, 30.0, -36.0, 1), ix, iz), "CAT", "SHCS", "steel"))   # 91290A172
    out.append(P("Nyloc_M4_idler", at(H.nyloc(4, -16.5, 1), ix, iz), "CAT", "NYLOC", "steel"))
    # stage-2 belt (forearm frame: wraps E pulley at x=0 and D pulley at x=L3)
    _b, _c, pd = H.gt2_pulley(GT2_T, -33.0, -25.5, 10.6)
    belt, bchk = H.gt2_belt(L3, -35.25, -26.25, pd)
    out.append(Part_("GT2_Belt_9mm_Stage2", belt, bchk, "CAT", "GT2-BELT", "motor", "GT2 9 mm (2GT-9), clamp-spliced, tensioned by idler"))
    return out


def body_rocker():
    v1 = u(K["V1_ANG"], K["V1_LEN"])
    yc = Y["ROCK"]
    pl = plate([(0, 0, 15), (v1[0], v1[1], 8.5)], yc, [(v1[0], v1[1], 2.55)])   # D5.1: takes the stock 5 mm shoulder
    pl = pl.cut(hexhole(19, 0, 0, yc - 2, yc + 2))
    out = [Part_("Level_Rocker_CF3", pl, pl, "CF", "custom: 3 mm CF plate (DXF), hex af19", "cf")]
    pul, _pd = gt2_level_pulley("GT2_Pulley_Elbow")
    out += pul
    out.append(P("Sleeve_E_outer", (ring(0, 0, -44.0, -39.0, 6.5, 5.05),) * 2,
                 "AL", "custom: D13/D10 sleeve", "alu"))
    out.append(P("Washer_PTFE_E", (ring(0, 0, -25.5, -19.5, 6.5, 5.05),) * 2, "PTFE", "custom: PTFE rod D13, turned thrust sleeve", "pad"))
    out.append(P("Shim_Ev1", at((ring(0, 0, -39.5, -39.0, 4.0, 2.55),) * 2, *v1), "SHIM", "custom: 301 SS shim stock 0.5, laser cut", "steel"))
    # stock 5 mm shoulder (SHLD050-005): step ends 0.5 mm inside the rocker's D5.1 hole, nyloc clamps the stack
    out.append(P("SB5x4_Ev1", at(H.shoulder(5, 4.0, 4, 9, -43.5, 1), *v1), "CAT", "SB5", "steel"))   # McMaster 92981A747: step on the race face, nyloc clamps shim + rocker
    out.append(P("Nyloc_M4_Ev1", at(H.nyloc(4, -36.0, 1), *v1), "CAT", "NYLOC", "steel"))
    return out
