# -*- coding: utf-8 -*-
"""Gripper variant SCREW (rev A): Tr8x8 bidirectional lead screw, M2006 via 20T/32T, MGN9 rails, 6061 jaw
brackets, constant-torque spring-motor release.  API: screw_bodies(), screw_placements(Hd, jaw).
"""
import os

from arm.core import *  # noqa: F401,F403
from arm.wrist import *  # noqa: F401,F403

from arm.core import _vprism  # noqa: F401
from arm.wrist import _xscrew  # noqa: F401

_S = params.load("gripper_screw")   # params/gripper_screw.toml
LEAD = _S["LEAD"]
Z_SCREW_T, Z_MOTOR_T = _S["Z_SCREW_T"], _S["Z_MOTOR_T"]
HXJ = HX + _S["HXJ_OFF"]       # rails / jaws datum (clear of the hub flange)
XR = _S["XR_OFF"] + HXJ        # rail centre line = lead-screw axis x
ZS = _S["ZS"]                  # lead-screw axis z
ZM = ZS + _S["ZM_OFF"]         # M2006 axis z
ZTOP = _S["ZTOP"]
YEB = _S["YEB"]
RAIL_END = _S["RAIL_END"]
MOT_FACE = _S["MOT_FACE"]
M2006_FRONT = _S["M2006_FRONT"]
GEAR_Y0, GEAR_Y1 = _S["GEAR_Y0"], _S["GEAR_Y1"]



