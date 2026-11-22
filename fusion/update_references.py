"""Bring the assemblies' out-of-date references up to date ("Get latest") and save them.

A shared document (the four-bar gripper) keeps the versions of its parts it was saved with, so a part updated
after the gripper's last save (21 Nov: catalogue masses on the D4 pins and washer, the palm's servo pocket) shows
as out of date in every assembly that uses the gripper. Update the inner document first, then the top assemblies.

Run it from a Fusion MCP script, loaded by path (importlib):
    run_docs(names, mode)   names in update order; mode "list" (dry run) or "apply"
Each document is opened visibly (updateAllReferences crashes Fusion on an invisibly opened one). "apply" saves
a new version only when something was out of date, then closes the documents it opened.
Results go to fusion/checks/out/update_references.json as each document finishes.

Limit (2026-11-22): references nested inside a shared sub-assembly (the gripper's palm and pins, as seen from rev A
or rev B) cannot be updated through the API: updateAllReferences leaves them stale, and getLatestVersion() or
setting .version raises InternalValidationError. Use Get Latest in Fusion's UI for those, then save.
"""
import json
import os

import adsk.core
import adsk.fusion

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(REPO, "fusion", "checks", "out", "update_references.json")


def _stale(doc):
    out = []
    for i in range(doc.documentReferences.count):
        r = doc.documentReferences.item(i)
        if r.isOutOfDate:
            out.append("%s v%d -> v%d" % (r.dataFile.name, r.version, r.dataFile.latestVersionNumber))
    return out


def _find(app, name):
    # Only top-level open documents: opening a document through a reference of an open assembly returns the
    # nested copy, which has no documentReferences and cannot be updated. Open each one first, e.g. with the
    # Fusion MCP's document open (by lineage id).
    # app.documents also lists every nested copy (same name); a nested one raises on documentReferences.
    for i in range(app.documents.count):
        d = app.documents.item(i)
        if d.dataFile and d.dataFile.name == name:
            try:
                d.documentReferences.count
            except RuntimeError:
                continue
            return d, False
    raise RuntimeError("open %s as its own document first" % name)


def _write(results):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)


def run_docs(names, mode="list"):
    app = adsk.core.Application.get()
    home = app.activeDocument
    results = []
    for name in names:
        doc, opened = _find(app, name)
        r = dict(doc=name, version=doc.dataFile.versionNumber, stale=_stale(doc))
        if mode == "apply" and r["stale"]:
            doc.activate()
            doc.updateAllReferences()
            r["still_stale"] = _stale(doc)
            done = [s for s in r["stale"] if s not in r["still_stale"]]
            if done:                                     # save only what was actually updated
                doc.save("Get latest: %s" % "; ".join(done))
                r["saved_as"] = doc.dataFile.latestVersionNumber
        if opened:
            doc.close(False)
        results.append(r)
        _write(results)
    if home.isValid:
        home.activate()
    return results
