# -*- coding: utf-8 -*-
"""Forearm: FOREARM, ROCKER, ROD2 and the level-keeping hubs.

Level keeping stage 2 (elbow E -> wrist D) is a parallelogram: lever on the rocker at E and on the level member at D
(both V2_LEN at V2_ANG, constant orientation) joined by ROD2 (length L3, parallel to the forearm). It replaced the
GT2 belt (stiffer, no tension/skip). Dead points at th2 = V2_ANG and V2_ANG - 180 lie outside the task elbow range.
"""
from arm.core import *  # noqa: F401,F403
from arm.base import *  # noqa: F401,F403
from arm.upper_arm import *  # noqa: F401,F403

from arm.core import _hull2  # noqa: F401


def level_hub(name):
    """Aluminium hub keyed to its plate by a hex (af19), 6700 bearing inside: the old GT2 pulley's axial stack
    (y -39 .. -25.5) without the teeth, slimmed to D14 where rod 2 sweeps past (y -35 .. -31).
    The D15.2 shoulder (y -35 .. -34.4) stops the bearing's outer race and joins the D14 neck to the seat: without it
    the D15 seat reached the neck's face and the hub was two solids (the printed necks strung in mid-air, 2026-11-27).
    It clears rod 2 by 2.4 mm at every task pose; a 0.3 mm D12.6 relief keeps it off the inner race."""
    hexk = H._hexprism(19, -39.0, -36.0)
    hub = hexk.fuse(ycyl(0, 0, -36.0, -35.0, 9.5)).fuse(ycyl(0, 0, -35.0, -25.5, 7.0))
    hub = hub.fuse(ycyl(0, 0, -35.0, -34.4, 7.6))
    hub = hub.cut(ycyl(0, 0, -39.1, -35.0, 7.5)).cut(ycyl(0, 0, -35.1, -34.7, 6.3)).cut(ycyl(0, 0, -43, -20, 5.3))
    return [Part_(name, hub, hub, "AL", "custom: 6061 turned hub, hex key af19, 6700 seat", "alu"),
            P(name + "_Brg_6700", H.bearing(10, 15, 4, -39.0, 1), "CAT", "6700ZZ", "alu")]


def v2_pin(name, x, z, tapped=False):
    """Stage-2 pin on a lever (rocker or level member, plate y -39..-36). From the inboard side: shoulder screw
    head (y -30.5..-27), 0.5 washer (D7: inner race only), rod-2 MR105 inner race (-35..-31), 1 mm PTFE washer, the
    plate. Nut version (CF level member): SB5x8, step 0.5 inside the plate, nyloc on the outboard face clamps the
    stack. Tapped version (6061 rocker): SB5x6, step sits in a 0.5 counterbore, M4 thread engages the plate's own
    3 mm, tip flush outboard - nothing in rod 1's layer (y -43.5..-40.5), which sweeps over this pin near th1 150."""
    out = [P("Washer_" + name + "_head", at((ring(0, 0, -31.0, -30.5, 3.5, 2.6),) * 2, x, z), "SHIM",
             "custom: 301 SS shim stock 0.5, laser cut", "steel"),
           P("Washer_PTFE_" + name, at((ring(0, 0, -36.0, -35.0, 4.5, 2.6),) * 2, x, z), "PTFE",
             "custom: PTFE sheet 1.0, laser cut", "pad")]
    if tapped:
        out.append(P("SB5x6_" + name, at(H.shoulder(5, 6.0, 4, 2.5, -30.5, -1), x, z), "CAT", "SB5", "steel",
                     "M4 into the tapped 6061 rocker, threadlocker"))
    else:
        out.append(P("SB5x8_" + name, at(H.shoulder(5, 8.0, 4, 7.0, -30.5, -1), x, z), "CAT", "SB5", "steel"))
        out.append(P("Nyloc_M4_" + name, at(H.nyloc(4, -39.0, -1), x, z), "CAT", "NYLOC", "steel"))
    return out


