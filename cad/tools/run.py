# -*- coding: utf-8 -*-
"""Run a FreeCAD script headless and never lose its output, traceback or exit code.

    python -I cad/tools/run.py cad/tools/check_engagement.py [args ...]
    python -I cad/tools/run.py --grip FOURBAR cad/tests/test_catalogue_mass.py
    python -I cad/tools/run.py --timeout 600 cad/check_interference.py

Why (cad/docs/tooling_issues.md TI-010, TI-018): on this machine `freecadcmd script.py`
  - printed nothing at all for short scripts (a PASS/FAIL test looked like it passed), and
  - exited 1 with no output when the script raised (the traceback was swallowed).
This launcher (plain Python, no FreeCAD import) starts freecadcmd with `-c` code that runs the script through
runpy with a real __file__ and sys.argv, prints any traceback, flushes, and exits with the script's code.
It ends with one line:  RUN <script>: OK|FAIL (exit N) in S s.
Exit codes: the script's own (0 OK, a SystemExit code, 1 on an uncaught exception), 124 on timeout, 2 on bad usage.
"""
import argparse
import json
import os
import subprocess
import sys
import time

FREECADCMD = os.environ.get("FREECADCMD") or os.path.join(
    os.environ.get("LOCALAPPDATA", ""), "Programs", "FreeCAD 1.1", "bin", "freecadcmd.exe")

# Runs inside freecadcmd. Values arrive as one JSON literal, so paths and args need no quoting.
BOOT = r'''
import json as _j, os as _o, runpy as _r, sys as _s, traceback as _t
_a = _j.loads(%s)
_s.argv = [_a["script"]] + _a["args"]
_d = _o.path.dirname(_a["script"])
if _d not in _s.path:
    _s.path.insert(0, _d)
_code = 0
try:
    _r.run_path(_a["script"], run_name="__main__")
except SystemExit as _e:
    _code = _e.code if isinstance(_e.code, int) else (0 if _e.code is None else 1)
    if not isinstance(_e.code, (int, type(None))):
        print(_e.code)
except BaseException:
    _t.print_exc(file=_s.stdout)
    _code = 1
_s.stdout.flush(); _s.stderr.flush()
_o._exit(_code)
'''

BANNER = ("FreeCAD ", "(C) 2001", "FreeCAD is free and open-source")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--grip", help="set GRIP for the run (SCREW / FOURBAR)")
    ap.add_argument("--timeout", type=float, default=900, help="seconds (default 900)")
    ap.add_argument("--banner", action="store_true", help="keep FreeCAD's start-up banner")
    ap.add_argument("script")
    ap.add_argument("args", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    script = os.path.abspath(a.script)
    if not os.path.isfile(script):
        print("RUN %s: no such file" % a.script)
        return 2
    if not os.path.isfile(FREECADCMD):
        print("RUN: freecadcmd not found at %s (set FREECADCMD)" % FREECADCMD)
        return 2
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    if a.grip:
        env["GRIP"] = a.grip.upper()
    payload = json.dumps(json.dumps({"script": script, "args": a.args}))
    t0 = time.time()
    try:
        p = subprocess.run([FREECADCMD, "-c", BOOT % payload], env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=a.timeout)
        out, code = p.stdout, p.returncode
    except subprocess.TimeoutExpired as e:
        out, code = e.stdout or b"", 124
    text = out.decode("utf-8", "replace")
    lines = [ln for ln in text.splitlines() if a.banner or not ln.startswith(BANNER)]
    while lines and not lines[0].strip():
        lines.pop(0)
    body = "\n".join(lines)
    try:
        print(body)
    except UnicodeEncodeError:
        print(body.encode("ascii", "backslashreplace").decode("ascii"))
    tag = "OK" if code == 0 else ("TIMEOUT" if code == 124 else "FAIL")
    print("RUN %s: %s (exit %d) in %.1f s" % (os.path.relpath(script), tag, code, time.time() - t0))
    return code


if __name__ == "__main__":
    sys.exit(main())
