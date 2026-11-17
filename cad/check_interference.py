# -*- coding: utf-8 -*-
"""
Interference sweep for the ARC Engineer arm.  Run headless:
    freecadcmd check_interference.py         (or via the FreeCAD MCP headless tool)

1. Static assembly: every pair of parts (same or different body) at STOW.
2. Motion sweep: joint-space interpolation through the donut and pipe sequences
   (STEPS per segment), every pair of parts on different rigid bodies, plus
   the held objective vs the arm.
3. Field clearance: arm (+ held objective) vs Battlefield items at each task pose.
Writes cad/out/<variant>/interference_report.txt (+ manifest entry). Overlap threshold 0.5 mm^3
(face-to-face mating contacts such as a bearing in its bore report 0).

Results are cached in .cache/interference_cache.json, keyed by a geometry
fingerprint of each part's check shape plus the pair's relative placement, so
a re-run only re-booleans pairs whose geometry or relative pose changed
(delete the file or set NOCACHE=1 to force a full recompute).
"""
import json
import re
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, HERE)
import arm_model as M          # noqa: E402
import params                  # noqa: E402
import field as F              # noqa: E402

TOL = 0.5
STEPS = 5


def bodies_for(jaw=None):
    return M.build_bodies()


CACHE_FILE = os.path.join(HERE, ".cache", "interference_cache.json")
CACHE = {}
STATS = dict(hit=0, miss=0)
_FP = {}


def fingerprint(shape):
    """Cheap geometry fingerprint of a shape in its own frame."""
    k = id(shape)
    if k not in _FP:
        b = shape.BoundBox
        _FP[k] = "%.2f/%.2f/%d/%.2f,%.2f,%.2f,%.2f,%.2f,%.2f" % (
            shape.Volume, shape.Area, len(shape.Faces), b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)
    return _FP[k]


def relkey(pa, pb):
    m = pa.inverse().multiply(pb).toMatrix()
    return ",".join("%.3f" % v for v in (m.A11, m.A12, m.A13, m.A14, m.A21, m.A22, m.A23, m.A24,
                                          m.A31, m.A32, m.A33, m.A34))


def overlaps(a, b, ka=None, kb=None):
    """a, b: world shapes; ka, kb: (local fingerprint, body placement) for caching."""
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    key = None
    if ka and kb and not os.environ.get("NOCACHE"):
        key = ka[0] + "|" + kb[0] + "|" + relkey(ka[1], kb[1])
        if key in CACHE:
            STATS["hit"] += 1
            return CACHE[key]
    STATS["miss"] += 1
    try:
        v = a.common(b).Volume
    except Exception:
        v = -1.0          # boolean failure -> flag for manual look
    if key:
        CACHE[key] = v
    return v


def pose_shapes(q, jaw, held_scene=None):
    """-> list of (body, part, world_shape, (local fingerprint, body placement))."""
    plc = M.placements(*q, jaw=jaw)
    out = [(b, p, s, (fingerprint(p.chk), plc[b])) for (b, p, s) in M.placed(bodies_for(jaw), *q, jaw=jaw)
           if p.check]
    if held_scene:
        h = F.held_object(held_scene)
        if h:
            s = h[1].copy()
            s.Placement = plc["HEAD"]
            out.append(("HELD", M.Part_(h[0], h[1], h[1], "-", "-", h[2]), s, (fingerprint(h[1]), plc["HEAD"])))
    return out


