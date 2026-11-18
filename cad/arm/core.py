# -*- coding: utf-8 -*-
"""Shared core of the arm model: frames and global parameters (K, Y, T), jaw/pad geometry shared by every
gripper, motor interface (DM), purchased-part catalogue (CAT), materials (MAT), the Part_ record and the
geometry helpers (box, ycyl, plate, at, to_z, ...).  Every other arm module star-imports this one.
"""


import math
import os
import FreeCAD as App
import Part
import hardware as H
import iface
import params

V = App.Vector

# ----------------------------------------------------------------- kinematics
_ARM = params.load("arm")            # params/arm.toml: kinematics, layer stack, plate thickness
K = dict(_ARM["K"])
T = _ARM["T"]
Y = dict(_ARM["Y"])
# ---- jaw pads (shared by every gripper variant): R50 donut arc + 90 deg pipe V-notch; 'jaw' = pad-arc gap at the TCP
_PADS = params.load("pads")          # params/pads.toml: shared by every gripper variant
PAD_R, NOTCH, WRAP = _PADS["PAD_R"], _PADS["NOTCH"], _PADS["WRAP"]
PIPE_R = _PADS["PIPE_OD"] / 2
O_PIPE = PIPE_R * math.sqrt(2) - NOTCH  # pad-face half gap when the V-notches hold the pipe
O_REF = O_PIPE         # jaw half-opening at which jaw bodies are modelled (pipe grip)
PIPE_JAW = 2 * O_PIPE  # 'jaw' value = gap between the arc-bottom pad faces at the TCP
GT2_T = _ARM["level_keeping"]["GT2_T"]          # rev A belt drive only (build_assembly.py)
ROD2_T = _ARM["level_keeping"]["ROD2_T"]
ROD2_W = _ARM["level_keeping"]["ROD2_W"]
UA_HUB_SCREWS = _ARM["j1_hub"]["UA_HUB_SCREWS"]
HUB_R = _ARM["j1_hub"]["HUB_R"]

# motor interface (from Damiao drawing + vendor STEP, model frame, angles atan2(z,x))
DM = params._tuples(dict(iface.load("dm_j4340__hub_tower")["DM"]))   # motor interface (vendor drawing)

# ------------------------------------------------------- purchased-part data
CAT = {k: dict(v) for k, v in params.data("catalogue").items()}   # data/catalogue.toml

MAT = dict(params.load("materials"))   # params/materials.toml (g/cm^3)


class Part_:
    def __init__(self, name, vis, chk, kind, src, color, note="", sub=None, check=True):
        self.name, self.vis, self.chk, self.kind, self.src, self.color = name, vis, chk, kind, src, color
        self.note, self.sub, self.check = note, sub, check
        self.shape = chk          # back-compat
        self.where = _builder_site()   # "arm/wrist.py:123 roll_hub_parts" - where this part is built (MAP.md)


def _builder_site():
    """First stack frame outside the Part_/P constructors and outside core helpers: the line that built the part."""
    import sys as _sys
    f = _sys._getframe(2)
    while f is not None:
        fn = f.f_code.co_filename.replace("\\", "/")
        if "/arm/" in fn and not (fn.endswith("/core.py") and f.f_code.co_name in ("P", "Part_", "__init__")):
            rel = fn[fn.rindex("/arm/") + 1:]
            return "%s:%d %s" % (rel, f.f_lineno, f.f_code.co_name)
        f = f.f_back
    return "?"


# ------------------------------------------------------------------ helpers
def u(deg, length=1.0):
    a = math.radians(deg)
    return (length * math.cos(a), length * math.sin(a))


def add(p, q, s=1.0):
    return (p[0] + s * q[0], p[1] + s * q[1])


def ycyl(x, z, y0, y1, r):
    y0, y1 = sorted((y0, y1))
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def ring(x, z, y0, y1, ro, ri):
    return ycyl(x, z, y0, y1, ro).cut(ycyl(x, z, min(y0, y1) - 1, max(y0, y1) + 1, ri))


def box(x0, y0, z0, x1, y1, z1):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def hexhole(af, x, z, y0, y1):
    s = H._hexprism(af, min(y0, y1), max(y0, y1))
    s.translate(V(x, 0, z))
    return s


