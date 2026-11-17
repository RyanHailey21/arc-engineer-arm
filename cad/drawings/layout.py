# -*- coding: utf-8 -*-
"""
Overlap-free annotation layout for TechDraw pages, measured on TechDraw's own Qt scene
(TechDrawGui.getSceneForPage): every view, dimension, balloon and rich annotation is a
QGIV group whose data(1) is the FreeCAD object name; their rendered rectangles are exact.

auto_layout(doc, page) - fixed obstacles: view geometry, template title/tolerance blocks,
outside of the drawing frame.  Movable: dimension labels, balloons (datums, FCFs, hole
callouts), rich annotations.  Each movable that collides is moved to the nearest free spot
(spiral search); leaders/extension lines follow automatically.  Returns a report; the
page is re-measured after moving, and remaining collisions are listed.
Scene units: 0.1 mm, Y down  ->  page mm: x/10, -y/10.
"""
import math
import re
import time

import FreeCAD as App
import FreeCADGui as Gui
import Part

FRAME = (21.0, 21.0, 410.0, 258.0)                 # inner drawing frame, page mm (x0, y0, x1, y1), Y up
TEMPLATE = [(194.0, 19.0, 412.0, 70.5)]            # tolerance block + title block
GAP = 2.0                                          # min clearance between labels (mm)
WHY = {}                                           # rejection reason counters (debug)


def _why(r):
    WHY[r] = WHY.get(r, 0) + 1
    return False


def _scene(page):
    import TechDrawGui
    return TechDrawGui.getSceneForPage(page)


def _mm(r):
    return (r.x() / 10.0, -(r.y() + r.height()) / 10.0, (r.x() + r.width()) / 10.0, -r.y() / 10.0)


