# -*- coding: utf-8 -*-
"""Negative test (TI-040): check_working_doc.compare() must flag a working document that no longer shows the model,
the TI-025 defect class (the GUI document kept STS3215 case screws 13.2 mm off their holes after the model was fixed).
In memory only: the model is placed at STOW exactly as check_working_doc.main() places it, copied into a new document
(one Part::Feature per part, by Label).  Two copies, each compared once:
  clean    unedited, except one part moved 0.01 mm (under BB_TOL)          -> no difference
  broken   four defects, each on its own part, each must give exactly its row:
             moved    a STS3215 PAN case screw moved 13.2 mm along z (TI-025)
             changed  a part replaced by a solid box of its own bbox (same bbox, other volume)
             missing  a part's object deleted
             extra    a stray box added
Exit 1 on FAIL.  Builds the model once; the documents are never saved.
    python -I cad/tools/run.py cad/tests/test_working_doc_sync_defects.py      (then with BASE_DRIVE=DIRECT)
"""
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
import FreeCAD as App            # noqa: E402
import Part                      # noqa: E402
import arm_model as M            # noqa: E402
import check_seated as S         # noqa: E402
import check_working_doc as C    # noqa: E402

bodies = M.build_bodies()
model = C.model_shapes(M, bodies)
names = sorted(model)
src = {p.name: str(p.src) for ps in bodies.values() for p in ps if p.kind == "CAT"}
screws = ([n for n in names if src.get(n, "").startswith(S.SCREW_PREFIX)] +   # PAN case screws (TI-025) first
          [n for n in names if src.get(n) in S.SCREW_SRC])
solids = [n for n in names if n not in screws and model[n].Volume > 100.0]
fails = []
if not screws or len(solids) < 3:
    fails.append("fixture: %d screws, %d solid parts in the model" % (len(screws), len(solids)))
    screws, solids = screws or names[:1], (solids + names)[:3]


def make_doc():
    doc = App.newDocument("WD_sync_test")
    for n in names:
        o = doc.addObject("Part::Feature", "P")
        o.Label = n
        o.Shape = model[n].copy()
    return doc


def obj(doc, label):
    return [o for o in doc.Objects if o.Label == label][0]


def check(title, edits, want_kinds):
    """Break one fresh copy with each edit(doc) -> label and require exactly those rows, each on its own label."""
    doc = make_doc()
    try:
        exp = []
        for edit, kind in zip(edits, want_kinds):
            label = edit(doc)
            if kind:
                exp.append((kind, label))
        got = [(k, lab) for k, lab, _d in C.compare(doc, model)]
        ok = sorted(got) == sorted(exp)
        if not ok:
            fails.append("%s: want %s, got %s" % (title, exp, got[:6]))
        print("  %-7s %-4s want %s\n  %-12s got  %s" % (title, "ok" if ok else "FAIL", exp or "no difference", "",
                                                      got or "no difference"))
    finally:
        App.closeDocument(doc.Name)


def labels_check(doc):
    bad = [n for n in names if obj(doc, n).Label != n]
    if bad:
        fails.append("fixture: FreeCAD relabelled %s" % bad[:3])
    return None


def jitter(doc):
    o = obj(doc, solids[0])
    s = o.Shape.copy()
    s.translate(App.Vector(0.01, 0, 0))
    o.Shape = s
    return None                   # expected: no row at all


def moved(doc):
    o = obj(doc, screws[0])
    s = o.Shape.copy()
    s.translate(App.Vector(0, 0, 13.2))
    o.Shape = s
    return screws[0]


def changed(doc):
    o = obj(doc, solids[1])
    b = C._bb(o.Shape)
    o.Shape = Part.makeBox(b.XLength, b.YLength, b.ZLength, App.Vector(b.XMin, b.YMin, b.ZMin))
    return solids[1]


def missing(doc):
    doc.removeObject(obj(doc, solids[2]).Name)
    return solids[2]


def extra(doc):
    o = doc.addObject("Part::Feature", "Stray")
    o.Label = "Stray_Box_TI040"
    o.Shape = Part.makeBox(5, 5, 5, App.Vector(0, 0, 900))
    return o.Label


print("Working doc sync defects (%s, STOW, %d parts; BB_TOL %.2f mm, VOL_TOL %g):" % (
    M.VARIANT, len(names), C.BB_TOL, C.VOL_TOL))
check("clean", [labels_check, jitter], [None, None])
check("broken", [moved, changed, missing, extra], ["moved", "changed", "missing", "extra"])
print("TEST %s: %s%s" % ("FAIL" if fails else "PASS", M.VARIANT, "".join("\n  " + f for f in fails)))
sys.stdout.flush()
sys.exit(1 if fails else 0)
