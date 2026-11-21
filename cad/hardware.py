# -*- coding: utf-8 -*-
"""
hardware.py - purchased-part geometry.

* Vendor STEP models (cad/vendor/...) for parts whose makers publish CAD:
  Feetech STS3215, Damiao DM-J4340.  Loaded once, cached as BREP,
  re-oriented to a canonical frame (axis +Y, mounting face at y=0).
* ISO/DIN standard hardware generated at standard dimensions (same approach as
  the FreeCAD Fasteners workbench): ISO 4762 SHCS, ISO 7380 BHCS, ISO 10511
  nyloc, ISO 7379 shoulder screws, DIN 6799 e-clips,
  ISO 8734 dowels, deep-groove bearings (rings + shields), M3 round standoffs.
* Catalogue parts without public CAD, modelled to catalogue drawings:
  spur gears, cable clips, P-clips.

Every builder returns (vis_shape, chk_shape): vis is the detailed display
geometry, chk is the simplified solid used by the interference sweep.
All builders produce parts on the +Y axis through the origin unless noted.
"""
import math
import os
import FreeCAD as App
import Part

V = App.Vector
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
VENDOR = os.path.join(HERE, "vendor")


def _ycyl(r, y0, y1, x=0.0, z=0.0):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def _ring(ro, ri, y0, y1, x=0.0, z=0.0):
    return _ycyl(ro, y0, y1, x, z).cut(_ycyl(ri, y0 - 0.1, y1 + 0.1, x, z))


def _hexprism(af, y0, y1, x=0.0, z=0.0):
    r = af / math.sqrt(3)
    pts = [V(x + r * math.cos(math.radians(30 + 60 * i)), y0, z + r * math.sin(math.radians(30 + 60 * i)))
           for i in range(6)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, y1 - y0, 0))


# -------------------------------------------------------------- vendor models
_VCACHE = {}


def vendor(name):
    """Return the vendor shape in canonical frame (copy).  Canonical frames:
    STS3215: output spline on +Y through the origin, horn seat at y=0, body to -y, long axis +x (horns removed).
    DM4340: Damiao DM-J4340-2EC (BASE_DRIVE=DIRECT): axis +Y, OUTPUT face at y=0, housing extends to y=+53.25."""
    if name in _VCACHE:
        return _VCACHE[name].copy()
    cache = os.path.join(VENDOR, "cache_%s.brep" % name)
    if os.path.exists(cache):
        s = Part.Shape()
        s.read(cache)
    else:
        if name == "DM4340":
            s = Part.Shape()
            s.read(os.path.join(VENDOR, "damiao", "DM-J4340-2EC-V1.1.stp"))
            s = Part.makeCompound(s.Solids)           # model already axis Y, output face y=0
        elif name == "STS3215":
            raw = Part.Shape()
            raw.read(os.path.join(VENDOR, "feetech", "STS3215.stp"))
            # drop the two supplied horns (D19.95, on the output axis at vendor x=-25.5): modelled as their own parts
            keep = [x.copy() for x in raw.Solids
                    if not (abs(x.BoundBox.Center.x + 25.5) < 0.6 and abs(x.BoundBox.XLength - 19.95) < 0.3)]
            s = Part.makeCompound(keep)
            s.translate(V(25.5, -4.7, 0))             # output axis -> x=0, horn seat -> y=0 (canonical frame above)
        s.exportBrep(cache)
    _VCACHE[name] = s
    return s.copy()


# ------------------------------------------------------------ ISO fasteners
# d: (head_d, head_k, socket_af)  ISO 4762 / ISO 7380 / ISO 4032-10511
SHCS = {2.5: (4.5, 2.5, 2.0), 3: (5.5, 3.0, 2.5), 4: (7.0, 4.0, 3.0), 5: (8.5, 5.0, 4.0)}
BHCS = {3: (5.7, 1.65, 2.0), 4: (7.6, 2.2, 2.5)}
NUT = {2.5: (5.0, 3.0), 3: (5.5, 4.0), 4: (7.0, 5.0)}         # nyloc af, m


