# -*- coding: utf-8 -*-
"""apply_patch tests (plain Python, no FreeCAD):  python -I cad/tests/test_apply_patch.py
Edits apply all-or-nothing; a missed anchor writes nothing and points at the closest line (TI-002)."""
import contextlib
import io
import json
import os
import sys
import tempfile

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CAD, "tools"))
import apply_patch as AP  # noqa: E402

CASES = []


def case(fn):
    CASES.append(fn)
    return fn


def run(spec_text, files, ext=".toml", *flags):
    """Write `files` into a temp dir, run the spec there; return (code, output, dir)."""
    d = tempfile.mkdtemp(prefix="apply_patch_")
    for name, text in files.items():
        with open(os.path.join(d, name), "w", encoding="utf-8", newline="") as f:
            f.write(text)
    spec = os.path.join(d, "spec" + ext)
    with open(spec, "w", encoding="utf-8") as f:
        f.write(spec_text.replace("@D@", d.replace("\\", "/")))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = AP.main([spec, *flags])
    return code, buf.getvalue(), d


def read(d, name):
    return open(os.path.join(d, name), encoding="utf-8", newline="").read()


@case
def find_replace():
    code, out, d = run("[[edit]]\nfile = '@D@/a.py'\nfind = '''L = 47.0'''\nreplace = '''L = 42.0'''\n",
                       {"a.py": "x = 1\nL = 47.0\n"})
    assert code == 0, out
    assert read(d, "a.py") == "x = 1\nL = 42.0\n"


@case
def miss_writes_nothing_and_hints():
    spec = ("[[edit]]\nfile = '@D@/a.py'\nfind = 'x = 1'\nreplace = 'x = 2'\n"
            "[[edit]]\nfile = '@D@/a.py'\nfind = 'L = 47.5'\nreplace = 'L = 42.0'\n")
    code, out, d = run(spec, {"a.py": "x = 1\nL = 47.0\n"})
    assert code == 1, out
    assert read(d, "a.py") == "x = 1\nL = 47.0\n", "first edit must not land when the second misses"
    assert "not found" in out and "L = 47.0" in out and "nothing written" in out, out


@case
def whitespace_only_difference_is_named():
    code, out, _ = run("[[edit]]\nfile = '@D@/a.py'\nfind = 'if  x:'\nreplace = 'if y:'\n",
                       {"a.py": "if x:\n    pass\n"})
    assert code == 1 and "different whitespace at line 1" in out, out


@case
def count_must_match():
    code, out, d = run("[[edit]]\nfile = '@D@/a.txt'\nfind = 'a'\nreplace = 'b'\n", {"a.txt": "a a a"})
    assert code == 1 and "occurs 3 times" in out, out
    code, out, d = run("[[edit]]\nfile = '@D@/a.txt'\nfind = 'a'\nreplace = 'b'\ncount = 'all'\n", {"a.txt": "a a a"})
    assert code == 0 and read(d, "a.txt") == "b b b", out


@case
def block_between_anchors_from_file():
    src = "def f():\n    return 1\n\n\ndef g():\n    return 2\n"
    code, out, d = run("[[edit]]\nfile = '@D@/m.py'\nstart = 'def f('\nend = 'def g('\nreplace_file = 'new.py'\n",
                       {"m.py": src, "new.py": "def f():\n    s = '''triple'''\n    return s\n\n\n"})
    assert code == 0, out
    assert read(d, "m.py") == "def f():\n    s = '''triple'''\n    return s\n\n\ndef g():\n    return 2\n"


@case
def crlf_file_keeps_crlf():
    code, out, d = run("[[edit]]\nfile = '@D@/w.txt'\nfind = '''a\nb'''\nreplace = '''A\nB'''\n",
                       {"w.txt": "a\r\nb\r\nc\r\n"})
    assert code == 0, out
    assert read(d, "w.txt") == "A\r\nB\r\nc\r\n"


@case
def syntax_error_blocks_write():
    code, out, d = run("[[edit]]\nfile = '@D@/a.py'\nfind = 'return 1'\nreplace = 'return (1'\n",
                       {"a.py": "def f():\n    return 1\n"})
    assert code == 1 and "does not compile" in out, out
    assert read(d, "a.py") == "def f():\n    return 1\n"


@case
def insert_after_and_create():
    spec = ("[[edit]]\nfile = '@D@/n.md'\nafter = '''## Log\n'''\ninsert = '''- one\n'''\n"
            "[[create]]\nfile = '@D@/new.txt'\ntext = 'hello'\n")
    code, out, d = run(spec, {"n.md": "# T\n## Log\n- zero\n"})
    assert code == 0, out
    assert read(d, "n.md") == "# T\n## Log\n- one\n- zero\n" and read(d, "new.txt") == "hello"
    code, out, _ = run("[[create]]\nfile = '@D@/n.md'\ntext = 'x'\n", {"n.md": "keep"})
    assert code == 1 and "already exists" in out, out


@case
def check_mode_writes_nothing():
    code, out, d = run("[[edit]]\nfile = '@D@/a.txt'\nfind = 'a'\nreplace = 'b'\n", {"a.txt": "a"}, ".toml", "--check")
    assert code == 0 and "would change" in out and read(d, "a.txt") == "a", out


@case
def json_spec_and_bad_spec():
    spec = json.dumps({"edit": [{"file": "@D@/a.txt", "find": "a", "replace": "b"}]})
    code, out, d = run(spec, {"a.txt": "a"}, ".json")
    assert code == 0 and read(d, "a.txt") == "b", out
    code, out, _ = run("[[edit]]\nfile = '@D@/a.txt'\nreplace = 'b'\n", {"a.txt": "a"})
    assert code == 2 and "exactly one of" in out, out


@case
def git_bash_paths_resolve():
    assert AP.resolve("/c/Users/x/y.py", "C:/") == os.path.normpath("c:/Users/x/y.py")


if __name__ == "__main__":
    bad = 0
    for fn in CASES:
        try:
            fn()
            print("PASS", fn.__name__)
        except AssertionError as e:
            bad += 1
            print("FAIL", fn.__name__, " ", e)
    print("%d/%d passed" % (len(CASES) - bad, len(CASES)))
    sys.exit(1 if bad else 0)