def body_head():
    """Roll head (rotates about the roll axis): hub, roll horn, palm, MGN9 rails and the
    gripper linear drive frame - two 6061 end blocks with 688ZZ bearings for the Tr8x8
    bidirectional lead screw, a CF bridge closing the frame, the M2006 gear motor clamped
    under the bridge (drives the screw through a 20T/32T m1 reduction) and the constant-
    torque spring motor on the R screw end that spins the jaws open when power is cut."""
    Dp = K["DROP"]
    out = []
    out += roll_hub_parts()
    front = IF_PALM.points_yz()                 # palm <-> hub bolt pattern (interfaces/roll_hub__gripper_palm.toml)
    # ---- palm (PETG-CF print, hollow): carries rails + end blocks
    PY = YEB + 9.0
    palm = box(30 + HX, -PY, -Dp - 6, 61 + HX, PY, 4)
    palm = fillet_y(palm, 4.0)
    palm = palm.cut(box(32 + HX, -PY + 2, -Dp - 4, 59 + HX, PY - 2, 2))
    for (y, z) in front:
        palm = palm.fuse(Part.makeCylinder(4.0, 5, V(30 + HX, y, z), V(1, 0, 0))).cut(
            Part.makeCylinder(IF_PALM["side_b"]["clearance_d"] / 2, 6, V(30 + HX - 0.5, y, z), V(1, 0, 0)))
    rails_y = [(14.0, RAIL_END), (-RAIL_END, -14.0)]
    holes = []
    for (a_, b_) in rails_y:
        r, rc, hy = H.mgn9_rail(a_, b_, XR, 4.0)
        holes += hy
        out.append(Part_("MGN9_Rail_%s" % ("L" if a_ > 0 else "R"), r, rc, "CAT", "MGN9-RAIL", "steel"))
    for hy in holes:
        palm = palm.fuse(Part.makeCylinder(4.0, 8, V(XR, hy, -4))).cut(Part.makeCylinder(2.0, 5, V(XR, hy, -1)))
    eb_holes = [(XR + dx, sg * (YEB + 4.0)) for sg in (-1, 1) for dx in (-10.0, 10.0)]     # top: bridge screws
    eb_bot = [(XR + dx, sg * (YEB + 4.0)) for sg in (-1, 1) for dx in (-6.0, 6.0)]        # bottom: palm through-bolts
    for (x, y) in eb_bot:        # through-bolt tubes, counterbored from below
        palm = palm.fuse(Part.makeCylinder(4.5, 30, V(x, y, -Dp - 6))).cut(Part.makeCylinder(1.65, 32, V(x, y, -Dp - 7))).cut(
            Part.makeCylinder(2.9, 3.5, V(x, y, -Dp - 6.5)))
    out.append(Part_("Gripper_Palm", palm, palm, "PRINT", "custom: PETG-CF print, M3 inserts", "pla"))
    for i, (y, z) in enumerate(front):
        out.append(_xscrew("BHCS_M3x8_palmhub_%d" % i, 35.0 + HX, 8.0, y, z, direction=-1))
    for i, hy in enumerate(holes):
        out.append(P("SHCS_M3x8_rail_%d" % i, to_z(H.screw("SHCS", 3, 8, 0, -1), XR, hy, 7.0), "CAT", "SHCS", "steel"))
        out.append(P("Insert_M3_rail_%d" % i, to_z((ring(0, 0, 0, 4, 2.0, 1.25),) * 2, XR, hy, -1.0), "CAT", "INSERT", "brass"))
    # ---- lead-screw end blocks (6061) + 688ZZ bearings
    for sg, nm in ((1, "L"), (-1, "R")):
        y_in, y_out = sg * YEB, sg * (YEB + 8.0)
        eb = box(XR - 17.5, y_in, 4, XR + 17.5, y_out, ZTOP)
        eb = eb.cut(ycyl(XR, ZS, sg * (YEB + 3.0), sg * (YEB + 9.0), 8.0))        # 688 seat (from outside)
        eb = eb.cut(ycyl(XR, ZS, sg * (YEB - 1.0), sg * (YEB + 4.0), 5.0))        # screw clearance
        eb = eb.cut(box(XR - 10, y_in - sg, ZS + 13, XR + 10, y_out + sg, ZTOP - 12))  # lightening window
        for (x, y) in [h for h in eb_holes if h[1] * sg > 0]:
            eb = eb.cut(Part.makeCylinder(1.25, 9, V(x, y, ZTOP - 8)))
        for (x, y) in [h for h in eb_bot if h[1] * sg > 0]:
            eb = eb.cut(Part.makeCylinder(1.25, 16, V(x, y, 3)))    # M3 drill 15 in the block: 13.5 thread > 13 engaged (M3x40, 91290A136)
        if sg < 0:                                   # spring-motor cassette tabs (outer face)
            for dx in (-13.5, 13.5):
                eb = eb.cut(ycyl(XR + dx, ZS - 22.0, y_out - 1.0, y_out + 8.0, 1.25))
        eb = fillet_y(eb, 0.0) if False else eb
        out.append(Part_("Screw_End_Block_%s" % nm, eb, eb, "AL", "custom: 6061 machined, 688 seat, M3 tapped", "alu"))
        out.append(P("Brg_688_Screw_%s" % nm, at(H.bearing(8, 16, 5, sg * (YEB + 8.0), -sg), XR, ZS), "CAT", "688ZZ", "alu"))
    # two-drum constant-torque spring motor around a stock constant-force strip (opens the jaws unpowered, R52)
    sm = H.ct_spring_motor(-(YEB + 8.5), -1, phi_deg=float(os.environ.get("CT_PHI", "90")), split=True)
    tabs = sm["tabs"]
    out.append(Part_("Spring_Housing", at((sm["housing"],) * 2, XR, ZS)[0], at((sm["housing"],) * 2, XR, ZS)[0], "PRINT",
                     "custom: PETG-CF print, two-drum spring housing", "pad"))
    out.append(Part_("Spring_Output_Drum", at((sm["drum"],) * 2, XR, ZS)[0], at((sm["drum"],) * 2, XR, ZS)[0], "AL",
                     "custom: 6061 turned, D20 drum on the D8 screw journal, M3 set screw", "alu"))
    out.append(P("Dowel_3x20_spring", at((sm["pin"],) * 2, XR, ZS), "CAT", "DOWEL", "steel", "storage-drum axle, stock 3x20 (91595A122)"))
    out.append(P("SetScrew_M3x3_drum", to_z(H.set_screw(3, 3.5, 0, -1), XR, sm["hub_y"], ZS + 7.5), "CAT", "SETSCREW", "steel"))
    out.append(P("Spring_Motor_Cassette", at((sm["strip"],) * 2, XR, ZS), "CAT", "SPRING-MOTOR", "steel",
                 "constant-force strip 9293K337, back-wound onto the output drum: turns the screw towards OPEN"))
    for i, (x, z) in enumerate(tabs):
        out.append(P("BHCS_M3x8_cassette_%d" % i, at(H.screw("BHCS", 3, 8, -(YEB + 11.0), 1), XR + x, ZS + z),
                     "CAT", "BHCS", "steel"))
    for i, (x, y) in enumerate(eb_bot):
        out.append(P("SHCS_M3x40_endblock_%d" % i, to_z(H.screw("SHCS", 3, 40, 0, 1), x, y, -Dp - 3.0), "CAT", "SHCS", "steel"))   # 91290A136
    for i, (x, y) in enumerate(eb_holes):
        out.append(P("BHCS_M3x8_bridge_%d" % i, to_z(H.screw("BHCS", 3, 8, 0, -1), x, y, ZTOP + 3.0), "CAT", "BHCS", "steel"))
    # ---- bridge (3 mm CF, XY plane) closes the frame and carries the motor clamps
    clamp_y = ((7.0, 15.0), (27.0, 35.0))
    brd = box(XR - 16, -(YEB + 8.0), ZTOP, XR + 16, YEB + 8.0, ZTOP + 3.0)
    for (x, y) in eb_holes:
        brd = brd.cut(Part.makeCylinder(1.65, 5, V(x, y, ZTOP - 1)))
    for (ya, yb) in clamp_y:
        for dx in (-10.0, 10.0):
            brd = brd.cut(Part.makeCylinder(1.65, 5, V(XR + dx, (ya + yb) / 2, ZTOP - 1)))
    for (ya, yb) in ((42.0, YEB - 8.0), (-(YEB - 8.0), -6.0)):
        brd = brd.cut(zslot(XR, ya, XR, yb, 7.0, ZTOP - 1, ZTOP + 4))
    brd = fillet_z(brd, 3.0)
    out.append(Part_("Gripper_Bridge_CF3", brd, brd, "CF", "custom: 3 mm CF plate (DXF, XY)", "cf"))
    # ---- M2006 gear motor (vendor STEP): shaft tip at y=-3 inside the 32T gear
    mot = H.vendor("M2006")
    # flip 180 deg about Z (model +Y shaft -> world -Y) and put the gearbox face at MOT_FACE
    mot.Placement = App.Placement(V(XR, MOT_FACE + M2006_FRONT, ZM), App.Rotation(V(0, 0, 1), 180)).multiply(mot.Placement)
    y_rear = MOT_FACE + M2006_FRONT + 2.4                                  # rear cap face
    mchk = ycyl(XR, ZM, MOT_FACE, y_rear - 2.4, 12.2).fuse(ycyl(XR, ZM, y_rear - 2.4, y_rear, 11.85)).fuse(
        ycyl(XR, ZM, MOT_FACE - 16.5, GEAR_Y0, 2.9))                       # shaft beyond the gear
    out.append(Part_("Grip_Motor_M2006", mot, mchk, "CAT", "M2006-P36", "motor", "output shaft through the 20T gear; drives the Tr8x8 screw through 20T/32T"))
    for i, (ya, yb) in enumerate(clamp_y):
        ym = (ya + yb) / 2
        cl = box(XR - 16, ya, ZM - 19, XR + 16, yb, ZTOP).cut(ycyl(XR, ZM, ya - 1, yb + 1, 12.25))
        cl = cl.cut(box(XR - 0.75, ya - 1, ZM - 20, XR + 0.75, yb + 1, ZM - 11))           # pinch slit
        cl = cl.cut(Part.makeCylinder(1.65, 34, V(XR - 17, ym, ZM - 15.5), V(1, 0, 0)))
        for dx in (-10.0, 10.0):
            cl = cl.cut(Part.makeCylinder(2.0, 5, V(XR + dx, ym, ZTOP - 5)))
        out.append(Part_("Motor_Clamp_%d" % i, cl, cl, "PRINT", "custom: PETG-CF print, M3 inserts, pinch slit", "pla"))
        out.append(_xscrew("SHCS_M3x30_motorclamp_%d" % i, XR - 16.0, 30.0, ym, ZM - 15.5, kind="SHCS"))
        for j, dx in enumerate((-10.0, 10.0)):
            out.append(P("BHCS_M3x8_clamp_%d%d" % (i, j), to_z(H.screw("BHCS", 3, 8, 0, -1), XR + dx, ym, ZTOP + 3.0),
                         "CAT", "BHCS", "steel"))
            out.append(P("Insert_M3_clamp_%d%d" % (i, j), to_z((ring(0, 0, 0, 4, 2.0, 1.25),) * 2, XR + dx, ym, ZTOP - 4.0),
                         "CAT", "INSERT", "brass"))
    return out


