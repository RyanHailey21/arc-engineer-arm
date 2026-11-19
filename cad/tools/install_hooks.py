# -*- coding: utf-8 -*-
"""
Install this repo's git hooks into .git/hooks (only this clone; the global git config is not touched).

    python -I cad/tools/install_hooks.py            install / update
    python -I cad/tools/install_hooks.py --remove   remove the hooks this script installed

pre-commit: prints the bloat report's counts (tools/bloat_report.py --counts, ~2 s, writes nothing).
            NON-blocking: it always exits 0, so a commit is never stopped by it.

A hook file that this script did not write is left alone (the script says so); pass --force to replace it.
"""
import os
import subprocess
import sys

MARK = "# installed by cad/tools/install_hooks.py"
PRE_COMMIT = """#!/bin/sh
%s (non-blocking: always exits 0)
root="$(git rev-parse --show-toplevel)"
py=python
command -v "$py" >/dev/null 2>&1 || py=python3
command -v "$py" >/dev/null 2>&1 || py=py
"$py" -I "$root/cad/tools/bloat_report.py" --counts 2>/dev/null || echo "bloat report: could not run (ignored)"
exit 0
""" % MARK


def hooks_dir(root=None):
    root = root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    r = subprocess.run(["git", "-C", root, "rev-parse", "--git-path", "hooks"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("not a git repository: %s" % root)
    d = r.stdout.strip()
    return d if os.path.isabs(d) else os.path.join(root, d)


def install(root=None, force=False, remove=False):
    d = hooks_dir(root)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "pre-commit")
    ours = os.path.exists(p) and MARK in open(p, encoding="utf-8", errors="replace").read()
    if os.path.exists(p) and not ours and not force:
        print("pre-commit: %s exists and was not written by this script; left alone (--force replaces it)" % p)
        return 1
    if remove:
        if ours:
            os.remove(p)
            print("pre-commit: removed %s" % p)
        return 0
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(PRE_COMMIT)
    os.chmod(p, 0o755)
    print("pre-commit: installed %s (prints bloat counts, never blocks)" % p)
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    root = a[a.index("--root") + 1] if "--root" in a else None
    sys.exit(install(root, force="--force" in a, remove="--remove" in a))
