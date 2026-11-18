# -*- coding: utf-8 -*-
"""
Thread engagement check for tapped holes in custom metal parts (headless):
    freecadcmd cad/tools/check_engagement.py      (writes cad/out/<variant>/engagement_report.txt; release variant also cad/fab/)

For every tapped hole (modelled tap-drill radius -> thread size) in an AL/BRASS custom part, the screw
that sits in it (assembled STOW pose) is found and its penetration L along the hole axis measured.
  FAIL  L > threaded length (blind: drill depth - 1.5 mm runout, as the drawing generator calls it)
  WARN  L < 0.8 D (short engagement in aluminium)
Through-tapped holes are threaded over their full length.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else \
    r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, HERE)
import FreeCAD as App  # noqa: E402
import Part            # noqa: E402
import arm_model as M  # noqa: E402
import params  # noqa: E402

V = App.Vector
TAP = {1.25: 3, 1.27: 3, 1.4: 3, 1.7: 4, 2.1: 5}     # modelled radius -> M size
RUNOUT = 1.5
SCREWS = ("SHCS", "BHCS", "CSK", "SETSCREW", "SB5")     # data/catalogue.toml keys of screw types


def is_screw(p):
    """A screw is a CAT part whose catalogue key is a screw type.  Name matching missed parts twice (TI-017):
    an exact first token never saw SB5x6_... shoulder screws, and a prefix still missed SetScrew_... (case).
    Regression test: tests/test_engagement_screws.py."""
    return p.kind == "CAT" and p.src in SCREWS


def holes(shape):
    out = {}
    for f in shape.Faces:
        s = f.Surface
        if s.__class__.__name__ != "Cylinder" or round(s.Radius, 2) not in TAP:
            continue
        ax, c = V(s.Axis).normalize(), V(s.Center)
        p = f.valueAt(*[(a + b) / 2 for a, b in zip(f.ParameterRange[0::2], f.ParameterRange[1::2])])
        n = f.normalAt(*[(a + b) / 2 for a, b in zip(f.ParameterRange[0::2], f.ParameterRange[1::2])])
        rad = (p - c) - ax * (p - c).dot(ax)
        if rad.Length < 1e-9 or n.dot(rad) > 0:
            continue                                    # convex = shaft, not a hole
        foot = c - ax * c.dot(ax)
        key = (round(foot.x, 2), round(foot.y, 2), round(foot.z, 2), round(abs(ax.x), 3), round(abs(ax.y), 3), round(abs(ax.z), 3), round(s.Radius, 2))
        ts = [(v.Point - c).dot(ax) for v in f.Vertexes]
        h = out.setdefault(key, dict(r=s.Radius, c=c, ax=ax, t0=1e9, t1=-1e9))
        h["t0"], h["t1"] = min(h["t0"], min(ts)), max(h["t1"], max(ts))
    return list(out.values())


def main():
    bodies = M.build_bodies()
    q, jaw = M.pose_q("STOW")
    placed = list(M.placed(bodies, *q, jaw=jaw, which="vis"))
    screws = [(p, s) for (_b, p, s) in placed if is_screw(p)]
    rows, nf, nw, n = [], 0, 0, 0
    for (_b, p, s) in placed:
        if p.kind not in ("AL", "BRASS") or s.isNull():
            continue
        for h in holes(s):
            n += 1
            c, ax, r = h["c"], h["ax"], h["r"]
            L_h = h["t1"] - h["t0"]
            e0, e1 = c + ax * (h["t0"] - 0.3), c + ax * (h["t1"] + 0.3)
            o0, o1 = not s.isInside(e0, 1e-4, True), not s.isInside(e1, 1e-4, True)
            thru = o0 and o1
            thread = L_h if thru else max(L_h - RUNOUT, 0.0)
            probe = Part.makeCylinder(r + 0.3, L_h, c + ax * h["t0"], ax)
            best = None
            for (sp, ss) in screws:
                if not ss.BoundBox.intersect(probe.BoundBox):
                    continue
                cm = ss.common(probe)
                if cm.Volume < 1e-3:
                    continue
                ts = [(v.Point - c).dot(ax) for v in cm.Vertexes] or [0.0]
                L = max(ts) - min(ts)
                if best is None or L > best[1]:
                    best = (sp.name, L)
            if best is None:
                continue                                # no screw (e.g. spare / set-screw access) - not judged
            D = TAP[round(r, 2)]
            st = "OK"
            if best[1] > thread + 0.05:
                st, nf = "FAIL", nf + 1
            elif best[1] < 0.8 * D:
                st, nw = "WARN", nw + 1
            rows.append("%-4s %-28s M%d %s drill %.1f thread %.1f  screw %-28s engages %.1f" % (
                st, p.name, D, "THRU" if thru else "blind", L_h, thread, best[0], best[1]))
    head = "Thread engagement: %d tapped holes, %d with screws -> %d FAIL (screw past thread), %d WARN (< 0.8D)" % (
        n, len(rows), nf, nw)
    txt = "\n".join([head] + sorted(rows))
    outs = [os.path.join(params.out_dir(), "engagement_report.txt")]
    if params.grip() == params.release_variant():
        outs.append(os.path.join(HERE, "fab", "engagement_report.txt"))      # read by the rev A TDP
    for o in outs:
        with open(o, "w", encoding="utf-8") as fh:
            fh.write(txt + "\n")
    print(txt)
    params.record("engagement", "FAIL" if nf else ("WARN" if nw else "PASS"), outs, head)


if not os.environ.get("QC_IMPORT"):          # tests import is_screw / holes without running the check
    main()
