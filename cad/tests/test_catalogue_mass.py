# -*- coding: utf-8 -*-
"""Purchased-part mass sanity (TI-015): for every catalogue item, the modelled mass must equal
units x catalogue mass.  Nothing caught it on 2026-11-16 when each DM-J4340 (stator part + rotor part) was counted
twice in part_mass_g; it was found only while building the BOM.  The check itself is tools/catalogue_mass.py
(also run by quick_check); this test runs it on the real model and on a restored copy of the old bug.

Prints TEST PASS / TEST FAIL.  Run for the variant in GRIP (both).  TI-010: exec it, because a short script
passed to freecadcmd by path printed nothing:
    set GRIP=SCREW   (then FOURBAR)
    freecadcmd -c "exec(open(r'cad/tests/test_catalogue_mass.py').read())"
"""
import os
import sys
CAD = r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
import arm_model as M          # noqa: E402
import catalogue_mass as CM    # noqa: E402

bodies = M.build_bodies()
fails = []
ok, d = CM.check(bodies, M.CAT, M.part_mass_g)
if not ok:
    fails += d["fails"]


def double_count(p):          # the pre-fix part_mass_g: every split part at full catalogue mass
    if p.kind == "CAT":
        return M.CAT[p.src]["mass"] if p.src in M.CAT else 0
    return M.part_mass_g(p)


if d["split"]:
    ok2, d2 = CM.check(bodies, M.CAT, double_count)
    if ok2 or not any("modelled" in f for f in d2["fails"]):
        fails.append("negative case: the restored double count was NOT reported")

print("TEST %s: catalogue mass %s, %d keys, %d purchased units%s%s" % (
    "FAIL" if fails else "PASS", M.GRIP, d["keys"], d["units"],
    "; split: " + ", ".join("%s %s" % kv for kv in d["split"].items()) if d["split"] else "",
    "".join("\n  " + f for f in fails)))
sys.stdout.flush()
