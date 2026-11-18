# -*- coding: utf-8 -*-
"""Regression test (TI-017): check_engagement must judge every screw in the model.
  - Until 2026-11-17 it matched name.split('_')[0], so SB5x6_..., SB5x12_... shoulder screws were never checked.
  - The prefix fix still missed SetScrew_M3x3_drum / _screwgear / SetScrew_M3_motorgear (case), SCREW variant.
is_screw() now uses the catalogue key.  This test cross-checks it against the names: every CAT part whose name
starts (any case) with a screw type, SB5 or SetScrew must be picked, and every picked part must be CAT.
Fails (exit 1) if a screw is missed or the variant has no shoulder screw to exercise the regression.
    python -I cad/tools/run.py --grip SCREW cad/tests/test_engagement_screws.py      (then --grip FOURBAR)
"""
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
import arm_model as M            # noqa: E402
import check_engagement as E     # noqa: E402

NAME_PREFIX = ("SHCS", "BHCS", "CSK", "SETSCREW", "SB5")
missed, odd, n, kinds = [], [], 0, {}
for bn, ps in M.build_bodies().items():
    for p in ps:
        got = E.is_screw(p)
        by_name = p.kind == "CAT" and p.name.upper().startswith(NAME_PREFIX)
        n += got
        if got:
            kinds[p.src] = kinds.get(p.src, 0) + 1
        if by_name and not got:
            missed.append("%s/%s (src %s)" % (bn, p.name, p.src))
        if got and not by_name:
            odd.append("%s/%s (src %s)" % (bn, p.name, p.src))     # screw by catalogue, unusual name: report only
fails = ["missed: " + ", ".join(missed[:8])] if missed else []
if not kinds.get("SB5"):
    fails.append("fixture: no SB5 shoulder screw in this variant, so the original regression is not exercised")
print("TEST %s: %s %d screws by catalogue key (%s)%s%s" % (
    "FAIL" if fails else "PASS", M.GRIP, n, ", ".join("%s %d" % kv for kv in sorted(kinds.items())),
    "; unusual names: " + ", ".join(odd[:5]) if odd else "", "".join("\n  " + f for f in fails)))
sys.stdout.flush()
if fails:
    sys.exit(1)