def _inter(a, b, pad=0.0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def _union(rs):
    rs = [r for r in rs if r[2] - r[0] > 1e-6 or r[3] - r[1] > 1e-6]
    if not rs:
        return None
    return (min(r[0] for r in rs), min(r[1] for r in rs), max(r[2] for r in rs), max(r[3] for r in rs))


def _seg_x(a, b, c, d):
    """Proper intersection of segments ab and cd (touching endpoints do not count)."""
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2, d3, d4 = o(c, d, a), o(c, d, b), o(a, b, c), o(a, b, d)
    return d1 * d2 < -1e-9 and d3 * d4 < -1e-9


def _pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _seg_d(a, b, c, d):
    if _seg_x(a, b, c, d):
        return 0.0
    return min(_pt_seg(a, c, d), _pt_seg(b, c, d), _pt_seg(c, a, b), _pt_seg(d, a, b))


def _conflict(a, b, c, d, gap=0.8):
    """Leader ab vs line cd: crossing, or running closer than gap (collinear overlap).
    Shared endpoints (same anchor) are ignored."""
    if min(math.hypot(a[0] - c[0], a[1] - c[1]), math.hypot(a[0] - d[0], a[1] - d[1])) < 1e-3:
        return False
    return _seg_d(a, b, c, d) < gap


def _seg_box(a, b, box, shrink=0.4):
    x0, y0, x1, y1 = box[0] + shrink, box[1] + shrink, box[2] - shrink, box[3] - shrink
    if x1 <= x0 or y1 <= y0:
        return False
    if x0 <= a[0] <= x1 and y0 <= a[1] <= y1 or x0 <= b[0] <= x1 and y0 <= b[1] <= y1:
        return True
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    return any(_seg_x(a, b, e0, e1) for e0, e1 in edges)


def _near(box, p):
    return (min(max(p[0], box[0]), box[2]), min(max(p[1], box[1]), box[3]))


def _segments(item):
    """Line segments (page mm) of a QGraphicsPathItem."""
    out = []
    try:
        path = item.path()
        pts = []
        for i in range(path.elementCount()):
            e = path.elementAt(i)
            q = item.mapToScene(e.x, e.y)
            pt = (q.x() / 10.0, -q.y() / 10.0)
            if e.isMoveTo():
                pts = [pt]
            else:
                if pts:
                    out.append((pts[-1], pt))
                pts.append(pt)
    except Exception:
        pass
    return out


def _origin(obj):
    """Balloon leader anchor in page mm."""
    try:
        cx, cy = _view_centre(obj.SourceView)
        s_ = _view_scale(obj)
        return (cx + float(obj.OriginX) * s_, cy + float(obj.OriginY) * s_)
    except Exception:
        return None


def measure(doc, page):
    """{name: dict(kind, box)}: box = label rect for annotations, geometry rect for views."""
    sc = _scene(page)
    out = {}
    for it in sc.items():
        try:
            if it.data(0) != "QGIV":
                continue
            name = it.data(1)
        except Exception:
            continue
        obj = doc.getObject(name) if name else None
        if obj is None:
            continue
        t = obj.TypeId
        kids = it.childItems()
        if t in ("TechDraw::DrawViewDimension", "TechDraw::DrawViewBalloon"):
            lab = [k for k in kids if k.zValue() >= 110 and type(k).__name__ == "QGraphicsObject"]
            box = _union([_mm(k.sceneBoundingRect()) for k in lab]) if lab else None
            kind = "dim" if "Dimension" in t else "balloon"
            if kind == "balloon" and box:
                # frame-inclusive (ported back from the freecad-mcp copy): the bubble frame (datum box, FCF
                # frame) is a z=111 path item ~1.8 mm larger than the text - a leader clipping the frame
                # but not the text was invisible to the checker
                mx, my = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                shp = [_mm(k.sceneBoundingRect()) for k in kids
                       if type(k).__name__ == "QGraphicsPathItem" and abs(k.zValue() - 111) < 0.5]
                box = _union([box] + [r for r in shp if r[0] <= mx <= r[2] and r[1] <= my <= r[3]])
                if getattr(obj, "BubbleShape", "") == "None" and obj.Label.startswith(("Call_", "Prof_")):
                    box = (box[0] - 4.0, box[1], box[2] + 4.0, box[3])   # the landing line (shoulder) is part
                if obj.Label.startswith("Datum_") and re.search(r"_g\d+$", obj.Label):   # of the callout
                    o_ = _origin(obj)                 # attached datum owns its triangle up to the FCF edge
                    if o_ is not None:
                        box = _union([box, (min(box[0], o_[0]), box[1], max(box[2], o_[0]), box[3])])
            segs, lsegs = [], []
            if kind == "dim":
                for k in kids:
                    if type(k).__name__ == "QGraphicsPathItem":
                        segs += _segments(k)
            elif kind == "balloon" and box and obj.Label.startswith(("Call_", "Prof_")):
                for k in kids:                     # the leader TechDraw actually drew (callouts/profile only:
                                                   # FCF cells and datum triangles are not leaders)
                    if type(k).__name__ == "QGraphicsPathItem" and abs(k.zValue() - 111) > 0.5:
                        for a_, b_ in _segments(k):
                            if math.hypot(b_[0] - a_[0], b_[1] - a_[1]) > 0.8:
                                lsegs.append((a_, b_))
            if box:
                d_ = dict(kind=kind, box=box, obj=obj, segs=segs, lsegs=lsegs,
                          origin=_origin(obj) if kind == "balloon" else None)
                if kind == "balloon" and getattr(obj, "Anchors", ""):
                    try:
                        cx, cy = _view_centre(obj.SourceView)
                        s_ = _view_scale(obj)
                        d_["anchors"] = [(cx + float(a.split(",")[0]) * s_, cy + float(a.split(",")[1]) * s_)
                                         for a in obj.Anchors.split(";") if a]
                        d_["ar"], d_["vc"], d_["s"] = float(obj.AnchorR) * s_, (cx, cy), s_
                    except Exception:
                        pass
                out[name] = d_
            continue
        elif t == "TechDraw::DrawRichAnno":
            box = _mm(it.sceneBoundingRect())
            kind = "rich"
        elif t in ("TechDraw::DrawViewPart", "TechDraw::DrawViewSection", "TechDraw::DrawProjGroupItem"):
            geo = [_mm(k.sceneBoundingRect()) for k in kids if type(k).__name__ == "QGraphicsPathItem" and k.zValue() < 100]
            box = _union(geo)
            # stand-alone reference views (iso) may move; projection-group views stay aligned
            kind = "isoview" if (t == "TechDraw::DrawViewPart" and obj.Label.lower().startswith("iso")) else "view"
        else:
            continue
        if box:
            out[name] = dict(kind=kind, box=box, obj=obj)
    return out


def _view_scale(b):
    v = b.SourceView
    s = getattr(v, "Scale", 1.0)
    grp = None
    try:
        grp = next((o for o in v.InList if o.TypeId == "TechDraw::DrawProjGroup"), None) if v.TypeId == "TechDraw::DrawProjGroupItem" else None
    except Exception:
        grp = None
    if grp is not None and grp.TypeId == "TechDraw::DrawProjGroup":
        s = grp.Scale
    return float(s)


def _move(obj, kind, dx, dy):
    if kind == "balloon":
        s = _view_scale(obj)
        obj.X = float(obj.X) + dx / s
        obj.Y = float(obj.Y) + dy / s
        if obj.Label.startswith("FCF_g") or (obj.Label.startswith("Datum_") and re.search(r"_g\d+$", obj.Label)):
            # FCF / datum attached to an FCF or dimension: the anchor moves with it. A datum on a
            # feature (no group) keeps its triangle on the feature; only the boxed letter moves.
            obj.OriginX = float(obj.OriginX) + dx / s
            obj.OriginY = float(obj.OriginY) + dy / s
    elif kind == "isoview":
        obj.X = float(obj.X.Value if hasattr(obj.X, "Value") else obj.X) + dx
        obj.Y = float(obj.Y.Value if hasattr(obj.Y, "Value") else obj.Y) + dy
    else:                                           # dims + rich annos: page mm
        obj.X = float(obj.X.Value if hasattr(obj.X, "Value") else obj.X) + dx
        obj.Y = float(obj.Y.Value if hasattr(obj.Y, "Value") else obj.Y) + dy


def _leader(v, dx=0.0, dy=0.0):
    if v.get("origin") is None or v["kind"] != "balloon":
        return None
    b = v["box"]
    bb = (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)
    o = v["origin"]
    lab = v["obj"].Label
    if lab.startswith("FCF_g") or (lab.startswith("Datum_") and re.search(r"_g\d+$", lab)):
        return None                                  # attached datum symbols / FCFs: no free leader
    if lab.startswith("Datum_"):                     # datum on a feature: straight leader to the box
        return (o, (min(max(o[0], bb[0]), bb[2]), min(max(o[1], bb[1]), bb[3])))
    return (o, _kink_end(v, bb, o))


def _kink_end(v, bb, o):
    """End of the horizontal shoulder TechDraw draws from the label side nearer the anchor (Y14.5 4.4.4)."""
    try:
        kl = float(v["obj"].KinkLength)
    except Exception:
        kl = 0.0
    ym = (bb[1] + bb[3]) / 2
    if o[0] < (bb[0] + bb[2]) / 2:
        return (bb[0] - kl, ym)
    return (bb[2] + kl, ym)


def _leader_opts(v, dx=0.0, dy=0.0):
    """Candidate leaders: any instance of the hole pattern, attached on the rim facing the label."""
    if v["kind"] != "balloon" or v["obj"].Label.startswith(("Datum_", "FCF_g")):
        return []
    b = v["box"]
    bb = (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)
    if not v.get("anchors"):
        return [] if v.get("origin") is None else [(v["origin"], _kink_end(v, bb, v["origin"]))]
    out = []
    for a in v["anchors"]:
        e = _kink_end(v, bb, a)
        L = math.hypot(e[0] - a[0], e[1] - a[1])
        if L < 1e-6:
            continue
        o = (a[0] + (e[0] - a[0]) / L * v["ar"], a[1] + (e[1] - a[1]) / L * v["ar"])   # radial (4.4.4.2)
        out.append((o, _kink_end(v, bb, o)))
    out.sort(key=lambda l: math.hypot(l[1][0] - l[0][0], l[1][1] - l[0][1]))
    return out


def _set_origin(v, o):
    cx, cy = v["vc"]
    v["obj"].OriginX = (o[0] - cx) / v["s"]
    v["obj"].OriginY = (o[1] - cy) / v["s"]


def _refresh(doc, n=4):
    doc.recompute()
    for _ in range(n):
        Gui.updateGui()
        time.sleep(0.15)



def _obstacles(items):
    """Views (by object name) and every callout target hole (page centre, radius) on the sheet."""
    views = {v["obj"].Name: v["box"] for v in items.values() if v["kind"] in ("view", "isoview")}
    holes = []
    for v in items.values():
        if v.get("anchors") and v.get("ar", 0) > 0:
            holes += [(a, v["ar"]) for a in v["anchors"]]
    return views, holes


def _leader_hits(ld, src_view, views, holes):
    """A leader may cross only its own view, and may touch only its own target hole."""
    o, e = ld
    for nm, b in views.items():
        if nm != src_view and _seg_box(o, e, b, 0.6):
            return "leader through view " + nm
    for c, r in holes:
        if math.hypot(c[0] - o[0], c[1] - o[1]) <= r + 0.5:
            continue                                 # this is the leader's own target
        if _pt_seg(c, o, e) < r + 0.4:
            return "leader through a hole"
    return None


def _src(v):
    try:
        return v["obj"].SourceView.Name
    except Exception:
        return None


def _same_group(v, w):
    """Callout / FCF / attached datum of ONE group abut by design (Y14.5 Fig 6-30, 3.3.3)."""
    m1 = re.search(r"_g(\d+)$", v["obj"].Label)
    m2 = re.search(r"_g(\d+)$", w["obj"].Label)
    return bool(m1 and m2 and m1.group(1) == m2.group(1))


def collisions(items):
    fixed = [v["box"] for v in items.values() if v["kind"] == "view"] + TEMPLATE
    mov = [(k, v) for k, v in items.items() if v["kind"] != "view"]
    bad = []
    for i, (k, v) in enumerate(mov):
        b = v["box"]
        if b[0] < FRAME[0] or b[1] < FRAME[1] or b[2] > FRAME[2] or b[3] > FRAME[3]:
            bad.append((k, "outside frame"))
        for f in fixed:
            if _inter(b, f, -0.3):
                bad.append((k, "on view/template"))
                break
        for k2, v2 in mov[i + 1:]:
            if _inter(b, v2["box"], -0.3) and not _same_group(v, v2):
                bad.append((k, "on " + k2))
    # leaders: through other labels, across dimension/extension lines, across other leaders
    lds = [(k, _leader(v)) for k, v in mov]
    lds = [(k, l) for k, l in lds if l is not None]
    segs = [(k, sg) for k, v in items.items() for sg in v.get("segs", [])]
    views_, holes_ = _obstacles(items)
    for k, (a0, a1) in lds:
        why_ = _leader_hits((a0, a1), _src(items[k]), views_, holes_)
        if why_:
            bad.append((k, why_))
        for k2, v2 in mov:
            if k2 != k and _seg_box(a0, a1, v2["box"], 0.4 if _same_group(items[k], v2) else -0.8):
                bad.append((k, "leader through " + k2))
        L_ = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
        t_ = min(1.0, 1.0 / L_) if L_ > 1e-9 else 1.0
        a0t = (a0[0] + (a1[0] - a0[0]) * t_, a0[1] + (a1[1] - a0[1]) * t_)   # the leader STARTS on the
        for k2, (s0, s1) in segs:                                            # feature, which may be collinear
            if t_ < 1.0 and _conflict(a0t, a1, s0, s1):                      # with an extension line: test
                bad.append((k, "leader crosses " + k2))                      # from 1 mm out
                break
    # the DRAWN leaders (scene geometry): through any other label, own-group FCF included, across dimension
    # lines and across other drawn leaders - catches what the leader model above cannot
    def _trim(sg, o):                                # a leader ENDS on its feature: an extension line starting
        if o is None:                                # at the same corner only touches it there - test from 1 mm off
            return sg
        a_, b_ = sg
        L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        if L < 2.0:
            return sg
        if math.hypot(a_[0] - o[0], a_[1] - o[1]) < 1.0:
            a_ = (a_[0] + (b_[0] - a_[0]) / L, a_[1] + (b_[1] - a_[1]) / L)
        if math.hypot(b_[0] - o[0], b_[1] - o[1]) < 1.0:
            b_ = (b_[0] - (b_[0] - a_[0]) / L, b_[1] - (b_[1] - a_[1]) / L)
        return (a_, b_)
    drawn = [(k, _trim(sg, v.get("origin"))) for k, v in mov for sg in v.get("lsegs", [])]
    for k, (a0, a1) in drawn:
        for k2, v2 in mov:
            if k2 != k and _seg_box(a0, a1, v2["box"], 0.4):
                bad.append((k, "drawn leader through " + k2))
                break
        for k2, (s0, s1) in segs:
            if _conflict(a0, a1, s0, s1):
                bad.append((k, "drawn leader on " + k2))
                break
    for i, (k, (a0, a1)) in enumerate(drawn):
        for k2, (b0, b1) in drawn[i + 1:]:
            if k2 != k and _seg_x(a0, a1, b0, b1):
                bad.append((k, "drawn leader crosses " + k2))
    for i, (k, (a0, a1)) in enumerate(lds):
        for k2, (b0, b1) in lds[i + 1:]:
            if _conflict(a0, a1, b0, b1, gap=2.0):
                bad.append((k, "leader crosses leader " + k2))
    return bad


def _units(items, order="default"):
    """Movable units: annotations sharing a '_g<i>' label suffix move together."""
    groups, units = {}, []
    for k, v in items.items():
        if v["kind"] == "view":
            continue
        m = re.search(r"_g(\d+)$", v["obj"].Label)
        if m:
            groups.setdefault(m.group(1), []).append((k, v))
        else:
            units.append([(k, v)])
    units += list(groups.values())
    prio = {"isoview": -1, "dim": 0, "balloon": 1, "rich": 2}
    cx = lambda u: _union([v["box"] for _k, v in u])[0]
    cy = lambda u: -_union([v["box"] for _k, v in u])[3]
    sec = {"default": lambda u: 0, "x": cx, "-x": lambda u: -cx(u), "y": cy, "-y": lambda u: -cy(u)}[order]
    units.sort(key=lambda u: (min(prio[v["kind"]] for _k, v in u), sec(u)))
    return units


def snapshot(doc):
    snap = {}
    for o in doc.Objects:
        if o.TypeId in ("TechDraw::DrawViewBalloon", "TechDraw::DrawViewDimension", "TechDraw::DrawRichAnno") or                 (o.TypeId == "TechDraw::DrawViewPart" and o.Label.lower().startswith("iso")):
            v = {}
            for pn in ("X", "Y", "OriginX", "OriginY"):
                if hasattr(o, pn):
                    q = getattr(o, pn)
                    v[pn] = float(q.Value if hasattr(q, "Value") else q)
            snap[o.Name] = v
    return snap


def restore(doc, snap):
    for n, v in snap.items():
        o = doc.getObject(n)
        for pn, val in v.items():
            setattr(o, pn, val)
    _refresh(doc)


def best_layout(doc, page, orders=("default", "x", "-x", "y", "-y"), budget=150.0):
    """auto_layout with retries: other unit orders from the same start, keep the fewest collisions."""
    start = snapshot(doc)
    best = None
    tries = [(od, 3, 45.0) for od in orders] + [(od, 6, 90.0) for od in orders]   # 2nd round: wider search
    deadline = time.time() + budget                  # ceiling, not a target: a clean result returns at once
    for i_, (od, ps_, mr_) in enumerate(tries):
        if i_ and time.time() > deadline:
            break
        if i_:
            restore(doc, start)
        rep, _r = auto_layout(doc, page, passes=ps_, max_r=mr_, order=od, deadline=deadline)
        rem = collisions(measure(doc, page))
        if best is None or len(rem) < len(best[2]):
            best = (od, snapshot(doc), rem, rep)
        if not rem:
            break
    if best[1] is not None and (best[0] != od or rem):
        restore(doc, best[1])
    return best[3] + ["order %s" % best[0]], best[2]


def auto_layout(doc, page, passes=3, max_r=45.0, step=2.0, order="default", deadline=None):
    _refresh(doc)
    report = []
    for p in range(passes):
        items = measure(doc, page)
        fixed = [v["box"] for v in items.values() if v["kind"] == "view"] + TEMPLATE
        dimsegs = [sg for v in items.values() for sg in v.get("segs", [])]
        views_, holes_ = _obstacles(items)
        placed = []
        leaders = []                                  # (unit id, segment) of placed units
        moved = 0
        for unit in _units(items, order):
            boxes = [v["box"] for _k, v in unit]
            ub = _union(boxes)

            uid = id(unit)
            own_dims = {k for k, v in unit if v["kind"] == "dim"}
            other_dimsegs = [sg for k2, v2 in items.items() if k2 not in own_dims for sg in v2.get("segs", [])]

            chosen = {}

            def lead_ok(ld, own=(), v_=None):
                if v_ is not None and _leader_hits(ld, _src(v_), views_, holes_):
                    return _why("leader through view/hole")
                if any(_seg_box(ld[0], ld[1], q, -0.8) for q in placed):
                    return _why("leader through placed label")
                if any(_seg_box(ld[0], ld[1], q) for q in own):
                    return _why("leader through own group")
                if any(_conflict(ld[0], ld[1], s0, s1) for s0, s1 in other_dimsegs):
                    return _why("leader on dim line")
                if any(_conflict(ld[0], ld[1], s0, s1, gap=2.0) for _u, (s0, s1) in leaders):
                    return _why("leader on leader")
                return True

            def ok(dx, dy):
                chosen.clear()
                for k_, v in unit:                    # this unit's leaders: clear of labels, dim lines, leaders
                    opts = _leader_opts(v, dx, dy)
                    if not opts:
                        continue
                    own = [(v2["box"][0] + dx, v2["box"][1] + dy, v2["box"][2] + dx, v2["box"][3] + dy)
                           for k2, v2 in unit if k2 != k_]
                    pick = next((ld for ld in opts if lead_ok(ld, own, v)), None)
                    if pick is None:
                        return _why("no leader option")
                    chosen[k_] = pick
                for b in boxes:
                    bb = (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)
                    if bb[0] < FRAME[0] or bb[1] < FRAME[1] or bb[2] > FRAME[2] or bb[3] > FRAME[3]:
                        return _why("outside frame")
                    if any(_inter(bb, f, GAP) for f in fixed):
                        return _why("label on view/template")
                    if any(_inter(bb, q, GAP) for q in placed):
                        return _why("label on label")
                    if any(_seg_box(s0, s1, bb, 0.0) for _u, (s0, s1) in leaders):
                        return _why("label on leader")      # label must not sit on an existing leader
                    bbg = (bb[0] - GAP, bb[1] - GAP, bb[2] + GAP, bb[3] + GAP)
                    if unit[0][1]["kind"] != "dim" and any(_seg_box(s0, s1, bbg, 0.0) for s0, s1 in other_dimsegs):
                        return _why("label on dim line")    # notes / callouts off dimension + extension lines
                return True
            def commit_leaders(dx, dy):
                ok(dx, dy)
                for k_, v in unit:
                    ld = chosen.get(k_) or (_leader_opts(v, dx, dy) or [None])[0]
                    if ld is not None:
                        leaders.append((uid, ld))
                        if v.get("anchors"):
                            _set_origin(v, ld[0])
            if ok(0.0, 0.0) and not any(_leader_opts(v) for _k, v in unit):
                commit_leaders(0.0, 0.0)
                placed += boxes
                if unit[0][1]["kind"] == "isoview":
                    fixed += boxes
                continue
            best = None
            r = step
            lim = 160.0 if unit[0][1]["kind"] in ("rich", "isoview") else (120.0 if any(_leader_opts(v) for _k, v in unit) else max_r)
            has_leader = any(_leader_opts(v) for _k, v in unit)

            def cost(dx, dy):
                c = 0.3 * math.hypot(dx, dy)
                for _k, v in unit:
                    o_ = _leader_opts(v, dx, dy)
                    if o_:
                        ld = o_[0]
                        c += math.hypot(ld[1][0] - ld[0][0], ld[1][1] - ld[0][1])
                        ang = abs(math.degrees(math.atan2(ld[1][1] - ld[0][1], ld[1][0] - ld[0][0]))) % 90.0
                        if ang < 15.0 or ang > 75.0:
                            c += 25.0                 # Y14.5 4.4.4: leaders inclined, not horizontal/vertical
                return c
            best_c = None
            if ok(0.0, 0.0):
                best, best_c = (0.0, 0.0), cost(0.0, 0.0)
            while r <= lim:
                if deadline is not None and time.time() > deadline and best is not None:
                    break                              # budget spent: keep the best spot found so far
                n = max(8, int(2 * math.pi * r / step))
                for i in range(n):
                    a = 2 * math.pi * i / n
                    dx, dy = r * math.cos(a), r * math.sin(a)
                    if (best_c is None or cost(dx, dy) < best_c) and ok(dx, dy):
                        best, best_c = (dx, dy), cost(dx, dy)
                if best is not None and (not has_leader or 0.3 * r > best_c):
                    break                              # farther rings cannot beat the current best
                r += step
            if best is None:
                # big blocks (notes): full-frame grid scan, nearest free spot wins
                cand = []
                for gx in range(int(FRAME[0]), int(FRAME[2]), 4):
                    for gy in range(int(FRAME[1]), int(FRAME[3]), 4):
                        dx, dy = gx - ub[0], gy - ub[1]
                        cand.append((dx * dx + dy * dy, dx, dy))
                best_c2 = None
                for _d, dx, dy in sorted(cand):
                    if deadline is not None and time.time() > deadline and best is not None:
                        break
                    c2 = cost(dx, dy)
                    if (best_c2 is None or c2 < best_c2) and ok(dx, dy):
                        best, best_c2 = (dx, dy), c2      # cheapest valid spot (short leaders), not merely nearest
            if best is None:
                commit_leaders(0.0, 0.0)
                placed += boxes
                report.append("pass %d: no free spot for %s" % (p, ", ".join(k for k, _v in unit)))
                continue
            commit_leaders(best[0], best[1])
            for k, v in unit:
                _move(v["obj"], v["kind"], best[0], best[1])
            placed += [(b[0] + best[0], b[1] + best[1], b[2] + best[0], b[3] + best[1]) for b in boxes]
            moved += 1
        report.append("pass %d: moved %d, leaders %d, dim segments %d" % (p, moved, len(leaders), len(dimsegs)))
        _refresh(doc)
        if moved == 0:
            break
    remaining = collisions(measure(doc, page))
    return report, remaining


def _view_centre(v):
    try:
        grp = next((o for o in v.InList if o.TypeId == "TechDraw::DrawProjGroup"), None) if v.TypeId == "TechDraw::DrawProjGroupItem" else None
    except Exception:
        grp = None
    f = lambda q: float(q.Value if hasattr(q, "Value") else q)
    if grp is not None and grp.TypeId == "TechDraw::DrawProjGroup":
        return f(grp.X) + f(v.X), f(grp.Y) + f(v.Y)
    return f(v.X), f(v.Y)


SNAP_FEATURE_DATUMS = False


def snap_datums(doc, page):
    """Datum feature symbols attached to a feature control frame: put the triangle exactly on
    the FCF's left edge (measured) and the boxed letter 9 mm to its left."""
    items = measure(doc, page)
    n = 0
    for k, v in items.items():
        o = v["obj"]
        if v["kind"] != "balloon" or not o.Label.startswith("Datum_"):
            continue
        m = re.search(r"_g(\d+)$", o.Label)
        if not m:
            continue
        fcf = [w for w in items.values() if w["kind"] == "balloon" and w["obj"].Label == "FCF_g" + m.group(1)]
        if not fcf:
            continue
        b = fcf[0]["box"]
        cx, cy = _view_centre(o.SourceView)
        s_ = _view_scale(o)
        ox, oy = (b[0] - cx) / s_, ((b[1] + b[3]) / 2 - cy) / s_
        o.OriginX, o.OriginY = ox, oy
        o.X, o.Y = ox - 9.0 / s_, oy
        n += 1
    # datum symbols on a feature (no group): triangle exactly on the nearest real edge of the view,
    # read from the view's CURRENT geometry (values captured before the last rescale can be stale)
    for o in ([] if not SNAP_FEATURE_DATUMS else doc.Objects):   # off: edge coords and origins differ in scale
        if o.TypeId != "TechDraw::DrawViewBalloon" or not o.Label.startswith("Datum_") or re.search(r"_g\d+$", o.Label):
            continue
        v = o.SourceView
        p = App.Vector(float(o.OriginX), float(o.OriginY), 0)
        best = None
        for i in range(2000):
            try:
                e = v.getEdgeByIndex(i)
            except Exception:
                break
            if e is None:
                break
            try:
                d_, pts, _info = e.distToShape(Part.Vertex(p))
            except Exception:
                continue
            if best is None or d_ < best[0]:
                best = (d_, pts[0][0])
        if best is not None and best[0] > 1e-3:
            dx_, dy_ = best[1].x - p.x, best[1].y - p.y
            o.OriginX, o.OriginY = best[1].x, best[1].y
            o.X, o.Y = float(o.X) + dx_, float(o.Y) + dy_
            n += 1
    _refresh(doc)
    return n


def _gid(lab):
    m = re.search(r"_g(\d+)$", lab)
    return m.group(1) if m else None


def repair_drawn(doc, page, max_rounds=4):
    """Fix what only the DRAWN geometry shows (TechDraw draws a callout leader from the end of its text, which
    the planning model approximates):
      1. a callout's leader through its own FCF -> slide the FCF (+ attached datum) away from the leader side;
      2. any other drawn-leader conflict -> try small moves of the whole group, re-measured, keep the best."""
    log_ = []
    for _rnd in range(max_rounds):
        items = measure(doc, page)
        bad = collisions(items)
        drawn = list(bad)                           # any conflict left after planning (drawn or modelled)
        if not drawn:
            break
        k, why = drawn[0]
        v = items[k]
        gid = _gid(v["obj"].Label)
        unit = [(k2, v2) for k2, v2 in items.items() if gid is not None and _gid(v2["obj"].Label) == gid
                and v2["kind"] in ("balloon", "rich")] or [(k, v)]
        tgt = why.split(" ")[-1]
        own_fcf = [(k2, v2) for k2, v2 in unit if k2 == tgt and v2["obj"].Label.startswith("FCF_g")]
        if own_fcf and v.get("lsegs"):
            cb, fb = v["box"], own_fcf[0][1]["box"]
            sx = v["lsegs"][0][0][0]                 # where the drawn leader leaves the callout
            right = sx > (cb[0] + cb[2]) / 2
            dx = ((cb[2] - 2.0) - fb[2]) if right else ((cb[0] + 2.0) - fb[0])
            if (right and dx < 0) or (not right and dx > 0):
                for k2, v2 in unit:
                    if k2 == tgt or v2["obj"].Label.startswith("Datum_"):
                        _move(v2["obj"], v2["kind"], dx, 0.0)
                _refresh(doc)
                log_.append("repair: %s slid %.1f mm off the leader of %s" % (tgt, dx, k))
                continue
        n0 = len(bad)
        start = snapshot(doc)
        prof = [(kk, vv) for kk, vv in ((k, v), (tgt, items.get(tgt))) if vv and vv["obj"].Label.startswith("Prof_")]
        if prof and prof[0][1].get("anchors"):      # the profile leader may land on ANY outline corner: try others
            kk, vv = prof[0]
            bestp = (n0, None)
            for ld in _leader_opts(vv)[:25]:
                restore(doc, start)
                _set_origin(vv, ld[0])
                _refresh(doc, 2)
                n = len(collisions(measure(doc, page)))
                if n < bestp[0]:
                    bestp = (n, ld[0])
                    if n == 0:
                        break
            restore(doc, start)
            if bestp[1] is not None:
                _set_origin(vv, bestp[1])
                _refresh(doc)
                log_.append("repair: profile leader re-anchored -> %d conflicts" % bestp[0])
                continue
        tv_ = items.get(tgt)                         # the other party of the conflict, as a movable unit
        tgid = _gid(tv_["obj"].Label) if tv_ else None
        tunit = ([(k2, v2) for k2, v2 in items.items() if tgid is not None and _gid(v2["obj"].Label) == tgid
                  and v2["kind"] in ("balloon", "rich")] or ([(tgt, tv_)] if tv_ and tv_["kind"] == "balloon" else []))
        def _movable(un):
            return [(k2, v2) for k2, v2 in un if v2["kind"] in ("balloon", "rich")
                    and not v2["obj"].Label.startswith("Notes") and v2["obj"].Name != "Notes"]
        unit, tunit = _movable(unit), _movable(tunit)
        best = (n0, None, None)
        for which, un in (("own", unit), ("other", tunit)):
            if not un:
                continue
            for dx, dy in [(a * st, b * st) for st in (4.0, 8.0, 12.0, 18.0, 26.0, 36.0) for a, b in
                           ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1))]:
                restore(doc, start)
                for k2, v2 in un:
                    _move(v2["obj"], v2["kind"], dx, dy)
                _refresh(doc, 2)
                n = len(collisions(measure(doc, page)))
                if n < best[0]:
                    best = (n, (dx, dy), un)
                    if n == 0:
                        break
            if best[0] == 0:
                break
        restore(doc, start)
        if best[1] is None:
            log_.append("repair: no better spot for %s (%s)" % (k, why))
            break
        for k2, v2 in best[2]:
            _move(v2["obj"], v2["kind"], *best[1])
        _refresh(doc)
        log_.append("repair: moved group of %s by %s -> %d conflicts" % (best[2][0][0], best[1], best[0]))
    return log_


def snap_allover(doc, page):
    """'ALL OVER' (Y14.5 11.3.1.5(b)) centred just beneath the profile FCF, measured after layout."""
    items = measure(doc, page)
    fcf_ = [v for v in items.values() if v["obj"].Label == "Prof_g99"]
    ao = [o for o in doc.Objects if o.Label == "AllOver_g99"]
    if not fcf_ or not ao:
        return False
    b = fcf_[0]["box"]
    hb = items[ao[0].Name]["box"] if ao[0].Name in items else None
    h = (hb[3] - hb[1]) if hb else 7.0              # the anno's box includes Qt document padding (~11 mm tall)
    ao[0].X, ao[0].Y = (b[0] + b[2]) / 2.0, b[1] - h / 2.0 - 4.5   # the glyphs sit at the TOP of the padded
                                                                   # box: 4.5 mm more keeps them off the frame
    _refresh(doc)
    return True


def views_outside_frame(doc, page):
    items = measure(doc, page)
    return [k for k, v in items.items() if v["kind"] in ("view", "isoview") and
            (v["box"][0] < FRAME[0] or v["box"][1] < FRAME[1] or v["box"][2] > FRAME[2] or v["box"][3] > FRAME[3])]
