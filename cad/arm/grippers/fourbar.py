# -*- coding: utf-8 -*-
"""Gripper variant FOURBAR (concept): gear-synchronised parallel four-bar, STS3215 direct drive, torsion-spring
release.  API: fourbar_bodies(), fb_placements(Hd, jaw).  Parameters in FB.
"""
from arm.core import *  # noqa: F401,F403
from arm.wrist import *  # noqa: F401,F403

from arm.core import _vprism  # noqa: F401
from arm.wrist import _xscrew  # noqa: F401

# ================================================================== four-bar gripper (GRIP=FOURBAR, default)
# Gear-synchronised parallel four-bar: each jaw is carried by a drive link and an idler link (two CF layers,
# 10 mm apart) pivoting on the printed palm; sector gears on the two drive links mesh at y=0, so the jaws
# move symmetrically and the pads stay parallel.  One STS3215 (direct, on the left drive pivot) closes the
# jaws; a torsion spring on the right drive pivot biases them OPEN, back-driving the servo when unpowered.
# GRIP=SCREW rebuilds the rev A lead-screw gripper.
FB = dict(params.load("gripper_fourbar")["FB"])   # params/gripper_fourbar.toml (units, reasons)
SPRING = dict(params.load("gripper_fourbar")["SPRING"])
SERVO = dict(params.load("gripper_fourbar")["SERVO"])


def fb_theta(jaw):
    """Drive-link angle (deg, from +x towards +y for the left jaw) for a pad-arc gap 'jaw'."""
    ycp = jaw / 2.0 + FB["E"]
    return math.degrees(math.asin(max(-1.0, min(1.0, (ycp - FB["YG"]) / FB["L"]))))


FB_TREF = fb_theta(2 * O_REF)          # jaws are modelled at the pipe grip


def zc(x, y, z0, z1, r):
    z0, z1 = sorted((z0, z1))
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0))


def zprism(pts, z0, z1):
    pp = [V(x, y, z0) for (x, y) in pts]
    return Part.Face(Part.makePolygon(pp + [pp[0]])).extrude(V(0, 0, z1 - z0))


def zlink(p0, p1, r, z0, z1, hole):
    """Stadium link plate between pin centres p0, p1 (XY), holes at both ends."""
    a = zc(p0[0], p0[1], z0, z1, r).fuse(zc(p1[0], p1[1], z0, z1, r))
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    nx, ny = -dy / n * r, dx / n * r
    a = a.fuse(zprism([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny),
                       (p0[0] - nx, p0[1] - ny)], z0, z1))
    for p in (p0, p1):
        a = a.cut(zc(p[0], p[1], z0 - 1, z1 + 1, hole))
    return a.removeSplitter()


def fb_pivots(s=1):
    """Ground and coupler pivots (s=+1 left, -1 right) at the reference (pipe) angle."""
    XG, YG, L, S = FB["XG"], FB["YG"], FB["L"], FB["S"]
    c, sn = math.cos(math.radians(FB_TREF)), math.sin(math.radians(FB_TREF))
    pts = [(XG, YG), (XG, YG + S), (XG + L * c, YG + L * sn), (XG + L * c, YG + S + L * sn)]
    return [(x, s * y) for (x, y) in pts]