def _hull2(x1, z1, r1, x2, z2, r2, y0, t):
    dx, dz = x2 - x1, z2 - z1
    L = math.hypot(dx, dz)
    a = math.atan2(dz, dx)
    phi = math.asin(max(-1.0, min(1.0, (r1 - r2) / L)))
    # outer tangents: normal n with (c2 - c1).n = r1 - r2  ->  angle a +- (pi/2 - phi)
    n1 = (math.cos(a + math.pi / 2 - phi), math.sin(a + math.pi / 2 - phi))
    n2 = (math.cos(a - math.pi / 2 + phi), math.sin(a - math.pi / 2 + phi))
    poly = [V(x1 + r1 * n1[0], y0, z1 + r1 * n1[1]), V(x2 + r2 * n1[0], y0, z2 + r2 * n1[1]),
            V(x2 + r2 * n2[0], y0, z2 + r2 * n2[1]), V(x1 + r1 * n2[0], y0, z1 + r1 * n2[1])]
    s = Part.Face(Part.makePolygon(poly + [poly[0]])).extrude(V(0, t, 0))
    return s.fuse(ycyl(x1, z1, y0, y0 + t, r1)).fuse(ycyl(x2, z2, y0, y0 + t, r2))


def _convex_hull(points):
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def plate(points_r, yc, holes=(), t=T, pockets=()):
    """Plate (normal Y) = true convex hull of circles [(x, z, r)], with holes
    [(x, z, r)] and rounded-slot pockets [((x,z,r),(x,z,r))]."""
    y0 = yc - t / 2
    pts = list(points_r)
    if len(pts) == 1:
        x, z, r = pts[0]
        s = ycyl(x, z, y0, y0 + t, r)
    elif len(pts) == 2:
        s = _hull2(*pts[0], *pts[1], y0, t)
    else:
        # sampled hull only decides WHICH circles are on the hull and in what (CCW) order; the outline
        # itself uses exact outer-tangent points (as _hull2) so the fused arcs meet the straight sides
        # tangentially - a polygon with vertices ON the circles leaves ~1e-5 mm sliver edges that
        # break meshing (FEA negative Jacobians) and DXF export.
        cloud, owner = [], {}
        for ci, (x, z, r) in enumerate(pts):
            for k in range(64):
                a = 2 * math.pi * k / 64
                q = (round(x + r * math.cos(a), 6), round(z + r * math.sin(a), 6))
                cloud.append(q)
                owner.setdefault(q, ci)
        order = []
        for q in _convex_hull(cloud):
            ci = owner[q]
            if not order or order[-1] != ci:
                order.append(ci)
        if len(order) > 1 and order[0] == order[-1]:
            order.pop()
        poly = []
        for k in range(len(order)):
            (x1, z1, r1), (x2, z2, r2) = pts[order[k]], pts[order[(k + 1) % len(order)]]
            dx, dz = x2 - x1, z2 - z1
            L = math.hypot(dx, dz)
            a = math.atan2(dz, dx)
            phi = math.asin(max(-1.0, min(1.0, (r1 - r2) / L)))
            n = (math.cos(a - math.pi / 2 + phi), math.sin(a - math.pi / 2 + phi))   # outward for a CCW hull
            poly += [V(x1 + r1 * n[0], y0, z1 + r1 * n[1]), V(x2 + r2 * n[0], y0, z2 + r2 * n[1])]
        clean = [poly[0]]
        for p_ in poly[1:]:
            if (p_ - clean[-1]).Length > 1e-6:
                clean.append(p_)
        if (clean[0] - clean[-1]).Length < 1e-6:
            clean.pop()
        s = Part.Face(Part.makePolygon(clean + [clean[0]])).extrude(V(0, t, 0))
        for (x, z, r) in pts:
            s = s.fuse(ycyl(x, z, y0, y0 + t, r))
    cuts = [ycyl(x, z, y0 - 1, y0 + t + 1, r) for (x, z, r) in holes]
    for (a, b) in pockets:
        cuts.append(_hull2(*a, *b, y0 - 1, t + 2))
    for c in cuts:
        s = s.cut(c)
    return s.removeSplitter()


