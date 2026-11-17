# -*- coding: utf-8 -*-
"""
Manufacturing drawings (ASME Y14.5-2018 conventions) built with FreeCAD TechDraw.
Run INSIDE the FreeCAD GUI (TechDraw PDF export needs the GUI):
    g = {}; exec(open(r"<repo>/cad/drawings/make_drawings.py", encoding="utf-8").read(), g)
    doc, page = g["hub_j1"](); g["export"](doc, page, "ARC-101_J1_Output_Hub")

Uses what FreeCAD already provides (no hand-drawn symbology):
  * sheet: drawings/templates/ANSIB_Landscape_Y14.svg = FreeCAD's bundled ASME
    ANSIB_Landscape.svg (title block, third-angle symbol) plus an "unless otherwise
    specified" tolerance block whose lines are freecad:editable template fields
    (TOL_UNITS, TOL_LIN1, TOL_LIN2, TOL_ANGLE, TOL_FINISH, TOL_STANDARD);
  * datum feature symbols + feature control frames: native TechDraw balloons
    (Rectangle bubble, '|' compartments, filled-triangle end) as documented on
    wiki.freecad.org/TechDraw_Geometric_dimensioning_and_tolerancing;
  * basic dimensions: DrawViewDimension.TheoreticalExact (boxed);
  * bolt circles / clocking lines: TechDraw cosmetic circles and lines;
  * notes, captions: TechDraw rich-text annotations.
Coordinates for balloons/dimension labels: model mm from the view centre, Y up,
scaled with the view.  Review the TechDraw PDF export (not the SVG: third-party SVG
rasterisers shift the balloon text).
"""
import math
import os
import sys
import time

import FreeCAD as App
import FreeCADGui as Gui

HERE = r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "drawings", "out")
os.makedirs(OUT, exist_ok=True)
TPL = os.path.join(HERE, "drawings", "templates", "ANSIB_Landscape_Y14.svg")   # bundled ASME ANSI B + editable tolerance block
V = App.Vector

SYM = {"position": "\u2316", "flatness": "\u23e5", "perpendicularity": "\u27c2", "circularity": "\u25cb",
       "runout": "\u2197", "parallelism": "\u2225", "profile_surface": "\u2313"}
DIA, MMC, CBORE, DEPTH = "\u2300", "\u24c2", "\u2334", "\u21a7"

GENERAL_TOL = {"TOL_UNITS": "DIMENSIONS ARE IN MILLIMETERS",
               "TOL_LIN1": "LINEAR \u00b10.1",
               "TOL_LIN2": "HOLE \u2300 +0.1/0",
               "TOL_ANGLE": "ANGLES \u00b10.5\u00b0",
               "TOL_FINISH": "SURFACE ROUGHNESS Ra 3.2 \u00b5m MAX",
               "TOL_STANDARD": "INTERPRET PER ASME Y14.5-2018"}


# ------------------------------------------------------------- sheet
def new_sheet(name, title1, title2, title3, number, scale_txt, weight_txt, drawn="AI 2026-11-14", tol=None):
    if name in App.listDocuments():
        App.closeDocument(name)
    doc = App.newDocument(name)
    page = doc.addObject("TechDraw::DrawPage", "Page")
    tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    tpl.Template = TPL
    page.Template = tpl
    et = dict(tpl.EditableTexts)
    et.update({"CompanyName": "ARC S2 ENGINEER ARM", "CompanyAddress": "light_weight_arm / cad",
               "DrawingTitle1": title1, "DrawingTitle2": title2, "DrawingTitle3": title3,
               "drawing_number": number, "revision_index": "A", "DrawnBy": drawn,
               "CheckedBy": "PENDING", "Approved1": "PENDING", "Approved2": "PENDING", "scale": scale_txt,
               "Code": "", "Weight": weight_txt, "Sheet": "1 OF 1"})
    et.update(GENERAL_TOL)                      # tolerance block fields (override per part via tol=)
    et.update(tol or {})
    tpl.EditableTexts = et
    return doc, page


