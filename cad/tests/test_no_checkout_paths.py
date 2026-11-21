# -*- coding: utf-8 -*-
"""TI-022: no live code names an absolute checkout path.  Plain Python:  python -I cad/tests/test_no_checkout_paths.py

Four tests and a quick-check script set CAD = r"C:\\Users\\<user>\\light_weight_arm\\cad".  Run from a git worktree
(.claude/worktrees/<name>/), they imported, checked and wrote to the user's main checkout instead.  Code must find
the repo from its own __file__.

Rule, for every tracked or untracked-not-ignored *.py (the bloat_report file list, so .claude/ is skipped) outside the
frozen rev A package and release generators (bloat_keep.toml [[path]] globs):
  - a string constant holding an absolute user-home path (X:\\Users\\..., /c/Users/..., /home/..., /Users/...) is a
    finding,
  - unless it is a docstring (usage examples), or
  - its statement is the `... if "__file__" in globals() else r"..."` fallback, which only applies when the
    code is exec'd in the FreeCAD GUI without a __file__.
Part 2 is the negative test: planted sources with a bare path are flagged, the allowed forms are not.
Exit 1 on FAIL.
"""
import ast
import fnmatch
import os
import re
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CAD, "tools"))
import bloat_report as B  # noqa: E402



def repo_name():
    """Folder name of the main checkout (a worktree's own folder is named after the worktree, not the repo)."""
    for args in (["rev-parse", "--path-format=absolute", "--git-common-dir"],):
        out = B._git(*args)
        if out:
            return os.path.basename(os.path.dirname(os.path.normpath(out[0].strip())))
    return os.path.basename(B.ROOT)


REPO = repo_name()
SEP = r"(?:\\\\|\\|/)+"
# X:\Users\<u>\...\<repo>, /c/Users/<u>/.../<repo>, /home/<u>/.../<repo>: a home path that leads into this repo.
# Paths to other tools (an MWT_DIR default, synthetic test data) are not this hazard and are not flagged.
HOME_PATH = re.compile(r"(?:\b[A-Za-z]:%s|(?<![\w.])/(?:[a-z]/)?)(?:Users|home)%s(?:[^\\/\s\"']+%s)*?%s(?![\w-])"
                       % (SEP, SEP, SEP, re.escape(REPO)), re.IGNORECASE)


def _docstrings(tree):
    ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                ids.add(id(b.value))
    return ids


def findings(path, src):
    """[(path, line, text)] for every absolute home path in a non-docstring string outside a __file__ fallback."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [(path, e.lineno or 0, "syntax error: cannot check")]
    lines = src.splitlines()
    docs = _docstrings(tree)
    stmts = [n for n in ast.walk(tree) if isinstance(n, ast.stmt)]
    out = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)) or id(n) in docs:
            continue
        m = HOME_PATH.search(n.value)
        if not m:
            continue
        inner = min((s for s in stmts if s.lineno <= n.lineno <= s.end_lineno),
                    key=lambda s: s.end_lineno - s.lineno, default=None)
        seg = "\n".join(lines[inner.lineno - 1:inner.end_lineno]) if inner else ""
        if "__file__" in seg and "globals()" in seg:
            continue                                   # GUI exec fallback (no __file__ there)
        out.append((path, n.lineno, m.group(0)))
    return out


fails = []

# 1: the real tree
paths, _items = B.load_keep()
globs = [p["glob"] for p in paths]
SELF = "cad/tests/test_no_checkout_paths.py"            # its planted sources in part 2 are paths on purpose
files = [f for f in B.py_files() if f != SELF and not any(fnmatch.fnmatch(f, g) for g in globs)]
files.append("cad/tools/bloat_report.py")              # B.py_files() leaves out its own source; check it too
real = []
for f in sorted(set(files)):
    real += findings(f, open(os.path.join(B.ROOT, f), encoding="utf-8", errors="replace").read())
for p, ln, txt in real:
    fails.append("1: %s:%d names %s; resolve the repo from __file__" % (p, ln, txt))
if len(files) < 30:
    fails.append("1: only %d files checked; the file list is broken" % len(files))

# 2: negative and allowed forms
BAD = {
    "bare_assign": 'CAD = r"C:\\Users\\someone\\@R@\\cad"\n',
    "sys_path": 'import sys\nsys.path.insert(0, r"C:\\Users\\someone\\@R@\\cad")\n',
    "forward_slash": 'P = "C:/Users/someone/@R@/cad"\n',
    "nested": 'P = r"D:\\Users\\someone\\src\\@R@"\n',
    "git_bash": 'P = "/c/Users/someone/@R@"\n',
    "posix_home": 'P = "/home/someone/work/@R@/cad"\n',
    "escaped": 'P = "C:\\\\Users\\\\someone\\\\@R@\\\\cad"\n',
    "fstring": 'x = 1\nP = f"C:\\\\Users\\\\someone\\\\@R@\\\\{x}"\n',
}
OK = {
    "file_fallback": 'import os\nCAD = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \\\n'
                     '    r"C:\\Users\\someone\\@R@\\cad"\n',
    "docstring": '"""Usage:  {"python": r"C:\\\\Users\\\\someone\\\\@R@\\\\x.py"}"""\nX = 1\n',
    "comment": 'X = 1   # was C:\\Users\\someone\\@R@\n',
    "relative": 'P = "cad/out/users/x.json"\n',
    "other_tool": 'import os\nT = os.environ.get("MWT_DIR", r"C:\\Users\\someone\\tools\\template")\n',
    "longer_name": 'P = r"C:\\Users\\someone\\@R@_old\\cad"\n',
    "test_data": 'P = "/c/Users/x/y.py"\n',
}
BAD = {k: v.replace("@R@", REPO) for k, v in BAD.items()}
OK = {k: v.replace("@R@", REPO) for k, v in OK.items()}
for name, src in BAD.items():
    if not findings(name + ".py", src):
        fails.append("2: planted %s not flagged" % name)
for name, src in OK.items():
    got = findings(name + ".py", src)
    if got:
        fails.append("2: allowed form %s flagged: %s" % (name, got))

print("TEST %s: no absolute checkout paths in %d live .py files (%d planted bad, %d allowed forms)%s" % (
    "FAIL" if fails else "PASS", len(files), len(BAD), len(OK), "".join("\n  " + f for f in fails)))
sys.exit(1 if fails else 0)
