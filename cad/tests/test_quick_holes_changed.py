# -*- coding: utf-8 -*-
"""Negative test (TI-005): quick_check's holes/eng step must flag a hole-wall and a thread-engagement defect in the
parts the fingerprint says changed, the defects that used to surface only in the full run.  In memory only:
  1. a second hole is drilled 0.5 mm beside a full hole of Jaw_Block_L (wall < check_holes.MIN_ABS);
  2. the screw of the first blind tapped hole in the engagement report (J1_Output_Hub M3 on GEARED) is pushed
     1 mm past the end of its thread.
Each must be found by changed_parts() from fingerprint entries and FAIL in changed_holes(); before the edit the same
parts must pass.  Exit 1 on FAIL.
    python -I cad/tools/run.py cad/tests/test_quick_holes_changed.py      (then with BASE_DRIVE=DIRECT)
"""
import os
import sys
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(CAD, "tools"))
os.environ["QC_IMPORT"] = "1"
os.environ["QC_NOMAIN"] = "1"
import FreeCAD as App            # noqa: E402
import Part                      # noqa: E402
import arm_model as M            # noqa: E402
import check_engagement as E     # noqa: E402
import check_holes as H          # noqa: E402
import fingerprint as F          # noqa: E402
import quick_check as Q          # noqa: E402

bodies = M.build_bodies()
find = {p.name: (bn, p) for bn, ps in bodies.items() for p in ps}
fails = []


def entry(p):
    return dict(kind=p.kind, chk=F.shape_fp(p.chk), vis=F.shape_fp(p.vis))


def run(case, bn, p, edit, want):
    key = (bn, p.name)
    ok0, rows0, _n = Q.changed_holes(bodies, {key})
    if not ok0:
        fails.append("%s: fails before the edit: %s" % (case, rows0[:2]))
    before = {"parts": {"%s/%s" % key: entry(p)}}
    edit(p)
    after = {"parts": {"%s/%s" % key: entry(p)}}
    changed = Q.changed_parts(before, after)
    if changed != {key}:
        fails.append("%s: changed_parts gave %s, want %s" % (case, changed, {key}))
    ok1, rows1, note = Q.changed_holes(bodies, changed or {key})
    hit = [r for r in rows1 if r.startswith(want) and p.name in r]
    if ok1 or not hit:
        fails.append("%s: not flagged (%s; %s)" % (case, note, rows1[:2]))
    print("  %-11s %s -> %s" % (case, note, hit[0] if hit else "no %s row" % want))


# 1. thin wall: a parallel hole 0.5 mm beside the first full hole of a gripper part
bn, jaw = find["Jaw_Block_L"]
full = [g for g in H.hole_groups(jaw.vis).values() if g["span"] >= 359.0]
if not full:
    fails.append("fixture: Jaw_Block_L has no full hole")
else:
    g = full[0]
    ax, r = g["axis"], g["r"]
    side = ax.cross(App.Vector(0, 0, 1) if abs(ax.z) < 0.9 else App.Vector(1, 0, 0)).normalize()
    bb = jaw.vis.BoundBox

    def drill(p):
        L = bb.DiagonalLength * 2
        cyl = Part.makeCylinder(r, L, g["centre"] + side * (2 * r + 0.5) - ax * (L / 2), ax)
        p.vis = p.vis.cut(cyl)
    run("thin wall", bn, jaw, drill, ("FAIL", "BROKEN"))

# 2. engagement: the screw of the first blind tapped hole pushed 1 mm past the end of its thread
q, jaw_ = M.pose_q("STOW")
placed = list(M.placed(bodies, *q, jaw=jaw_, which="vis"))
blind = sorted(r for r in E.scan(placed)[0] if r.startswith("OK") and " blind " in r)
if not blind:
    fails.append("fixture: no blind tapped hole with a screw in %s" % M.VARIANT)
else:
    w = blind[0].split()                 # OK part M3 blind drill 4.5 thread 3.0 screw NAME engages 3.0
    hub_name, size, thread, scr_name, eng = w[1], int(w[2][1:]), float(w[7]), w[9], float(w[11])
    bn_s, scr = find[scr_name]
    shp = {p.name: s for (_b, p, s) in placed if p.name in (scr_name, hub_name)}
    sc = shp[scr_name].BoundBox.Center

    def off_axis(h):
        d = sc - h["c"]
        return (d - h["ax"] * d.dot(h["ax"])).Length
    h = min((h for h in E.holes(shp[hub_name]) if E.TAP.get(round(h["r"], 2)) == size), key=off_axis)
    ts = (sc - h["c"]).dot(h["ax"])
    deeper = h["ax"] * (1.0 if abs(h["t1"] - ts) > abs(h["t0"] - ts) else -1.0)
    # the screw is in body bn_s's frame; carry the world-frame push back into it
    loc = M.placements(*q, jaw=jaw_)[bn_s].inverse()
    push = loc.Rotation.multVec(deeper * (thread - eng + 1.0))

    def sink(p):
        for sh in (p.vis, p.chk):
            sh.translate(push)
    run("engagement", bn_s, scr, sink, ("FAIL",))

print("TEST %s: quick_check holes/eng on changed parts%s" % ("FAIL" if fails else "PASS", "".join("\n  " + f for f in fails)))
sys.stdout.flush()
if fails:
    sys.exit(1)
