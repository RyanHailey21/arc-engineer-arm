# -*- coding: utf-8 -*-
"""tools/run.py tests (plain Python; starts freecadcmd, ~10 s):  python -I cad/tests/test_run.py
A raising script must show its traceback and exit 1; a short printing script must show its output (TI-010/TI-018)."""
import os
import subprocess
import sys
import tempfile

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(CAD, "tools", "run.py")


def run(src, *args):
    d = tempfile.mkdtemp(prefix="run_py_")
    f = os.path.join(d, "s.py")
    open(f, "w", encoding="utf-8").write(src)
    p = subprocess.run([sys.executable, "-I", RUN, *args, f], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


CASES = [
    ("short_print_shows", 'print("hello from freecad")\n', [], 0, ["hello from freecad", ": OK (exit 0)"]),
    ("traceback_shows", 'def f():\n    raise ValueError("boom 42")\nf()\n', [], 1,
     ["Traceback", "ValueError: boom 42", ": FAIL (exit 1)"]),
    ("exit_code_kept", 'import sys\nprint("x")\nsys.exit(3)\n', [], 3, [": FAIL (exit 3)"]),
    ("file_and_grip", 'import os\nprint("F", os.path.basename(__file__), os.environ.get("GRIP"))\n',
     ["--grip", "fourbar"], 0, ["F s.py FOURBAR"]),
    ("freecad_imports", 'import FreeCAD, Part\nprint("vol", round(Part.makeBox(1, 2, 3).Volume))\n', [], 0, ["vol 6"]),
]

if __name__ == "__main__":
    bad = 0
    for name, src, args, want_code, want in CASES:
        code, out = run(src, *args)
        miss = [w for w in want if w not in out]
        if code != want_code or miss:
            bad += 1
            print("FAIL %s: exit %s (want %s), missing %s\n%s" % (name, code, want_code, miss, out))
        else:
            print("PASS", name)
    print("%d/%d passed" % (len(CASES) - bad, len(CASES)))
    sys.exit(1 if bad else 0)
