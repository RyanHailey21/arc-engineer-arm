# -*- coding: utf-8 -*-
"""Negative test: the envelope check must catch the pole clash the first four-bar head had
(jaw blocks reaching x 165 above the pads).  Run with freecadcmd; prints TEST PASS / TEST FAIL."""
import os
import sys
CAD = r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["GRIP"] = "FOURBAR"
os.environ["QC_NOMAIN"] = "1"
import arm_model as M          # noqa: E402
M.FB["XMAX"] = 165.0           # the original (clashing) reach
import quick_check as Q        # noqa: E402
ok, res = Q.envelopes(M.build_bodies())
hit = [r for r in res if r["envelope"] == "pole_above_fingers" and not r["ok"]]
print("TEST %s: pole_above_fingers %s" % ("PASS" if hit else "FAIL",
      "flagged " + ", ".join(h["part"] for h in hit[0]["hits"]) if hit else "NOT flagged"))
