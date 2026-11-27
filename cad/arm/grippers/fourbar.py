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
FB = dict(params.load("gripper_fourbar")["FB"])   # params/gripper_fourbar.toml (units, reasons)
SPRING = dict(params.load("gripper_fourbar")["SPRING"])
SERVO = dict(params.load("actuators")["STS3215"])   # the jaw servo: same STS3215 as the joints


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
    a = _stadium_raw(p0, p1, r, z0, z1)
    for p in (p0, p1):
        a = a.cut(zc(p[0], p[1], z0 - 1, z1 + 1, hole))
    return a.removeSplitter()


def stadium(p0, p1, r, z0, z1):
    """Solid stadium (true arcs) round two pin centres p0, p1, extruded z0..z1: rounded lugs and tabs."""
    return _stadium_raw(p0, p1, r, z0, z1).removeSplitter()


def _stadium_raw(p0, p1, r, z0, z1):
    a = zc(p0[0], p0[1], z0, z1, r).fuse(zc(p1[0], p1[1], z0, z1, r))
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    nx, ny = -dy / n * r, dx / n * r
    return a.fuse(zprism([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny),
                          (p0[0] - nx, p0[1] - ny)], z0, z1))


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
    # STS3215 (vendor model, hardware.sts3215), spline on the left drive-pivot axis pointing +z, horn seat at SEAT_Z,
    # body running outboard (+y): canonical (x long, y spline, z width) -> palm (y, z, x)
    seat, YO = FB["SEAT_Z"], FB["Y_OUT"]
    m = App.Matrix(0, 0, 1, XG, 1, 0, 0, YG, 0, 1, 0, seat, 0, 0, 0, 1)
    svv, sv = (s_.transformGeometry(m) for s_ in H.sts3215(0.0, -1))
    out.append(Part_("Grip_Servo_STS3215", svv, sv, "CAT", "STS3215", "motor", "direct drive on the left drive link (disc horn)"))
    St, c_ = H.STS, IF_STS["pocket"]["clearance"]
    pk = box(XG - St["w"] - c_, YG + St["x0"] - c_, seat + St["bottom"] - 0.05,
             XG + St["w"] + c_, YG + St["x1"] + c_, 20.0)                     # servo pocket (open top)
    # palm: mount plate on the hub flange, servo cradle, ground layer, spring boss
    # corners: every block that runs out from the mount plate ends at x = XG + 15; its two free vertical corners there
    # get the same R3 (blocks sharing a footprint stay flush), while its corners on the mount plate (x = 69) stay
    # sharp so no round leaves a groove at the joint. The mount plate's own outer corners (x = 65) get R2.
    XE = XG + 15.0

    def _round_end(shape, r=3.0, x=XE):
        # also the back corners (x = 69) that stand past the mount plate's ends (y -47.5 .. Y_OUT): free there too
        def free(e):
            b = e.BoundBox
            if abs(b.XMin - x) < 1e-6:
                return True
            return x == XE and abs(b.XMin - 69.0) < 1e-6 and not (-(YG + 9) - 1e-6 <= b.YMin <= YO + 1e-6)
        es = [e for e in shape.Edges if e.Curve.TypeId == "Part::GeomLine" and e.BoundBox.ZLength > 1e-6
              and e.BoundBox.XLength < 1e-6 and e.BoundBox.YLength < 1e-6 and free(e)]
        return shape.makeFillet(r, es) if es else shape
    palm = _round_end(box(65, -(YG + 9), FB["ZGB"][0], 69, YO, g1), 2.0, 65.0)   # mount plate (bottom flush with the lower plates)
    palm = palm.fuse(_round_end(box(69, YG - 14.0, -19.0, XE, YO, 19.0)).cut(
        pk))                                                                             # cradle (open top)
    palm = palm.fuse(_round_end(box(69, -(YG + S + 6), g0, XE, YG + S + 6, g1)))         # ground-pivot layer
    SP = SPRING
    z_sp1 = FB["ZL0"][0] - 0.3                                                             # spring top, under the lower link
    z_sp0 = z_sp1 - SP["length"]
    palm = palm.fuse(_round_end(box(69, -(YG + 9), z_sp0 - 3.0, XE, -(YG - 9), z_sp0)))        # spring boss (right drive pivot)
    palm = palm.fuse(zc(XG, -YG, z_sp0 - 0.1, z_sp1, SP["arbor_d"] / 2))                   # printed arbor inside the coil
    # central web tying the ground-pivot layer down to the mount plate (FEA: the cantilevered 6 mm layer with
    # lightening windows reached SF 1.3; links/servo/horn/spring all sit at |y| > 25 here, so the web is free space)
    palm = palm.fuse(_round_end(box(69, -6.0, -19.0, XE, 6.0, g0)))      # |y| <= 6: the M3 heads at y +-10.8 keep 2 mm
    # lower ground-pivot layer (bottom links, params ZGB): the servo cradle's floor thickened on the left; on the right
    # a plate flush with the top ground-pivot layer above it (same y extent), both off the mount plate, free corners R3
    b0, b1 = FB["ZGB"]
    palm = palm.fuse(_round_end(box(69, YG - 14.0, b0, XE, YO, b1)))
    palm = palm.fuse(_round_end(box(69, -(YG + S + 6.0), b0, XE, -(YG - 14.0), b1)))
    palm = palm.removeSplitter()                  # flush blocks share one face: no seam lines where they meet
    for (y, z) in front:
        palm = palm.cut(Part.makeCylinder(IF_PALM["side_b"]["clearance_d"] / 2, 6, V(IF_PALM.frame_x - 1.0, y, z), V(1, 0, 0)))
    for p in fb_pivots(1)[:2] + fb_pivots(-1)[:2]:
        palm = palm.cut(zc(p[0], p[1], 10, g1 + 1, FB["PIN_R"] + 0.05))
        # D4x8 press-fit bores (nominal; ream for press), THROUGH the lower plate so the pin presses in from below and
        # drifts out from above, with no thin skin over a blind bore (left: opens into the servo pocket, clear of it)
        palm = palm.cut(zc(p[0], p[1], FB["ZGB"][0] - 1, FB["ZGB"][1] + 1, FB["PIN_R"]))
    # reliefs in the mount plate's top (z > 22; a slot at y -38..-28 and the corner y > 54), mount plate only (x < 69, the
    # ground-pivot layer starts at 69): level-keeping rod 2 passes there at PIPE_CHUTE (wrist pitch 90) and at
    # PIPE_CHUTE_ROLL90 (head rolled 90 brings the +y corner round). Hub-flange screws and the cradle (z <= 19) are clear;
    # the -y side is only a slot so the ground-layer joint keeps its outer part (palm FEA: SF 1.5 with a full corner cut).
    # 2 mm rounds on the cutters' bottom edges (along x) give rounded inside corners: printed, so free to make. (A fillet
    # on the palm itself after the cuts produced an invalid solid; rounding the simple cutter boxes is robust.)
    def _rounded_cutter(y0, y1, round_y, z0=22.0):
        # round only the bottom edges at y in round_y: rounding the outer edge of the corner cutter (beyond the palm's
        # side at y Y_OUT) left a thin sliver at the palm edge (check_holes flagged it as a broken-out D4 'hole')
        c = box(64.0, y0, z0, 69.0, y1, g1 + 1.0)
        return c.makeFillet(2.0, [e for e in c.Edges if e.BoundBox.YLength < 1e-6 and e.BoundBox.ZLength < 1e-6
                                  and abs(e.BoundBox.ZMin - z0) < 1e-6
                                  and any(abs(e.BoundBox.YMin - y) < 1e-6 for y in round_y)])
    palm = palm.cut(_rounded_cutter(-38.0, -28.0, (-38.0, -28.0)))   # slot over rod 2's plane only (y -35..-31)
    palm = palm.cut(_rounded_cutter(54.0, YO + 1.0, (54.0,), 19.0))   # down to the cradle top: no ledge above it
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
    for nm, p in (("LD", gl), ("LI", gli), ("RD", gr), ("RI", gri)):                 # bottom-link ground pins
        z0 = FB["ZLB"][0] - 0.3
        pin = zc(p[0], p[1], z0, z0 + 8.0, FB["PIN_R"])
        out.append(Part_("Pin_D4x8_ground_bot_%s" % nm, pin, pin, "CAT", "PIN-D4x8", "steel"))
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
    for lv, (z0, z1) in (("lo", FB["ZL0"]), ("hi", FB["ZL1"]), ("bot", FB["ZLB"])):
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
            St, z0 = H.STS, FB["SEAT_Z"]                            # supplied horn: D9 hub on the spline, D19.95 disc on top
            zd = z0 + St["horn_t"] - St["horn_disc_t"]
            horn = zc(g[0], g[1], z0, zd, St["horn_hub_d"] / 2).fuse(zc(g[0], g[1], zd, z0 + St["horn_t"], St["horn_d"] / 2))
            horn = horn.cut(zc(g[0], g[1], z0 - 1, z0 + St["horn_t"] + 1, 2.6))
            out.append(Part_("Servo_Horn_STS_disc", horn, horn, "CAT", "HORN-25T", "alu", "STS3215 disc horn, screwed to the lower drive link"))
            pin = zc(g[0], g[1], FB["ZSEC"][1] + 0.5 - 20.0, FB["ZSEC"][1] + 0.5, FB["PIN_R"])
            out.append(Part_("Pin_D4x20_ground_LD", pin, pin, "CAT", "PIN-D4x20", "steel", "turns with the drive link, bushed in the palm"))
    return out


