"""Fusion -> repo snapshot: export one revision's top assembly as diffable text plus one STEP.

Runs inside Autodesk Fusion. Send it through the Fusion MCP (featureType "script", readOnly true) or run it as a
Fusion script. It only reads: no design is changed, and nothing is saved.

Efficiency and crash safety (Fusion API notes in fusion/README.md):
  - one cloud data-API touch: findFileById plus documents.open of the top assembly. Every part comes in through the
    assembly's references, so masses, materials, placements and joints are read locally, with no per-part document
    opens;
  - no doEvents and no waiting loops inside Fusion;
  - each output file is written as soon as it is ready, so a call that times out on the client side still leaves
    its results.

Output: <repo>/fusion/snapshot/<rev>/
  snapshot.json   occurrences (path, component, source doc id + version, world transform, bbox, mass, COM, volume,
                  bodies with materials), joints and motion links (type, value, limits), a summary
  params.toml     the revision's master user parameters (name = value, unit, expression, comment)
  bom.csv         unique parts and their quantity, material, mass and source document
  assembly.step   the assembly at its saved pose (the checks read this)

Usage from the MCP: replace REV and ASSEMBLY_ID / MASTER_ID below, or call export(rev, assembly_id, master_id, out_root).
"""
import json
import os
import time

import adsk.core
import adsk.fusion

REPO = r"C:\Users\ryanh\light_weight_arm"
REVS = {
    "rev_b": ("urn:adsk.wipprod:dm.lineage:cGWSAxvSQQaYddhXmTl3HA", "urn:adsk.wipprod:dm.lineage:lOOS22UVSUahWVQdqcVwbg"),
    "rev_a": ("urn:adsk.wipprod:dm.lineage:tGjaaP6BR9alz_2ZsIQF-g", "urn:adsk.wipprod:dm.lineage:KQIqmPAoQN-XdIPTQOXkJQ"),
}
CM = 10.0  # Fusion's internal length unit is cm; the repo uses mm


def _mat(m):
    """4x4 row-major in mm (translation scaled)."""
    a = list(m.asArray())
    for i in (3, 7, 11):
        a[i] *= CM
    return [round(x, 6) for x in a]


def _bbox(b):
    return [round(v * CM, 4) for v in (b.minPoint.x, b.minPoint.y, b.minPoint.z, b.maxPoint.x, b.maxPoint.y, b.maxPoint.z)]


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _open(app, file_id):
    for d in app.documents:                       # already open: reuse it, no cloud call
        if d.dataFile and d.dataFile.id == file_id:
            return d, False
    f = app.data.findFileById(file_id)
    return app.documents.open(f, False), True     # invisible: no tab, no redraw