def check_pose(shapes, same_body=False):
    hits = []
    for i in range(len(shapes)):
        bi, pi, si, ki = shapes[i]
        for j in range(i + 1, len(shapes)):
            bj, pj, sj, kj = shapes[j]
            if bi == bj and not same_body:
                continue
            # held object legitimately touches pads only (zero volume) - still checked
            v = overlaps(si, sj, ki, kj)
            if v > TOL or v < 0:
                hits.append((pi.name, pj.name, v))
    return hits


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def main():
    t0 = time.time()
    if os.path.exists(CACHE_FILE) and not os.environ.get("NOCACHE"):
        try:
            CACHE.update(json.load(open(CACHE_FILE)))
        except Exception:
            pass
    lines = []
    log = lines.append
    log("ARC Engineer arm - interference report")
    log("threshold %.1f mm^3, %d steps per segment\n" % (TOL, STEPS))

    # 1. static assembly
    q, jaw = M.pose_q("STOW")
    hits = check_pose(pose_shapes(q, jaw), same_body=True)
    log("[1] static assembly @STOW (all part pairs): %d overlaps" % len(hits))
    for h in hits:
        log("    %-34s x %-34s %8.1f mm^3" % h)

    # 2. motion: FULL=1 -> interpolated sweep through both sequences; default -> every task pose
    worst = {}
    n = 0
    if os.environ.get("FULL"):
        segs = []
        for seq_name, seq in M.SEQUENCES.items():
            segs += [(seq_name, a_, b_) for a_, b_ in zip(seq[:-1], seq[1:])]
        steps = STEPS
    else:
        segs = [("pose", p_, p_) for p_ in M.POSES]
        steps = 0
    for seq_name, a, b in segs:
        qa, ja = M.pose_q(a)
        qb, jb = M.pose_q(b)
        held = None
        if a.startswith(("DONUT_LIFT", "DONUT_PLACE")) or (a == "DONUT_PICK" and b != a):
            held = "DONUT_LIFT"
        if a.startswith(("PIPE_LIFT", "PIPE_CHUTE")) or (a == "PIPE_GRASP" and b != a):
            held = "PIPE_LIFT"
        if (a == "DONUT_PLACE" or a.startswith("PIPE_CHUTE")) and b == "STOW":
            held = None
        for k in range(steps + 1):
            t = k / steps if steps else 0.0
            q = lerp(qa, qb, t)
            jaw = ja + (jb - ja) * t
            for h in check_pose(pose_shapes(q, jaw, held)):
                key = (h[0], h[1])
                if key not in worst or h[2] > worst[key][0]:
                    worst[key] = (h[2], "%s %s->%s t=%.1f q=(%.0f,%.0f,%.0f,%.0f)" % (seq_name, a, b, t, *q))
            n += 1
    log("\n[2] motion %s: %d poses, %d distinct overlapping pairs" % ("sweep" if steps else "task poses (quick)", n, len(worst)))
    for (pa, pb), (v, where) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
        log("    %-34s x %-34s %8.1f mm^3  worst @ %s" % (pa, pb, v, where))

    # 3. field clearance at task poses
    log("\n[3] field clearance at task poses")
    total = 0
    for name in M.POSES:
        if name == "STOW":
            continue
        q, jaw = M.pose_q(name)
        shapes = pose_shapes(q, jaw, name)
        items = F.scene_items(name)
        if q[3]:   # rolled grasp: the target pipe leans with the jaws (models grasping a leaning pipe)
            plc0 = M.placements(q[0], q[1], q[2], 0.0, jaw)["HEAD"]
            T = M.placements(*q, jaw=jaw)["HEAD"].multiply(plc0.inverse())
            items = [(n_, (s_.transformGeometry(T.toMatrix()) if n_.endswith("Target") else s_), c_) for (n_, s_, c_) in items]
        bad = []
        ident = M.App.Placement()
        for (fname, fs, _c) in items:
            kf = (fingerprint(fs), ident)
            for (bn, p, s, k) in shapes:
                v = overlaps(s, fs, k, kf)
                if v > TOL or v < 0:
                    bad.append((p.name, fname, v))
        total += len(bad)
        log("  %-15s q=(%6.1f,%6.1f,%5.1f) jaw=%5.1f : %s" % (name, q[0], q[1], q[2], jaw,
                                                            "clear" if not bad else "%d overlaps" % len(bad)))
        for b in bad:
            log("      %-34s x %-28s %8.1f mm^3" % b)

    # 3b. donut lift along the pole (Cartesian path + chassis strafe), arm + held donut vs pole/tier
    path = F.donut_lift_path(n=int(os.environ.get("PATH_N", "24")))
    pole_items = [it for it in F.scene_items("DONUT_LIFT")]
    bad_path = {}
    for (z, yc, rl) in path:
        q = M.ik(F.POLE_X, z, 0.0) + (0.0, rl)
        shapes = pose_shapes(q, 100.0, "DONUT_LIFT")
        T = M.App.Placement(M.App.Vector(0, -yc, 0), M.App.Rotation())
        for (fname, fs, _c) in pole_items:
            ws = fs.copy()
            ws.Placement = T
            kf = (fingerprint(fs), T)
            for (bn, p, s, k) in shapes:
                v = overlaps(s, ws, k, kf)
                if v > TOL or v < 0:
                    key = (p.name, fname)
                    if key not in bad_path or v > bad_path[key][0]:
                        bad_path[key] = (v, z)
    log("\n[3b] donut lift along the pole: %d samples (tcp z %.0f..%.0f, strafe %.0f..%.0f mm): %s" % (
        len(path), path[0][0], path[-1][0], min(p_[1] for p_ in path), max(p_[1] for p_ in path),
        "clear" if not bad_path else "%d overlapping pairs" % len(bad_path)))
    for (pa, pb), (v, z) in sorted(bad_path.items(), key=lambda kv: -kv[1][0]):
        log("      %-34s x %-28s %8.1f mm^3 worst @ tcp z %.0f" % (pa, pb, v, z))

    # 4. static torque with modelled masses
    log("\n[4] static joint torques from modelled masses (N*m: shoulder J1, elbow J2, wrist pitch J3, roll J4)")
    for name in M.POSES:
        q, jaw = M.pose_q(name)
        pay = 300.0 if name.startswith(("DONUT_LIFT", "DONUT_PLACE")) else (165.0 if name.startswith(("PIPE_LIFT", "PIPE_CHUTE")) else 0.0)
        arm = 250.0 - 47.0 if name.startswith(("PIPE_LIFT", "PIPE_CHUTE")) else None
        tau = M.static_torques(bodies_for(jaw), *q, payload_g=pay, payload_arm=arm, jaw=jaw)
        log("  %-17s payload %3.0f g : J1 %6.2f  J2 %6.2f  J3 %6.2f  J4 %6.2f" % (name, pay, *tau))
    mass = sum(M.part_mass_g(p) for parts in bodies_for().values() for p in parts)   # motors split stator/rotor in part_mass_g
    log("\nModelled arm mass incl. motors and gripper drive: %.0f g" % mass)
    log("boolean cache: %d hits, %d computed" % (STATS["hit"], STATS["miss"]))
    log("elapsed %.0f s" % (time.time() - t0))
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(CACHE, f)
    rep = os.path.join(params.out_dir(), "interference_report.txt")
    with open(rep, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    txt = "\n".join(lines)
    bad = [int(n) for n in re.findall(r"(\d+) (?:distinct )?overlapping", txt) + re.findall(r": (\d+) overlaps", txt)]
    params.record("interference_full", "FAIL" if any(bad) else "PASS", [rep],
                  "static, 14 task poses, field clearance, donut lift")


main()
