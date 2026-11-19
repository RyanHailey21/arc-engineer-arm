# -*- coding: utf-8 -*-
"""Test for tools/bloat_report.py: planted bloat is found, keep-listed items are not flagged.  Plain Python.
    python -I cad/tests/test_bloat_report.py          (exit 1 on FAIL)

1. A planted module with a dead function, an unused import and an unused local, plus a planted params file with
   an orphan key: all four are findings; the function and key the planted code does use are not.
2. The same dead function under a keep-list item is "kept" with its reason, not a finding.
3. The real keep-list: nothing in the rev A package (fab/, drawings/out, fea/out, render/) or a release generator
   is a finding; the GT2 belt hardware and the GT2-BELT catalogue entry are never findings.
"""
import fnmatch
import os
import sys
import tempfile

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CAD, "tools"))
import bloat_report as B  # noqa: E402

fails = []
PLANT = '''import json
import os


def planted_live_helper():
    return os.getcwd()


def planted_dead_helper_xq():
    unused_local_xq = 3
    return 1


P = {"PLANTED_READ_KEY_XQ": planted_live_helper()}
'''
TOML = """[PLANTED]
PLANTED_READ_KEY_XQ = 1.0
PLANTED_ORPHAN_KEY_XQ = 2.0     # nothing reads this
"""
path = "cad/tests/_planted_bloat.py"
files = [f for f in B.py_files() if not f.endswith("test_bloat_report.py")]   # this file names the plants in strings
with tempfile.TemporaryDirectory() as td:
    with open(os.path.join(td, "planted.toml"), "w") as fh:
        fh.write(TOML)
    res = B.scan(files=files, extra_sources={path: PLANT}, params_dir=td)
    ids = {f["id"] for f in res["findings"]}
    want = ["dead-def:%s:planted_dead_helper_xq" % path, "unused-import:%s:json" % path,
            "unused-variable:%s:planted_dead_helper_xq.unused_local_xq" % path]
    for w in want:
        if w not in ids:
            fails.append("1: planted %s not found" % w)
    if not any(i.startswith("orphan-param:") and i.endswith("PLANTED.PLANTED_ORPHAN_KEY_XQ") for i in ids):
        fails.append("1: planted orphan param not found")
    for bad in ("planted_live_helper", "PLANTED_READ_KEY_XQ", "unused-import:%s:os" % path):
        if any(bad in i for i in ids):
            fails.append("1: false positive: %s" % bad)

    # 2: keep-list item for the planted dead function
    paths, items = B.load_keep()
    keep = (paths, items + [dict(kind="dead-def", name="planted_dead_*", reason="planted keep for the test")])
    res2 = B.scan(files=files, extra_sources={path: PLANT}, keep=keep, params_dir=td)
    did = "dead-def:%s:planted_dead_helper_xq" % path
    if did in {f["id"] for f in res2["findings"]}:
        fails.append("2: keep-listed dead function still a finding")
    if not any(f["id"] == did and f["kept"] == "planted keep for the test" for f in res2["kept"]):
        fails.append("2: keep-listed dead function not reported as kept")

# 3: the real report against the real keep-list
res3 = B.scan()
frozen = ["cad/fab/**", "cad/drawings/out/**", "cad/fea/out/**", "cad/render/**", "cad/export_fab.py",
          "cad/fea/run_fea.py", "cad/drawings/*.py", "cad/build_assembly.py"]
for f in res3["findings"]:
    if any(fnmatch.fnmatch(f["path"], g) for g in frozen) or any(fnmatch.fnmatch(f.get("other", ""), g) for g in frozen):
        fails.append("3: frozen/release item flagged: %s" % f["id"])
    if f["name"] in ("GT2-BELT", "GT2_T") or f["name"].startswith("gt2_"):
        fails.append("3: rev A belt item flagged: %s" % f["id"])

print("TEST %s: bloat_report planted bloat found, keep-list respected (%s)%s" % (
    "FAIL" if fails else "PASS", B.counts_line(res3), "".join("\n  " + f for f in fails)))
sys.exit(1 if fails else 0)
