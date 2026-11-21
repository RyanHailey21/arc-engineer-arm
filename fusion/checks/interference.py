"""Interference check on a Fusion snapshot's assembly STEP (the pose it was saved in, STOW).

    python -I cad/tools/run.py --timeout 1800 fusion/checks/interference.py      (rev from SNAP_REV)

It loads fusion/snapshot/<rev>/assembly.step headless, prefilters every pair of solids by bounding box, and
reports pairs whose common volume exceeds MIN_MM3. That is the same 0.5 mm^3 threshold check_interference.py
uses. Unlike the code-CAD check, this one runs on the full Fusion geometry: real gear teeth and full vendor models,
not simplified check shapes. Expected contacts (pressed bearings, threads) therefore show up and are listed, not
hidden.

Writes fusion/checks/out/<rev>_interference.json.
"""
import itertools
import json
import os
import time

import FreeCAD as App
import Import

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
REV = os.environ.get("SNAP_REV", "rev_b")
MIN_MM3 = float(os.environ.get("MIN_MM3", "0.5"))
t0 = time.time()
doc = App.newDocument("snap")
Import.insert(os.path.join(REPO, "fusion", "snapshot", REV, "assembly.step"), doc.Name)
solids = []
for o in doc.Objects:
    s = getattr(o, "Shape", None)
    if s is None or s.isNull() or not s.Solids or o.TypeId != "Part::Feature":
        continue
    pl = o.getGlobalPlacement() if hasattr(o, "getGlobalPlacement") else o.Placement
    sh = s.copy()
    sh.Placement = pl
    for i, so in enumerate(sh.Solids):
        solids.append(("%s%s" % (o.Label, "" if len(sh.Solids) == 1 else "#%d" % i), so))
print("solids:", len(solids), "load %.0f s" % (time.time() - t0), flush=True)
boxes = [s.BoundBox for _, s in solids]
hits, tested = [], 0
for i, j in itertools.combinations(range(len(solids)), 2):
    if not boxes[i].intersect(boxes[j]):
        continue
    tested += 1
    try:
        v = solids[i][1].common(solids[j][1]).Volume
    except Exception as e:
        hits.append(dict(a=solids[i][0], b=solids[j][0], error=str(e)))
        continue
    if v > MIN_MM3:
        hits.append(dict(a=solids[i][0], b=solids[j][0], volume_mm3=round(v, 2)))
hits.sort(key=lambda h: -h.get("volume_mm3", 0))
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
res = dict(revision=REV, solids=len(solids), pairs_tested=tested, min_mm3=MIN_MM3, overlaps=hits,
           seconds=round(time.time() - t0, 1))
json.dump(res, open(os.path.join(HERE, "out", "%s_interference.json" % REV), "w"), indent=1)
print("pairs tested %d, overlaps > %.1f mm3: %d, %.0f s" % (tested, MIN_MM3, len(hits), time.time() - t0))
for h in hits[:25]:
    print("  %8s  %s  x  %s" % (h.get("volume_mm3", "ERR"), h["a"], h["b"]))
