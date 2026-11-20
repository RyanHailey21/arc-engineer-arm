# -*- coding: utf-8 -*-
"""
Install this repo's git hooks into .git/hooks (only this clone; the global git config is not touched).

    python -I cad/tools/install_hooks.py            install / update
    python -I cad/tools/install_hooks.py --remove   remove the hooks this script installed

pre-commit:  prints the bloat report's counts (tools/bloat_report.py --counts, ~2 s, writes nothing).
             NON-blocking: it always exits 0, so a commit is never stopped by it.
post-commit: runs Git LFS's post-commit, then pushes the branch to origin (the user wants every commit pushed,
             2026-11-20).  A branch without an upstream is pushed with -u.  Skipped on a detached HEAD (rebase,
             bisect) and when GIT_NO_AUTOPUSH=1.  A failed push is reported but never undoes the commit.

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


POST_COMMIT = """#!/bin/sh
%s (Git LFS post-commit, then push)
if command -v git-lfs >/dev/null 2>&1; then git lfs post-commit "$@"; fi
[ "$GIT_NO_AUTOPUSH" = "1" ] && exit 0
branch="$(git symbolic-ref --quiet --short HEAD)" || exit 0
if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
  git push --quiet || echo "auto-push: push of $branch failed; run git push" >&2
else
  git push --quiet -u origin "$branch" || echo "auto-push: push of $branch failed; run git push -u origin $branch" >&2
fi
exit 0
""" % MARK
LFS_STOCK = "git lfs post-commit"     # Git LFS's own hook may be replaced: ours runs it first


def hooks_dir(root=None):
    root = root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    r = subprocess.run(["git", "-C", root, "rev-parse", "--git-path", "hooks"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("not a git repository: %s" % root)
    d = r.stdout.strip()
    return d if os.path.isabs(d) else os.path.join(root, d)


def _write(d, name, body, force, remove, replaceable=None):
    p = os.path.join(d, name)
    cur = open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""
    ours = MARK in cur
    stock = bool(replaceable) and replaceable in cur and len(cur.strip().splitlines()) <= 3
    if cur and not (ours or stock or force):
        print("%s: %s exists and was not written by this script; left alone (--force replaces it)" % (name, p))
        return 1
    if remove:
        if ours:
            os.remove(p)
            print("%s: removed %s" % (name, p))
        return 0
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    os.chmod(p, 0o755)
    print("%s: installed %s" % (name, p))
    return 0


def install(root=None, force=False, remove=False):
    d = hooks_dir(root)
    os.makedirs(d, exist_ok=True)
    rc = _write(d, "pre-commit", PRE_COMMIT, force, remove)
    rc |= _write(d, "post-commit", POST_COMMIT, force, remove, replaceable=LFS_STOCK)
    if remove and not rc:      # give Git LFS its own hook back
        subprocess.run(["git", "-C", root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "lfs", "install", "--local"], capture_output=True)
    return rc


if __name__ == "__main__":
    a = sys.argv[1:]
    root = a[a.index("--root") + 1] if "--root" in a else None
    sys.exit(install(root, force="--force" in a, remove="--remove" in a))