def link_pockets(L, r0, r1, holes, web=6.0, min_r=3.0):
    """Rounded-slot lightening pockets along a tapered link between holes [(x, r)]:
    every pocket keeps 'web' to the plate edge and to each hole (or screw-head footprint)."""
    out = []
    hs = sorted(holes)
    k = (r1 - r0) / L
    rad = lambda x: r0 + k * x
    for (a, ra_h), (b, rb_h) in zip(hs[:-1], hs[1:]):
        xa = (a + ra_h + r0) / (1 - k)                 # xa - (rad(xa) - web) = a + ra_h + web
        xb = (b - rb_h - r0) / (1 + k)                 # xb + (rad(xb) - web) = b - rb_h - web
        if xb - xa < 12:
            continue
        ra, rb = rad(xa) - web, rad(xb) - web
        if min(ra, rb) < min_r:
            continue
        out.append(((xa, 0, ra), (xb, 0, rb)))
    return out


def fillet_z(shape, r):
    try:
        es = [e for e in shape.Edges if e.Curve.TypeId == "Part::GeomLine"
              and abs(abs(e.tangentAt(e.FirstParameter).z) - 1) < 1e-6]
        return shape.makeFillet(r, es) if es else shape
    except Exception:
        return shape


def fillet_y(shape, r):
    try:
        es = [e for e in shape.Edges if e.Curve.TypeId == "Part::GeomLine"
              and abs(abs(e.tangentAt(e.FirstParameter).y) - 1) < 1e-6]
        return shape.makeFillet(r, es) if es else shape
    except Exception:
        return shape


def at(pair, x=0.0, z=0.0, y=0.0):
    out = []
    for s in pair[:2]:
        s = s.copy()
        s.translate(V(x, y, z))
        out.append(s)
    return out


def to_z(pair, x, y, z):
    """Move a Y-axis built fastener to a +Z axis at (x, y, z)."""
    out = []
    for s in pair[:2]:
        s = s.copy()
        s.rotate(V(0, 0, 0), V(1, 0, 0), 90)       # +Y -> +Z
        s.translate(V(x, y, z))
        out.append(s)
    return out


def to_x(pair, x, y, z):
    """Move a Y-axis built item to the -X axis (Y -> -X) at (x, y, z)."""
    out = []
    for s in pair[:2]:
        s = s.copy()
        s.rotate(V(0, 0, 0), V(0, 0, 1), 90)
        s.translate(V(x, y, z))
        out.append(s)
    return out


def clip_at(x, z, y_face, sgn):
    """Cable-tie mount stuck on a Y-normal face at (x, y_face, z), pointing sgn*Y."""
    out = []
    for s_ in H.cable_clip()[:2]:
        s_ = s_.copy()
        s_.rotate(V(0, 0, 0), V(1, 0, 0), -90 * sgn)
        s_.translate(V(x, y_face, z))
        out.append(s_)
    return out


def P(name, pair, kind, src, color, note="", sub=None, check=True):
    return Part_(name, pair[0], pair[1], kind, src, color, note, sub, check)


def csk(d, L, y_face, direction):
    """ISO 10642 countersunk screw, head flush at y_face, shank in 'direction'."""
    dk = 2 * d
    k = (dk - d) / 2                         # 90 deg included head (ISO 10642); 0.6d gave 79.6 deg
    ya, yb = sorted((y_face, y_face + direction * k))
    r0, r1 = (dk / 2, d / 2) if direction > 0 else (d / 2, dk / 2)
    head = Part.makeCone(r0, r1, k, V(0, ya, 0), V(0, 1, 0))
    sa, sb = sorted((y_face, y_face + direction * L))
    s = head.fuse(H._ycyl(0.41 * d, sa, sb))
    return s, s


def _vprism(x, y_apex, z0, z1, depth=60.0):
    """90 deg V-notch prism, apex at (x, y_apex), opening towards -Y."""
    pts = [V(x, y_apex, z0), V(x + depth, y_apex - depth, z0), V(x - depth, y_apex - depth, z0)]
    return Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, z1 - z0))



# active gripper variant (GRIP=FOURBAR default, GRIP=SCREW = rev A); see arm/grippers/
GRIP = params.grip()      # $GRIP, else params/variant.toml