def _pad_shape(o, z0, z1, t=0.0):
    """Pad outline: R PAD_R arc (inner face) to R PAD_R+16 (back) inside the wrap wedge, 90 deg V-notch NOTCH deep.
    t > 0 offsets both contact faces back by t (arc to R PAD_R+t, notch apex t*sqrt2 deeper): the printed body
    under a t-thick rubber sheet."""
    XT = K["GRIP"]
    cen = V(XT, o - PAD_R, z0)
    ann = Part.makeCylinder(PAD_R + 16.0, z1 - z0, cen).cut(Part.makeCylinder(PAD_R + t, z1 - z0, cen))
    w = math.radians(WRAP)
    L_ = 120.0
    wp = [(XT, o - PAD_R), (XT - L_ * math.sin(w), o - PAD_R + L_ * math.cos(w)), (XT + L_ * math.sin(w), o - PAD_R + L_ * math.cos(w))]
    return ann.common(zprism(wp, z0 - 1, z1 + 1)).cut(_vprism(XT, o + NOTCH + t * math.sqrt(2), z0 - 1, z1 + 1))


def _pad_zone(o, z0, z1, gap):
    """The pad's footprint grown by 'gap' (annulus to R PAD_R+16+gap inside the wrap wedge + gap): keep-out for
    printed jaw features beside the pad."""
    XT = K["GRIP"]
    R = PAD_R + 16.0 + gap
    w = math.radians(WRAP) + gap / R
    L_ = 120.0
    wp = [(XT, o - PAD_R), (XT - L_ * math.sin(w), o - PAD_R + L_ * math.cos(w)), (XT + L_ * math.sin(w), o - PAD_R + L_ * math.cos(w))]
    return Part.makeCylinder(R, z1 - z0, V(XT, o - PAD_R, z0)).common(zprism(wp, z0, z1))