def screw(kind, d, L, y_head, direction):
    """Screw whose head bearing face sits at y_head and whose shank extends in
    'direction' (+1/-1) along Y by L.  Returns (vis, chk)."""
    sgn = direction
    if kind == "SHCS":
        dk, k, s = SHCS[d]
    else:
        dk, k, s = BHCS[d]
    y_shank0, y_shank1 = sorted((y_head, y_head + sgn * L))
    y_hd0, y_hd1 = sorted((y_head, y_head - sgn * k))
    shank_r = 0.41 * d                                   # thread minor-ish: fits tapped holes
    shank = _ycyl(shank_r, y_shank0, y_shank1)
    if kind == "SHCS":
        head = _ycyl(dk / 2, y_hd0, y_hd1)
    else:
        head = Part.makeSphere(dk / 2 * 1.05, V(0, y_head - sgn * 0.0, 0))
        head = head.common(_ycyl(dk / 2, y_hd0, y_hd1))
    vis = shank.fuse(head)
    sock = _hexprism(s, y_hd0 - 0.01, y_hd1 + 0.01)
    sock = sock.common(_ycyl(dk, (y_hd1 - 0.6 * k) if sgn > 0 else y_hd0, y_hd1 + 0.1) if sgn > 0 else
                       _ycyl(dk, y_hd0 - 0.1, y_hd0 + 0.6 * k))
    vis = vis.cut(sock)
    return vis, shank.fuse(_ycyl(dk / 2, y_hd0, y_hd1))


def nyloc(d, y_face, direction):
    af, m = NUT[d]
    y0, y1 = sorted((y_face, y_face + direction * m))
    n = _hexprism(af, y0, y1).cut(_ycyl(0.42 * d, y0 - 1, y1 + 1))
    return n, n


def washer(d, y_face, direction, od=None, t=0.5):
    od = od or 2.0 * d + 1
    y0, y1 = sorted((y_face, y_face + direction * t))
    w = _ring(od / 2, d / 2 + 0.1, y0, y1)
    return w, w


def shoulder(d, L_shoulder, thread_d, thread_L, y_head, direction):
    """ISO 7379 shoulder screw: head (1.6d x 0.6d+?) at y_head, shoulder d x L,
    then thread_d x thread_L."""
    sgn = direction
    dk, k = {5: (9.0, 3.5), 6: (10.0, 4.5), 4: (7.0, 2.6)}[d]
    hs = sorted((y_head, y_head - sgn * k))
    sh = sorted((y_head, y_head + sgn * L_shoulder))
    th = sorted((y_head + sgn * L_shoulder, y_head + sgn * (L_shoulder + thread_L)))
    head = _ycyl(dk / 2, *hs).cut(_hexprism(3.0 if d == 5 else 2.5, *hs).common(
        _ycyl(dk, hs[0], hs[0] + 0.6 * k) if sgn > 0 else _ycyl(dk, hs[1] - 0.6 * k, hs[1])))
    s = head.fuse(_ycyl(d / 2, *sh)).fuse(_ycyl(0.41 * thread_d, *th))
    chk = _ycyl(dk / 2, *hs).fuse(_ycyl(d / 2, *sh)).fuse(_ycyl(0.41 * thread_d, *th))
    return s, chk


def eclip(shaft_d, y_face, direction):
    """DIN 6799 retaining washer (approx): OD ~ 2.1*groove, thickness 0.9."""
    gd = {10: 7.0}.get(shaft_d, shaft_d - 1.0 if shaft_d >= 8 else shaft_d - 0.6)   # DIN 6799 size 7 groove for D10
    od = {10: 17.0, 5: 9.0, 12: 19.0}.get(shaft_d, 2 * shaft_d)
    y0, y1 = sorted((y_face, y_face + direction * 0.9))
    e = _ring(od / 2, gd / 2, y0, y1).cut(Part.makeBox(od, 1.2 * gd, 3, V(0, y0 - 1, -0.6 * gd)))
    return e, _ring(od / 2, shaft_d / 2, y0, y1)