def zslot(x0, y0, x1, y1, r, z0, z1):
    """Rounded slot (stadium) prism along Z between centres (x0,y0)-(x1,y1)."""
    a = Part.makeCylinder(r, z1 - z0, V(x0, y0, z0)).fuse(Part.makeCylinder(r, z1 - z0, V(x1, y1, z0)))
    if abs(x1 - x0) < 1e-9:
        return a.fuse(box(x0 - r, min(y0, y1), z0, x0 + r, max(y0, y1), z1))
    return a.fuse(box(min(x0, x1), y0 - r, z0, max(x0, x1), y0 + r, z1))


def body_screw():
    """Rotating lead-screw assembly: Tr8x8 bidirectional screw, 20T drive gear,
    two set-screw collars + shims (axial location against the 688 inner races).
    The R collar doubles as the clamp for the spring-motor arbor."""
    out = []
    span = YEB - 2.0
    out.append(P("Leadscrew_Tr8x8_bidir", at(H.leadscrew(-(YEB + 14.5), YEB + 14.5,
                                                          [(-span, -34.0, "LH"), (34.0, span, "RH")], 8.0, 2.0), XR, ZS),
                 "CAT", "TR8X8-BIDIR", "steel"))
    g, gc, _rp = H.spur_gear(1.0, Z_SCREW_T, GEAR_Y0, GEAR_Y1, 8.0, hub=(14.0, -6.0))
    hole = Part.makeCylinder(1.4, 5, V(0, GEAR_Y0 - 3.0, 3.5))
    g, gc = g.cut(hole), gc.cut(hole)
    out.append(P("Screw_Gear_m1_%dT" % Z_SCREW_T, at((g, gc), XR, ZS), "CAT", "GEAR-M1-%dT" % Z_SCREW_T, "alu"))
    out.append(P("SetScrew_M3x3_screwgear", to_z(H.set_screw(3, 3.0, 0, -1), XR, GEAR_Y0 - 3.0, ZS + 7.0), "CAT", "SETSCREW", "steel"))
    for sg, nm in ((1, "L"), (-1, "R")):
        yb = sg * (YEB + 8.0)
        out.append(P("Shim_8x10_%s" % nm, at((ring(0, 0, yb, yb + sg * 0.5, 5.0, 4.05),) * 2, XR, ZS), "SHIM", "custom: 301 SS shim stock 0.5, laser cut", "steel"))
        if nm == "R":
            continue                         # right end: the spring motor's output drum hub retains the screw instead
        out.append(P("Collar_D8_%s" % nm, at(H.shaft_collar(8.0, 16.0, 8.0, yb + sg * 0.5, sg), XR, ZS), "CAT", "COLLAR8", "steel"))
        # the collar's own M4x5 set screw (supplied with Stafford 34LM008P2) - not a separate purchase line
    return out


