# -*- coding: utf-8 -*-
"""Parameter flow test: a value set in params/gripper_fourbar.toml must reach the geometry.  Overrides XMAX at
the loader (as if the TOML were edited back to the first head's 165) and expects the pole envelope to fire;
also checks the default variant comes from params/variant.toml.  Run with freecadcmd; prints TEST PASS / FAIL."""
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # this checkout or worktree (TI-022)
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ.pop("GRIP", None)
os.environ["QC_NOMAIN"] = "1"
import params                                                   # noqa: E402
fb = params.load("gripper_fourbar")
fb["FB"]["XMAX"] = 165.0                                        # loader-level override = edited TOML
import arm_model as M                                           # noqa: E402
import quick_check as Q                                         # noqa: E402
ok_var = M.GRIP == params.load("variant")["grip"].upper()
ok, res = Q.envelopes(M.build_bodies())
hit = [r for r in res if r["envelope"] == "pole_above_fingers" and not r["ok"]]
print("TEST %s: variant from file %s (%s); XMAX=165 from params %s" % (
    "PASS" if hit and ok_var else "FAIL", ok_var, M.GRIP, "flagged by the pole envelope" if hit else "NOT flagged"))
