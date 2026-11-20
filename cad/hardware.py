# -*- coding: utf-8 -*-
"""
hardware.py - purchased-part geometry.

* Vendor STEP models (cad/vendor/...) for parts whose makers publish CAD:
  Feetech STS3215, DJI M2006 P36, DJI C610.  Loaded once, cached as BREP,
  re-oriented to a canonical frame (axis +Y, mounting face at y=0).
* ISO/DIN standard hardware generated at standard dimensions (same approach as
  the FreeCAD Fasteners workbench): ISO 4762 SHCS, ISO 7380 BHCS, ISO 10511
  nyloc, ISO 7379 shoulder screws, DIN 6799 e-clips, ISO 4026 set screws,
  ISO 8734 dowels, deep-groove bearings (rings + shields), M3 round standoffs.
* Catalogue parts without public CAD, modelled to catalogue drawings:
  HIWIN MGN9 rail + MGN9H block, GT2 20T pulley + 6 mm belt, standard-size
  AS5600 board, springs.

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
    M2006 : axis +Y; rear cap at y=0 (4 mm rear stub to y=-6.3), gearbox front face at y=42,
            D6 output shaft (flat + tapped centre hole) from y=42 to 58.5.
    C610  : as delivered, recentred on its PCB bounding box."""
    if name in _VCACHE:
        return _VCACHE[name].copy()
    cache = os.path.join(VENDOR, "cache_%s.brep" % name)
    if os.path.exists(cache):
        s = Part.Shape()
        s.read(cache)
    else:
        if name == "STS3215":
            raw = Part.Shape()
            raw.read(os.path.join(VENDOR, "feetech", "STS3215.stp"))
            # drop the two supplied horns (D19.95, on the output axis at vendor x=-25.5): modelled as their own parts
            keep = [x.copy() for x in raw.Solids
                    if not (abs(x.BoundBox.Center.x + 25.5) < 0.6 and abs(x.BoundBox.XLength - 19.95) < 0.3)]
            s = Part.makeCompound(keep)
            s.translate(V(25.5, -4.7, 0))             # output axis -> x=0, horn seat -> y=0 (canonical frame above)
        elif name == "M2006":
            raw = Part.Shape()
            raw.read(os.path.join(VENDOR, "dji", "RoboMaster_M2006_P36.STEP"))
            # motor axis is -Z at (x,y)=(-13.639, 15.257); keep only geometry within
            # r<=13.5 of that axis (drops the lead wires drawn across the sheet)
            ax = V(-13.638938799791816, 15.25716373873701, 0)
            keep = [sh for sh in raw.Shells if math.hypot(sh.BoundBox.Center.x - ax.x,
                                                          sh.BoundBox.Center.y - ax.y) < 13.5
                    and sh.BoundBox.XLength < 30 and sh.BoundBox.YLength < 30]
            s = Part.makeCompound(keep)
            # find shaft tip = max z of r3 cylinder faces -> output end
            zt = max(f.BoundBox.ZMax for f in s.Faces if f.Surface.TypeId == "Part::GeomCylinder"
                     and abs(f.Surface.Radius - 3.0) < 0.05)
            zb = s.BoundBox.ZMin
            # shoulder (mounting) face: top of r12 housing
            zf = max(f.BoundBox.ZMax for f in s.Faces if f.Surface.TypeId == "Part::GeomCylinder"
                     and abs(f.Surface.Radius - 12.0) < 0.3)
            s.translate(V(-ax.x, -ax.y, -zf))
            # map +Z (shaft) -> -Y
            s.rotate(V(0, 0, 0), V(1, 0, 0), 90)
            s = s.copy()
            _ = (zt, zb)
        elif name == "C610":
            raw = Part.Shape()
            raw.read(os.path.join(VENDOR, "dji", "RoboMaster_C610.STEP"))
            sol = sorted(raw.Solids, key=lambda x: -x.Volume)
            # ESC body spans y -33..18.5 in the vendor file; longer solids are the leads
            body = [x for x in sol if x.BoundBox.YMin > -33.0 and x.BoundBox.YMax < 18.5]
            s = Part.makeCompound(body)
            c = s.BoundBox.Center
            s.translate(V(-c.x, -c.y, -s.BoundBox.ZMin))
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


# ------------------------------------------------------- GT2 pulley and belt
def gt2_pulley(teeth, y0, y1, bore, flange_d=None, flange_t=1.0):
    """GT2 pulley body (toothed) between y0..y1 with flanges flange_t each side."""
    pd = teeth * 2.0 / math.pi
    od = pd - 0.508
    rr = od / 2 - 0.75                                 # root radius
    body = _ycyl(od / 2, y0 + flange_t, y1 - flange_t)
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        body = body.cut(_ycyl(0.55, y0 + flange_t - 0.1, y1 - flange_t + 0.1, (od / 2 + 0.05) * math.cos(a), (od / 2 + 0.05) * math.sin(a)))
    fd = flange_d or od + 3
    body = body.fuse(_ycyl(fd / 2, y0, y0 + flange_t)).fuse(_ycyl(fd / 2, y1 - flange_t, y1))
    body = body.cut(_ycyl(bore / 2, y0 - 1, y1 + 1))
    return body, _ring(fd / 2, bore / 2, y0, y1), pd