def body_mgear():
    """Motor gear (m1, Z_MOTOR_T) on the M2006 output shaft (rotates with the motor shaft)."""
    g, gc, _rp = H.spur_gear(1.0, Z_MOTOR_T, GEAR_Y0, GEAR_Y1, 6.0, phase=180.0 / Z_MOTOR_T)
    rr = Z_MOTOR_T / 2.0 - 1.25
    hole = Part.makeCylinder(1.4, rr, V(0, (GEAR_Y0 + GEAR_Y1) / 2, 2.5))     # radial set screw through the web
    g, gc = g.cut(hole), gc.cut(hole)
    return [P("Motor_Gear_m1_%dT" % Z_MOTOR_T, at((g, gc), XR, ZM), "CAT", "GEAR-M1-%dT" % Z_MOTOR_T, "steel"),
            P("SetScrew_M3_motorgear", to_z(H.set_screw(3, rr - 3.2, 0, -1), XR, (GEAR_Y0 + GEAR_Y1) / 2, ZM + rr - 0.2),
              "CAT", "SETSCREW", "steel")]


def body_jaw(s):
    """Jaw at reference half-opening O_REF (pipe grip).  s=+1 left (+y), -1 right
    (built as the left jaw and mirrored).  6061 bracket on the MGN9H block, Tr8
    flange nut on its upright, two 3 mm CF finger plates (XY) with the curved
    edge, and a TPU pad between them: R50 arc wraps the donut OD, the central
    90 deg V-notch self-centres the D26.7 pipe on 4 lines.  The pad is captured on two
    D6 standoffs that also tie the finger plates (button heads only below the fingers)."""
    XT = K["GRIP"]
    o = O_REF
    nm = "L" if s > 0 else "R"
    out = []
    blk, blkc, bh = H.mgn9h_block(o + 19.95, XR, 4.0)
    out.append(Part_("MGN9H_Block_" + nm, blk, blkc, "CAT", "MGN9H", "steel"))
    # 6061 bracket: top plate on the block, nut upright, gusset, finger root wall
    yw0, yw1 = o + 35.9, o + 39.9
    br = box(XR - 12, o + 1, 14, 108, o + 39.9, 18)
    br = br.fuse(box(XR - 12, yw0, 18, XR + 12, yw1, 43))
    br = br.fuse(box(XR + 12, yw0, 18, 100, yw1, 24))
    br = br.fuse(box(100, o + 6, -26, 108, o + 38, 24))
    br = br.cut(ycyl(XR, ZS, yw0 - 1, yw1 + 1, 5.3))
    nut, nutc, nh = H.flange_nut_t8(yw1 + 3.5, -1)
    for (x, z) in nh:
        br = br.cut(ycyl(XR + x, ZS + z, yw0 - 1, yw1 + 1, 1.25))
    for (hx, hy) in bh:
        br = br.cut(Part.makeCylinder(1.65, 6, V(hx, hy, 13)))
    fing = [(104.0, o + 12.0), (104.0, o + 32.0)]
    for (x, y) in fing:
        br = br.cut(Part.makeCylinder(1.25, 8, V(x, y, 17))).cut(Part.makeCylinder(1.25, 8, V(x, y, -27)))   # 8 drill: 6.5 thread > 6 screw
    out.append(Part_("Jaw_Bracket_" + nm, br, br, "AL", "custom: 6061 machined, M3 tapped", "alu"))
    if s > 0:      # RH: stock Creality T8 4-start brass nut
        out.append(P("Nut_Tr8x8_RH", at((nut, nutc), XR, ZS), "CAT", "NUT-T8", "brass"))
    else:          # LH: no stock LH 8 mm-lead nut exists -> machined brass part (thread-milled Tr8x8(P2) LH)
        nl = at((nut, nutc), XR, ZS)
        out.append(Part_("Nut_Tr8x8_LH", nl[0], nl[1], "BRASS", "custom: CW614N brass, Tr8x8(P2) LH 4-start thread-milled", "brass"))
    for i, (x, z) in enumerate(nh):
        out.append(P("BHCS_M3x6_nut%s_%d" % (nm, i), at(H.screw("BHCS", 3, 6, yw1 + 3.5, -1), XR + x, ZS + z), "CAT", "BHCS", "steel"))
    for i, (hx, hy) in enumerate(bh):
        out.append(P("BHCS_M3x6_jaw%s_%d" % (nm, i), to_z(H.screw("BHCS", 3, 6, 0, -1), hx, hy, 18.0), "CAT", "BHCS", "steel"))
    # CF finger plates (top z 24..27, bottom z -29..-26) with the curved gripping edge
    pad_holes = [(XT - 12.0, o + 9.0), (XT + 12.0, o + 9.0)]
    posts = [(150.0, o + 20.0), (125.0, o + 28.0)]
    poly = [(100, o + 6), (XT - 26, o - 8), (XT + 26, o - 8), (XT + 26, o + 16), (150, o + 30), (100, o + 38)]
    for lvl, (z0, z1) in (("top", (24.0, 27.0)), ("bot", (-29.0, -26.0))):
        pp = [V(x, y, z0) for (x, y) in poly]
        f = Part.Face(Part.makePolygon(pp + [pp[0]])).extrude(V(0, 0, z1 - z0))
        f = f.cut(Part.makeCylinder(PAD_R + 2.0, 40, V(XT, o - PAD_R, z0 - 10)))
        f = f.cut(_vprism(XT, o + NOTCH + 2.0 * math.sqrt(2), z0 - 1, z1 + 1))
        for (x, y) in fing + pad_holes + posts:
            f = f.cut(Part.makeCylinder(1.65, 10, V(x, y, z0 - 3)))
        f = fillet_z(f, 1.5)
        out.append(Part_("Finger_%s_%s_CF3" % (nm, lvl), f, f, "CF", "custom: 3 mm CF plate (DXF, XY)", "cf"))
    # TPU pad: R50 arc (donut) +-WRAP deg, 90 deg V-notch (pipe), captured by 2 through-bolts
    cen = V(XT, o - PAD_R, -26.0)
    ann = Part.makeCylinder(PAD_R + 16.0, 50, cen).cut(Part.makeCylinder(PAD_R, 50, cen))
    w = math.radians(WRAP)
    L_ = 120.0
    wp = [V(XT, o - PAD_R, -27), V(XT - L_ * math.sin(w), o - PAD_R + L_ * math.cos(w), -27),
          V(XT + L_ * math.sin(w), o - PAD_R + L_ * math.cos(w), -27)]
    wedge = Part.Face(Part.makePolygon(wp + [wp[0]])).extrude(V(0, 0, 52))
    pad = ann.common(wedge).cut(_vprism(XT, o + NOTCH, -27, 25))
    for (x, y) in pad_holes:
        pad = pad.cut(Part.makeCylinder(3.1, 52, V(x, y, -27)))
    out.append(Part_("Pad_%s_TPU" % nm, pad, pad, "TPU", "custom: TPU 95A print, R50 arc + 90 deg V, bolted", "pad"))
    for i, (x, y) in enumerate(posts + pad_holes):
        out.append(P("Finger_Standoff_D6x50_%s%d" % (nm, i), to_z(H.standoff_round(6, 50, 0, 1), x, y, -26.0),
                     "AL", "custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer)", "alu", "D6 x 50 M3 female"))
    for i, (x, y) in enumerate(fing + posts + pad_holes):
        out.append(P("BHCS_M3x8_fingtop%s_%d" % (nm, i), to_z(H.screw("BHCS", 3, 8 if i < 2 else 6, 0, -1), x, y, 27.0),
                     "CAT", "BHCS", "steel"))
        out.append(P("BHCS_M3x8_fingbot%s_%d" % (nm, i), to_z(H.screw("BHCS", 3, 8 if i < 2 else 6, 0, 1), x, y, -29.0),
                     "CAT", "BHCS", "steel"))
    return mirror_y(out) if s < 0 else out




# ---- gripper API (see arm/grippers/__init__.py)
def screw_bodies():
    return dict(HEAD=body_head, SCREW=body_screw, MGEAR=body_mgear,
                JAW_L=lambda: body_jaw(1), JAW_R=lambda: body_jaw(-1))


def screw_placements(Hd, jaw):
    """Lead-screw jaws slide +/-d on the rails; the screw and motor gear turn with the jaw travel."""
    d = jaw / 2.0 - O_REF
    phi = 360.0 * d / LEAD
    scr = App.Placement(V(0, 0, 0), App.Rotation(V(0, 1, 0), phi), V(XR, 0, ZS))
    mg = App.Placement(V(0, 0, 0), App.Rotation(V(0, 1, 0), -phi * Z_SCREW_T / Z_MOTOR_T), V(XR, 0, ZM))
    return dict(SCREW=Hd.multiply(scr), MGEAR=Hd.multiply(mg),
                JAW_L=Hd.multiply(App.Placement(V(0, d, 0), App.Rotation())),
                JAW_R=Hd.multiply(App.Placement(V(0, -d, 0), App.Rotation())))
