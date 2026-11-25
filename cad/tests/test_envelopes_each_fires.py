# -*- coding: utf-8 -*-
"""Negative test (TI-037): quick_check's envelope step (step 1) must flag a part inside EVERY keep-out of
cad/envelopes/*.toml, at every pose it lists, and only in the scope it names.  Until now only pole_above_fingers
had a test (test_envelope_catches_pole.py, gripper frame); the five world-frame keep-outs (base plate, lower tier,
perimeter wall, scoring platform) and pole_below_donut were never shown to fire.  In memory only:
  1. for each (keep-out, pose) a 4 mm probe cube is added to HEAD (in both scopes), placed so that at that pose it
     sits inside the keep-out box (10 mm inside any open bound): that row must FAIL with the probe among its hits,
     and no row that passed before may gain a hit from any other part;
  2. scope: for each "gripper" keep-out the same probe on FOREARM (not a gripper body) must NOT be flagged there.
The unmodified model must pass every row first.  Exit 1 on FAIL.
    python -I cad/tools/run.py cad/tests/test_envelopes_each_fires.py      (then with BASE_DRIVE=DIRECT)
"""
import os
import sys
import tomllib
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # this checkout or worktree (TI-022)
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
os.environ["QC_NOMAIN"] = "1"
import FreeCAD as App            # noqa: E402
import Part                      # noqa: E402
import arm_model as M            # noqa: E402
import quick_check as Q          # noqa: E402

V = App.Vector
SIDE, INSET, OPEN = 4.0, 10.0, 1e4 - 1.0
PROBE = "EnvelopeProbe"


def target(kz):
    """A point inside the keep-out box: the middle of a closed span, INSET inside a one-sided bound, 0 if open."""
    pt = []
    for lo, hi in zip(kz["min"], kz["max"]):
        lo_open, hi_open = lo <= -OPEN, hi >= OPEN
        pt.append(0.0 if lo_open and hi_open else hi - INSET if lo_open else lo + INSET if hi_open else (lo + hi) / 2)
    return V(*pt)


def frame_of(body, kz, pose):
    """Placement of `body` in the keep-out's frame at `pose`, as the check computes it."""
    q, jaw = M.pose_q(pose)
    jaw = kz.get("jaw", jaw)
    if kz["frame"] == "gripper":
        plc = M.placements(q[0], q[1], q[2], 0.0, jaw=jaw)
        return plc["GRIPPER"].inverse().multiply(plc[body])
    return M.placements(*q, jaw=jaw)[body]


def probe(body, kz, pose):
    """A SIDE mm cube in `body`'s frame whose centre lands on target(kz) at `pose`."""
    local = frame_of(body, kz, pose).inverse().multVec(target(kz))
    box = Part.makeBox(SIDE, SIDE, SIDE, local - V(SIDE, SIDE, SIDE) * 0.5)
    return M.Part_(PROBE, box, box, "PRINT", None, (1, 0, 0))


def run_with(bodies, body, part):
    bodies[body].append(part)
    try:
        return Q.envelopes(bodies)
    finally:
        bodies[body].remove(part)


def key(r):
    return r["envelope"], r["pose"]


bodies = M.build_bodies()
keepouts = []
for fn in sorted(os.listdir(os.path.join(CAD, "envelopes"))):
    if fn.endswith(".toml"):
        keepouts += tomllib.load(open(os.path.join(CAD, "envelopes", fn), "rb"))["keepout"]

fails = []
ok0, res0 = Q.envelopes(bodies)
base = {key(r): {h["part"] for h in r["hits"]} for r in res0}
if not ok0:
    fails.append("fixture: envelopes FAIL on the unmodified model: %s" % [k for k, v in base.items() if v])
n_rows = 0
for kz in keepouts:
    for pose in kz["poses"]:
        n_rows += 1
        ok, res = run_with(bodies, "HEAD", probe("HEAD", kz, pose))
        row = {key(r): {h["part"] for h in r["hits"]} for r in res}
        if ok or PROBE not in row.get((kz["name"], pose), set()):
            fails.append("%s @ %s: probe at %s inside the box NOT flagged" % (kz["name"], pose, tuple(target(kz))))
        other = {k: v - base.get(k, set()) - {PROBE} for k, v in row.items()}
        other = {k: v for k, v in other.items() if v}
        if other:
            fails.append("%s @ %s: other parts started hitting: %s" % (kz["name"], pose, other))
        print("  %-26s %-18s flagged %s" % (kz["name"], pose, PROBE in row.get((kz["name"], pose), set())))
        if kz["bodies"] == "gripper":
            _ok, res = run_with(bodies, "FOREARM", probe("FOREARM", kz, pose))
            row = {key(r): {h["part"] for h in r["hits"]} for r in res}
            if PROBE in row.get((kz["name"], pose), set()):
                fails.append("%s @ %s: probe on FOREARM flagged by a gripper-only keep-out" % (kz["name"], pose))
            print("  %-26s %-18s FOREARM probe ignored %s" % ("", "", PROBE not in row.get((kz["name"], pose), set())))

if n_rows != len(res0):
    fails.append("expected %d (keep-out, pose) rows, the check reported %d" % (n_rows, len(res0)))
for f in fails:
    print("  FAIL " + f)
print("TEST %s: %d keep-outs, %d (keep-out, pose) rows each flag a probe inside them (%s)" % (
    "FAIL" if fails else "PASS", len(keepouts), n_rows, M.VARIANT))
sys.exit(1 if fails else 0)