def export(rev="rev_b", out_root=None, step=True):
    t0 = time.time()
    app = adsk.core.Application.get()
    asm_id, master_id = REVS[rev]
    out = os.path.join(out_root or os.path.join(REPO, "fusion", "snapshot"), rev)
    doc, opened = _open(app, asm_id)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        root = design.rootComponent
        occs, bom = [], {}
        # Source document per referenced component. Occurrence.documentReference only works at the top level, so
        # map every reference in the whole tree once: component name -> data file.
        src_of = {}
        for ref in doc.allDocumentReferences:
            try:
                rd = ref.referencedDocument
                rc = adsk.fusion.Design.cast(rd.products.itemByProductType("DesignProductType")).rootComponent
                src_of.setdefault(rc.name, ref.dataFile)
            except Exception:
                pass
        for occ in root.allOccurrences:
            src = src_of.get(occ.component.name) if occ.isReferencedComponent else None
            pp = occ.getPhysicalProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy)
            bodies = [dict(name=b.name, material=b.material.name if b.material else None,
                           appearance=b.appearance.name if b.appearance else None)
                      for b in occ.bRepBodies]
            com = pp.centerOfMass
            row = dict(path=occ.fullPathName, component=occ.component.name, body_group=occ.fullPathName.split("+")[0],
                       source_id=src.id if src else None, source_version=src.versionNumber if src else None,
                       transform=_mat(occ.transform2), bbox=_bbox(occ.boundingBox) if occ.boundingBox else None,
                       mass_g=round(pp.mass * 1000.0, 3), volume_mm3=round(pp.volume * 1000.0, 3),
                       com_mm=[round(com.x * CM, 4), round(com.y * CM, 4), round(com.z * CM, 4)], bodies=bodies,
                       visible=occ.isLightBulbOn)
            occs.append(row)
            if bodies:                            # leaf parts with geometry make the BOM
                k = occ.component.name
                e = bom.setdefault(k, dict(qty=0, mass_g=row["mass_g"], material=bodies[0]["material"],
                                           source_id=row["source_id"], source_version=row["source_version"]))
                e["qty"] += 1
        joints = []
        for coll, kind in ((root.allJoints, "joint"), (root.allAsBuiltJoints, "as-built")):
            for j in coll:
                m = j.jointMotion

                def occ_path(get):
                    # some joints' occurrence proxies don't resolve from the root context; record what we can
                    try:
                        o = get()
                        return o.fullPathName if o else None
                    except Exception:
                        return None
                def safe(get):
                    try:
                        return get()
                    except Exception:
                        return None
                row = dict(name=j.name, kind=kind, type=str(m.jointType),
                           occ1=occ_path(lambda: j.occurrenceOne), occ2=occ_path(lambda: j.occurrenceTwo),
                           suppressed=safe(lambda: j.isSuppressed))
                if row["occ1"] is None and row["occ2"] is None:
                    row["broken"] = True       # neither occurrence resolves: a joint left over from a deleted part
                for attr in ("rotationValue", "slideValue"):
                    if hasattr(m, attr):
                        row[attr] = getattr(m, attr)
                for lim in ("rotationLimits", "slideLimits"):
                    if hasattr(m, lim):
                        L = getattr(m, lim)
                        row[lim] = dict(min=L.minimumValue if L.isMinimumValueEnabled else None,
                                        max=L.maximumValue if L.isMaximumValueEnabled else None)
                joints.append(row)
        links = [dict(name=l.name) for l in root.allMotionLinks] if hasattr(root, "allMotionLinks") else []
        summary = dict(revision=rev, document=doc.name, document_id=asm_id,
                       document_version=doc.dataFile.versionNumber if doc.dataFile else None,
                       occurrences=len(occs), parts=len(bom), joints=len(joints), motion_links=len(links),
                       total_mass_g=round(sum(o["mass_g"] for o in occs if o["bodies"]), 1),
                       exported=time.strftime("%Y-%m-%dT%H:%M:%S"))
        snap = dict(summary=summary, occurrences=occs, joints=joints, motion_links=links)
        _write(os.path.join(out, "snapshot.json"), json.dumps(snap, indent=1, sort_keys=True))
        lines = ["component,qty,material,mass_g,source_id,source_version"]
        for k in sorted(bom):
            e = bom[k]
            lines.append('"%s",%d,"%s",%.3f,%s,%s' % (k, e["qty"], e["material"], e["mass_g"], e["source_id"], e["source_version"]))
        _write(os.path.join(out, "bom.csv"), "\n".join(lines) + "\n")
        if step:
            em = design.exportManager
            em.execute(em.createSTEPExportOptions(os.path.join(out, "assembly.step"), root))
    finally:
        if opened:
            doc.close(False)
    # parameters: the master document (one more open; only parameters are read)
    mdoc, mopened = _open(app, master_id)
    try:
        md = adsk.fusion.Design.cast(mdoc.products.itemByProductType("DesignProductType"))
        rows = ["# Generated from Fusion (%s, v%s) by fusion/snapshot_export.py: do not edit; change it in Fusion"
                % (mdoc.name, mdoc.dataFile.versionNumber if mdoc.dataFile else "?")]
        um = md.unitsManager
        for p in sorted(md.userParameters, key=lambda p: p.name):
            # Fusion stores lengths in cm and angles in rad; report each value in its own display unit
            try:
                if p.unit in ("deg", "rad"):
                    v = um.convert(p.value, "rad", p.unit)
                elif p.unit:
                    v = um.convert(p.value, "cm", p.unit)
                else:
                    v = p.value
            except Exception:
                v = None                          # text parameter: the expression carries its value
            value = repr(round(v, 9)) if isinstance(v, (int, float)) else json.dumps(p.expression)
            rows.append('%s = { value = %s, unit = "%s", expression = %s, comment = %s }'
                        % (p.name, value, p.unit, json.dumps(p.expression), json.dumps(p.comment or "")))
        _write(os.path.join(out, "params.toml"), "\n".join(rows) + "\n")
    finally:
        if mopened:
            mdoc.close(False)
    summary["seconds"] = round(time.time() - t0, 1)
    _write(os.path.join(out, "summary.json"), json.dumps(summary, indent=1, sort_keys=True))
    return summary


def run(_context: str):
    print(json.dumps(export("rev_b")))
