# -*- coding: utf-8 -*-
"""Upper arm: UPPER (J1-driven upper-arm plates), CRANK (J2-driven crank) and the parallel rods (body_rod).
"""
from arm.core import *  # noqa: F401,F403
from arm.base import *  # noqa: F401,F403


IF_UA_ST = iface.load("ua_plate__ua_standoff")   # plates <-> standoffs (interfaces/ua_plate__ua_standoff.toml)
UA_CLIP_X = tuple(IF_UA_ST.stations_x())          # UA standoff stations (P-clips on the L side)
UA_CLIP_YZ = params.load("arm")["harness"]["UA_CLIP_YZ"]   # harness bundle centre in the UA frame (y, z)


def body_upper():
    L2 = K["L2"]
    out = []
    # holes and the lightening-pocket layout both come from the standoff stations (the interface file), so the plates
    # and the standoffs cannot drift apart
    st_r = IF_UA_ST["side_a"]["clearance_d"] / 2.0
    pk = link_pockets(L2, 22, 13, [(0.0, 12.0)] + [(x, 3.0) for x in UA_CLIP_X] + [(L2, 7.5)])
    for side, yc in (("L", Y["UA"]), ("R", -Y["UA"])):
        holes = [(L2, 0, 7.5)] + [(x, 0, st_r) for x in UA_CLIP_X]
        if side == "L":
            holes += [(0, 0, 6.05)] + [(*u(a_, 10.0), 1.65) for a_ in UA_HUB_SCREWS]
        else:
            holes += [(0, 0, 9.0)]
        pl = plate([(0, 0, 22), (L2, 0, 13)], yc, holes, pockets=pk)
        out.append(Part_("Upper_Arm_%s_CF3" % side, pl, pl, "CF", "custom: 3 mm CF plate (DXF)", "cf"))
    out.append(P("Brg_6700_Elbow_UA_L", at(H.bearing(10, 15, 4, -44.0, -1), L2, 0), "CAT", "6700ZZ", "alu"))
    out.append(P("Brg_6700_Elbow_UA_R", at(H.bearing(10, 15, 4, 44.0, 1), L2, 0), "CAT", "6700ZZ", "alu"))
    out.append(P("Brg_6701_Shoulder_UA_R", H.bearing(12, 18, 4, 47.0, -1), "CAT", "6701ZZ", "alu"))
    out += motor_hub(-1)
    out += drive_gear_parts(-1, 1)
    for k, a_ in enumerate(UA_HUB_SCREWS):
        p = u(a_, 10.0)
        out.append(P("BHCS_M3x6_UA_hub_%d" % k, at(H.screw("BHCS", 3, 6, -44.0, -1), p[0], p[1]), "CAT", "BHCS", "steel"))   # x6: 3 mm in the 3 mm thread of the 4.5 mm drill
    for i, x in enumerate(UA_CLIP_X):
        out.append(P("UA_Standoff_D8_%d" % i, at(H.standoff_round(8, 88, -44.0, 1), x, 0), "AL", "custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer)", "alu",
                     "D8 x 88 M3 female"))
        # harness P-clip clamped under the outboard standoff screw on UA-L (screw 2 mm longer)
        pc = H.p_clip(-47.0, -1)
        out.append(P("PClip_UA_%d" % i, at(pc[:2], x, 0), "CAT", "PCLIP", "steel", "harness: J3 servo + M2006 bundle"))
        for sgn in (-1, 1):
            y_head = -47.8 if sgn < 0 else 47.0
            out.append(P("BHCS_M3x%d_UA_st_%d%s" % (8 if sgn < 0 else 6, i, "L" if sgn < 0 else "R"),
                         at(H.screw("BHCS", 3, 8 if sgn < 0 else 6, y_head, -sgn), x, 0), "CAT", "BHCS", "steel"))
    return out


def body_crank():
    L1 = K["L1"]
    yc = Y["CRANK"]
    out = []
    cr = plate([(0, 0, 14), (L1, 0, 8)], yc, [(0, 0, 6.075), (L1, 0, 2.5)],
               pockets=[((22, 0, 5), (L1 - 18, 0, 3.5))])
    cr = cr.fuse(ycyl(0, 0, yc - T / 2, yc + T / 2, 6.075).common(box(5.6, yc - T / 2, -7, 7.0, yc + T / 2, 7)))   # D-bore at mid-limit (12.15 / 5.6)
    out.append(Part_("Crank_CF3", cr, cr, "CF", "custom: 3 mm CF plate (DXF), D-bore on journal flat", "cf"))
    out += motor_hub(1, journal=True)
    out += drive_gear_parts(1, 2)
    out.append(P("Washer_M4_crank", H.washer(4, 33.0, -1, od=12, t=0.8), "CAT", "WASHER", "steel"))
    out.append(P("SHCS_M4x8_crank", H.screw("SHCS", 4, 8, 32.2, 1), "CAT", "SHCS", "steel", "axial retention"))
    # pivot A
    out.append(P("Shim_A", at((ring(0, 0, 31.5, 33.0, 4.0, 2.55),) * 2, L1, 0), "SHIM", "custom: 301 SS shim stock 1.5, laser cut", "steel"))
    # stock 8 mm shoulder (Kipp K0705.05X08): step ends inside the crank's D5.1 hole, nyloc clamps bearing race + shim + crank
    out.append(P("SB5x8_A", at(H.shoulder(5, 8.0, 4, 5, 27.5, 1), L1, 0), "CAT", "SB5", "steel"))   # McMaster 90265A577
    out.append(P("Nyloc_M4_A", at(H.nyloc(4, 36.0, 1), L1, 0), "CAT", "NYLOC", "steel"))
    return out


def body_rod(name, L, yc):
    pk = link_pockets(L, 8.5, 8.5, [(0, 5.0), (L / 3, 0), (2 * L / 3, 0), (L, 5.0)], web=4.0, min_r=3.0)
    pk = [((a[0], a[1], 3.5), (b[0], b[1], 3.5)) for a, b in [((18, 0, 0), (L / 2 - 6, 0, 0)), ((L / 2 + 6, 0, 0), (L - 18, 0, 0))]]
    pl = plate([(0, 0, 8.5), (L, 0, 8.5)], yc, [(0, 0, 5.0), (L, 0, 5.0)], pockets=pk)
    out = [Part_(name + "_CF3", pl, pl, "CF", "custom: 3 mm CF plate (DXF)", "cf")]
    for x in (0, L):
        out.append(P("Brg_MR105_%s_%d" % (name, x), at(H.bearing(5, 10, 4, yc - T / 2, 1), x, 0), "CAT", "MR105ZZ", "alu"))
    return out
