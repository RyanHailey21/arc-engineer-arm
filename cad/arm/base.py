# -*- coding: utf-8 -*-
"""Base: GROUND body (chassis deck, towers, J1/J2 drives: STS3215 servo + printed m2 spur stage on a printed drive
frame per tower) and the J1/J2 output hubs with their 54T gears (motor_hub, drive_gear_parts).  The drive's mates
come from interfaces/drive_frame__tower.toml, base_hub__drive.toml and sts3215__cradle.toml; its sizes from
params/base_drive.toml.
"""
from arm.core import *  # noqa: F401,F403


def drive_layout():
    """Shoulder axis S, pinion centre and drive-frame leg points (GROUND x, z): the same on both towers."""
    S = (K["SX"], K["SZ"])
    pc = add(S, u(GEAR["pinion_angle"], GEAR_CD))
    legs = [add(S, u(a, IF_DRIVE_TOWER["pattern"]["radius"])) for a in IF_DRIVE_TOWER["pattern"]["angles_deg"]]
    return S, pc, legs


def _y_seat():
    """|y| of the base servos' horn seat: the pinion's outboard face carries the horn disc."""
    return GEAR["y0"] + GEAR["face"] + H.STS["horn_t"]


def drive_frame(sgn):
    """Printed drive frame (PETG-CF): bearing wall around S (6804 seat + outboard lip), the STS3215 pocket that runs
    through the wall plane, and three legs to the tower with M3 heat-set inserts."""
    S, pc, legs = drive_layout()
    B, SR = IF_HUB_DRIVE["bearing"], IF_STS["pocket"]
    w0, w1 = B["y"]
    ang, ys = GEAR["pinion_angle"], _y_seat()
    # pocket outline corners (canonical servo frame -> GROUND x, z) for the wall's hull
    c, w = SR["clearance"] + SR["wall"], H.STS["w"]
    corners = [sts_xz(px, pz, sgn, ang, *pc) for px in (H.STS["x0"] - c + 3, H.STS["x1"] + c - 3)
               for pz in (-(w + c) + 3, (w + c) - 3)]
    pts = [(S[0], S[1], DFRAME["boss_r"])] + [(x, z, DFRAME["leg_d"] / 2 + 1) for (x, z) in legs] + \
          [(x, z, 3.0) for (x, z) in corners]
    wall = plate(pts, sgn * (w0 + w1) / 2, [(S[0], S[1], B["D"] / 2)], t=w1 - w0)
    # the servo passes through the wall plane: cut its pocket opening, then add the pocket (walls + floor)
    top_c = ys - w0                                       # wall's inboard face in the servo's canonical y
    inner = box(H.STS["x0"] - SR["clearance"], -60, -(w + SR["clearance"]), H.STS["x1"] + SR["clearance"], top_c + 1,
                w + SR["clearance"])
    wall = wall.cut(sts_place(inner, sgn * ys, sgn, ang, *pc))
    fr = wall.fuse(sts_place(sts_pocket(top_c), sgn * ys, sgn, ang, *pc))
    # bearing lip (outboard) and legs with insert bores
    fr = fr.fuse(ring(S[0], S[1], sgn * w1, sgn * (w1 + DFRAME["lip"]), DFRAME["boss_r"] - 4, DFRAME["lip_d"] / 2))
    y_tw = abs(Y["TW"]) + T / 2
    ins = IF_DRIVE_TOWER["side_b"]
    for (x, z) in legs:
        fr = fr.fuse(ycyl(x, z, sgn * y_tw, sgn * w0, DFRAME["leg_d"] / 2))
        fr = fr.cut(ycyl(x, z, sgn * (y_tw - 1), sgn * (y_tw + ins["drill_depth"]), ins["drill_d"] / 2))
    return fr.removeSplitter()