def dowel(d, y0, y1):
    y0, y1 = sorted((y0, y1))              # a negative height gives an inside-out (invalid) cylinder
    p = _ycyl(d / 2, y0, y1)
    return p, p


def standoff_round(od, L, y0, direction, thread=3):
    y_a, y_b = sorted((y0, y0 + direction * L))
    s = _ring(od / 2, 0.42 * thread * 1.0 + 0.01, y_a, y_b)
    return s, s


# ------------------------------------------------------------------ bearings
def bearing(d, D, B, y0, direction):
    """Deep-groove bearing: inner + outer race, two shields with chamfer look."""
    ya, yb = sorted((y0, y0 + direction * B))
    w = (D - d) / 2
    ri_o = d / 2 + 0.28 * w
    ro_i = D / 2 - 0.28 * w
    inner = _ring(ri_o, d / 2, ya, yb)
    outer = _ring(D / 2, ro_i, ya, yb)
    shield = _ring(ro_i, ri_o + 0.15, ya + 0.15, yb - 0.15)
    vis = inner.fuse(outer).fuse(shield)
    return vis, _ring(D / 2, d / 2, ya, yb)


# ------------------------------------------------- Feetech STS3215 (vendor STEP, cad/vendor/feetech/STS3215.stp)
# Canonical frame (vendor("STS3215")): output spline on +Y through the origin, horn seat at y=0, body below (-y),
# long axis along +x (spline 10.1 mm from the near end), width along z.  Heights measured from the vendor model:
# case top 0.2 within 10 mm of the spline, 2.8 on the raised far end; bottom-cap screw bosses at -30.3;
# lowest point (idler shaft, connectors) -32.9.  Bottom-cap screws (4x PA2.0, replaced by longer ones to fix the
# servo): (8.3, +-10.25) and (32.75, +-10.25).
STS = dict(x0=-10.14, x1=35.11, w=12.39, top_near=0.2, top_far=2.8, far_x=10.0, boss_y=-30.3, bottom=-32.9,
           base_y=-30.25, conn=(15.0, 29.0, 8.0), idler_r=1.5,   # bottom: case at -30.3 except the connector block
                                                                  # (x 15..29, |z|<8) and the idler shaft (x=0), to -32.9
           screws=((8.3, 10.25), (8.3, -10.25), (32.75, 10.25), (32.75, -10.25)),
           horn_t=4.5, horn_disc_t=2.5, horn_d=19.95, horn_hub_d=9.0)


def _sts_place(shapes, y_seat, direction):
    """Canonical STS3215 frame -> spline on the Y axis, horn seat at y_seat, body towards 'direction' (+1/-1)."""
    out = []
    for s_ in shapes:
        s_ = s_.copy()
        if direction > 0:
            s_.rotate(V(0, 0, 0), V(1, 0, 0), 180)          # body to +y, keeps a right-handed frame
        s_.translate(V(0, y_seat, 0))
        out.append(s_)
    return out


def sts3215(y_seat, direction):
    """Feetech STS3215 (vendor model, horns removed) with the horn seat at y_seat and the body towards direction.
    chk: the body footprint from the case bottom (-30.25) to the near-spline top, the raised far end, and the
    connector block and idler shaft that reach -32.9 (they sit over the cradle floor's window / clear of its bosses)."""
    S = STS
    vis = vendor("STS3215")
    chk = Part.makeBox(S["x1"] - S["x0"], S["top_near"] - S["base_y"], 2 * S["w"], V(S["x0"], S["base_y"], -S["w"]))
    cx0, cx1, cz = S["conn"]
    chk = chk.fuse(Part.makeBox(cx1 - cx0, S["base_y"] - S["bottom"] + 0.01, 2 * cz, V(cx0, S["bottom"], -cz)))
    chk = chk.fuse(_ycyl(S["idler_r"], S["bottom"], S["base_y"] + 0.01))
    for (sx_, sz_) in S["screws"]:                                         # bottom-cap screw pilot holes (case)
        chk = chk.cut(_ycyl(0.85, S["base_y"] - 1, S["base_y"] + 7.0, sx_, sz_))
    chk = chk.fuse(Part.makeBox(S["x1"] - S["far_x"], S["top_far"] - S["top_near"], 2 * S["w"],
                                V(S["far_x"], S["top_near"], -S["w"])))
    chk = chk.cut(_ycyl(S["horn_hub_d"] / 2 + 0.1, -1.0, S["top_near"] + 0.1))     # the horn hub seats on the spline
    return tuple(_sts_place((vis, chk), y_seat, direction))


