"""Level hubs (Level_Hub_Elbow / Level_Hub_Wrist): join the D14 neck to the 6700 seat (2026-11-27).

The D15 "6700 outer race seat" ran up to y -35, where the D14 "Relieved shaft boss" starts, so each hub was two
bodies (the printed necks strung in mid-air). Code-CAD: cad/arm/forearm.py level_hub. Per hub document (run with it
active), after the existing timeline:
  - "Neck shoulder": D15.2 / D10.6 ring from the -35 datum, 0.6 mm toward the neck (new body), then combined with
    the hub and the sleeve into one body "Level_Hub_*" (the bearing's outer race now stops against it);
  - "Inner race relief": D12.6 cut 0.3 mm from -35, so the shoulder clears the inner race.
Load by path from a Fusion MCP script (importlib):  run_hub(mode)  mode "list" (dry run) or "apply"; no save.
"""
import adsk.core
import adsk.fusion

DATUM = "Relieved shaft boss datum"          # the -35 mm plane


def _vi(s):
    return adsk.core.ValueInput.createByString(s)


def _ring_sketch(r, plane, name, dias):
    sk = r.sketches.add(plane)
    sk.name = name
    for d in dias:
        c = sk.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), d / 20.0)
        sk.sketchDimensions.addDiameterDimension(c, adsk.core.Point3D.create(d / 15.0, 0, 0)).parameter.expression = "%g mm" % d
    return sk


def _extrude(r, prof, dist, op, name, signs=("", "-")):
    """Extrude prof by dist toward the neck (+y). For a new body try one direction and flip if it lands on the -y
    side; returns (feature, sign) so later features reuse the sign."""
    ex = r.features.extrudeFeatures
    for sgn in signs:
        inp = ex.createInput(prof, op)
        inp.setDistanceExtent(False, _vi(sgn + dist))
        f = ex.add(inp)
        if op != adsk.fusion.FeatureOperations.NewBodyFeatureOperation or f.bodies.item(0).boundingBox.minPoint.y > -3.51:
            f.name = name
            return f, sgn
        f.deleteMe()
    raise RuntimeError("could not extrude %s toward +y" % name)


def run_hub(mode="list"):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    r = d.rootComponent
    hub = app.activeDocument.name.split(" v")[0].strip()
    out = {"doc": app.activeDocument.name, "mode": mode,
           "bodies_before": [(b.name, round(b.volume, 4)) for b in r.bRepBodies],
           "has_datum": r.constructionPlanes.itemByName(DATUM) is not None,
           "already": r.features.extrudeFeatures.itemByName("Neck shoulder") is not None}
    if mode != "apply" or out["already"]:
        return out
    pl = r.constructionPlanes.itemByName(DATUM)
    sk = _ring_sketch(r, pl, "Neck shoulder cross-section", (15.2, 10.6))
    ring = min((sk.profiles.item(i) for i in range(sk.profiles.count)),
               key=lambda p: abs(p.areaProperties().area - 3.14159 * (0.76 ** 2 - 0.53 ** 2)))
    sh, sgn = _extrude(r, ring, "0.6 mm", adsk.fusion.FeatureOperations.NewBodyFeatureOperation, "Neck shoulder")
    bodies = [b for b in r.bRepBodies]
    main = next(b for b in bodies if b.name == hub) if any(b.name == hub for b in bodies) else bodies[0]
    tools = adsk.core.ObjectCollection.create()
    for b in bodies:
        if b != main:
            tools.add(b)
    ci = r.features.combineFeatures.createInput(main, tools)
    ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cf = r.features.combineFeatures.add(ci)
    cf.name = "Join neck to seat"
    sk2 = _ring_sketch(r, pl, "Inner race relief cross-section", (12.6,))
    _extrude(r, sk2.profiles.item(0), "0.3 mm", adsk.fusion.FeatureOperations.CutFeatureOperation, "Inner race relief",
             signs=(sgn,))
    out["shoulder_y_cm"] = (round(sh.bodies.item(0).boundingBox.minPoint.y, 3) if sh.bodies.count else None)
    out["bodies_after"] = [(b.name, round(b.volume, 4), b.shells.count) for b in r.bRepBodies]
    out["health"] = [(it.name, it.errorOrWarningMessage) for it in d.timeline
                     if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    return out