def body_fb_palm():
    """HEAD body for the four-bar gripper: roll horn + hub (unchanged), printed palm (hub mount plate,
    servo cradle, ground-pivot layer, spring boss), STS3215, ground pins, torsion spring."""
    out = []
    out += roll_hub_parts()
    front = IF_PALM.points_yz()                 # palm <-> hub bolt pattern (interfaces/roll_hub__gripper_palm.toml)
    XG, YG, S = FB["XG"], FB["YG"], FB["S"]
    g0, g1 = FB["ZG"]
    # STS3215 (45.2 x 24.7 x 35), spline on the left drive-pivot axis pointing +z, 11 mm from the body end
    sv = box(XG - 12.35, YG - 11.0, -16.0, XG + 12.35, YG - 11.0 + 45.2, 19.0)        # body runs outboard
    svv = sv.fuse(zc(XG, YG, 19.0, 19.5, 3.0))
    out.append(Part_("Grip_Servo_STS3215", svv, sv, "CAT", "STS3215", "motor", "direct drive on the left drive link (disc horn)"))
    # palm: mount plate on the hub flange, servo cradle, ground layer, spring boss
    palm = box(65, -(YG + 9), -22, 69, YG + 37.0, g1)                                   # mount plate on the hub flange
    palm = palm.fuse(box(69, YG - 14.0, -19.0, XG + 15.0, YG + 37.0, 19.0).cut(
        box(XG - 12.65, YG - 11.3, -16.3, XG + 12.65, YG - 11.0 + 45.5, 20.0)))         # cradle (open top)
    palm = palm.fuse(box(69, -(YG + S + 6), g0, XG + 15.0, YG + S + 6, g1))              # ground-pivot layer
    SP = SPRING
    z_sp1 = FB["ZL0"][0] - 0.3                                                             # spring top, under the lower link
    z_sp0 = z_sp1 - SP["length"]
    palm = palm.fuse(box(69, -(YG + 9), z_sp0 - 3.0, XG + 15.0, -(YG - 9), z_sp0))        # spring boss (right drive pivot)
    palm = palm.fuse(zc(XG, -YG, z_sp0 - 0.1, z_sp1, SP["arbor_d"] / 2))                   # printed arbor inside the coil
    # central web tying the ground-pivot layer down to the mount plate (FEA: the cantilevered 6 mm layer with
    # lightening windows reached SF 1.3; links/servo/horn/spring all sit at |y| > 25 here, so the web is free space)
    palm = palm.fuse(box(69, -6.0, -19.0, XG + 15.0, 6.0, g0))      # |y| <= 6: the M3 heads at y +-10.8 keep 2 mm
    for (y, z) in front:
        palm = palm.cut(Part.makeCylinder(IF_PALM["side_b"]["clearance_d"] / 2, 6, V(IF_PALM.frame_x - 1.0, y, z), V(1, 0, 0)))
    for p in fb_pivots(1)[:2] + fb_pivots(-1)[:2]:
        palm = palm.cut(zc(p[0], p[1], 10, g1 + 1, FB["PIN_R"] + 0.05))
    out.append(Part_("Gripper_Palm", palm, palm, "PRINT", "custom: PETG-CF print (concept)", "pla"))
    for i, (y, z) in enumerate(front):
        # M3x8 (stock ISO 7380): 4 mm mount plate + full 3 mm of the hub flange thread; tip 1 mm clear of the roll housing
        out.append(_xscrew("BHCS_M3x8_palmhub_%d" % i, 69.0, 8.0, y, z, direction=-1))
    gl, gli = fb_pivots(1)[:2]
    gr, gri = fb_pivots(-1)[:2]
    zi = FB["ZL0"][0] - 0.1                                    # stock dowel lengths (ISO 8734 D4 m6)
    for nm, p, z0, L_, pn in (("LI", gli, zi, 14.0, "PIN-D4x14"), ("RI", gri, zi, 14.0, "PIN-D4x14"),
                              ("RD", gr, FB["ZSEC"][1] - 30.0, 30.0, "PIN-D4x30")):
        pin = zc(p[0], p[1], z0, z0 + L_, FB["PIN_R"])
        out.append(Part_("Pin_D4x%d_ground_%s" % (L_, nm), pin, pin, "CAT", pn, "steel"))
    # torsion spring coil around the arbor (legs not modelled: one hooks the boss, one bears on the lower drive link)
    spr = zc(gr[0], gr[1], z_sp0, z_sp1, SP["od"] / 2).cut(zc(gr[0], gr[1], z_sp0 - 1, z_sp1 + 1, SP["od"] / 2 - SP["wire"]))
    out.append(Part_("Torsion_Spring_Open", spr, spr, "CAT", SP["pn"], "steel",
                     "biases the jaws OPEN (power-off release); %.0f deg preload at full open" % SP["preload_deg"]))
    return out


