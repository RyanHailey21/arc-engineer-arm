# -*- coding: utf-8 -*-
"""TI-039: every test in cad/tests/ can exit non-zero.  Plain Python:  python -I cad/tests/test_tests_exit_code.py

Two tests printed TEST FAIL but always exited 0, so `tools/run.py` reported "OK (exit 0)" on a failure and a gate
that reads the exit code passed (the TI-010 class).  Rule, for every cad/tests/test_*.py: it must contain a
`sys.exit(X)`, `os._exit(X)` or `raise SystemExit(X)` whose X is not a constant 0 / None / False (so a FAIL path
exists).  `sys.exit(main())` and `sys.exit(1 if fails else 0)` pass; a file with only `sys.exit(0)` or none fails.
Part 2 is the negative test: planted sources without a failing exit are flagged, the allowed forms are not.
Exit 1 on FAIL.
"""
import ast
import glob
import os
import sys

TESTS = os.path.dirname(os.path.abspath(__file__))


def _is_exit_call(node):
    f = node.func
    return isinstance(f, ast.Attribute) and (
        (f.attr == "exit" and isinstance(f.value, ast.Name) and f.value.id == "sys")
        or (f.attr == "_exit" and isinstance(f.value, ast.Name) and f.value.id == "os"))


def _can_fail(args):
    """False when the exit status is missing or a constant success (0, None, False)."""
    if not args:
        return False
    a = args[0]
    return not (isinstance(a, ast.Constant) and a.value in (0, None, False))


def has_fail_exit(src):
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and _is_exit_call(n) and _can_fail(n.args):
            return True
        if isinstance(n, ast.Raise) and n.exc is not None:
            e = n.exc
            if isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and e.func.id == "SystemExit" \
                    and _can_fail(e.args):
                return True
    return False


fails = []

# 1: the real tests
files = sorted(glob.glob(os.path.join(TESTS, "test_*.py")))
for f in files:
    name = os.path.basename(f)
    try:
        ok = has_fail_exit(open(f, encoding="utf-8").read())
    except SyntaxError as e:
        fails.append("1: %s: syntax error line %s" % (name, e.lineno))
        continue
    if not ok:
        fails.append("1: %s never exits non-zero; end it with sys.exit(0 if passed else 1)" % name)
if len(files) < 20:
    fails.append("1: only %d tests found; the glob is broken" % len(files))

# 2: planted sources, (name, source, can it exit non-zero?)
CASES = [
    ("print_only", 'print("TEST FAIL")\n', False),
    ("exit_zero", 'import sys\nprint("TEST FAIL")\nsys.exit(0)\n', False),
    ("exit_none", 'import sys\nsys.exit()\n', False),
    ("raise_zero", 'raise SystemExit(0)\n', False),
    ("other_exit", 'import foo\nfoo.exit(1)\n', False),
    ("ternary", 'import sys\nfails = []\nsys.exit(1 if fails else 0)\n', True),
    ("main", 'import sys\ndef main():\n    return 0\nsys.exit(main())\n', True),
    ("guarded", 'import sys\nok = True\nif not ok:\n    sys.exit(1)\n', True),
    ("raise", 'ok = True\nraise SystemExit(0 if ok else 1)\n', True),
    ("os_exit", 'import os\nos._exit(2)\n', True),
]
wrong = [(n, want) for n, src, want in CASES if has_fail_exit(src) != want]
fails += ["2: %s %s" % (n, "allowed form flagged" if want else "planted, not flagged") for n, want in wrong]
n_bad = sum(1 for c in CASES if not c[2])

print("TEST %s: %d tests in cad/tests/ can exit non-zero (%d planted bad, %d allowed forms)%s" % (
    "FAIL" if fails else "PASS", len(files), n_bad, len(CASES) - n_bad, "".join("\n  " + f for f in fails)))
sys.exit(1 if fails else 0)