def sts_horn(y_seat, direction):
    """The STS3215's supplied aluminium horn (Feetech spec p.7): D9 hub on the 25T spline, D19.95 x 2.5 disc on top,
    4x M3 tapped on PCD 14; 4.5 tall from the horn seat, on the side away from the servo body."""
    S = STS
    h = _ycyl(S["horn_hub_d"] / 2, 0.0, S["horn_t"] - S["horn_disc_t"]).fuse(
        _ycyl(S["horn_d"] / 2, S["horn_t"] - S["horn_disc_t"], S["horn_t"]))
    h = h.cut(_ycyl(2.95, -1, S["horn_t"] + 1))
    for i in range(4):
        a = math.radians(45 + 90 * i)
        h = h.cut(_ycyl(1.25, -1, S["horn_t"] + 1, HORN_PCD / 2 * math.cos(a), HORN_PCD / 2 * math.sin(a)))
    return tuple(_sts_place((h, h), y_seat, direction))


def pan_screw(d, L, y_head, direction):
    """Pan-head screw (ISO 7045 proportions; also the STS3215's PA2.0 self-tapping case screws), head bearing face
    at y_head, shank towards direction."""
    dk, k = 2.0 * d, 0.7 * d
    y0, y1 = sorted((y_head, y_head + direction * L))
    h0, h1 = sorted((y_head, y_head - direction * k))
    s = _ycyl(0.41 * d, y0, y1).fuse(_ycyl(dk / 2, h0, h1))
    return s, s


HORN_D, HORN_PCD = 20.0, 14.0     # 25T aluminium disc horn: D20, 4x M3 on PCD 14 (the STS3215's own horn uses the same PCD)


def _involute_profile(module, teeth, phase_deg, pa_deg=20.0, n_flank=8):
    """Closed 2D outline (list of (x, z)) of an involute spur gear, tooth centres at
    phase + k*360/teeth (angle measured in the XZ plane, x = r cos, z = r sin)."""
    rp = module * teeth / 2.0
    ra, rf = rp + module, rp - 1.25 * module
    pa = math.radians(pa_deg)
    rb = rp * math.cos(pa)
    inv = lambda r: (lambda al: math.tan(al) - al)(math.acos(min(1.0, rb / r)))
    half_p = math.pi / (2 * teeth) + inv(rp)              # half tooth angle at the base of the involute
    r0 = max(rb, rf)
    radii = [r0 + (ra - r0) * i / n_flank for i in range(n_flank + 1)]
    pts = []
    for k in range(teeth):
        c = 2 * math.pi * k / teeth + math.radians(phase_deg)
        psi0 = half_p - inv(r0)
        if rf < r0:                                         # radial flank below the base circle
            pts.append((rf, c - psi0 - 0.15 * math.pi / teeth))
        for r in radii:                                     # leading flank
            pts.append((r, c - (half_p - inv(r))))
        for r in reversed(radii):                           # trailing flank
            pts.append((r, c + (half_p - inv(r))))
        if rf < r0:
            pts.append((rf, c + psi0 + 0.15 * math.pi / teeth))
    return [(r * math.cos(t), r * math.sin(t)) for (r, t) in pts]


