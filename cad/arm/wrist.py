# -*- coding: utf-8 -*-
"""Wrist: LEVEL (level member + J3 pitch servo), GRIPPER (pitch frame: shaft, clevis plates, roll housing,
J4 roll servo, 6805 bearing) and the roll hub shared by every gripper variant (roll_hub_parts, built from
interfaces/roll_*.toml).  Roll-stage constants: HX, ROLL_Z, ROLL_XS.
"""
from arm.core import *  # noqa: F401,F403
from arm.base import *  # noqa: F401,F403
from arm.upper_arm import *  # noqa: F401,F403
from arm.forearm import *  # noqa: F401,F403


_W = params.load("wrist")            # params/wrist.toml
SERVO_ANG = _W["SERVO_ANG"]
HX = _W["HX"]
ROLL_Z = _W["ROLL_Z"]
ROLL_XS = _W["ROLL_XS"]


def _servo_rot():
    return App.Rotation(V(0, 1, 0), -SERVO_ANG)


def body_level():
    yc = Y["ROCK"]
    R = _servo_rot()
    sv, svc, hx, y_ear = H.servo_std(-45.0, -1)
    st_pts = []
    for x in hx:
        for z in (-5.0, 5.0):
            p = R.multVec(V(x, 0, z))
            st_pts.append((p.x, p.z))
    v2 = u(K["V2_ANG"], K["V2_LEN"])         # stage-2 lever (same as the rocker's: the parallelogram's far end)
    pts = [(0, 0, 14), (v2[0], v2[1], 8.5)] + [(x, z, 6) for (x, z) in st_pts]
    pl = plate(pts, yc, [(x, z, 1.65) for (x, z) in st_pts] + [(v2[0], v2[1], 2.55)])
    pl = pl.cut(hexhole(19, 0, 0, yc - 2, yc + 2))
    for (x, z) in st_pts:     # countersinks on the inboard face for ISO 10642
        pl = pl.cut(Part.makeCone(3.0, 1.5, 1.5, V(x, yc + T / 2, z), V(0, -1, 0)))
    out = [Part_("Wrist_Level_Member_CF3", pl, pl, "CF", "custom: 3 mm CF plate (DXF), hex af19", "cf")]
    out += level_hub("Level_Hub_Wrist")
    out += v2_pin("Dv2", *v2)
    sv.Placement = App.Placement(V(), R).multiply(sv.Placement)
    svc.Placement = App.Placement(V(), R).multiply(svc.Placement)
    out.append(Part_("J3_Wrist_Servo_DS3225", sv, svc, "CAT", "DS3225MG", "motor"))
    for i, (x, z) in enumerate(st_pts):
        out.append(P("Servo_Standoff_%d" % i, at(H.standoff_round(6, abs(y_ear - (yc - T / 2)), y_ear, 1), x, z),
                     "AL", "custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer)", "alu", "D6 x %.0f M3 female" % abs(y_ear - (yc - T / 2))))
        out.append(P("CSK_M3x6_level_%d" % i, at(csk(3, 6, yc + T / 2, -1), x, z), "CAT", "CSK", "steel"))
        out.append(P("BHCS_M3x6_servo_%d" % i, at(H.screw("BHCS", 3, 6, y_ear - 2.5, 1), x, z), "CAT", "BHCS", "steel"))
    return out


def _to_roll_axis(pair):
    """Map a part built on the Y axis (servo/horn convention) onto the roll axis:
    servo Y -> +X, servo X -> Z, servo Z -> Y, then drop to z = ROLL_Z."""
    m = App.Matrix(0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1)
    pl = App.Placement(V(0, 0, ROLL_Z), App.Rotation()).multiply(App.Placement(m))
    out = []
    for s_ in pair[:2]:
        s_ = s_.copy()
        s_.Placement = pl.multiply(s_.Placement)
        out.append(s_)
    return out


def xcyl(x0, x1, r, y=0.0, z=ROLL_Z):
    x0, x1 = sorted((x0, x1))
    return Part.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))


def _xscrew(name, x_head, length, y, z, kind="BHCS", direction=1):
    scr = H.screw(kind, 3, length, 0, direction)
    s2 = []
    for s_ in scr[:2]:
        s_ = s_.copy()
        s_.rotate(V(0, 0, 0), V(0, 0, 1), -90)        # +Y -> +X
        s_.translate(V(x_head, y, z))
        s2.append(s_)
    return P(name, s2, "CAT", kind, "steel")


IF_PALM = iface.load("roll_hub__gripper_palm")
IF_HORN = iface.load("roll_horn__roll_hub")


