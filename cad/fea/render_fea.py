# -*- coding: utf-8 -*-
"""
FEA result images from the CalculiX .vtu exports (VTK bundled with FreeCAD, off-screen):
    "<FreeCAD>/bin/python.exe" cad/fea/render_fea.py   -> cad/fea/out/img/<case>_vm.png, <case>_disp.png
von Mises contour on the deformed shape (auto-scaled so peak deflection reads ~5 % of the part),
peak-stress node marked, scalar bar in MPa / mm, caption with load case and verdict.
"""
import json
import os

import vtk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IMG = os.path.join(OUT, "img")
os.makedirs(IMG, exist_ok=True)


def lut(lo, hi):
    t = vtk.vtkLookupTable()
    t.SetHueRange(0.667, 0.0)                     # blue -> red
    t.SetTableRange(lo, hi)
    t.SetNumberOfTableValues(12)                  # banded contour, easier to read in print
    t.Build()
    return t


def render(case, field, unit, title, fname, res):
    r = vtk.vtkXMLUnstructuredGridReader()
    r.SetFileName(os.path.join(OUT, case + ".vtu"))
    r.Update()
    grid = r.GetOutput()
    # FreeCAD's VTK export is SI (Pa, m) on mm geometry: add display arrays in MPa / mm
    from vtk.util import numpy_support as ns
    pd_ = grid.GetPointData()
    for src, dst, f in (("von Mises Stress", "vm_MPa", 1e-6), ("Displacement Magnitude", "disp_mm", 1e3)):
        a_ = ns.numpy_to_vtk(ns.vtk_to_numpy(pd_.GetArray(src)) * f, deep=1)
        a_.SetName(dst)
        pd_.AddArray(a_)
    field = {"von Mises Stress": "vm_MPa", "Displacement Magnitude": "disp_mm"}[field]
    grid.GetPointData().SetActiveVectors("Displacement")
    b = grid.GetBounds()
    size = max(b[1] - b[0], b[3] - b[2], b[5] - b[4])
    dmax = grid.GetPointData().GetArray("Displacement Magnitude").GetRange()[1]      # m
    ext = sorted([b[1] - b[0], b[3] - b[2], b[5] - b[4]])
    k = 0.05 * size / dmax if dmax > 0 else 0.0
    warp = vtk.vtkWarpVector()
    warp.SetInputData(grid)
    warp.SetScaleFactor(k)
    surf = vtk.vtkDataSetSurfaceFilter()
    surf.SetInputConnection(warp.GetOutputPort())
    surf.Update()
    poly = surf.GetOutput()
    arr = poly.GetPointData().GetArray(field)
    poly.GetPointData().SetActiveScalars(field)
    lo, hi = arr.GetRange()
    m = vtk.vtkPolyDataMapper()
    m.SetInputData(poly)
    m.SetScalarModeToUsePointData()
    m.SetLookupTable(lut(lo, hi))
    m.SetScalarRange(lo, hi)
    a = vtk.vtkActor()
    a.SetMapper(m)
    # undeformed outline for reference
    og = vtk.vtkDataSetSurfaceFilter()
    og.SetInputData(grid)
    fe = vtk.vtkFeatureEdges()
    fe.SetInputConnection(og.GetOutputPort())
    fe.BoundaryEdgesOn(); fe.FeatureEdgesOn(); fe.SetFeatureAngle(40); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff()
    fe.ColoringOff()
    om = vtk.vtkPolyDataMapper()
    om.SetInputConnection(fe.GetOutputPort())
    om.ScalarVisibilityOff()
    oa = vtk.vtkActor()
    oa.SetMapper(om)
    oa.GetProperty().SetColor(0.35, 0.35, 0.35)
    oa.GetProperty().SetOpacity(0.5)
    # peak marker
    imax = max(range(arr.GetNumberOfTuples()), key=arr.GetValue)
    p = poly.GetPoint(imax)
    sph = vtk.vtkSphereSource()
    sph.SetCenter(p); sph.SetRadius(max(0.6, min(0.02 * size, 0.6 * ext[1] / 4))); sph.SetThetaResolution(16); sph.SetPhiResolution(16)
    sm = vtk.vtkPolyDataMapper(); sm.SetInputConnection(sph.GetOutputPort())
    sa = vtk.vtkActor(); sa.SetMapper(sm); sa.GetProperty().SetColor(0, 0, 0)
    bar = vtk.vtkScalarBarActor()
    bar.SetLookupTable(m.GetLookupTable())
    bar.SetTitle(unit)
    bar.SetNumberOfLabels(7)
    bar.SetLabelFormat("%.3g")
    bar.SetWidth(0.08); bar.SetHeight(0.7); bar.SetPosition(0.9, 0.15)
    for tp in (bar.GetTitleTextProperty(), bar.GetLabelTextProperty()):
        tp.SetColor(0.1, 0.1, 0.1); tp.ItalicOff(); tp.ShadowOff(); tp.SetFontSize(22)
    txt = vtk.vtkTextActor()
    txt.SetInput("%s\n%s   peak %.3g %s (black marker)   deformation shown x%.0f" % (title, res["part"], hi, unit, k / 1000.0))
    txt.GetTextProperty().SetFontSize(26); txt.GetTextProperty().SetColor(0.1, 0.1, 0.1)
    txt.SetPosition(12, 12)
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    for x in (a, oa, sa):
        ren.AddActor(x)
    ren.AddActor2D(bar); ren.AddActor2D(txt)
    cam = ren.GetActiveCamera()
    # look along the thinnest axis (plates face the camera), tilted for depth
    lens = [b[1] - b[0], b[3] - b[2], b[5] - b[4]]
    ax = lens.index(min(lens))
    c = [(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2]
    d = [0.0, 0.0, 0.0]; d[ax] = 1.0
    up = [0.0, 0.0, 1.0] if ax != 2 else [0.0, 1.0, 0.0]
    if sorted(lens)[0] < 0.25 * sorted(lens)[1]:          # plate: face the camera
        cam.SetFocalPoint(c)
        cam.SetPosition([c[i] + d[i] * 10 * size for i in range(3)])
        cam.SetViewUp(up)
        ren.ResetCamera()
        cam.Azimuth(28); cam.Elevation(22)
    else:                                                  # block: isometric
        cam.SetFocalPoint(c)
        cam.SetPosition([c[0] + 10 * size, c[1] - 10 * size, c[2] + 8 * size])
        cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.Zoom(0.8)
    cam.Zoom(1.25)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(1400, 900)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(os.path.join(IMG, fname)); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
    return os.path.join(IMG, fname)


def main():
    res = {}
    for f in ("fea_results_main.json", "fea_results_endblock.json", "fea_results_forearm.json", "fea_results_dbore.json", "fea_results.json"):
        p = os.path.join(OUT, f)
        if os.path.exists(p):
            for r_ in json.load(open(p)):
                if "max_von_mises_MPa" in r_:
                    res[r_["case"]] = r_
    json.dump(list(res.values()), open(os.path.join(OUT, "fea_results_all.json"), "w"), indent=1)
    for case, r_ in res.items():
        if not os.path.exists(os.path.join(OUT, case + ".vtu")):
            continue
        render(case, "von Mises Stress", "MPa", "%s - von Mises stress, SF %.1f vs %s MPa (%s)" %
               (case, r_["safety_factor"], r_["allowable_MPa"], r_["verdict"]), case + "_vm.png", r_)
        render(case, "Displacement Magnitude", "mm", "%s - displacement magnitude" % case, case + "_disp.png", r_)
        print("rendered", case)


main()
