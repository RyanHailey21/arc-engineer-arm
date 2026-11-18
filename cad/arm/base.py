# -*- coding: utf-8 -*-
"""Base: GROUND body (chassis deck, towers, J1/J2 DM-J4340 stators) and the J1/J2 output hubs (motor_hub).
"""
from arm.core import *  # noqa: F401,F403


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
    # --- towers + motors
    for side, sgn in (("L", -1), ("R", 1)):
        yc = sgn * 51.0
        pts = [(sx - 60, zb + 8, 3), (sx + 60, zb + 8, 3), (sx, sz, 34)]
        holes = [(sx, sz, HUB_R + 1.5)]
        sh_ang = [(180 - a if sgn < 0 else a) for a in DM["stator_holes"]]
        dw_ang = [(180 - a if sgn < 0 else a) for a in DM["stator_dowels"]]
        for a in sh_ang:
            p = add(S, u(a, 25.0)); holes.append((p[0], p[1], 1.65))
        for a in dw_ang:
            p = add(S, u(a, 25.0)); holes.append((p[0], p[1], 1.5))
        for bx in (sx - 45, sx + 45):
            holes.append((bx, zb + 17, 1.65))
        if side == "L":
            pts.append((G1[0], G1[1], 10))
            holes.append((G1[0], G1[1], 2.1))
        tw = plate(pts, yc, holes, pockets=[((sx - 30, zb + 22, 6), (sx + 30, zb + 22, 6))])
        out.append(Part_("Tower_%s_CF3" % side, tw, tw, "CF", "custom: 3 mm CF plate (DXF)", "cf"))
        # vendor motor stator (rotor parts live in UPPER / CRANK bodies)
        st, _rot = dm_split()
        pl = App.Placement(V(sx, sgn * DM["face"], sz), App.Rotation(V(0, 0, 1), 180 if sgn < 0 else 0))
        st.Placement = pl.multiply(st.Placement)
        chk = ring(sx, sz, sgn * 52.5, sgn * 58.5, 28.5, 18.0).fuse(ycyl(sx, sz, sgn * 58.5, sgn * 104.75, 28.5))
        for a in sh_ang:
            p = add(S, u(a, 25.0))
            chk = chk.cut(ycyl(p[0], p[1], sgn * 52.4, sgn * 57.5, 1.25))
        out.append(Part_("J%d_Motor_DM-J4340_stator" % (1 if sgn < 0 else 2), st, chk, "CAT", "DM-J4340-2EC", "motor"))
        for i, a in enumerate(sh_ang):
            p = add(S, u(a, 25.0))
            out.append(P("BHCS_M3x8_motor%s_%d" % (side, i), at(H.screw("BHCS", 3, 8, sgn * 49.5, sgn), p[0], p[1]),
                         "CAT", "BHCS", "steel"))
        for i, a in enumerate(dw_ang):
            p = add(S, u(a, 25.0))
            out.append(P("Dowel_3x7_motor%s_%d" % (side, i),            # stock ISO 8734 3x7 (McMaster 91595A113)
                         at(H.dowel(3, min(sgn * 49.5, sgn * 56.5), max(sgn * 49.5, sgn * 56.5)), p[0], p[1]),
                         "CAT", "DOWEL", "steel", check=False))
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


_DM = {}


def dm_split():
    """DM-J4340 vendor model split into stator and output rotor.

    The vendor STEP fuses the output flange into the housing solid (one solid from the output face y=0 to
    y=42.45), so no whole solid is the rotor.  The rotor is cut out of the solids that reach the output face:
    the D35 output boss (radius DM.rotor_r) down to the depth of its D4 dowel holes (DM.rotor_depth).  That puts
    the dowel holes and PCD27 tapped holes on the rotor, which turns with the J1/J2 hub; left on the stator
    they sat ~50 deg away from the hub dowels at STOW (check_seated, TI-016)."""
    if "s" not in _DM:
        m = H.vendor("DM4340")
        cut = Part.makeCylinder(DM["rotor_r"], DM["rotor_depth"] + 0.2, V(0, -0.2, 0), V(0, 1, 0))
        st, rot = [], []
        for s in m.Solids:
            if s.BoundBox.YMin < 0.5:                      # carries the output face
                rot += s.common(cut).Solids
                st += s.cut(cut).Solids
            else:
                st.append(s)
        _DM["s"] = Part.makeCompound(st)
        _DM["r"] = Part.makeCompound(rot) if rot else Part.Shape()
    return _DM["s"].copy(), _DM["r"].copy()


