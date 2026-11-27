"""Drive frames (rev B) without leg standoffs: flat inboard face, M3 through holes for spacer bolts (2026-11-26).

The frames' three integral legs held the bearing wall 10.5 mm off the bed, so the frame needed tree supports all round
(6 h, 108 g). Now three separate printed spacers carry it off the tower and M3x25 BHCS go through tower, spacer and
wall into a nyloc (interfaces/drive_frame__tower.toml, code-CAD cad/arm/base.py drive_frame).

Per frame document (run with that document active):
  - deletes the "Tower leg i" extrude, its cross-section sketch and its datum;
  - turns "Insert bore i" into "Spacer bolt hole i": D = drive_frame__tower_side_a_clearance_d_Ref (3.3), from a datum
    1 mm inboard of the wall's inboard face, cut through all outboard.
Load by path from a Fusion MCP script (importlib):  run_frame(mode)  mode "list" (dry run) or "apply"; no save.
"""
import adsk.core
import adsk.fusion

STATIONS = (1, 2, 3)


def _root():
    return adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct).rootComponent


def run_frame(mode="list"):
    app = adsk.core.Application.get()
    r = _root()
    ext, sk, pl = r.features.extrudeFeatures, r.sketches, r.constructionPlanes
    out = {"doc": app.activeDocument.name, "mode": mode, "volume_cm3_before": round(r.bRepBodies.item(0).volume, 4)}
    plan = []
    for i in STATIONS:
        for coll, nm in ((ext, "Tower leg %d" % i), (sk, "Tower leg %d cross-section" % i), (pl, "Tower leg %d datum" % i)):
            plan.append(("delete", nm, coll.itemByName(nm) is not None))
        plan.append(("rework", "Insert bore %d" % i, ext.itemByName("Insert bore %d" % i) is not None))
    out["plan"] = plan
    if mode != "apply":
        return out
    # take every handle before deleting anything: itemByName misses items once earlier ones are deleted
    legs = [x for i in STATIONS for x in (ext.itemByName("Tower leg %d" % i), sk.itemByName("Tower leg %d cross-section" % i),
                                          pl.itemByName("Tower leg %d datum" % i)) if x is not None]
    bores = [(ext.itemByName("Insert bore %d" % i) or ext.itemByName("Spacer bolt hole %d" % i),
              sk.itemByName("Insert bore %d cross-section" % i) or sk.itemByName("Spacer bolt hole %d cross-section" % i),
              pl.itemByName("Insert bore %d datum" % i) or pl.itemByName("Spacer bolt hole %d datum" % i), i)
             for i in STATIONS]
    if any(x is None for b in bores for x in b[:3]):
        raise RuntimeError("bore features not found: %s" % [[x is not None for x in b[:3]] for b in bores])
    left = app.activeDocument.name.rstrip().split(" v")[0].endswith("_L")
    for x in legs:
        x.deleteMe()
    for f, s, p, i in bores:
        f.timelineObject.rollTo(True)
        inb = "( bearing_y_1_Ref - 1 mm )"                              # 1 mm inboard of the wall's inboard face
        p.definition.offset.expression = ("-" + inb) if left else inb     # L frame sits at y < 0
        for dd in s.sketchDimensions:
            if dd.parameter.expression == "drive_frame__tower_side_b_drill_d_Ref":
                dd.parameter.expression = "drive_frame__tower_side_a_clearance_d_Ref"
        for dirn in (adsk.fusion.ExtentDirections.NegativeExtentDirection,   # the side with the wall in it
                     adsk.fusion.ExtentDirections.PositiveExtentDirection):
            try:
                f.setOneSideExtent(adsk.fusion.ThroughAllExtentDefinition.create(), dirn,
                                   adsk.core.ValueInput.createByString("0 deg"))
                break
            except RuntimeError as e:
                if "body not found" not in str(e) or dirn == adsk.fusion.ExtentDirections.PositiveExtentDirection:
                    raise
        f.name, s.name, p.name = "Spacer bolt hole %d" % i, "Spacer bolt hole %d cross-section" % i, \
            "Spacer bolt hole %d datum" % i
    r.parentDesign.timeline.moveToEnd()
    out["volume_cm3_after"] = round(r.bRepBodies.item(0).volume, 4)
    out["health"] = [(it.name, it.errorOrWarningMessage) for it in r.parentDesign.timeline
                     if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    return out