def body_ground():
    S = (K["SX"], K["SZ"])
    sx, sz, zb = S[0], S[1], K["DECK_Z"]
    G1 = add(S, u(K["V1_ANG"], K["V1_LEN"]))
    out = []
    # --- base plate
    base = fillet_z(box(sx - 275, -112, zb, sx + 70, 112, zb + 5), 10)
    corners = [(sx - 262, -99), (sx - 262, 99), (sx + 57, -99), (sx + 57, 99)]
    for (x, y) in corners:
        base = base.cut(Part.makeCylinder(2.25, 7, V(x, y, zb - 1)))
    tapped = [(bx, sg * 64.5) for bx in (sx - 45, sx + 45) for sg in (-1, 1)]
    for (x, y) in tapped:
        base = base.cut(Part.makeCylinder(1.25, 7, V(x, y, zb - 1)))
    out.append(Part_("Base_Plate_AL5", base, base, "AL", "custom: 5 mm 6061, waterjet + tap", "alu",
                     "4x M4 to chassis; M3 tapped for brackets / ESC / cable clips"))
    for i, (x, y) in enumerate(corners):
        out.append(P("SHCS_M4x12_base_%d" % i, to_z(H.screw("SHCS", 4, 12, 0, -1), x, y, zb + 5),
                     "CAT", "SHCS", "steel", "M4x12 into chassis", check=False))
    # --- towers + J1/J2 drives (STS3215 -> 18T pinion -> 54T gear on the hub, all on the drive frame)
    _S, pc, legs = drive_layout()
    ang, ys = GEAR["pinion_angle"], _y_seat()
    y_tw_in, y_tw_out = abs(Y["TW"]) - T / 2, abs(Y["TW"]) + T / 2
    LT, B = IF_DRIVE_TOWER, IF_HUB_DRIVE["bearing"]
    for side, sgn in (("L", -1), ("R", 1)):
        jn = 1 if sgn < 0 else 2
        yc = sgn * abs(Y["TW"])
        pts = [(sx - 60, zb + 8, 3), (sx + 60, zb + 8, 3), (sx, sz, 34)] + [(x, z, 7) for (x, z) in legs]
        holes = [(sx, sz, HUB_R + 1.5)] + [(x, z, LT["side_a"]["clearance_d"] / 2) for (x, z) in legs]
        for bx in (sx - 45, sx + 45):
            holes.append((bx, zb + 17, 1.65))
        if side == "L":
            pts.append((G1[0], G1[1], 10))
            holes.append((G1[0], G1[1], 2.1))
        tw = plate(pts, yc, holes, pockets=[((sx - 30, zb + 22, 6), (sx + 30, zb + 22, 6))])
        out.append(Part_("Tower_%s_CF3" % side, tw, tw, "CF", "custom: 3 mm CF plate (DXF)", "cf"))
        fr = drive_frame(sgn)
        out.append(Part_("Drive_Frame_%s" % side, fr, fr, "PRINT", "custom: PETG-CF print, 3x M3 heat-set inserts", "pla",
                         "J%d bearing wall + STS3215 cradle" % jn))
        for i, (x, z) in enumerate(legs):
            out.append(P("Insert_M3_frame_%s%d" % (side, i), at((ring(0, 0, sgn * y_tw_out, sgn * (y_tw_out + 3.8), 2.0, 1.25),) * 2, x, z),
                         "CAT", "INSERT", "brass"))
            f = LT["fastener"]
            out.append(P("BHCS_M3x%d_frame_%s%d" % (f["length"], side, i),
                         at(H.screw("BHCS", 3, f["length"], sgn * y_tw_in, sgn), x, z), "CAT", "BHCS", "steel"))
        # 6804 bearing in the frame wall (outer race static; the hub's journal turns in it)
        out.append(P("Brg_6804_J%d" % jn, at(H.bearing(B["d"], B["D"], B["B"], sgn * B["y"][0], sgn), sx, sz), "CAT", "6804ZZ", "alu"))
        # servo, its horn, the pinion and the screws (the servo turns its pinion; modelled static at the STOW clocking)
        sv, svc = H.sts3215(0.0, -1)
        out.append(Part_("J%d_Servo_STS3215" % jn, sts_place(sv, sgn * ys, sgn, ang, *pc), sts_place(svc, sgn * ys, sgn, ang, *pc),
                         "CAT", "STS3215", "motor", "J%d drive, 3:1 through the 18T/54T stage" % jn))
        hv, hc = H.sts_horn(0.0, -1)
        out.append(Part_("Servo_Horn_STS_J%d" % jn, sts_place(hv, sgn * ys, sgn, ang, *pc), sts_place(hc, sgn * ys, sgn, ang, *pc),
                         "CAT", "HORN-25T", "alu", "supplied with the servo"))
        out += sts_case_screws("J%d" % jn, sgn * ys, sgn, ang, *pc)
        m, zp = GEAR["module"], GEAR["z_pinion"]
        y_g0, y_g1 = sgn * GEAR["y0"], sgn * (GEAR["y0"] + GEAR["face"])
        pv, pchk, _rp = H.spur_gear(m, zp, min(y_g0, y_g1), max(y_g0, y_g1), 4.0, phase=ang + 180.0 + 180.0 / zp)   # a gap faces the 54T gear
        hp = IF_STS["horn"]
        for a in hp["angles_deg"]:
            px, pz = sts_xz(hp["pcd"] / 2 * math.cos(math.radians(a)), hp["pcd"] / 2 * math.sin(math.radians(a)), sgn, ang)
            pv = pv.cut(ycyl(px, pz, y_g0 - sgn, y_g1 + sgn, 1.65)).cut(ycyl(px, pz, y_g0 - sgn, sgn * (GEAR["y0"] + 3.0), 3.0))
            pchk = pchk.cut(ycyl(px, pz, y_g0 - sgn, y_g1 + sgn, 1.65)).cut(ycyl(px, pz, y_g0 - sgn, sgn * (GEAR["y0"] + 3.0), 3.0))
        out.append(P("Pinion_m2_%dT_J%d" % (zp, jn), at((pv, pchk), *pc), "PRINT", "custom: PA12 / PETG-CF print, m2 %dT, 4x M3 cbore" % zp, "pom"))
        for k, a in enumerate(hp["angles_deg"]):
            px, pz = sts_xz(hp["pcd"] / 2 * math.cos(math.radians(a)), hp["pcd"] / 2 * math.sin(math.radians(a)), sgn, ang, *pc)
            out.append(P("BHCS_M3x8_pinion_J%d_%d" % (jn, k), at(H.screw("BHCS", 3, 8, sgn * (GEAR["y0"] + 3.0), sgn), px, pz),
                         "CAT", "BHCS", "steel"))
        # printed angle brackets (outboard) tower -> base
        for j, bx in enumerate((sx - 45, sx + 45)):
            yo0, yo1 = sgn * 52.5, sgn * 56.5
            br = box(bx - 8, yo0, zb + 5, bx + 8, yo1, zb + 25).fuse(box(bx - 8, yo0, zb + 5, bx + 8, sgn * 72.5, zb + 9))
            br = br.cut(ycyl(bx, zb + 17, yo0 - sgn, yo1 + sgn, 1.65))
            br = br.cut(Part.makeCylinder(1.65, 6, V(bx, sgn * 64.5, zb + 4)))
            br = fillet_z(br, 1.5)
            out.append(Part_("Tower_Bracket_%s%d" % (side, j), br, br, "PRINT", "custom: PETG-CF print", "pla"))
            out.append(P("BHCS_M3x10_bracket_%s%d" % (side, j), at(H.screw("BHCS", 3, 10, sgn * 49.5, sgn), bx, zb + 17),
                         "CAT", "BHCS", "steel"))
            out.append(P("Nyloc_M3_bracket_%s%d" % (side, j), at(H.nyloc(3, sgn * 56.5, sgn), bx, zb + 17),
                         "CAT", "NYLOC", "steel"))
            out.append(P("BHCS_M3x8_bracketbase_%s%d" % (side, j), to_z(H.screw("BHCS", 3, 8, 0, -1), bx, sgn * 64.5, zb + 9),
                         "CAT", "BHCS", "steel"))
    # --- G1 ground pivot (stage-1 level-keeping): spacer + shoulder screw + nyloc
    out.append(P("Spacer_G1", at((ring(0, 0, -49.5, -43.5, 4.5, 2.6),) * 2, G1[0], G1[1]), "AL", "custom: D9/D5.2 x 6 alu", "alu"))
    out.append(P("SB5x10_G1", at(H.shoulder(5, 10, 4, 8, -39.5, -1), G1[0], G1[1]), "CAT", "SB5", "steel"))
    out.append(P("Nyloc_M4_G1", at(H.nyloc(4, -52.5, -1), G1[0], G1[1]), "CAT", "NYLOC", "steel"))
    for i, (x, y) in enumerate(((sx - 70, -78), (sx - 170, -40), (sx - 230, 40))):
        out.append(P("Cable_Clip_Base_%d" % i, at(H.cable_clip(), x, zb + 5, y), "CAT", "CLIP", "pad", "harness to C610 / PDB"))
    # --- C610 ESC (vendor) on base plate under J1
    esc = H.vendor("C610")
    bb = esc.BoundBox
    esc.translate(V(sx - 120 - bb.Center.x, -80 - bb.Center.y, zb + 6 - bb.ZMin))
    out.append(Part_("ESC_C610", esc, Part.makeBox(bb.XLength, bb.YLength, bb.ZLength,
                                                   V(sx - 120 - bb.XLength / 2, -80 - bb.YLength / 2, zb + 6)),
                     "CAT", "C610", "motor", "on 1 mm VHB pad"))
    return out


