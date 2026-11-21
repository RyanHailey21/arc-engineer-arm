# -*- coding: utf-8 -*-
"""
Working-document sync check (TI-017): the FreeCAD working document must show the model as it is now.
    python -I cad/tools/run.py --grip FOURBAR cad/tools/check_working_doc.py   (the saved .FCStd)
    In the FreeCAD GUI:  import check_working_doc as W; W.main()                (the OPEN document, and the file)

Why: the coloured GUI build of ARC_Arm_Fourbar was made before a fix to hardware.pan_screw (the STS3215 case
screws were translated twice, 13.2 mm off their holes).  The file on disk was later rebuilt headless and was
right, but the document left open in the GUI still showed floating screws, and no check looked at it.

Rule: build the model, place it at STOW (vis shapes, exactly as working_doc.py does) and compare every part, by
Label, with the document's Part::Feature objects:
  FAIL  missing      a model part has no object in the document
  FAIL  extra        a document object is not in the model
  FAIL  moved/changed  bounding box differs by > BB_TOL mm on any side, or volume by > VOL_TOL (relative)
Exit 1 on any FAIL.  Not part of quick_check (opening the 10 MB document costs ~15 s, and quick_check cannot see
the GUI's open document anyway); its evidence line goes STALE after a design edit like any check.  Run it in the GUI
after tools/working_doc.py, before showing the user the model.
"""
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else \
    r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
import FreeCAD as App  # noqa: E402

BB_TOL, VOL_TOL = 0.05, 1e-4


def doc_path(M):
    name = "ARC_Arm_%s" % M.VARIANT.capitalize()
    return name, os.path.join(CAD, "out", M.VARIANT.lower(), name + ".FCStd")


def model_shapes(M, bodies=None, pose="STOW"):
    bodies = bodies or M.build_bodies()
    q, jaw = M.pose_q(pose)
    return {p.name: s for _b, p, s in M.placed(bodies, *q, jaw=jaw, which="vis") if not s.isNull()}


def _bb(s):
    """Exact box: Shape.BoundBox is loose round spheres and B-splines and tightens once the GUI has meshed the shape,
    so a displayed document and a fresh model would differ by up to ~1.3 mm on a button head."""
    try:
        return s.optimalBoundingBox(False, False)
    except Exception:
        return s.BoundBox


def compare(doc, model):
    """[(kind, label, detail)] differences between a FreeCAD document and {part name: placed vis shape}."""
    objs = {o.Label: o for o in doc.Objects if o.TypeId == "Part::Feature"}
    out = []
    for name, s in model.items():
        o = objs.get(name)
        if o is None:
            out.append(("missing", name, "not in the document"))
            continue
        a, b = _bb(s), _bb(o.Shape)
        dev = max(abs(x - y) for x, y in zip((a.XMin, a.YMin, a.ZMin, a.XMax, a.YMax, a.ZMax),
                                              (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)))
        va, vb = s.Volume, o.Shape.Volume
        if dev > BB_TOL:
            ca, cb = a.Center, b.Center
            out.append(("moved", name, "bbox off by %.2f mm (centre doc (%.1f, %.1f, %.1f) vs model (%.1f, %.1f, %.1f))"
                        % (dev, cb.x, cb.y, cb.z, ca.x, ca.y, ca.z)))
        elif abs(va - vb) > VOL_TOL * max(abs(va), 1.0):
            out.append(("changed", name, "volume %.1f vs model %.1f mm3" % (vb, va)))
    for lab in objs:
        if lab not in model:
            out.append(("extra", lab, "not in the model"))
    return out


def main():
    if App.GuiUp:
        import arm
        import iface
        iface._CACHE.clear()
        arm.reload_all()
    import arm_model as M
    import params
    model = model_shapes(M)
    name, path = doc_path(M)
    targets = []
    gui_doc = App.getDocument(name) if (App.GuiUp and name in App.listDocuments()) else None
    if gui_doc is not None:           # what the user is looking at
        targets.append(("open document", compare(gui_doc, model)))
    same_file = gui_doc is not None and os.path.normcase(gui_doc.FileName) == os.path.normcase(path)
    if not os.path.exists(path):
        targets.append(("file", [("missing", path, "no working document; run tools/working_doc.py")]))
    elif not same_file:               # (opening a path that is already open would return the open document)
        tmp = App.openDocument(path, True)
        try:
            targets.append(("file", compare(tmp, model)))
        finally:
            App.closeDocument(tmp.Name)
    rows = ["FAIL %-13s %-8s %-34s %s" % (t, k, lab, det) for t, diffs in targets for k, lab, det in diffs]
    head = "Working doc sync (%s, STOW): %d model parts vs %s -> %d FAIL" % (
        M.VARIANT, len(model), " + ".join(t for t, _d in targets), len(rows))
    txt = "\n".join([head] + rows[:60] + (["... %d more" % (len(rows) - 60)] if len(rows) > 60 else []))
    out = os.path.join(params.out_dir(), "working_doc_sync.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    print(txt)
    if not App.GuiUp:
        params.record("working_doc_sync", "FAIL" if rows else "PASS", [out], head)
    return 1 if rows else 0


if not os.environ.get("QC_IMPORT") and not App.GuiUp:
    sys.exit(main())