def gt2_belt(L, y0, y1, pd):
    """Closed belt loop around two pulleys centred at x=0 and x=L (XZ plane)."""
    t = 1.38
    rp = pd / 2

    def stadium(r):
        f = Part.makeBox(L, y1 - y0, 2 * r, V(0, y0, -r))
        f = f.fuse(_ycyl(r, y0, y1)).fuse(_ycyl(r, y0, y1, L, 0))
        return f
    b = stadium(rp - 0.254 + t).cut(stadium(rp - 0.254))     # belt land sits on pulley OD
    return b, b


# ------------------------------------------------------- MGN9 rail / block
MGN9 = dict(W_R=9.0, H_R=6.5, P=20.0, E=7.5, hole_d=3.5, cb_d=6.0,
            W=20.0, L=39.9, L1=26.8, H=10.0, H1=2.0, C=15.0, B=15.0, K=10.0)


def mgn9_rail(y0, y1, x0, z0):
    """Rail along Y from y0..y1, base centred at x0 on plane z0."""
    m = MGN9
    r = Part.makeBox(m["W_R"], y1 - y0, m["H_R"], V(x0 - m["W_R"] / 2, y0, z0))
    for s in (-1, 1):   # ball grooves
        r = r.cut(Part.makeCylinder(1.0, y1 - y0 + 2, V(x0 + s * m["W_R"] / 2, y0 - 1, z0 + 4.3), V(0, 1, 0)))
    n = int((y1 - y0 - 2 * m["E"]) // m["P"]) + 1
    yy = y0 + ((y1 - y0) - (n - 1) * m["P"]) / 2
    holes = []
    for i in range(n):
        y = yy + i * m["P"]
        holes.append(y)
        r = r.cut(Part.makeCylinder(m["hole_d"] / 2, m["H_R"] + 2, V(x0, y, z0 - 1)))
        r = r.cut(Part.makeCylinder(m["cb_d"] / 2, 3.5, V(x0, y, z0 + m["H_R"] - 3.5)))
    return r, r, holes


def mgn9h_block(yc, x0, z0):
    """MGN9H block centred at y=yc on rail with base plane z0 (rail bottom)."""
    m = MGN9
    zb = z0 + m["H1"]
    zt = z0 + m["H"]
    body = Part.makeBox(m["W"], m["L1"], zt - zb, V(x0 - m["W"] / 2, yc - m["L1"] / 2, zb))
    for s in (-1, 1):   # end seals / caps
        y_cap = yc + s * m["L1"] / 2
        cap = Part.makeBox(m["W"] - 1.0, (m["L"] - m["L1"]) / 2, zt - zb - 0.8,
                           V(x0 - m["W"] / 2 + 0.5, min(y_cap, y_cap + s * (m["L"] - m["L1"]) / 2), zb + 0.4))
        body = body.fuse(cap)
    chan = Part.makeBox(m["W_R"] + 0.6, m["L"] + 2, m["H_R"] + 0.3 - m["H1"],
                        V(x0 - m["W_R"] / 2 - 0.3, yc - m["L"] / 2 - 1, zb - 0.01))
    body = body.cut(chan)
    holes = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            hx, hy = x0 + sx * m["B"] / 2, yc + sy * m["C"] / 2
            holes.append((hx, hy))
            body = body.cut(Part.makeCylinder(1.25, 3.5, V(hx, hy, zt - 3.5)))
    chk = Part.makeBox(m["W"], m["L"], zt - zb, V(x0 - m["W"] / 2, yc - m["L"] / 2, zb)).cut(chan)
    for (hx, hy) in holes:
        chk = chk.cut(Part.makeCylinder(1.25, 3.5, V(hx, hy, zt - 3.5)))
    return body, chk, holes


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


# ------------------------------------------------- gripper linear drive parts
def set_screw(d, L, y_face, direction):
    """ISO 4026 flat-point set screw (hex socket) on the Y axis, outer face at y_face,
    extending 'direction'.  Used for collars, gear hubs and the wrist coupler."""
    y0, y1 = sorted((y_face, y_face + direction * L))
    s = _ycyl(0.45 * d, y0, y1)
    sock = _hexprism(0.5 * d, (y_face - 0.01) if direction > 0 else (y_face - 0.6 * d),
                     (y_face + 0.6 * d) if direction > 0 else (y_face + 0.01))
    return s.cut(sock), s


def leadscrew(y0, y1, thread_spans, d=8.0, lead=2.0):
    """Trapezoidal lead screw (e.g. Tr8x2 bidirectional) on the Y axis.  Threaded
    spans [(ya, yb, hand)] get a modelled helix-free thread look (rings at the
    lead); plain spans are ground D8 journals.  chk is a 0.02 mm undersize rod."""
    vis = _ycyl(d / 2, y0, y1)
    for (ya, yb, _hand) in thread_spans:
        n = int((yb - ya) / lead)
        for i in range(n):
            y = ya + (i + 0.5) * lead
            vis = vis.cut(_ring(d / 2 + 0.1, d / 2 - 0.55, y - 0.35, y + 0.35))
    return vis, _ycyl(d / 2 - 0.02, y0, y1)


def flange_nut_t8(y_flange_out, direction):
    """Tr8 brass flange nut: flange D22 x 3.5 (4x D3.5 on PCD16) with the D10.2
    body extending 'direction' from the flange inner face (total length 15)."""
    sgn = direction
    fa, fb = sorted((y_flange_out, y_flange_out + sgn * 3.5))
    ba, bb = sorted((y_flange_out + sgn * 3.5, y_flange_out + sgn * 15.0))
    n = _ycyl(11.0, fa, fb).fuse(_ycyl(5.1, ba, bb))
    holes = []
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, z = 8.0 * math.cos(a), 8.0 * math.sin(a)
        holes.append((x, z))
        n = n.cut(_ycyl(1.75, fa - 1, fb + 1, x, z))
    n = n.cut(_ycyl(4.05, min(fa, ba) - 1, max(fb, bb) + 1))
    return n, n, holes


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


def shaft_collar(d, od, w, y0, direction):
    """Set-screw shaft collar (e.g. Misumi PSCS) on the Y axis, radial M3 tapped."""
    ya, yb = sorted((y0, y0 + direction * w))
    c = _ring(od / 2, d / 2, ya, yb)
    ym = (ya + yb) / 2
    c = c.cut(Part.makeCylinder(1.7 if d >= 8 else 1.4, od, V(0, ym, d / 2 - 0.5), V(0, 0, 1)))   # M4 set screw on D8 (Stafford)
    return c, c


def cable_clip(w=19.0, h=6.0, cable_d=4.0):          # Panduit ABMM-AT-D0: 19 mm (3/4") adhesive base
    """Adhesive-base cable tie mount with a cable tie (display only), base on z=0
    plane centred at origin, cable along X."""
    base = Part.makeBox(w, w, 1.2, V(-w / 2, -w / 2, 0))
    loop = Part.makeTorus(cable_d / 2 + 0.8, 0.6, V(0, 0, 1.2 + cable_d / 2), V(1, 0, 0))
    return base.fuse(loop), base


def _yhull2(x1, z1, r1, x2, z2, r2, ya, yb):
    """Convex hull of two circles in the XZ plane, extruded ya..yb along Y."""
    dx, dz = x2 - x1, z2 - z1
    L = math.hypot(dx, dz)
    a = math.atan2(dz, dx)
    phi = math.asin(max(-1.0, min(1.0, (r1 - r2) / L)))
    n1 = (math.cos(a + math.pi / 2 - phi), math.sin(a + math.pi / 2 - phi))
    n2 = (math.cos(a - math.pi / 2 + phi), math.sin(a - math.pi / 2 + phi))
    poly = [V(x1 + r1 * n1[0], ya, z1 + r1 * n1[1]), V(x2 + r2 * n1[0], ya, z2 + r2 * n1[1]),
            V(x2 + r2 * n2[0], ya, z2 + r2 * n2[1]), V(x1 + r1 * n2[0], ya, z1 + r1 * n2[1])]
    s = Part.Face(Part.makePolygon(poly + [poly[0]])).extrude(V(0, yb - ya, 0))
    return s.fuse(_ycyl(r1, ya, yb, x1, z1)).fuse(_ycyl(r2, ya, yb, x2, z2)).removeSplitter()


CT_SPRING = dict(pn="9293K337", load_N=21.9, width=15.9, coil_od=28.6, coil_id=21.8, length=610.0)


def ct_spring_motor(y_back, direction, phi_deg=90.0, out_drum_d=20.0, arbor_clear=9.0, wall=1.5,
                    tabs=((13.5, -22.0), (-13.5, -22.0)), split=False):
    """Two-drum constant-torque spring motor (NEG'ATOR principle) built around a stock constant-force
    strip (McMaster 9293K337: 21.9 N, 15.9 mm wide, 610 mm): the strip is stored on a free drum and
    back-wound onto the output drum on the screw axis, torque = F * r_out = 21.9 N * 10 mm = 0.22 N*m,
    ~9.7 turns.  Housing: hull of the output drum (on the Y axis) and the storage drum at 'phi_deg'
    (in XZ, 0 = +X, 90 = +Z), back wall at y_back, body extending 'direction'.
    Returns (vis, chk, tab_xz)."""
    sgn = direction
    w = CT_SPRING["width"] + 2 * wall + 0.6
    ya, yb = sorted((y_back, y_back + sgn * w))
    sep = out_drum_d / 2 + CT_SPRING["coil_od"] / 2 + 1.5
    sx, sz = sep * math.cos(math.radians(phi_deg)), sep * math.sin(math.radians(phi_deg))
    r_out, r_st = out_drum_d / 2 + 2.0, CT_SPRING["coil_od"] / 2 + 1.5
    outer = _yhull2(0, 0, r_out + wall, sx, sz, r_st + wall, ya, yb)
    inner = _yhull2(0, 0, r_out, sx, sz, r_st, ya + wall, yb - wall)
    shell = outer.cut(inner)
    back_y = (ya - 1, ya + wall + 0.1) if sgn > 0 else (yb - wall - 0.1, yb + 1)
    shell = shell.cut(_ycyl(arbor_clear, *back_y))
    for (x, z) in tabs:                                   # same mounting tabs as before (end block unchanged)
        t = _ycyl(4.0, ya, ya + 2.5, x, z) if sgn > 0 else _ycyl(4.0, yb - 2.5, yb, x, z)
        t = t.fuse(Part.makeBox(8, 2.5, 8, V(x - 4, (ya if sgn > 0 else yb - 2.5), z)))
        y0_, y1_ = (ya, ya + 2.5) if sgn > 0 else (yb - 2.5, yb)
        t = t.fuse(_yhull2(x, z, 3.0, x * 0.45, z * 0.45, 3.0, y0_, y1_))   # web: tab joined to the back wall (was 3.4 mm adrift)
        shell = shell.fuse(t).cut(inner).cut(_ycyl(arbor_clear, *back_y)).cut(_ycyl(1.65, ya - 1, yb + 1, x, z))
    ym0, ym1 = ya + wall + 0.3, yb - wall - 0.3
    # output drum on the D8 journal + D16 hub through the back-wall opening, bearing on the 688 shim:
    # it replaces the shaft collar there (axial retention by its M3 set screw)
    hub = _ycyl(8.0, ym1, yb) if sgn < 0 else _ycyl(8.0, ya, ym0)
    ymid = (ym0 + ym1) / 2
    drum = _ycyl(out_drum_d / 2, ym0, ym1).fuse(hub).cut(_ycyl(4.0, ya - 1, yb + 1))
    drum = drum.cut(Part.makeCylinder(1.4, out_drum_d, V(0, ymid, 0), V(0, 0, 1)))       # M3 tapped (modelled r1.4 as the collars), set screw on the journal
    pin = _ycyl(1.5, ya + (yb - ya - 20.0) / 2, yb - (yb - ya - 20.0) / 2, sx, sz)        # ISO 8734 3x20 dowel axle
    shell = shell.cut(_ycyl(1.5, ya - 1, yb + 1, sx, sz))
    coil = _ycyl(CT_SPRING["coil_od"] / 2, ym0, ym1, sx, sz).cut(_ycyl(CT_SPRING["coil_id"] / 2, ym0 - 1, ym1 + 1, sx, sz))
    wrap = _ycyl(out_drum_d / 2 + 0.6, ym0, ym1).cut(_ycyl(out_drum_d / 2, ym0 - 1, ym1 + 1))
    if split:
        return dict(housing=shell, drum=drum, pin=pin, strip=coil.fuse(wrap), tabs=list(tabs), pin_len=yb - ya,
                    hub_y=ymid)
    vis = shell.fuse(drum).fuse(pin).fuse(coil).fuse(wrap)
    chk = outer.cut(_ycyl(arbor_clear, ya - 1, yb + 1))
    for (x, z) in tabs:
        tt = _ycyl(4.0, ya, ya + 2.5, x, z) if sgn > 0 else _ycyl(4.0, yb - 2.5, yb, x, z)
        y0_, y1_ = (ya, ya + 2.5) if sgn > 0 else (yb - 2.5, yb)
        tt = tt.fuse(_yhull2(x, z, 3.0, x * 0.45, z * 0.45, 3.0, y0_, y1_))
        chk = chk.fuse(tt.fuse(Part.makeBox(8, 2.5, 8, V(x - 4, (ya if sgn > 0 else yb - 2.5), z)))).cut(_ycyl(1.65, ya - 1, yb + 1, x, z))
    return vis, chk, list(tabs)


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