def rebind_dims(doc):
    """Re-point vertex dimensions at the vertices that are at their recorded positions now."""
    n = 0
    for d in doc.Objects:
        rp = getattr(d, "RefPts", "")
        if d.TypeId != "TechDraw::DrawViewDimension" or not rp:
            continue
        view = d.References2D[0][0]
        verts = []
        for i in range(4000):
            try:
                q = view.getVertexByIndex(i)
            except Exception:
                break
            if q is None:
                break
            verts.append((i, q.Point))
        new = []
        for t in rp.split(";"):
            x, y = (float(c) for c in t.split(","))
            hit = [i for i, p in verts if abs(p.x - x) < 1e-3 and abs(p.y - y) < 1e-3]
            if not hit:
                break
            new.append("Vertex%d" % hit[0])
        if len(new) == len(rp.split(";")):
            old = list(d.References2D[0][1])
            if old != new:
                d.References2D = [(view, tuple(new))] if isinstance(d.References2D[0][1], tuple) else [(view, r) for r in new]
                n += 1
    doc.recompute()
    return n


def export(doc, page, stem):
    for o in doc.Objects:                       # S1: views re-run HLR at their CURRENT scale before anything
        if o.TypeId in ("TechDraw::DrawProjGroupItem", "TechDraw::DrawViewPart"):   # is measured or exported
            o.touch()
    doc.recompute()
    wait_views(doc, [o for o in doc.Objects if o.TypeId in ("TechDraw::DrawProjGroupItem", "TechDraw::DrawViewPart")])
    import TechDrawGui
    Gui.ActiveDocument = Gui.getDocument(doc.Name)
    page.ViewObject.doubleClicked()             # template is only drawn while the page is open
    for _ in range(6):
        Gui.updateGui()
        time.sleep(0.3)
    import importlib
    if os.path.join(HERE, "drawings") not in sys.path:
        sys.path.insert(0, os.path.join(HERE, "drawings"))
    import layout
    importlib.reload(layout)
    layout._refresh(doc)
    rebind_dims(doc)
    layout._refresh(doc)
    layout.snap_datums(doc, page)                            # datum symbols onto their FCFs FIRST, so the
    layout.snap_allover(doc, page)                          # (ALL OVER under its FCF too, before layout)
    rep, remaining = layout.best_layout(doc, page)          # layout moves the finished group as one unit
    before_ = layout.snapshot(doc)
    n_before = len(layout.collisions(layout.measure(doc, page)))
    if layout.snap_allover(doc, page) and len(layout.collisions(layout.measure(doc, page))) > n_before:
        layout.restore(doc, before_)                        # re-snap only if it adds no conflict
    rep += layout.repair_drawn(doc, page)                   # conflicts only the drawn leaders reveal
    for k_, why_ in layout.collisions(layout.measure(doc, page)):   # a REFERENCE size still in a leader's way:
        nm_ = why_.split(" ")[-1]                           # drop it (REF is information only, Y14.5 4.4.6)
        o_ = doc.getObject(nm_)
        if o_ is not None and o_.TypeId == "TechDraw::DrawViewDimension" and str(o_.FormatSpec).startswith("("):
            rep.append("dropped reference dimension %s (blocked %s)" % (nm_, k_))
            doc.removeObject(nm_)
            layout._refresh(doc)
    remaining = layout.collisions(layout.measure(doc, page))
    with open(os.path.join(OUT, stem + "_layout.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(rep + ["REMAINING %d" % len(remaining)] + ["%s: %s" % r for r in remaining]) + "\n")
    pdf = os.path.join(OUT, stem + ".pdf")
    TechDrawGui.exportPageAsPdf(page, pdf)
    doc.saveAs(os.path.join(OUT, stem + ".FCStd"))
    return pdf


# ------------------------------------------------------------- view geometry lookup
def _edges(view):
    out, i = [], 0
    while True:
        try:
            e = view.getEdgeByIndex(i)
        except Exception:
            break
        if e is None:
            break
        out.append((i, e))
        i += 1
    return out


def find_circle(view, r, cx=None, cy=None, tol=0.05):
    for i, e in _edges(view):
        c = e.Curve
        if c.__class__.__name__ == "Circle" and abs(c.Radius - r) < tol:
            if cx is None or (abs(c.Center.x - cx) < 0.2 and abs(c.Center.y - cy) < 0.2):
                return "Edge%d" % i, c
    return None, None


def find_vertex(view, x, y, tol=0.05):
    i = 0
    while True:
        try:
            p = view.getVertexByIndex(i)
        except Exception:
            return None
        if p is None:
            return None
        if abs(p.Point.x - x) < tol and abs(p.Point.y - y) < tol:
            return "Vertex%d" % i
        i += 1


def find_line(view, p0, p1, tol=0.05):
    for i, e in _edges(view):
        if e.Curve.__class__.__name__ in ("Line", "LineSegment") and len(e.Vertexes) == 2:
            a, b = e.Vertexes[0].Point, e.Vertexes[1].Point
            for (u, w) in ((a, b), (b, a)):
                if abs(u.x - p0[0]) < tol and abs(u.y - p0[1]) < tol and abs(w.x - p1[0]) < tol and abs(w.y - p1[1]) < tol:
                    return "Edge%d" % i
    return None


def _sig(v):
    es = _edges(v)
    if not es:
        return None
    xs = [p for _i, e in es for p in (e.Vertexes[0].Point.x, e.Vertexes[-1].Point.x)]
    ys = [p for _i, e in es for p in (e.Vertexes[0].Point.y, e.Vertexes[-1].Point.y)]
    return (len(es), round(min(xs), 3), round(max(xs), 3), round(min(ys), 3), round(max(ys), 3))


def wait_views(doc, views, tries=60):
    """Views are done when their HLR geometry is present AND unchanged over 3 polls (TechDraw computes
    in a background thread: an early read can return partial/stale geometry and vertex numbering)."""
    last, same = None, 0
    for _ in range(tries):
        doc.recompute()
        Gui.updateGui()
        busy = any(getattr(v, "isComputing", lambda: False)() for v in views if hasattr(v, "isComputing"))
        sig = None if busy else tuple(_sig(v) for v in views)
        if sig is not None and None not in sig:
            same = same + 1 if sig == last else 0
            last = sig
            if same >= 2:
                return True
        time.sleep(0.4)
    return False


# ------------------------------------------------------------- native TechDraw annotation helpers
TEXT_H = 3.5            # ASME Y14.2: 3-3.5 mm lettering for B-size sheets (TechDraw default is ~5 mm)


def _font(obj):
    vo = getattr(obj, "ViewObject", None)
    if vo is None:
        return
    for prop in ("Fontsize", "FontSize"):
        if hasattr(vo, prop):
            setattr(vo, prop, TEXT_H)
    if hasattr(vo, "Arrowsize"):
        vo.Arrowsize = 2.5


def add_view(page, v, x, y, scale):
    """page.addView() resets position/scale, so set them afterwards (custom scale)."""
    page.addView(v)
    if hasattr(v, "ScaleType"):
        v.ScaleType = "Custom"
    if hasattr(v, "Scale"):
        v.Scale = scale
    v.X, v.Y = x, y
    return v


def balloon(doc, page, view, text, origin, at, shape="Rectangle", end="Filled triangle", name="Balloon"):
    b = doc.addObject("TechDraw::DrawViewBalloon", name)
    b.SourceView = view
    page.addView(b)
    b.OriginX, b.OriginY = origin
    b.X, b.Y = at
    b.Text = text
    b.BubbleShape = shape
    b.EndType = end
    _font(b)
    return b


def fcf(doc, page, view, cells, at, name="FCF"):
    """Feature control frame: native balloon, '|' separates compartments, no leader."""
    b = balloon(doc, page, view, "|".join(cells), at, at, end="None", name=name)
    b.KinkLength = 0
    return b


def callout(doc, page, view, text, origin, at, name="Callout"):
    """Y14.5 hole callout / local note: native balloon without a frame, arrow leader."""
    b = balloon(doc, page, view, text, origin, at, shape="None", end="Filled arrow", name=name)
    return b


def datum(doc, page, view, letter, origin, at):
    """Datum feature symbol: boxed letter + leader + filled triangle on the feature."""
    d = balloon(doc, page, view, letter, origin, at, name="Datum_" + letter)
    d.KinkLength = 0                            # straight leader: no shoulder stub beside the box
    return d


def rich(doc, page, html, x, y, width=120, frame=False, name="Note"):
    r = doc.addObject("TechDraw::DrawRichAnno", name)
    page.addView(r)
    r.AnnoText = html
    r.MaxWidth = width
    r.ShowFrame = frame
    r.X, r.Y = x, y
    return r


def html_lines(lines, size_pt=8):
    body = "<br/>".join(l.replace("&", "&amp;").replace("<", "&lt;") for l in lines)
    return '<html><body style="font-family:osifont; font-size:%dpt;">%s</body></html>' % (size_pt, body)


def dimv(doc, page, view, refs, typ, fmt, at=None, basic=False, name="Dim"):
    """Dimension; 'at' = label offset from the view centre in PAGE mm (unscaled)."""
    d = doc.addObject("TechDraw::DrawViewDimension", name)
    d.Type = typ
    d.References2D = [(view, r) for r in refs]
    pts = []                                    # remember WHERE the vertices are: TechDraw renumbers them
    for r in refs:                              # on recompute, so rebind_dims() re-resolves before export
        if r.startswith("Vertex"):
            try:
                q = view.getVertexByIndex(int(r[6:])).Point
                pts.append("%.5f,%.5f" % (q.x, q.y))
            except Exception:
                pass
    if pts and len(pts) == len(refs):
        try:
            d.addProperty("App::PropertyString", "RefPts", "Layout")
            d.RefPts = ";".join(pts)
        except Exception:
            pass
    d.FormatSpec = fmt
    page.addView(d)
    _font(d)
    if basic and hasattr(d, "TheoreticalExact"):
        d.TheoreticalExact = True
    if at is not None:
        d.X, d.Y = at
    return d


def cos_circle(view, r):
    view.makeCosmeticCircle(V(0, 0, 0), r)


def cos_line(view, p0, p1):
    view.makeCosmeticLine(V(p0[0], p0[1], 0), V(p1[0], p1[1], 0))


def centre_circle_edge(view, r):
    for i, ed in _edges(view):
        c = ed.Curve
        if c.__class__.__name__ == "Circle" and abs(c.Radius - r) < 0.01 and abs(c.Center.x) < 0.01 and abs(c.Center.y) < 0.01:
            return "Edge%d" % i
    return None


# ============================================================= PILOT: J1 output hub
def hub_j1():
    import arm
    import params
    params.use_release_variant('make_drawings.py')   # drawings are the released package
    arm.reload_all()                       # hardware, iface, arm.* and the arm_model facade, in order
    import arm_model as M
    hub = [p for p in M.motor_hub(-1) if p.name == "J1_Output_Hub"][0].vis.copy()
    hub.rotate(V(0, 0, 0), V(1, 0, 0), -90)            # drawing frame: axis +Z, datum A face on z=0, pilot up
    hub.translate(V(0, 0, -hub.BoundBox.ZMin))
    mass = hub.Volume * 2.70e-3
    doc, page = new_sheet("DWG_ARC_101_J1_Hub", "J1 OUTPUT HUB", "6061-T6 ALUMINUM",
                          "CLEAR ANODIZE, SEE NOTE 3", "ARC-101", "3:1", "%.1f g" % mass)
    part = doc.addObject("Part::Feature", "J1_Output_Hub")
    part.Shape = hub
    part.ViewObject.Visibility = False
    S = 3.0
    top = doc.addObject("TechDraw::DrawViewPart", "TopView")
    top.Source = [part]
    top.Direction = V(0, 0, -1)                         # looking at the pilot side
    top.XDirection = V(1, 0, 0)
    top.HardHidden = True
    add_view(page, top, 105, 182, S)
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionAA")
    sec.BaseView = top
    sec.Source = [part]
    sec.SectionNormal = V(0, -1, 0)
    sec.SectionOrigin = V(0, 0, 0)
    sec.SectionDirection = "Down"
    sec.Direction = V(0, -1, 0)
    sec.XDirection = V(1, 0, 0)
    sec.SectionSymbol = "A"
    add_view(page, sec, 105, 78, S)
    iso = doc.addObject("TechDraw::DrawViewPart", "Iso")
    iso.Source = [part]
    iso.Direction = V(1, -1, 1.2)
    add_view(page, iso, 345, 222, 1.5)
    wait_views(doc, [top, sec, iso])
    hub_j1_annotate(doc, page, top, sec, mass)
    doc.recompute()
    return doc, page


def hub_j1_annotate(doc, page, top, sec, mass):
    D = DIA
    # ---------------- plan view (pilot side): sizes, basic bolt circles, clocking  (dims: page mm)
    e_od, _ = find_circle(top, 19.5)
    dimv(doc, page, top, [e_od], "Diameter", D + "%.1f", at=(-45, 50), name="Dim_OD")
    for r in (13.5, 12.0, 10.0):
        cos_circle(top, r)
    c30 = (12 * math.cos(math.radians(30)), 12 * math.sin(math.radians(30)))
    cos_line(top, (0, 0), (13.5, 0))
    cos_line(top, (0, 0), c30)
    cos_line(top, (0, 0), (0, 10))
    wait_views(doc, [top])
    for r, at, nm in ((13.5, (-72, 26), "Dim_PCD27"), (12.0, (-72, -36), "Dim_PCD24"), (10.0, (-72, -50), "Dim_PCD20")):
        e = centre_circle_edge(top, r)
        if e:
            dimv(doc, page, top, [e], "Diameter", D + "%.0f", at=at, basic=True, name=nm)
    l0, l1, l2 = find_line(top, (0, 0), (13.5, 0)), find_line(top, (0, 0), c30), find_line(top, (0, 0), (0, 10))
    if l0 and l1:
        dimv(doc, page, top, [l0, l1], "Angle", "%.0f", at=(27, 6), basic=True, name="Ang_30")
    if l1 and l2:
        dimv(doc, page, top, [l1, l2], "Angle", "%.0f", at=(10, 25), basic=True, name="Ang_60")
    # ---------------- hole callouts (Y14.5 leader notes) + feature control frames  (balloons: model mm)
    callout(doc, page, top, "6X " + D + "3.3 THRU", (14.6, 1.0), (30, 17.5), name="Call_thru")
    t2 = balloon(doc, page, top, CBORE + D + "6.5 " + DEPTH + "3.0", (30, 15.2), (30, 15.2), shape="None", end="None", name="Call_thru2")
    t2.KinkLength = 0
    fcf(doc, page, top, [SYM["position"], D + "0.2" + MMC, "A", "B", "C"], (30, 11.3), name="FCF_thru")
    callout(doc, page, top, "3X M3x0.5-6H " + DEPTH + "3.5", (0.9, 10.9), (30, 6.6), name="Call_tap")
    fcf(doc, page, top, [SYM["position"], D + "0.15", "A", "B", "C"], (30, 2.6), name="FCF_tap")
    callout(doc, page, top, "3X " + D + "4.0 H7 " + DEPTH + "2.5 FAR SIDE", (11.7, 7.3), (30, -2.4), name="Call_dowel")
    fcf(doc, page, top, [SYM["position"], D + "0.02", "A", "B"], (30, -6.4), name="FCF_dowel")
    datum(doc, page, top, "C", (27.5, -7.6), (27.5, -11.8))
    # ---------------- section A-A: thicknesses, pilot (datum B), datum A face
    a = find_vertex(sec, 19.5, 3.5)
    b = find_vertex(sec, 19.5, -1.0)
    c = find_vertex(sec, 6.0, -3.5)
    d = find_vertex(sec, -6.0, -3.5)
    if a and b:
        dimv(doc, page, sec, [a, b], "DistanceY", "%.1f", at=(68, 4), name="Dim_flange")
    if a and c:
        dimv(doc, page, sec, [a, c], "DistanceY", "%.1f", at=(82, 0), name="Dim_overall")
    if c and d:
        dimv(doc, page, sec, [d, c], "DistanceX", D + "%.0f h7", at=(0, -22), name="Dim_pilot")
    fcf(doc, page, sec, [SYM["perpendicularity"], D + "0.02", "A"], (0, -10.6), name="FCF_perp")
    datum(doc, page, sec, "B", (6, -7.33), (12, -10.6))
    datum(doc, page, sec, "A", (-14, 3.5), (-14, 8.5))
    flat = balloon(doc, page, sec, "|".join([SYM["flatness"], "0.01"]), (-17.5, 3.5), (-27, 8.5),
                   end="Filled arrow", name="FCF_flat")          # FCF with leader to the datum A surface
    rich(doc, page, html_lines(["SECTION A-A", "SCALE 3:1"], 9), 105, 30, 40, name="Cap_AA")
    rich(doc, page, html_lines(["ISOMETRIC VIEW (REF)", "SCALE 1.5:1"], 8), 345, 188, 45, name="Cap_iso")
    # ---------------- notes + tolerance block
    notes = ["NOTES:",
             "1. INTERPRET DIMENSIONS AND TOLERANCES PER ASME Y14.5-2018.",
             "2. MATERIAL: 6061-T6 ALUMINUM.",
             "3. FINISH: CLEAR ANODIZE PER MIL-A-8625 TYPE II CLASS 1 AFTER MACHINING.",
             "    MASK " + D + "4 H7 HOLES AND DATUM A FACE.",
             "4. BREAK ALL SHARP EDGES 0.2-0.4.",
             "5. DATUM A FACE AND " + D + "12 PILOT: Ra 0.8 \u00b5m.",
             "6. M3 THREADS PER ASME B1.13M, CLASS 6H.",
             "7. MATES DAMIAO DM-J4340-2EC OUTPUT FLANGE: 6X M3 ON " + D + "27,",
             "    3X " + D + "4 DOWELS ON " + D + "24 (VERIFY AGAINST VENDOR DRAWING).",
             "8. MASS %.1f g (REF)." % mass]
    rich(doc, page, html_lines(notes, 8), 335, 128, 165, name="Notes")