def roll_hub_parts():
    """Roll horn + 6061 roll hub + horn screws, shared by every gripper variant.  The two bolt patterns
    come from interfaces/roll_horn__roll_hub.toml (rear) and roll_hub__gripper_palm.toml (front)."""
    out = [P("Servo_Horn_25T_roll", _to_roll_axis(H.servo_horn_disc(ROLL_XS, 1)), "CAT", "HORN-25T", "alu")]
    fx, fl = IF_PALM.frame_x, IF_PALM["flange"]
    hub = xcyl(49, fx - fl["thickness"], fl["journal_od"] / 2).fuse(xcyl(fx - fl["thickness"], fx, fl["od"] / 2)).cut(xcyl(52, fx + 1, 11))
    hub = hub.cut(xcyl(48, 53, 3.0))           # rear wall = journal dia: the 6805 slides on from the rear
    rx = IF_HORN.frame_x
    for (y, z) in IF_HORN.points_yz():          # clearance through the rear wall to the horn
        hub = hub.cut(Part.makeCylinder(IF_HORN["side_b"]["clearance_d"] / 2, IF_HORN["side_b"]["depth"], V(rx - 1.0, y, z), V(1, 0, 0)))
    sa = IF_PALM["side_a"]
    for (y, z) in IF_PALM.points_yz():          # tapped M3 in the front flange only
        hub = hub.cut(Part.makeCylinder(sa["drill_d"] / 2, sa["drill_depth"], V(fx - fl["thickness"], y, z), V(1, 0, 0)))
    out.append(Part_("Roll_Hub", hub, hub, "AL", "custom: 6061 turned, D25 journal in 6805", "alu"))
    fz = IF_HORN["fastener"]
    for i, (y, z) in enumerate(IF_HORN.points_yz()):     # hub -> roll horn (horn holes are tapped)
        out.append(_xscrew("BHCS_M3x5_rollhorn_%d" % i, fz["head_face_x"], fz["length"], y, z, direction=-1))
    return out