def body_fb_link(s, drive):
    """One link pair (two CF layers) at the reference angle; the drive links carry the sync sector gear
    and a tube spacer (left drive also the servo disc horn and its own pin).  Rotates about its ground pivot."""
    gd, gi, cd, ci = fb_pivots(s)
    g, c = (gd, cd) if drive else (gi, ci)
    nm = ("L" if s > 0 else "R") + ("D" if drive else "I")
    out = []
    for lv, (z0, z1) in (("lo", FB["ZL0"]), ("hi", FB["ZL1"])):
        lk = zlink(g, c, 5.0, z0, z1, FB["PIN_R"] + 0.05)
        out.append(Part_("Link_%s_%s_CF3" % (nm, lv), lk, lk, "CF", "custom: 3 mm CF plate (concept)", "cf"))
    if drive:
        za, zb = FB["ZSEC"]
        nt = FB["TEETH"]
        gv, gch, _rp = H.spur_gear(1.0, nt, 0.0, zb - za, 2 * FB["PIN_R"] + 0.1, phase=(90.0 if s > 0 else -90.0 + 180.0 / nt))
        gv, gch = to_z((gv, gch), g[0], g[1], za)
        span = fb_theta(112.0) - FB_TREF + 6.0                              # contact must stay on the sector over the stroke
        lo, hi = (-90.0 - span, -84.0) if s > 0 else (84.0, 90.0 + span)
        R_ = 50.0
        wedge = zprism([(g[0], g[1])] + [(g[0] + R_ * math.cos(math.radians(a)), g[1] + R_ * math.sin(math.radians(a)))
                                         for a in (lo, (lo + hi) / 2, hi)], za - 1, zb + 1)
        hubd = zc(g[0], g[1], za, zb, 7.0).cut(zc(g[0], g[1], za - 1, zb + 1, FB["PIN_R"] + 0.05))
        sec, secc = gv.common(wedge).fuse(hubd), gch.common(wedge).fuse(hubd)
        for a in (lo + 20, hi - 20):              # lightening holes D8: 4.5 mm to the sector edges (D11 at 14 deg left 0.55)
            hx = g[0] + 25 * math.cos(math.radians(a))
            hy = g[1] + 25 * math.sin(math.radians(a))
            sec, secc = sec.cut(zc(hx, hy, za - 1, zb + 1, 4.0)), secc.cut(zc(hx, hy, za - 1, zb + 1, 4.0))
        out.append(Part_("Sector_m1_%dT_%s" % (nt, nm[0]), sec, secc, "PRINT", "custom: POM/PA12 sector gear m1 %dT, 5 thick (concept)" % nt, "pom"))
        sp = zc(g[0], g[1], FB["ZL0"][1], FB["ZG"][0] - 0.2, 4.0).fuse(zc(g[0], g[1], FB["ZG"][1] + 0.2, FB["ZL1"][0], 4.0))
        sp = sp.cut(zc(g[0], g[1], 0, 50, FB["PIN_R"] + 0.05))
        out.append(Part_("Washer_%s" % nm, sp, sp, "CAT", "WASHER-D4", "steel", "thrust washers either side of the ground layer"))
        if s > 0:
            horn = zc(g[0], g[1], 19.5, 23.5, 10.0).cut(zc(g[0], g[1], 19, 24, 2.6))
            out.append(Part_("Servo_Horn_STS_disc", horn, horn, "CAT", "HORN-25T", "alu", "STS3215 disc horn, screwed to the lower drive link"))
            pin = zc(g[0], g[1], FB["ZSEC"][1] + 0.5 - 20.0, FB["ZSEC"][1] + 0.5, FB["PIN_R"])
            out.append(Part_("Pin_D4x20_ground_LD", pin, pin, "CAT", "PIN-D4x20", "steel", "turns with the drive link, bushed in the palm"))
    return out


def _pad_shape(o, z0, z1):
    XT = K["GRIP"]
    cen = V(XT, o - PAD_R, z0)
    ann = Part.makeCylinder(PAD_R + 16.0, z1 - z0, cen).cut(Part.makeCylinder(PAD_R, z1 - z0, cen))
    w = math.radians(WRAP)
    L_ = 120.0
    wp = [(XT, o - PAD_R), (XT - L_ * math.sin(w), o - PAD_R + L_ * math.cos(w)), (XT + L_ * math.sin(w), o - PAD_R + L_ * math.cos(w))]
    return ann.common(zprism(wp, z0 - 1, z1 + 1)).cut(_vprism(XT, o + NOTCH, z0 - 1, z1 + 1))


