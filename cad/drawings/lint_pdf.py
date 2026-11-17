# -*- coding: utf-8 -*-
"""
Drawing overlap lint on the exported TechDraw PDF (PyMuPDF).
    python -I cad/drawings/lint_pdf.py cad/drawings/out/*.pdf      -> report, exit 1 on any overlap
Checks, in page millimetres:
  * text vs text   : two text lines whose boxes intersect (dimension values, callouts, notes)
  * text vs border : text outside the drawing frame (inner border) or inside the title-block area
                     when it is not template text
  * text vs geometry: text box crossed by vector strokes that are part of a view (hatch excluded)
Template text (title block, tolerance block, zone letters) is ignored by position.
"""
import json
import sys

import pymupdf

PT2MM = 25.4 / 72.0
FRAME = (20.0, 20.0, 412.0, 260.0)            # inner border (mm, y down) of ANSI B landscape
TEMPLATE_ZONE = (195.0, 210.0, 412.0, 260.0)  # tolerance + title block (y down)


def _inter(a, b, pad=0.0):
    return not (a[2] <= b[0] + pad or b[2] <= a[0] + pad or a[3] <= b[1] + pad or b[3] <= a[1] + pad)


def _area(a):
    return max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])


def _overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def text_boxes(page):
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            txt = "".join(sp["text"] for sp in ln["spans"]).strip()
            if not txt:
                continue
            x0, y0, x1, y1 = [v * PT2MM for v in ln["bbox"]]
            out.append(dict(t=txt, b=(x0, y0, x1, y1)))
    return out


def stroke_segments(page):
    segs = []
    for d in page.get_drawings():
        if d.get("fill") is not None and d.get("color") is None:
            continue                                       # filled shapes (arrowheads, hatch fills)
        for it in d["items"]:
            if it[0] == "l":
                p, q = it[1], it[2]
                segs.append((p.x * PT2MM, p.y * PT2MM, q.x * PT2MM, q.y * PT2MM))
            elif it[0] == "re":
                r = it[1]
                for (a, b, c, e) in ((r.x0, r.y0, r.x1, r.y0), (r.x1, r.y0, r.x1, r.y1),
                                     (r.x1, r.y1, r.x0, r.y1), (r.x0, r.y1, r.x0, r.y0)):
                    segs.append((a * PT2MM, b * PT2MM, c * PT2MM, e * PT2MM))
            elif it[0] == "c":
                p, q = it[1], it[4]
                segs.append((p.x * PT2MM, p.y * PT2MM, q.x * PT2MM, q.y * PT2MM))
    return segs


def _seg_hits_box(s, b, shrink=0.35):
    x0, y0, x1, y1 = b[0] + shrink, b[1] + shrink, b[2] - shrink, b[3] - shrink
    if x1 <= x0 or y1 <= y0:
        return False
    # Liang-Barsky clip
    dx, dy = s[2] - s[0], s[3] - s[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, s[0] - x0), (dx, x1 - s[0]), (-dy, s[1] - y0), (dy, y1 - s[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


def lint(path, own_boxes=None):
    page = pymupdf.open(path)[0]
    texts = [t for t in text_boxes(page) if not _inter(t["b"], TEMPLATE_ZONE)
             and t["b"][1] > 8 and t["b"][3] < 270 and t["b"][0] > 8]
    issues = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = texts[i], texts[j]
            ov = _overlap(a["b"], b["b"])
            if ov > 0.15 * min(_area(a["b"]), _area(b["b"])):
                issues.append(("text/text", a["t"], b["t"]))
    for t in texts:
        b = t["b"]
        if b[0] < FRAME[0] or b[2] > FRAME[2] or b[1] < FRAME[1] or b[3] > FRAME[3]:
            issues.append(("outside frame", t["t"], ""))
    segs = stroke_segments(page)
    for t in texts:
        hits = sum(1 for s in segs if _seg_hits_box(s, t["b"]))
        if hits >= 2:                                      # 1 = own underline / leader kink is normal
            issues.append(("text/lines", t["t"], "%d strokes" % hits))
    return issues


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    bad = 0
    res = {}
    for f in sys.argv[1:]:
        iss = lint(f)
        res[f] = iss
        bad += bool(iss)
        print("%-45s %s" % (f.split("\\")[-1].split("/")[-1], "OK" if not iss else "%d issues" % len(iss)))
        for i in iss[:12]:
            print("    %-14s %-38s %s" % i)
    sys.exit(1 if bad else 0)