def motor_hub(sgn, journal=False):
    """J1/J2 output hub (6061, turned): flange inside the tower bore, then the stub (interfaces/base_hub__drive.toml)
    - D24 collar, 19 AF hex for the 54T gear, D20 journal in the drive frame's 6804, M5 tapped end.
    J1: 3x M3 tapped PCD20 for UA-L + pilot.  J2: D12 h6 journal through UA-R 6701 to the crank."""
    st = IF_HUB_DRIVE["stub"]
    y_fl = sgn * st["collar_y"][0]                                        # flange outboard face (51.5)
    y_in = sgn * 47.0
    h = ycyl(0, 0, y_fl, y_in, HUB_R)
    h = h.fuse(ycyl(0, 0, sgn * st["collar_y"][0], sgn * st["collar_y"][1], st["collar_d"] / 2))
    h = h.fuse(hexhole(st["hex_af"], 0, 0, sgn * st["hex_y"][0], sgn * st["hex_y"][1]))
    h = h.fuse(ycyl(0, 0, sgn * st["journal_y"][0], sgn * st["journal_y"][1], st["journal_d"] / 2))
    h = h.cut(ycyl(0, 0, sgn * (st["journal_y"][1] - st["end_depth"]), sgn * (st["journal_y"][1] + 1), st["end_tap_d"] / 2))
    parts = []
    if not journal:
        h = h.fuse(ycyl(0, 0, y_in, sgn * 44.5, 6.0))                     # pilot into UA-L
        for a_ in UA_HUB_SCREWS:
            p = u(a_, 10.0)
            h = h.cut(ycyl(p[0], p[1], y_in, y_fl, 1.25))                 # 4.5 drill (full flange): 3 mm of thread
    else:
        h = h.fuse(ycyl(0, 0, y_in, sgn * 33.0, 6.0))                      # D12 journal
        fy = sorted((sgn * 32.5, sgn * 36.5))
        h = h.cut(box(5.5, fy[0], -7, 7.0, fy[1], 7))                       # 0.5 mm drive flat under the crank
        h = h.cut(ycyl(0, 0, sgn * 33.0, sgn * 42.5, 1.7))               # M4 tapped end, 9.5 drill: 8 thread > 7.2 screw
    name = "J2_Output_Hub_Journal" if journal else "J1_Output_Hub"
    parts.append(Part_(name, h.removeSplitter(), h.removeSplitter(), "AL", "custom: 6061 turned + milled hex", "alu"))
    return parts


