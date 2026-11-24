# -*- coding: utf-8 -*-
"""Negative test: quick_check's self-hit (step 3) and mass/torque (step 4) lines must FAIL on a defect of their own
class, injected in memory only:
  1. self-hit: at the pipe jaw only, JAW_L is moved 20 mm toward JAW_R, past the 13.8 mm pad gap.  The step caches each
     part pair by its relative placement, so this also proves a change at one jaw value is not masked by the pairs
     computed at the others: every hit must be at the pipe jaw, at both rolls, and include a JAW_L/JAW_R pair.
  2. mass/torque: a 1 kg steel block (STEEL density from params/materials.toml) added to HEAD at the TCP.  The
     past-wrist mass must rise by the block's mass and the worst J3 (wrist pitch) utilisation must pass 1.0.
The unmodified model must PASS both lines first, and both must PASS again afterwards.  Exit 1 on FAIL.
    python -I cad/tools/run.py cad/tests/test_quick_selfhit_torque.py      (then with BASE_DRIVE=DIRECT)
"""
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_NOMAIN"] = "1"           # import quick_check without running it
os.environ["QC_IMPORT"] = "1"
import FreeCAD as App            # noqa: E402
import Part                      # noqa: E402
import arm_model as M            # noqa: E402
import quick_check as Q          # noqa: E402

bodies = M.build_bodies()
fails = []

ok_sh, hits = Q.self_hit(bodies)
ok_mt, mt0 = Q.mass_torque(bodies)
if not ok_sh:
    fails.append("fixture: self-hit FAILs on the unmodified model: %s" % hits[:3])
if not ok_mt:
    fails.append("fixture: mass/torque FAILs on the unmodified model: %s" % mt0["rated_utilisation"])

# 1. self-hit: the jaws coincide at the pipe jaw only
real_placements = M.placements


def jaws_together(*a, **kw):
    """JAW_L moved 20 mm toward JAW_R (local -y; both jaws are built in the gripper frame, L at +y, R at -y), past
    the 13.8 mm pad gap, at the pipe jaw only."""
    plc = dict(real_placements(*a, **kw))
    if abs(kw.get("jaw", 0.0) - M.PIPE_JAW) < 1e-9:
        plc["JAW_L"] = plc["JAW_L"].multiply(App.Placement(App.Vector(0, -20.0, 0), App.Rotation()))
    return plc


jaw_l = {p.name for p in bodies["JAW_L"]}
jaw_r = {p.name for p in bodies["JAW_R"]}
M.placements = jaws_together
try:
    ok, hits = Q.self_hit(bodies)
finally:
    M.placements = real_placements
off_jaw = [h for h in hits if abs(h["jaw"] - M.PIPE_JAW) > 1e-9]
rolls = {h["roll"] for h in hits}
jaw_pair = [h for h in hits if {h["a"], h["b"]} & jaw_l and {h["a"], h["b"]} & jaw_r]
if ok or not hits:
    fails.append("self-hit: JAW_L 20 mm into JAW_R at jaw %.1f still PASS" % M.PIPE_JAW)
elif off_jaw or rolls != {0.0, 90.0} or not jaw_pair:
    fails.append("self-hit: expected hits only at jaw %.1f, both rolls, a JAW_L/JAW_R pair; got %d off-jaw, rolls %s, "
                 "%d jaw pairs" % (M.PIPE_JAW, len(off_jaw), sorted(rolls), len(jaw_pair)))

# 2. mass/torque: a 1 kg steel block at the TCP, in the HEAD frame
steel = M.MAT["STEEL"]                         # g/cm^3
side = (1000.0 / steel * 1000.0) ** (1 / 3)    # mm, cube of 1000 g
tcp = App.Vector(M.K["GRIP"], 0, -M.K["DROP"])
box = Part.makeBox(side, side, side, tcp - App.Vector(side, side, side) * 0.5)
block = M.Part_("TestBlock_1kg", box, box, "STEEL", None, (0.5, 0.5, 0.5), check=False)
bodies["HEAD"].append(block)
try:
    ok, mt = Q.mass_torque(bodies)
finally:
    bodies["HEAD"].remove(block)
added = mt["past_wrist_g"] - mt0["past_wrist_g"]
if abs(added - 1000.0) > 1.0:
    fails.append("mass/torque: past-wrist mass rose by %.1f g, expected 1000 g" % added)
if ok or mt["rated_utilisation"]["J3"] <= 1.0:
    fails.append("mass/torque: 1 kg at the TCP still PASS (J3 utilisation %.3f, was %.3f)" % (
        mt["rated_utilisation"]["J3"], mt0["rated_utilisation"]["J3"]))

ok_sh, _h = Q.self_hit(bodies)
ok_mt, _m = Q.mass_torque(bodies)
if not (ok_sh and ok_mt):
    fails.append("model not restored after the test")

print("TEST %s: %s/%s quick_check self-hit + mass/torque, 2 defects injected (J3 utilisation %.3f -> %.3f)%s" % (
    "FAIL" if fails else "PASS", M.GRIP, M.BASE_DRIVE, mt0["rated_utilisation"]["J3"], mt["rated_utilisation"]["J3"],
    "".join("\n  " + f for f in fails)))
sys.stdout.flush()
if fails:
    sys.exit(1)