def dm_rotor_part(name, sgn, hub_shape, local_y_face):
    """Rotor of the DM motor in the driven body's local frame."""
    _st, rot = dm_split()
    pl = App.Placement(V(0, sgn * local_y_face, 0), App.Rotation(V(0, 0, 1), 180 if sgn < 0 else 0))
    rot.Placement = pl.multiply(rot.Placement)
    chk = ycyl(0, 0, sgn * 51.45, sgn * 52.45, 17.4)
    return Part_(name, rot, chk, "CAT", "DM-J4340-2EC", "motor", "output rotor of vendor model", check=False)


def motor_hub(sgn, journal=False):
    """J1/J2 output hub (6061): D34 x 4.5 flange on the rotor face with 6x M3
    counterbored on PCD27 + 3x D4 dowels on PCD24.  J1: 3x M3 tapped PCD20
    for UA-L.  J2: D12 h6 journal through UA-R 6701 to the crank."""
    y_face = sgn * 51.5
    y_in = sgn * 47.0
    h = ycyl(0, 0, y_face, y_in, HUB_R)
    hang = [(180 - a if sgn < 0 else a) for a in DM["out_holes"]]
    dang = [(180 - a if sgn < 0 else a) for a in DM["out_dowels"]]
    for a in hang:
        p = u(a, 13.5)
        h = h.cut(ycyl(p[0], p[1], y_face, y_in, 1.65)).cut(ycyl(p[0], p[1], y_in, sgn * 50.0, 3.25))
    for a in dang:
        p = u(a, 12.0)
        h = h.cut(ycyl(p[0], p[1], y_face, sgn * 49.0, 2.0))
    parts = []
    if not journal:
        h = h.fuse(ycyl(0, 0, y_in, sgn * 44.5, 6.0))                     # pilot into UA-L
        for a_ in UA_HUB_SCREWS:
            p = u(a_, 10.0)
            h = h.cut(ycyl(p[0], p[1], y_in, sgn * 51.0, 1.25))
    else:
        h = h.fuse(ycyl(0, 0, y_in, sgn * 33.0, 6.0))                      # D12 journal
        fy = sorted((sgn * 32.5, sgn * 36.5))
        h = h.cut(box(5.5, fy[0], -7, 7.0, fy[1], 7))                       # 0.5 mm drive flat under the crank
        h = h.cut(ycyl(0, 0, sgn * 33.0, sgn * 42.5, 1.7))               # M4 tapped end, 9.5 drill: 8 thread > 7.2 screw
    name = "J2_Output_Hub_Journal" if journal else "J1_Output_Hub"
    parts.append(Part_(name, h, h, "AL", "custom: 6061 turned + drilled", "alu"))
    for i, a in enumerate(hang):
        p = u(a, 13.5)
        parts.append(P("SHCS_M3x6_%s_%d" % (name, i), at(H.screw("SHCS", 3, 6, sgn * 50.0, sgn), p[0], p[1]),
                       "CAT", "SHCS", "steel"))
    for i, a in enumerate(dang):
        p = u(a, 12.0)
        parts.append(P("Dowel_4x5_%s_%d" % (name, i), at(H.dowel(4, sgn * 49.0, sgn * 54.0), p[0], p[1]),   # stock 4x5 (91595A123)
                       "CAT", "DOWEL", "steel", check=False))
    return parts