def body_gripper():
    """Pitch frame: wrist shaft + pitch horn/coupler, clevis plates, roll
    housing with the J4 roll servo and the 6805 support bearing."""
    out = []
    # D10 shaft, stepped to D6 x 2 at the horn end so the coupler clears the commercial horn's PCD14 screws
    sh = ycyl(0, 0, -39.0, 27.0, 5.0).fuse(ycyl(0, 0, -43.0, -39.0, 3.0))     # D6 step clears the M3 BHCS heads too
    for y0_, y1_ in ((-25.5, -21.5), (21.5, 25.0)):
        sh = sh.cut(box(4.5, y0_, -6, 6.0, y1_, 6))                       # 0.5 mm drive flats under the clevis plates
    sh = sh.cut(box(2.5, -43.5, -4, 4.0, -39.0, 4))                        # 0.5 mm flat on the D6 step (coupler)
    sh = sh.cut(ycyl(0, 0, 25.0, 25.94, 6.0).cut(ycyl(0, 0, 24.9, 26.0, 3.5)))   # e-clip groove D7 x 0.94
    out.append(Part_("Wrist_Shaft_D10x70", sh, sh, "STEEL", "custom: cut from McMaster 6112K47 D10 h6 rod, D6x4 ground step, D-flats, e-clip groove", "steel"))
    ec = H.eclip(10, 25.0, 1)
    out.append(P("Eclip_D10_wrist", (ec[0], ycyl(0, 0, 25.0, 25.9, 8.5).cut(ycyl(0, 0, 24, 27, 3.5))), "CAT", "ECLIP", "steel"))
    out.append(P("Servo_Horn_25T_pitch", H.servo_horn_disc(-45.0, 1), "CAT", "HORN-25T", "alu"))
    cp = ring(0, 0, -43.0, -41.0, 12.0, 3.075)               # D6 bore on the stepped shaft end (mid-limit 6.15)
    cp = cp.fuse(ycyl(0, 0, -43.0, -41.0, 3.075).common(box(2.6, -43.0, -4, 4.0, -41.0, 4)))   # D-bore flat at mid-limit 2.6
    for k in range(4):
        p = u(45 + 90 * k, H.HORN_PCD / 2)
        cp = cp.cut(ycyl(p[0], p[1], -44, -40, 1.65))
    out.append(Part_("Wrist_Shaft_Coupler", cp, cp, "AL", "custom: 6061, D6 D-bore on the shaft step, 4x M3 clearance (horn)", "alu"))
    for k in range(4):
        p = u(45 + 90 * k, H.HORN_PCD / 2)
        out.append(P("BHCS_M3x5_horn_%d" % k, at(H.screw("BHCS", 3, 5, -41.0, -1), p[0], p[1]), "CAT", "BHCS", "steel"))   # 92095A177
    cl_holes = [(20, ROLL_Z - 15), (30, ROLL_Z + 30), (48, ROLL_Z - 15), (48, ROLL_Z + 30)]   # #1 at x30: its boss clears the forearm sweep
    for side, yc in (("L", -23.5), ("R", 23.5)):
        cl = plate([(0, 0, 12), (8, ROLL_Z - 22, 4), (54, ROLL_Z - 22, 4), (54, ROLL_Z + 38, 4), (8, ROLL_Z + 38, 4)], yc,
                   [(0, 0, 5.075)] + [(x, z, 1.65) for (x, z) in cl_holes],
                   pockets=[((28, ROLL_Z + 8, 5), (40, ROLL_Z + 8, 5))])
        cl = cl.fuse(ycyl(0, 0, yc - 1.5, yc + 1.5, 5.075).common(box(4.6, yc - 1.5, -6, 6.0, yc + 1.5, 6)))   # D-bore at mid-limit (10.15 / 4.6)
        sgn = -1 if side == "L" else 1
        if side == "L":     # belt side: flush countersunk screws (the GT2 belt passes 1.5 mm outboard)
            for (x, z) in cl_holes:
                cl = cl.cut(Part.makeCone(3.0, 1.5, 1.5, V(x, -25.0, z), V(0, 1, 0)))
        out.append(Part_("Clevis_%s_CF3" % side, cl, cl, "CF", "custom: 3 mm CF plate (DXF), D-bore" +
                         (", 4x csk" if side == "L" else ""), "cf"))
        for j, (x, z) in enumerate(cl_holes):
            if side == "L":
                out.append(P("CSK_M3x6_clevis_%s%d" % (side, j), at(csk(3, 6, -25.0, 1), x, z), "CAT", "CSK", "steel"))
            else:
                out.append(P("BHCS_M3x6_clevis_%s%d" % (side, j), at(H.screw("BHCS", 3, 6, sgn * 25.0, -sgn), x, z),
                             "CAT", "BHCS", "steel"))
            out.append(P("Insert_M3_clevis_%s%d" % (side, j), at((ring(0, 0, sgn * 22.0, sgn * 18.2, 2.0, 1.25),) * 2, x, z),
                         "CAT", "INSERT", "brass"))
    # roll housing (PETG-CF): side walls, ear bulkhead, bearing front plate, floor
    hz0, hz1 = ROLL_Z - 22.0, ROLL_Z + 40.0
    hs = box(8, 20, hz0, 60, 22, hz1).fuse(box(8, -22, hz0, 60, -20, hz1))
    hs = hs.fuse(box(34, -22, hz0, 37, 22, hz1)).fuse(box(53, -22, hz0, 60, 22, hz1))
    hs = hs.fuse(box(8, -22, hz0, 60, 22, hz0 + 3))
    hs = hs.cut(box(33, -10.3, ROLL_Z - 10.3, 38, 10.3, ROLL_Z + 30.3))                            # servo body through bulkhead
    hs = hs.cut(xcyl(52, 61, 18.5))                                               # 6805 seat
    ear_pts = [(y, z) for z in (ROLL_Z + 34.75, ROLL_Z - 14.75) for y in (-5.0, 5.0)]
    for (y, z) in ear_pts:
        hs = hs.cut(Part.makeCylinder(2.0, 4, V(33.5, y, z), V(1, 0, 0)))
    for (x, z) in cl_holes:
        for sg in (-1, 1):                          # 2 mm inside boss: 4 mm wall for the 3.8 mm insert (94180A331)
            hs = hs.fuse(ycyl(x, z, sg * 20.0, sg * 18.0, 3.6))
            hs = hs.cut(ycyl(x, z, sg * 22.5, sg * 17.5, 2.0))
    out.append(Part_("Roll_Housing", hs, hs, "PRINT", "custom: PETG-CF print, M3 inserts", "pla"))
    for i, (y, z) in enumerate(ear_pts):
        ins = Part.makeCylinder(2.0, 3, V(34, y, z), V(1, 0, 0)).cut(Part.makeCylinder(1.25, 3, V(34, y, z), V(1, 0, 0)))
        out.append(Part_("Insert_M3_rollear_%d" % i, ins, ins, "CAT", "INSERT", "brass"))
    sv, svc, _hx, _ye = H.servo_std(ROLL_XS, -1)
    sv, svc = _to_roll_axis((sv, svc))
    out.append(Part_("J4_Roll_Servo_DS3225", sv, svc, "CAT", "DS3225MG", "motor"))
    for i, (y, z) in enumerate(ear_pts):
        out.append(_xscrew("BHCS_M3x6_rollservo_%d" % i, ROLL_XS - 15.5, 6.0, y, z))
    brg = [b_.copy() for b_ in H.bearing(25, 37, 7, 0, 1)[:2]]
    for b_ in brg:
        b_.rotate(V(0, 0, 0), V(0, 0, 1), -90)
        b_.translate(V(53.0, 0, ROLL_Z))
    out.append(P("Brg_6805_Roll", brg, "CAT", "6805ZZ", "alu"))
    return out
