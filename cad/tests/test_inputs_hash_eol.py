# -*- coding: utf-8 -*-
"""TI-024: the design-inputs hash must not depend on line endings.  Plain Python:
    python -I cad/tests/test_inputs_hash_eol.py          (exit 1 on FAIL)

With core.autocrlf=true, git writes CRLF into a worktree or a fresh clone, while files written by the tools are
LF.  params.inputs_hash() hashed raw bytes, so the same commit hashed differently per checkout and every evidence
record read STALE in the other one.

1. input_sha: a CRLF copy and an LF copy of the same .py/.toml/.json/.md file hash identically; a real content
   change still changes the hash; a non-text input (vendor .brep/.stp) is hashed raw, CRLF included.
2. inputs_hash over the real input files, copied once all-LF and once all-CRLF, gives the same hash; the old
   raw-byte hash (negative) gives two different ones, so the copies really differ.
3. evidence snapshot: record()'s per-file sha256 list uses input_sha (EOL-neutral) too.
"""
import glob
import hashlib
import os
import shutil
import sys
import tempfile

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
import params  # noqa: E402

fails = []
LF = b"# design input\nA = 1.0     # mm\n[T]\nB = \"x\"\n"
CRLF = LF.replace(b"\n", b"\r\n")


def write(d, name, data):
    p = os.path.join(d, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(data)
    return p


def raw_hash(root):
    """The pre-TI-024 inputs_hash: raw bytes."""
    h = hashlib.sha256()
    for g in params.INPUT_GLOBS:
        for f in sorted(glob.glob(os.path.join(root, g))):
            if os.path.isfile(f):
                h.update(os.path.relpath(f, root).replace("\\", "/").encode())
                h.update(hashlib.sha256(open(f, "rb").read()).digest())
    return h.hexdigest()[:16]


with tempfile.TemporaryDirectory() as td:
    # 1: single files
    for ext in (".py", ".toml", ".json", ".md", ".TOML"):
        a, b = write(td, "lf/x" + ext, LF), write(td, "crlf/x" + ext, CRLF)
        if params.input_sha(a) != params.input_sha(b):
            fails.append("1: %s CRLF and LF copies hash differently" % ext)
        c = write(td, "chg/x" + ext, LF.replace(b"1.0", b"1.5"))
        if params.input_sha(c) == params.input_sha(a):
            fails.append("1: %s content change not seen" % ext)
    a, b = write(td, "lf/v.brep", LF), write(td, "crlf/v.brep", CRLF)
    if params.input_sha(a) == params.input_sha(b):
        fails.append("1: binary input normalised (.brep CRLF bytes must count)")

    # 2: the real input set, all-LF vs all-CRLF
    trees = {}
    for kind in ("lf", "crlf"):
        root = os.path.join(td, "tree_" + kind)
        for f in params.input_files():
            rel = os.path.relpath(f, CAD)
            dst = os.path.join(root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if f.lower().endswith(params.TEXT_INPUTS):
                d = open(f, "rb").read().replace(b"\r\n", b"\n")
                open(dst, "wb").write(d if kind == "lf" else d.replace(b"\n", b"\r\n"))
            else:
                shutil.copyfile(f, dst)
        trees[kind] = root
    n = len(params.input_files())
    saved = params.CAD
    try:
        hs = {}
        for kind, root in trees.items():
            params.CAD = root
            hs[kind] = params.inputs_hash()
    finally:
        params.CAD = saved
    if hs["lf"] != hs["crlf"]:
        fails.append("2: inputs_hash LF %s != CRLF %s" % (hs["lf"], hs["crlf"]))
    if raw_hash(trees["lf"]) == raw_hash(trees["crlf"]):
        fails.append("2: negative: raw hashes equal, the CRLF tree is not CRLF (test tests nothing)")
    if n < 20:
        fails.append("2: only %d input files" % n)

# 3: the record() snapshot uses the EOL-neutral digest
src = open(os.path.join(CAD, "params.py"), encoding="utf-8").read()
if "sha256=input_sha(f)) for f in ins" not in src:
    fails.append("3: record() input snapshot does not use input_sha")

print("TEST %s: inputs hash EOL-neutral (%d inputs; LF == CRLF tree %s; raw hash differs)%s" % (
    "FAIL" if fails else "PASS", n, hs.get("lf"), "".join("\n  " + f for f in fails)))
sys.exit(1 if fails else 0)