def drive_gear_parts(sgn, jn):
    """54T m2 gear on the hub stub's hex (turns with the joint's body) + the M5 end screw and washer that clamp the
    bearing's inner race against the hex shoulder."""
    m, zg = GEAR["module"], GEAR["z_gear"]
    y0, y1 = sgn * GEAR["y0"], sgn * (GEAR["y0"] + GEAR["face"])
    g, gc, _rp = H.spur_gear(m, zg, min(y0, y1), max(y0, y1), 4.0, phase=GEAR["pinion_angle"])     # a tooth faces the pinion at STOW
    hx = hexhole(IF_HUB_DRIVE["gear_bore"]["hex_af"], 0, 0, y0 - sgn, y1 + sgn)
    g, gc = g.cut(hx), gc.cut(hx)
    n, r, rr = GEAR["lightening"]
    for k in range(int(n)):
        p = u(30 + 360.0 * k / n, rr)
        g, gc = g.cut(ycyl(p[0], p[1], y0 - sgn, y1 + sgn, r)), gc.cut(ycyl(p[0], p[1], y0 - sgn, y1 + sgn, r))
    out = [Part_("Drive_Gear_m2_%dT_J%d" % (zg, jn), g, gc, "PRINT", "custom: PA12 / PETG-CF print, m2 %dT, 19 AF hex bore" % zg, "pom")]
    es, st = IF_HUB_DRIVE["end_screw"], IF_HUB_DRIVE["stub"]
    y_end = sgn * st["journal_y"][1]
    out.append(P("Washer_M5_hub_J%d" % jn, H.washer(es["size"], y_end, sgn, od=es["washer_od"], t=es["washer_t"]), "CAT", "WASHER", "steel"))
    out.append(P("SHCS_M5x%d_hub_J%d" % (es["length"], jn), H.screw("SHCS", es["size"], es["length"], y_end + sgn * es["washer_t"], -sgn),
                 "CAT", "SHCS", "steel", "clamps the 6804 inner race"))
    return out