def body_rod2():
    """Rod 2: CF plate ROD2_T x ROD2_W, pins L3 apart, MR105 in each eye, along +x from the rocker pin."""
    L, yc, t, w = K["L3"], Y["ROD2"], ROD2_T, ROD2_W
    # no lightening pockets: a 6 mm slot would drop the buckling load from ~340 N to ~210 N (SF < 2 at servo stall)
    pl = plate([(0, 0, w / 2), (L, 0, w / 2)], yc, [(0, 0, 5.0), (L, 0, 5.0)], t=t)
    # notch on the +z (upper) edge near the wrist: the four-bar's right sector gear passes there at PIPE_CHUTE (pitch 90).
    # The hubs only ever come at the rod from -z, so this edge is free; the section there is 7 x 4 mm.
    pl = pl.cut(_hull2(275.0, w / 2, 9.0, 295.0, w / 2, 9.0, yc - t / 2 - 1, t + 2))
    out = [Part_("Rod_2_CF%d" % t, pl, pl, "CF", "custom: %g mm CF plate (DXF)" % t, "cf")]
    for x in (0, L):
        out.append(P("Brg_MR105_Rod_2_%d" % x, at(H.bearing(5, 10, 4, yc - t / 2, 1), x, 0), "CAT", "MR105ZZ", "alu"))
    return out


def body_forearm():
    L1, L3 = K["L1"], K["L3"]
    out = []
    pk = [((22, 0, 6), (L3 / 3 - 15, 0, 6)), ((L3 / 3 + 15, 0, 6), (L3 / 2 - 15, 0, 6)),
          ((L3 / 2 + 15, 0, 6), (2 * L3 / 3 - 15, 0, 6)), ((2 * L3 / 3 + 15, 0, 6), (L3 - 28, 0, 5))]
    for side, yc in (("L", Y["FL"]), ("R", -Y["FL"])):
        holes = [(0, 0, 5.0), (L3, 0, 7.5), (L3 / 3, 0, 1.65), (2 * L3 / 3, 0, 1.65), (-L1, 0, 2.1)]
        lobes = [(-L1, 0, 9), (0, 0, 14), (L3, 0, 12)]
        pl = plate(lobes, yc, holes, pockets=pk)
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
    return out


def body_rocker():
    v1 = u(K["V1_ANG"], K["V1_LEN"])
    v2 = u(K["V2_ANG"], K["V2_LEN"])
    yc = Y["ROCK"]
    # Ev2 is a nut-clamped pin like Dv2: with the levers up (V2_ANG 72.7) rod 1 never comes near its outboard nut.
    # (A tapped 6061 rocker with a flush pin was needed only while the levers pointed down.)
    pl = plate([(0, 0, 15), (v1[0], v1[1], 8.5), (v2[0], v2[1], 8.5)], yc,
               [(v1[0], v1[1], 2.55), (v2[0], v2[1], 2.55)])   # D5.1: takes the stock 5 mm shoulders
    pl = pl.cut(hexhole(19, 0, 0, yc - 2, yc + 2))
    out = [Part_("Level_Rocker_CF3", pl, pl, "CF", "custom: 3 mm CF plate (DXF), hex af19", "cf")]
    out += level_hub("Level_Hub_Elbow")
    out += v2_pin("Ev2", *v2)
    out.append(P("Sleeve_E_outer", (ring(0, 0, -44.0, -39.0, 6.5, 5.05),) * 2,
                 "AL", "custom: D13/D10 sleeve", "alu"))
    out.append(P("Washer_PTFE_E", (ring(0, 0, -25.5, -19.5, 6.5, 5.05),) * 2, "PTFE", "custom: PTFE rod D13, turned thrust sleeve", "pad"))
    out.append(P("Shim_Ev1", at((ring(0, 0, -39.5, -39.0, 4.0, 2.55),) * 2, *v1), "SHIM", "custom: 301 SS shim stock 0.5, laser cut", "steel"))
    # stock 5 mm shoulder (SHLD050-005): step ends 0.5 mm inside the rocker's D5.1 hole, nyloc clamps the stack
    out.append(P("SB5x4_Ev1", at(H.shoulder(5, 4.0, 4, 9, -43.5, 1), *v1), "CAT", "SB5", "steel"))   # McMaster 92981A747: step on the race face, nyloc clamps shim + rocker
    out.append(P("Nyloc_M4_Ev1", at(H.nyloc(4, -36.0, 1), *v1), "CAT", "NYLOC", "steel"))
    return out
