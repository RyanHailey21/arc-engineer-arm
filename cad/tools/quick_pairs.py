# -*- coding: utf-8 -*-
"""
Targeted motion check: only parts whose name matches FILTER (regex) are checked
against every part on other bodies, at every task pose.  Use after a local
change instead of the full check_interference.py sweep.
    set FILTER=Belt|Pulley|Rocker|Level|Rod_1|Gear ; freecadcmd cad/tools/quick_pairs.py
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals()
                else r"C:\Users\ryanh\light_weight_arm\cad")
import arm_model as M   # noqa: E402

FILTER = re.compile(os.environ.get("FILTER", "."))
TOL = 0.5
t0 = time.time()
bodies = M.build_bodies()
worst = {}
for pose in M.POSES:
    q, jaw = M.pose_q(pose)
    sh = [x for x in M.placed(bodies, *q, jaw=jaw) if x[1].check]
    sel = [x for x in sh if FILTER.search(x[1].name)]
    for (ba, pa, sa) in sel:
        for (bb, pb, sb) in sh:
            if bb == ba or pb is pa or not sa.BoundBox.intersect(sb.BoundBox):
                continue
            key = tuple(sorted((pa.name, pb.name)))
            try:
                v = sa.common(sb).Volume
            except Exception:
                v = -1.0
            if (v > TOL or v < 0) and (key not in worst or v > worst[key][0]):
                worst[key] = (v, pose)
print("targeted motion check (%s): %d poses, %d overlapping pairs, %.0f s"
      % (FILTER.pattern, len(M.POSES), len(worst), time.time() - t0))
for (a, b), (v, pose) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
    print("  %-34s x %-34s %8.1f mm^3 @ %s" % (a, b, v, pose))
