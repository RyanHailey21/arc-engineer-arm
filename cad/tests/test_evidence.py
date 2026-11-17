# -*- coding: utf-8 -*-
"""Evidence-format tests (plain Python, no FreeCAD):  python -I cad/tests/test_evidence.py
params.record() must write cad-evidence/1 reports that the mechanical-workflow-template's verify_report accepts,
that it rejects once an artifact changes, and that map statuses honestly (WARN -> pass, crash -> unknown).
Uses a throw-away variant directory (cad/out/evidencetest/) and removes it afterwards."""
import json
import os
import shutil
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.environ.get("MWT_DIR", r"C:\Users\ryanh\tools\mechanical-workflow-template")
os.environ["GRIP"] = "EVIDENCETEST"
sys.path.insert(0, CAD)
import params  # noqa: E402

JOB = os.path.join(CAD, "out", "evidencetest")
fails = 0


def check(name, cond, detail=""):
    global fails
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else ": " + detail))
    fails += 0 if cond else 1


try:
    shutil.rmtree(JOB, ignore_errors=True)
    rep_txt = os.path.join(params.out_dir(), "demo_report.txt")
    open(rep_txt, "w").write("demo check: 0 problems\n")
    ext = os.path.join(CAD, "out", "evidence_external_copy.txt")          # outside the job dir -> external copy
    open(ext, "w").write("copy\n")
    ev = params.record("demo", "PASS", [rep_txt, ext], "synthetic check")
    rep = os.path.join(JOB, "demo.evidence.json")
    check("report written", os.path.exists(rep))
    check("schema", ev["schema"] == "cad-evidence/1" and ev["status"] == "pass", ev["schema"] + " " + ev["status"])
    check("external copy kept out of artifacts", ev["extensions"]["external_copies"] == ["out/evidence_external_copy.txt"]
          and [a["path"] for a in ev["artifacts"]] == ["demo_report.txt"], json.dumps(ev["artifacts"]))
    check("input snapshot inside job dir", ev["inputs"][0]["path"] == "evidence/demo.inputs.json")

    sys.path.insert(0, TEMPLATE)
    try:
        import evidence as mwt
    except ImportError:
        mwt = None
    check("template verify_report available", mwt is not None, TEMPLATE)
    if mwt:
        try:
            mwt.verify_report(rep)
            check("verify_report accepts the report", True)
        except Exception as e:
            check("verify_report accepts the report", False, repr(e))
        open(rep_txt, "a").write("tampered\n")
        try:
            mwt.verify_report(rep)
            check("verify_report rejects a changed artifact", False, "accepted")
        except ValueError as e:
            check("verify_report rejects a changed artifact", "changed" in str(e), str(e))

    check("WARN maps to pass", params.record("demo_warn", "WARN", [], "3 warnings")["status"] == "pass")
    check("crash maps to unknown", params.record("demo_crash", "TIMEOUT", [], "killed")["status"] == "unknown")
    man = json.load(open(os.path.join(JOB, "manifest.json")))
    check("manifest indexes reports", man["demo"]["evidence"] == "demo.evidence.json" and man["demo_warn"]["status"] == "WARN")
    ev_rows = {r[0]: r for r in params.evidence()}
    check("fresh against current inputs", ev_rows["demo"][3] == "FRESH", str(ev_rows.get("demo")))
finally:
    shutil.rmtree(JOB, ignore_errors=True)
    try:
        os.remove(os.path.join(CAD, "out", "evidence_external_copy.txt"))
    except OSError:
        pass

print("TESTS: %s" % ("all passed" if not fails else "%d failed" % fails))
sys.exit(1 if fails else 0)