def body_fb_jaw(s):
    """Jaw (left built, mirrored for s=-1) at the pipe grip: printed jaw block (coupler-pin layer between the
    link layers, riser beyond the link ends, top finger), CF bottom finger, TPU pad (R50 arc + 90 deg V),
    D6 standoffs through the pad, two coupler pins."""
    XT = K["GRIP"]
    o = O_REF
    nm = "L" if s > 0 else "R"
    _gd, _gi, cd, ci = fb_pivots(1)
    out = []
    g0, g1 = FB["ZG"]
    poly = [(XT - 26, o - 8), (XT + 26, o - 8), (XT + 26, o + 16), (XT + 8, o + 30), (XT - 26, o + 30)]
    pad_holes = [(XT - 12.0, o + 9.0), (XT + 12.0, o + 9.0)]
    post = [(XT + 12.0, o + 18.0)]                # rear post: 5.4 mm to the angled finger edge (was 1.33 at XT+16, o+20)

    def finger(z0, z1):
        f = zprism(poly, z0, z1)
        f = f.cut(Part.makeCylinder(PAD_R + 2.0, 60, V(XT, o - PAD_R, z0 - 10)))
        f = f.cut(_vprism(XT, o + NOTCH + 2.0 * math.sqrt(2), z0 - 1, z1 + 1))
        for (x, y) in pad_holes + post:
            f = f.cut(zc(x, y, z0 - 1, z1 + 1, 1.65))
        return fillet_z(f, 1.5)
    xb0, xb1 = cd[0] - 7.0, FB["XMAX"]
    blk = box(xb0, cd[1] - 6.0, g0, xb1, ci[1] + 6.0, g1)                              # coupler-pin layer
    blk = blk.fuse(box(cd[0] + 5.6, cd[1] - 6.0, FB["ZFT"][1], xb1, ci[1] + 6.0, g0))    # riser beyond the link bosses
    blk = blk.fuse(finger(*FB["ZFT"]))
    blk = blk.cut(zc(XT, 0.0, -60, 60, PIPE_R + 1.5))                                    # pipe clearance
    for p in (cd, ci):
        blk = blk.cut(zc(p[0], p[1], g0 - 1, g1 + 1, FB["PIN_R"] + 0.05))
    blk = blk.removeSplitter()
    out.append(Part_("Jaw_Block_" + nm, blk, blk, "PRINT", "custom: PETG-CF print (concept)", "pla"))
    fb = finger(*FB["ZFB"])
    out.append(Part_("Finger_%s_bot_CF3" % nm, fb, fb, "CF", "custom: 3 mm CF plate (concept)", "cf"))
    pad = _pad_shape(o, *FB["ZPAD"])
    for (x, y) in pad_holes:
        pad = pad.cut(zc(x, y, -40, 40, 3.1))
    out.append(Part_("Pad_%s_TPU" % nm, pad, pad, "TPU", "custom: TPU 95A print, R50 arc + 90 deg V", "pad"))
    for i, (x, y) in enumerate(pad_holes + post):
        st = zc(x, y, FB["ZPAD"][0], FB["ZPAD"][1], 3.0).cut(zc(x, y, -40, 40, 1.26))
        out.append(Part_("Standoff_D6_%s%d" % (nm, i), st, st, "AL", "custom: 6061 D6 standoff, M3 both ends", "alu"))
        # M3x6 button heads clamp the top finger (z 20..23) and the bottom CF finger (z -29..-26) to the standoff
        out.append(P("BHCS_M3x6_fingtop%s_%d" % (nm, i), to_z(H.screw("BHCS", 3, 6, 0, -1), x, y, FB["ZFT"][1]), "CAT", "BHCS", "steel"))
        out.append(P("BHCS_M3x6_fingbot%s_%d" % (nm, i), to_z(H.screw("BHCS", 3, 6, 0, 1), x, y, FB["ZFB"][0]), "CAT", "BHCS", "steel"))
    for i, p in enumerate((cd, ci)):
        z0 = FB["ZL0"][0] - 0.1                     # stock 4 x 14 dowel, 0.4 mm above the top finger
        pin = zc(p[0], p[1], z0, z0 + 14.0, FB["PIN_R"])
        out.append(Part_("Pin_D4x14_coupler_%s%d" % (nm, i), pin, pin, "CAT", "PIN-D4x14", "steel"))
    if s < 0:
        for p in out:
            p.vis = p.vis.mirror(V(0, 0, 0), V(0, 1, 0))
            p.chk = p.chk.mirror(V(0, 0, 0), V(0, 1, 0))
            p.shape = p.chk
    return out



def fb_placements(Hd, jaw):
    """Four-bar jaw/link placements (in the roll-head frame Hd) for a pad-arc gap 'jaw'."""
    th = fb_theta(jaw)
    d = th - FB_TREF
    L = FB["L"]
    dx = L * (math.cos(math.radians(th)) - math.cos(math.radians(FB_TREF)))
    dy = L * (math.sin(math.radians(th)) - math.sin(math.radians(FB_TREF)))
    out = dict(JAW_L=Hd.multiply(App.Placement(V(dx, dy, 0), App.Rotation())),
               JAW_R=Hd.multiply(App.Placement(V(dx, -dy, 0), App.Rotation())))
    for s, side in ((1, "L"), (-1, "R")):
        gd, gi, _cd, _ci = fb_pivots(s)
        for nm, g in (("D", gd), ("I", gi)):
            out["LK_" + side + nm] = Hd.multiply(App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), s * d), V(g[0], g[1], 0)))
    return out




# ---- gripper API (see arm/grippers/__init__.py)
def fourbar_bodies():
    return dict(HEAD=body_fb_palm, JAW_L=lambda: body_fb_jaw(1), JAW_R=lambda: body_fb_jaw(-1),
                LK_LD=lambda: body_fb_link(1, True), LK_LI=lambda: body_fb_link(1, False),
                LK_RD=lambda: body_fb_link(-1, True), LK_RI=lambda: body_fb_link(-1, False))
