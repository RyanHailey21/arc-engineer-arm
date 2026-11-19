"""Level-keeping stage-2 check (parallelogram rocker -> ROD2 -> level member, which replaced the GT2 belt).

  1. closure: rod 2's far pin lands on the level member's lever pin at every task pose and donut-lift sample;
  2. dead-point margin: |th2 - V2_ANG| mod 180 stays >= MARGIN_MIN over the task poses, the CAD donut-lift path
     and the elbow joint limits (export_robot.py) - so the linkage can never reach a dead point;
  3. sweep: ROD2, the rocker and level member (with their pins) against every other part (overlap volume), over
     the elbow range at reachable shoulder angles, and the wrist-pitch range at the task poses. CAD's interference check tests task
     poses only; this covers the motion between them for the parts that moved.

quick_check.py runs 1 + 2 (closure_margins(), < 1 s); 3 is the slow part and runs only here.
Writes out/<variant>/level_keeping.txt and a cad-evidence record.
    python -I cad/tools/run.py --grip FOURBAR cad/tools/check_level_keeping.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(HERE)
sys.path.insert(0, CAD)
import FreeCAD as App  # noqa: E402
import arm_model as M  # noqa: E402
import field as Fd  # noqa: E402
import params  # noqa: E402

V = App.Vector
MARGIN_MIN = 20.0           # deg from a dead point at any task pose / lift sample
LIMIT_MARGIN_MIN = 5.0      # deg from a dead point at the elbow joint limits
OVERLAP_MIN = 1.0           # mm^3: a real overlap (touching mates are ~0)
REL_RANGE = (-160.0, -50.0)  # elbow - shoulder: tasks use -150 (STOW) .. -60, plus 10 deg
TH1_RANGE = (35.0, 170.0)    # shoulder: tasks use 39 .. 165 (outside it, stage-1 parts touch: pre-existing)
PITCH_NEED = {"PIPE_CHUTE": (-10.0, 93.0), "PIPE_CHUTE_ROLL90": (-10.0, 93.0)}   # wrist pitch needed per pose (others: own pitch +/- 10)
ELBOW_LIMITS = (-86.0, 51.0)          # export_robot.py limits
PITCH_LIMITS = (-30.0, 120.0)
MOVED = ("ROD2", "ROCKER", "LEVEL")


def margin(th2):
    r = (M.K["V2_ANG"] - th2) % 180.0
    return min(r, 180.0 - r)


def closure_margins():
    """Checks 1 + 2 (pure kinematics, < 1 s, no shape booleans): (ok, report lines, summary dict).
    quick_check.py runs this; the sweep (check 3) stays a milestone check."""
    lines = []
    v2 = M.u(M.K["V2_ANG"], M.K["V2_LEN"])
    samples = [(n,) + tuple(M.pose_q(n)[0]) for n in M.POSES]
    samples += [("lift z%.0f" % z, *M.ik(Fd.POLE_X, z, 0.0), 0.0, r) for z, _y, r in Fd.donut_lift_path()]
    worst_c, worst_m, worst_n = 0.0, 180.0, ""
    for name, th1, th2, pitch, roll in samples:
        plc = M.placements(th1, th2, pitch, roll)
        c = (plc["ROD2"].multVec(V(M.K["L3"], 0, 0)) - plc["LEVEL"].multVec(V(v2[0], 0, v2[1]))).Length
        worst_c = max(worst_c, c)
        if margin(th2) < worst_m:
            worst_m, worst_n = margin(th2), name
    lim_m = min(margin(t) for t in ELBOW_LIMITS)
    ok_c, ok_m, ok_l = worst_c < 1e-6, worst_m >= MARGIN_MIN, lim_m >= LIMIT_MARGIN_MIN
    lines.append("closure: worst %.1e mm over %d poses/lift samples  %s" % (worst_c, len(samples), "PASS" if ok_c else "FAIL"))
    lines.append("dead-point margin: min %.1f deg at %s (need >= %.0f)  %s" % (worst_m, worst_n, MARGIN_MIN, "PASS" if ok_m else "FAIL"))
    lines.append("dead-point margin at elbow limits %s: %.1f deg (need >= %.0f)  %s"
                 % (ELBOW_LIMITS, lim_m, LIMIT_MARGIN_MIN, "PASS" if ok_l else "FAIL"))
    return ok_c and ok_m and ok_l, lines, dict(closure_mm=worst_c, samples=len(samples), margin_deg=round(worst_m, 1),
                                               margin_at=worst_n, limit_margin_deg=round(lim_m, 1))


def main():
    t0 = time.time()
    ok, lines, _d = closure_margins()
    B = M.build_bodies()

    # 3: sweep clearance of the moved bodies against every other body
    def placed_chk(plc, names):
        out = []
        for bn in names:
            for p in B[bn]:
                if p.chk.isNull() or not getattr(p, "check", True):
                    continue
                s = p.chk.copy()
                s.Placement = plc[bn].multiply(p.chk.Placement)
                out.append((bn, p.name, s))
        return out
    others = [b for b in B if b not in MOVED and b not in ("GROUND",)]

    def overlaps(th1, th2, pitch, roll=0.0):
        """[(pair, volume mm^3)] of moved-body parts overlapping any other part (touching mates have ~0 volume)."""
        plc = M.placements(th1, th2, pitch, roll)
        mv = placed_chk(plc, MOVED)
        ot = placed_chk(plc, others + list(MOVED))
        out = []
        for bn, pn, s in mv:
            bb = s.BoundBox
            for bo, po, so in ot:
                if bo == bn or (bo in MOVED and (bo, po) <= (bn, pn)) or not bb.intersect(so.BoundBox):
                    continue
                v = s.common(so).Volume
                if v > OVERLAP_MIN:
                    out.append(("%s/%s x %s/%s" % (bn, pn, bo, po), v))
        return out

    # (a) elbow sweep over the joint limits, at shoulder angles the elbow drive actually reaches
    #     (elbow - shoulder within REL_RANGE: the task poses use -156 .. -60)
    poses = []
    for k in range(23):
        th2 = ELBOW_LIMITS[0] + (ELBOW_LIMITS[1] - ELBOW_LIMITS[0]) * k / 22
        lo, hi = max(TH1_RANGE[0], th2 - REL_RANGE[1]), min(TH1_RANGE[1], th2 - REL_RANGE[0])
        if lo > hi:
            continue
        for j in range(5):
            poses.append((lo + (hi - lo) * j / 4, th2, 0.0))
    hits = {}
    for th1, th2, pitch in poses:
        for pair, v in overlaps(th1, th2, pitch):
            if v > hits.get(pair, (0, ""))[0]:
                hits[pair] = (v, "th1 %.0f th2 %.0f" % (th1, th2))
    ok_s = not hits
    lines.append("elbow sweep: %d poses (elbow %s, elbow-shoulder %s), moved bodies %s vs all parts: %d overlapping pairs  %s"
                 % (len(poses), ELBOW_LIMITS, REL_RANGE, MOVED, len(hits), "PASS" if ok_s else "FAIL"))
    for k, (v, where) in sorted(hits.items()):
        lines.append("  OVERLAP %s: %.1f mm^3 at %s" % (k, v, where))
    # (b) wrist-pitch sweep at the task poses: clash-free pitch range per pose vs what that pose needs
    ok_p = True
    for name in ("STOW", "DONUT_PLACE", "DONUT_LIFT", "PIPE_LIFT", "PIPE_CHUTE", "PIPE_CHUTE_ROLL90"):
        (th1, th2, p0, roll), _jaw = M.pose_q(name)
        need = PITCH_NEED.get(name, (p0 - 10.0, p0 + 10.0))
        lo, hi, first = PITCH_LIMITS[0], PITCH_LIMITS[1], None

        def edge(clear, hit):          # bisect the first contact between a clear and a hitting pitch (0.25 deg)
            while abs(hit - clear) > 0.25:
                mid = (clear + hit) / 2
                if overlaps(th1, th2, mid, roll):
                    hit = mid
                else:
                    clear = mid
            return clear
        prev = p0
        for k in range(31):                        # upward from the pose's own pitch
            pitch = p0 + (PITCH_LIMITS[1] - p0) * k / 30
            ov = overlaps(th1, th2, pitch, roll)
            if ov:
                hi, first = edge(prev, pitch), "%s near pitch %.1f" % (ov[0][0], pitch)
                break
            prev = pitch
        prev = p0
        for k in range(1, 31):                     # downward
            pitch = p0 - (p0 - PITCH_LIMITS[0]) * k / 30
            ov = overlaps(th1, th2, pitch, roll)
            if ov:
                lo = edge(prev, pitch)
                first = first or "%s near pitch %.1f" % (ov[0][0], pitch)
                break
            prev = pitch
        good = lo <= need[0] and hi >= need[1]
        ok_p = ok_p and good
        lines.append("pitch sweep %-12s (elbow %6.1f): clash-free %5.1f .. %5.1f deg, needs %4.0f .. %4.0f  %s%s"
                     % (name, th2, lo, hi, need[0], need[1], "PASS" if good else "FAIL",
                        ("  (first contact: %s)" % first) if first else ""))
    ok = ok and ok_s and ok_p
    verdict = "PASS" if ok else "FAIL"
    lines.append("LEVEL_KEEPING %s: %s (%.0f s)" % (M.GRIP.lower(), verdict, time.time() - t0))
    out_dir = os.path.join(CAD, "out", M.GRIP.lower())
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "level_keeping.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    params.record("level_keeping", verdict, files=[os.path.join(out_dir, "level_keeping.txt")], note=lines[-1])
    return 0 if ok else 1


if not os.environ.get("QC_IMPORT"):        # quick_check.py imports closure_margins() only
    sys.exit(main())