def spur_gear(module, teeth, y0, y1, bore, hub=None, phase=0.0):
    """Involute spur gear (20 deg) on the Y axis between y0..y1, tooth centres at
    phase + k*360/teeth, optional hub (od, length beyond y1 or before y0 if negative).
    chk = root cylinder, so a meshing pair never 'interferes' at the teeth."""
    rp = module * teeth / 2.0
    rr = rp - 1.25 * module
    ya, yb = sorted((y0, y1))
    pts = [V(x, ya, z) for (x, z) in _involute_profile(module, teeth, phase)]
    g = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, yb - ya, 0))
    chk = _ycyl(rr, y0, y1)
    if hub:
        hod, hl = hub
        ha, hb = sorted((y1, y1 + hl)) if hl > 0 else sorted((y0, y0 + hl))
        g = g.fuse(_ycyl(hod / 2, ha, hb))
        chk = chk.fuse(_ycyl(hod / 2, ha, hb))
    g = g.cut(_ycyl(bore / 2, min(y0, y1) - 20, max(y0, y1) + 20)).removeSplitter()
    chk = chk.cut(_ycyl(bore / 2, min(y0, y1) - 20, max(y0, y1) + 20))
    return g, chk, rp


def cable_clip(w=19.0, h=6.0, cable_d=4.0):          # Panduit ABMM-AT-D0: 19 mm (3/4") adhesive base
    """Adhesive-base cable tie mount with a cable tie (display only), base on z=0
    plane centred at origin, cable along X."""
    base = Part.makeBox(w, w, 1.2, V(-w / 2, -w / 2, 0))
    loop = Part.makeTorus(cable_d / 2 + 0.8, 0.6, V(0, 0, 1.2 + cable_d / 2), V(1, 0, 0))
    return base.fuse(loop), base


def _yhull2(x1, z1, r1, x2, z2, r2, ya, yb, clean=True):
    """Convex hull of two circles in the XZ plane, extruded ya..yb along Y (clean=False skips removeSplitter)."""
    dx, dz = x2 - x1, z2 - z1
    L = math.hypot(dx, dz)
    a = math.atan2(dz, dx)
    phi = math.asin(max(-1.0, min(1.0, (r1 - r2) / L)))
    n1 = (math.cos(a + math.pi / 2 - phi), math.sin(a + math.pi / 2 - phi))
    n2 = (math.cos(a - math.pi / 2 + phi), math.sin(a - math.pi / 2 + phi))
    poly = [V(x1 + r1 * n1[0], ya, z1 + r1 * n1[1]), V(x2 + r2 * n1[0], ya, z2 + r2 * n1[1]),
            V(x2 + r2 * n2[0], ya, z2 + r2 * n2[1]), V(x1 + r1 * n2[0], ya, z1 + r1 * n2[1])]
    s = Part.Face(Part.makePolygon(poly + [poly[0]])).extrude(V(0, yb - ya, 0))
    s = s.fuse(_ycyl(r1, ya, yb, x1, z1)).fuse(_ycyl(r2, ya, yb, x2, z2))
    return s.removeSplitter() if clean else s


def p_clip(y_face, direction, bundle_d=9.0, zc=9.0, w=7.0, t=0.8, screw_d=3.0):
    """Nylon-coated steel P-clip clamped under a screw head: tab around the screw axis
    (Y axis through the origin) lying on the face y_face, loop holding a cable bundle
    running along X at z = zc, sitting on the same face.  Returns (vis, chk, loop_centre_yz)."""
    sgn = direction
    ri = bundle_d / 2
    ro = ri + t
    y0, y1 = sorted((y_face, y_face + sgn * t))
    tab = _ring(3.5, screw_d / 2 + 0.2, y0, y1)
    tab = tab.fuse(Part.makeBox(w, t, zc - 3.5 - ro + 1.0, V(-w / 2, y0, 3.0)))
    yl = y_face + sgn * ro
    loop = Part.makeCylinder(ro, w, V(-w / 2, yl, zc), V(1, 0, 0)).cut(
        Part.makeCylinder(ri, w + 2, V(-w / 2 - 1, yl, zc), V(1, 0, 0)))
    c = tab.fuse(loop).removeSplitter()
    return c, c, (yl, zc)
