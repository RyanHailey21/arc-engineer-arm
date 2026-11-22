"""Remove the joints left over from before the gripper became a shared document (Rev A and Rev B top assemblies).

Runs inside Autodesk Fusion (Fusion MCP, featureType "script"). Set MODE = "list" to report only.
A root joint is a leftover when it is named "J4 roll (before shared gripper)", or when it is one of the eight
four-bar joints (Ground/Coupler LD, LI, RD, RI) in the ROOT component: the live copies sit inside the shared
gripper document and are untouched. Each target must be owned by the assembly's root component, and neither of its
occurrences resolves from the root (the snapshot records them as pointing at nothing). Results go to
fusion/checks/out/cleanup_joints.log, written as each step finishes.
"""
import os

import adsk.core
import adsk.fusion

REPO = r"C:\Users\ryanh\light_weight_arm"
LOG = os.path.join(REPO, "fusion", "checks", "out", "cleanup_joints.log")
ASSEMBLIES = {
    "rev_b": "urn:adsk.wipprod:dm.lineage:cGWSAxvSQQaYddhXmTl3HA",
    "rev_a": "urn:adsk.wipprod:dm.lineage:tGjaaP6BR9alz_2ZsIQF-g",
}
FOURBAR = {f"{k} {s}" for k in ("Ground", "Coupler") for s in ("LD", "LI", "RD", "RI")}
OLD_ROLL = "J4 roll (before shared gripper)"
MODE = "list"          # "list" or "delete"
REVS = ("rev_b", "rev_a")


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def safe(get):
    try:
        return get()
    except Exception:
        return "<error>"


def occ_name(j, which):
    def g():
        geo = j.geometryOrOriginOne if which == 1 else j.geometryOrOriginTwo
        ent = geo.entityOne if hasattr(geo, "entityOne") else None
        o = getattr(ent, "assemblyContext", None) if ent else None
        if o is None:
            o = j.occurrenceOne if which == 1 else j.occurrenceTwo
        return o.name if o else None
    return safe(g)


def run(_context: str):
    app = adsk.core.Application.get()
    for rev in REVS:
        fid = ASSEMBLIES[rev]
        doc = None
        for d in app.documents:
            if d.dataFile and d.dataFile.id == fid:
                doc = d
        if doc is None:
            doc = app.documents.open(app.data.findFileById(fid), True)
        doc.activate()
        des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        root = des.rootComponent
        log(f"== {rev} {doc.name} mode={MODE}")
        targets = []
        for coll, kind in ((root.allJoints, "joint"), (root.allAsBuiltJoints, "as-built")):
            for j in coll:
                o1, o2 = occ_name(j, 1), occ_name(j, 2)
                sup = safe(lambda: j.isSuppressed)
                pc = safe(lambda: j.parentComponent)
                pcn = getattr(pc, "name", pc)
                local = pcn == root.name                 # owned by this assembly's root, not by the shared gripper
                leftover = local and (j.name == OLD_ROLL or j.name in FOURBAR)
                log(f"  {kind} {j.name!r} in={pcn} local={local} suppressed={sup} occ1={o1} occ2={o2}"
                    + ("  <- leftover" if leftover else ""))
                if leftover:
                    targets.append(j)
        if MODE != "delete":
            continue
        n = 0
        for j in targets:
            name = j.name
            ok = (j.nativeObject or j).deleteMe()
            n += 1 if ok else 0
            log(f"  delete {name!r}: {ok}")
        des.computeAll()
        log(f"  deleted {n}/{len(targets)}; root as-built joints now {root.asBuiltJoints.count}")
        bad = [des.timeline.item(k).name for k in range(des.timeline.count)
               if des.timeline.item(k).healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState]
        log(f"  timeline errors after delete: {bad}")
        if not bad and n == len(targets):
            ok = doc.save("Remove leftover joints from before the shared gripper")
            log(f"  saved: {ok}")