def body_fb_jaw(s):
    """Jaw (left built, mirrored for s=-1) at the pipe grip: printed jaw block (coupler-pin layer between the
    link layers, riser beyond the link ends, top finger), CF bottom finger, printed pad (R50 arc + 90 deg V) faced with adhesive rubber,
    D6 standoffs through the pad, two coupler pins."""
    XT = K["GRIP"]
    o = O_REF
    nm = "L" if s > 0 else "R"
    _gd, _gi, cd, ci = fb_pivots(1)
    out = []
    g0, g1 = FB["ZG"]
    r_ear = 6.0                                   # pin ears round the coupler pivots (bore wall 3.95)
    top_y = ci[1] + r_ear                         # the outline's outer edge runs straight into the ears' tangent
    k = (top_y - (o + 16)) / 14.0
    poly = [(XT - 26, o - 8), (XT + 26, o - 8), (XT + 26, o + 16), (XT + 26 - 18 * k, top_y), (XT - 26, top_y)]
    pad_holes = [(XT - 12.0, o + 9.0), (XT + 12.0, o + 9.0)]
    post = []          # the rear D6 post is gone: the C-frame wall holds the pad's back (wall inserts replace it)
    ins = [(XT + dx, o + dy) for dx, dy in FB["WALL_INSERTS"]]

    def outline(z0, z1):
        """The jaw's one plan outline, shared by the printed block and the CF bottom finger: the finger plate,
        pin ears round both coupler pivots, and a tangent flank from the lower ear to the finger's rear corner
        (a convex, continuous outline: no steps between the ears and the finger)."""
        f = zprism(poly, z0, z1).fuse(stadium(cd, ci, r_ear, z0, z1))
        ax, ay = poly[0]
        dx, dy = ax - cd[0], ay - cd[1]
        d = math.hypot(dx, dy)
        a = math.acos(r_ear / d)
        b = math.atan2(dy, dx)
        tps = [(cd[0] + r_ear * math.cos(b + sg * a), cd[1] + r_ear * math.sin(b + sg * a)) for sg in (1, -1)]
        t = min(tps, key=lambda q: q[0])
        f = f.fuse(zprism([(ax, ay), t, cd, (ax, cd[1])], z0, z1))
        f = f.removeSplitter()
        f = f.cut(Part.makeCylinder(PAD_R + 2.0, 200, V(XT, o - PAD_R, z0 - 100)))        # object space (R52)
        f = f.cut(_vprism(XT, o + NOTCH + 2.0 * math.sqrt(2), z0 - 1, z1 + 1))
        return fillet_z(f.removeSplitter(), 1.5)

    def rounded_cutter(x0, x1, z0, z1, edges_at, r=1.5):
        """Box cutter whose edges along y at the given (x, z) corners are rounded ((x, z) uses r, (x, z, r_) its
        own radius): the cut leaves concave blends instead of sharp internal corners."""
        c = box(x0, -200, z0, x1, 200, z1)
        for ea in edges_at:
            x, z, r_ = (ea + (r,))[:3]
            es = [e for e in c.Edges if e.BoundBox.XLength < 1e-6 and e.BoundBox.ZLength < 1e-6
                  and abs(e.BoundBox.XMin - x) < 1e-6 and abs(e.BoundBox.ZMin - z) < 1e-6]
            if es:
                c = c.makeFillet(r_, es)
        return c

    # Printed jaw block = ONE extrusion of the outline over the jaw's whole height (bottom-finger top .. coupler-layer
    # top), with every feature cut from it:
    #   the pad's footprint (+ WALL_GAP) over the pad height -> the C-frame wall behind the pad, the top finger above it
    #     (the drive-side pin ear stays: it sits at the pad's back corner, and the pad's corner is notched round it);
    #   above the top finger nothing beyond XMAX (pole keep-out; params) -> a stepped-back coupler layer, blended R0.5;
    #   clevis slots where the bottom links run, and the back cut-out above the lower pin plate for the top-lower links
    #     (the links' bosses turn about the coupler pins, so both reach to the pin + 5.6); the top-upper links ride
    #     above the block;
    #   pipe clearance, pin bores, heat-set insert bores.
    zb0, zb1 = FB["ZFB"][1], g1
    blk = outline(zb0, zb1)
    pz = _pad_zone(o, zb0 - 1, FB["ZPAD"][1], FB["WALL_GAP"]).cut(zc(cd[0], cd[1], zb0 - 2, zb1 + 2, r_ear))
    blk = blk.cut(pz)
    ft1 = FB["ZFT"][1]
    # R0.5 only: the M3 button heads on the top finger at x 139 seat 0.75 mm beyond XMAX
    blk = blk.cut(rounded_cutter(FB["XMAX"], 300, ft1, zb1 + 10, [(FB["XMAX"], ft1)], r=0.5))
    xs = cd[0] + 5.6
    # behind the wall, between the lower pin plate and the top coupler layer, the block is cut back to the wall (no
    # added mass): one opening for the top-lower links, its inside corners blended (R4 into the lower pin plate)
    z_lp, z_tl = FB["ZLUG"][1], FB["ZL0"][1] + 0.5
    blk = blk.cut(rounded_cutter(0, xs, z_lp, z_tl, [(xs, z_lp, 4.0), (xs, z_tl, 1.5)]))
    blk = blk.cut(rounded_cutter(0, xs, zb0 - 1, FB["ZLB"][1] + 0.5, [(xs, FB["ZLB"][1] + 0.5)]))
    blk = blk.cut(zc(XT, 0.0, -60, 60, PIPE_R + 1.5))                                    # pipe clearance
    for p in (cd, ci):
        blk = blk.cut(zc(p[0], p[1], g0 - 1, g1 + 1, FB["PIN_R"] + 0.05))
        blk = blk.cut(zc(p[0], p[1], FB["ZLB"][1], FB["ZLUG"][1] + 0.5, FB["PIN_R"] + 0.05))
    for (x, y) in pad_holes:
        blk = blk.cut(zc(x, y, FB["ZFT"][0] - 1, FB["ZFT"][1] + 1, 1.65))
    for (x, y) in ins:
        blk = blk.cut(zc(x, y, zb0 - 1, zb0 + 4.0, 2.0))                                  # heat-set insert bores
    blk = blk.removeSplitter()
    out.append(Part_("Jaw_Block_" + nm, blk, blk, "PRINT", "custom: PETG-CF print (concept)", "pla"))
    # CF bottom finger: the same outline, so the plate and the block above it line up edge for edge; the lower
    # coupler pins press in here (double shear with the block above the bottom link)
    fb = outline(*FB["ZFB"])
    for p in (cd, ci):
        fb = fb.cut(zc(p[0], p[1], FB["ZFB"][0] - 1, FB["ZFB"][1] + 1, FB["PIN_R"]))      # press fit (nominal bore)
    for (x, y) in ins + pad_holes:
        fb = fb.cut(zc(x, y, FB["ZFB"][0] - 1, FB["ZFB"][1] + 1, 1.65))
    out.append(Part_("Finger_%s_bot_CF3" % nm, fb, fb, "CF", "custom: 3 mm CF plate (concept)", "cf"))
    for i, (x, y) in enumerate(ins):
        out.append(P("Insert_M3_wall_%s%d" % (nm, i), to_z((ring(0, 0, 0, 4, 2.0, 1.25),) * 2, x, y, FB["ZFB"][1]),
                     "CAT", "INSERT", "brass"))
        out.append(P("BHCS_M3x6_wall_%s%d" % (nm, i), to_z(H.screw("BHCS", 3, 6, 0, 1), x, y, FB["ZFB"][0]), "CAT", "BHCS", "steel"))
    # rigid printed pad (PLA/PETG), its faces RUBBER_T behind the contact faces; the rubber sheet stuck on them
    # (arc and both V flanks) brings the grip surface back to PAD_R / NOTCH, so 'jaw' and the grip checks hold
    pad = _pad_shape(o, *FB["ZPAD"], t=RUBBER_T)
    pad = pad.cut(zc(cd[0], cd[1], -60, 60, r_ear + FB["WALL_GAP"]))       # back-corner notch round the drive-pin ear
    for (x, y) in pad_holes:
        pad = pad.cut(zc(x, y, -40, 40, 3.1))
    out.append(Part_("Pad_%s" % nm, pad, pad, "PRINT",
                     "custom: PLA/PETG print, R50 arc + 90 deg V, faces %g mm under the rubber" % RUBBER_T, "pla"))
    skin = _pad_shape(o, *FB["ZPAD"]).cut(_pad_shape(o, FB["ZPAD"][0] - 1, FB["ZPAD"][1] + 1, t=RUBBER_T))
    out.append(Part_("Grip_Rubber_%s" % nm, skin, skin, "RUBBER",
                     "custom: %g mm solid neoprene sheet (40-60A), bonded (transfer tape or CA), strips on the R50 arc and both V flanks"
                     % RUBBER_T, "pad"))
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
        z0 = FB["ZFB"][0] + 0.1                     # bottom link: finger tab .. lug
        pin = zc(p[0], p[1], z0, z0 + 14.0, FB["PIN_R"])
        out.append(Part_("Pin_D4x14_coupler_bot_%s%d" % (nm, i), pin, pin, "CAT", "PIN-D4x14", "steel"))
    return mirror_y(out) if s < 0 else out



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
