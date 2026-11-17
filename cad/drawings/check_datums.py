# -*- coding: utf-8 -*-
"""ASME Y14.5 sheet check: every datum letter referenced in a feature control frame must be defined by a
datum feature symbol on the same sheet.  Reads the saved TechDraw FCStd files (no FreeCAD needed).
    python -I cad/drawings/check_datums.py      -> lists violations, exit 1 if any"""
import glob
import os
import re
import sys
import zipfile

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
bad = 0
for f in sorted(glob.glob(os.path.join(OUT, "ARC-1*.FCStd"))):
    x = zipfile.ZipFile(f).read("Document.xml").decode("utf-8", "replace")
    labels = dict(re.findall(r'<Object name="([^"]+)"[^>]*>\s*<Properties[^>]*>.*?<Property name="Label"[^>]*>\s*<String value="([^"]*)"', x, re.S))
    texts = {}
    for m in re.finditer(r'<Object name="([^"]+)"[^>]*>\s*<Properties.*?</Properties>', x, re.S):
        t = re.search(r'<Property name="Text"[^>]*>\s*<String value="([^"]*)"', m.group(0))
        lab = re.search(r'<Property name="Label"[^>]*>\s*<String value="([^"]*)"', m.group(0))
        if t and lab:
            texts[lab.group(1)] = t.group(1)
    defined = {v for k, v in texts.items() if k.startswith("Datum_")}
    used = set()
    for k, v in texts.items():
        if k.startswith("FCF_"):
            for cell in v.split("|")[2:]:
                cell = cell.strip()
                if re.fullmatch(r"[A-Z]", cell):
                    used.add(cell)
    missing = sorted(used - defined)
    selfref = []
    for k, v in texts.items():                 # a datum feature may not be referenced by its own FCF
        m_ = re.search(r"_g(\d+)$", k)
        if k.startswith("Datum_") and m_:
            f_ = texts.get("FCF_g" + m_.group(1), "")
            if v in [c.strip() for c in f_.split("|")[2:]]:
                selfref.append(v)
    if selfref:
        bad += 1
        print("%-45s datum feature references itself: %s" % (os.path.basename(f), ", ".join(selfref)))
    if missing:
        bad += 1
        print("%-45s datum(s) referenced but not defined: %s" % (os.path.basename(f), ", ".join(missing)))
print("sheets checked: %d, violations: %d" % (len(glob.glob(os.path.join(OUT, "ARC-1*.FCStd"))), bad))
sys.exit(1 if bad else 0)
