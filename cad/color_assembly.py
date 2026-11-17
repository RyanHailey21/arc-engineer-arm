# -*- coding: utf-8 -*-
"""GUI macro: apply appearance to every open ARC arm document (uses ColorKey)."""
import FreeCAD as App

COL = dict(cf=((0.10, 0.10, 0.11), 0), pla=((0.95, 0.42, 0.08), 0), alu=((0.78, 0.79, 0.82), 0),
           steel=((0.30, 0.30, 0.33), 0), brass=((0.80, 0.65, 0.25), 0), motor=((0.22, 0.22, 0.25), 0),
           pad=((0.15, 0.45, 0.85), 0), pom=((0.95, 0.95, 0.92), 0), pcb=((0.10, 0.40, 0.20), 0),
           donut=((0.92, 0.72, 0.12), 0), red=((0.85, 0.12, 0.12), 0), blue=((0.12, 0.30, 0.85), 0),
           field=((0.60, 0.60, 0.62), 40), wood=((0.72, 0.58, 0.40), 55), chassis=((0.40, 0.60, 0.40), 75),
           bowden=((0.05, 0.05, 0.05), 0), wire=((0.75, 0.10, 0.10), 0))


def repair_joint_viewproviders(doc):
    """Files built headless (freecadcmd) restore their joints' view providers without
    running attach(), so the GUI solver, dragging and simulation fail ('no attribute
    switch_JCS1').  Re-attach them; returns the number repaired."""
    n = 0
    for o in doc.Objects:
        if o.TypeId != "Assembly::JointGroup":
            continue
        for j in o.Group:
            vo = getattr(j, "ViewObject", None)
            pr = getattr(vo, "Proxy", None) if vo else None
            if pr is None or hasattr(pr, "switch_JCS1") or hasattr(pr, "app_obj"):
                continue
            try:
                pr.attach(vo)
                n += 1
            except Exception as ex:
                App.Console.PrintWarning("joint %s: %s\n" % (j.Label, ex))
    return n


def apply(doc):
    if not App.GuiUp:
        return
    n = repair_joint_viewproviders(doc)
    if n:
        App.Console.PrintMessage("%s: re-attached %d joint view providers (headless build)\n" % (doc.Name, n))
    for o in doc.Objects:     # objects saved by freecadcmd come back hidden
        if o.TypeId in ("Part::Feature", "App::Part", "Assembly::AssemblyObject", "App::DocumentObjectGroup",
                        "Assembly::JointGroup") and o.ViewObject:
            o.ViewObject.Visibility = True
    for o in doc.Objects:
        k = getattr(o, "ColorKey", None)
        if k and k in COL and hasattr(o, "ViewObject") and o.ViewObject:
            c, t = COL[k]
            try:
                o.ViewObject.ShapeAppearance = [App.Material(DiffuseColor=c, Shininess=0.35 if k in ("alu", "steel", "brass") else 0.1)]
            except Exception:
                o.ViewObject.ShapeColor = c
            o.ViewObject.Transparency = t
    for o in doc.Objects:
        if o.Name.startswith(("BELT_EQUIV", "Belt_equiv_link", "Datum_")):
            o.ViewObject.Visibility = False
    for o in doc.Objects:          # hide joint markers' clutter but keep joints
        if o.TypeId == "Assembly::JointGroup" and o.ViewObject:
            o.ViewObject.Visibility = True


for d in App.listDocuments().values():
    if d.Name.startswith("ARC_"):
        apply(d)
