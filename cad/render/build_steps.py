# -*- coding: utf-8 -*-
"""
Step pictures for the prototype build guide: plain FreeCAD views (Coin/OpenGL screenshots, no renderer, no meshes)
of the working document cad/out/<variant>/ARC_Arm_<Variant>.FCStd, coloured per step.

Run inside the FreeCAD GUI, after cad/tools/build_guide.py (it writes the per-step part lists):
    exec(open(r"<repo>/cad/render/build_steps.py").read())      (or the FreeCAD MCP execute_code tool)
It rebuilds the working document in the GUI first (tools/working_doc.py), so the view matches the model.
Writes cad/docs/paper/fig/build_<nn>_<key>.png. Orange: parts this step adds; blue: the bench sub-assemblies it
mounts; light grey: already built; everything else hidden. Orthographic, fitted to the orange and blue parts.
"""
import json
import os

import FreeCAD as App
import FreeCADGui as Gui

CAD = r"C:\Users\ryanh\light_weight_arm\cad"
COL = {"new": (0.95, 0.45, 0.10), "mount": (0.25, 0.48, 0.85), "context": (0.82, 0.82, 0.84)}
SIZE = (1400, 960)


def main(variant="fourbar", only=None):
    exec(open(os.path.join(CAD, "tools", "working_doc.py"), encoding="utf-8").read(), {"__name__": "__main__"})
    doc = App.ActiveDocument
    by_label = {o.Label: o for o in doc.Objects if o.TypeId == "Part::Feature"}
    data = json.load(open(os.path.join(CAD, "out", variant, "build", "steps.json"), encoding="utf-8"))
    fig = os.path.join(CAD, "docs", "paper", "fig")
    view = Gui.ActiveDocument.ActiveView
    Gui.ActiveDocument.ActiveView.setCameraType("Orthographic")
    missing = []
    for st in data["steps"]:
        if only and st["key"] != only:
            continue
        roles = {n: r for r in ("context", "mount", "new") for n in st["parts"][r]}
        for lab, o in by_label.items():
            vo = o.ViewObject
            r = roles.get(lab)
            vo.Visibility = r is not None
            if r:
                vo.ShapeColor = COL[r]
                vo.Transparency = 0
        missing += [n for n in roles if n not in by_label]
        d = App.Vector(*st["view"]).normalize()
        view.setViewDirection((-d.x, -d.y, -d.z))
        Gui.Selection.clearSelection()
        for n in st["parts"]["new"] + st["parts"]["mount"]:
            if n in by_label:
                Gui.Selection.addSelection(by_label[n])
        Gui.SendMsgToActiveView("ViewSelection")
        Gui.Selection.clearSelection()
        Gui.updateGui()
        view.saveImage(os.path.join(fig, st["png"]), SIZE[0], SIZE[1], "White")
    for o in by_label.values():
        o.ViewObject.Visibility = True
    return dict(steps=len(data["steps"]), missing=sorted(set(missing)))


RESULT = main()
print("BUILD_STEPS", RESULT)
