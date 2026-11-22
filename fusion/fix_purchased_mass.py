"""Set every purchased part's mass in Fusion to its catalogue mass (cad/data/catalogue.toml).

Vendor STEP models are often hollow shells or simplified, so volume x material density gives the wrong mass (6804
bearing 6 g instead of 19 g; STS3215 about 150 g instead of 60 g). For each document in 90 Purchased this script:
  - finds its catalogue mass (by document name, without " (placeholder)");
  - copies the bodies' current material into the document as "<name> (catalogue mass)";
  - sets that copy's density so the document's total mass equals the catalogue mass, and assigns it to every body;
  - saves a new version and closes the document.
It is idempotent: a document already within 1 % of its catalogue mass is skipped. Batches of documents run in one
Fusion call (opens and saves are not interleaved with other cloud work). Run it from the Fusion MCP:
    export_batch(start, count) -> list of results
"""
import json
import os
import tomllib

import adsk.core
import adsk.fusion

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # load this file by path (importlib)
PURCHASED = "urn:adsk.wipprod:fs.folder:co.FjIp-CuvSZqUB-D_Gh-nsg"
CAT = tomllib.load(open(os.path.join(REPO, "cad", "data", "catalogue.toml"), "rb"))
LOG = os.path.join(REPO, "fusion", "checks", "out", "purchased_mass_fix.jsonl")
SKIP = set()   # documents that hang Fusion when opened; fix them by hand


def _bodies(design):
    for comp in design.allComponents:
        for b in comp.bRepBodies:
            yield b


def _mass_g(design):
    return design.rootComponent.getPhysicalProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).mass * 1000.0


def fix_one(app, f):
    name = f.name.replace(" (placeholder)", "")
    target = CAT.get(name, {}).get("mass")
    if not target:
        return dict(doc=f.name, status="skipped: no catalogue mass")
    doc = app.documents.open(f, False)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        before = _mass_g(design)
        if before > 0 and abs(before / target - 1) < 0.01:
            return dict(doc=f.name, status="ok already", mass_g=round(before, 2), target_g=target)
        bodies = list(_bodies(design))
        if not bodies:
            return dict(doc=f.name, status="skipped: no bodies")
        base = bodies[0].material
        mname = "%s (catalogue mass)" % name
        mat = design.materials.itemByName(mname) or design.materials.addByCopy(base, mname)
        dens = mat.materialProperties.itemById("structural_Density")
        for b in bodies:
            b.material = mat
        # density scales mass linearly: correct it from the measured mass (twice, for round-off)
        for _ in range(2):
            m = _mass_g(design)
            if m <= 0:
                break
            dens.value = dens.value * target / m
        after = _mass_g(design)
        doc.save("Mass set to catalogue mass (%g g)" % target)
        return dict(doc=f.name, status="fixed", before_g=round(before, 2), after_g=round(after, 2), target_g=target)
    finally:
        doc.close(False)


def export_batch(start=0, count=20):
    app = adsk.core.Application.get()
    folder = app.data.findFolderById(PURCHASED)
    files = sorted(folder.dataFiles.asArray(), key=lambda f: f.name)
    out = []
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    for f in files[start:start + count]:
        if f.name in SKIP:
            r = dict(doc=f.name, status="skipped: hangs Fusion on open")
            out.append(r)
            continue
        with open(LOG + ".progress", "w", encoding="utf-8") as fh:   # which document is open, in case Fusion hangs
            fh.write("%d %s\n" % (files.index(f), f.name))
        try:
            r = fix_one(app, f)
        except Exception as e:
            r = dict(doc=f.name, status="error: %s" % str(e)[:200])
        out.append(r)
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r) + "\n")
    return dict(total=len(files), done=start + len(out), results=out)
