# -*- coding: utf-8 -*-
"""
Sync this checkout with GitHub when a Claude Code session opens it (SessionStart hook in .claude/settings.json),
so a second machine never starts from stale files.

    python -I cad/tools/sync_on_open.py        (also safe to run by hand)

What it does, never blocking the session (always exits 0, about 1-5 s, 20 s network cap):
  1. installs the repo's git hooks if this clone lacks them (auto-push after every commit, bloat counts);
  2. git fetch; if the branch is behind its upstream, fast-forwards it (git merge --ff-only, which also pulls the
     Git LFS files).  It never merges, rebases, stashes or discards anything: a diverged branch, or local edits
     to files the update would change, are reported and left alone;
  3. prints one status line, which Claude Code adds to the session's context.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NET_TIMEOUT = 20


def git(*args, timeout=10):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def ensure_hooks():
    rc, hooks = git("rev-parse", "--git-path", "hooks")
    if rc:
        return ""
    hooks = hooks if os.path.isabs(hooks) else os.path.join(ROOT, hooks)
    pc = os.path.join(hooks, "post-commit")
    if os.path.exists(pc) and "installed by cad/tools/install_hooks.py" in open(pc, encoding="utf-8",
                                                                              errors="replace").read():
        return ""
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "cad", "tools", "install_hooks.py")],
                       capture_output=True, text=True, timeout=30)
    return "git hooks installed (auto-push on commit); " if r.returncode == 0 else \
        "git hooks NOT installed (%s); " % (r.stdout + r.stderr).strip().splitlines()[-1:]


def main():
    note = ""
    try:
        note = ensure_hooks()
    except Exception as e:                       # never block the session
        note = "hook install failed (%s); " % e
    rc, branch = git("symbolic-ref", "--quiet", "--short", "HEAD")
    if rc:
        return note + "repo sync: detached HEAD, not synced"
    rc, up = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if rc:
        return note + "repo sync: %s has no upstream, not synced" % branch
    try:
        rc, out = git("fetch", "--quiet", timeout=NET_TIMEOUT)
    except subprocess.TimeoutExpired:
        return note + "repo sync: fetch timed out (offline?); %s not checked against %s" % (branch, up)
    if rc:
        return note + "repo sync: fetch failed (%s); %s not checked" % (out.splitlines()[-1:] or ["?"], branch)
    _rc, counts = git("rev-list", "--left-right", "--count", "HEAD...@{u}")
    ahead, behind = (int(x) for x in counts.split())
    if behind == 0:
        return note + "repo sync: %s is up to date with %s%s" % (
            branch, up, (" (%d local commit(s) not pushed yet)" % ahead) if ahead else "")
    if ahead:
        return note + ("repo sync: %s has DIVERGED from %s (%d local, %d remote commits). Not merged; reconcile "
                       "by hand (git pull --rebase or a merge)." % (branch, up, ahead, behind))
    try:
        rc, out = git("merge", "--ff-only", "--quiet", "@{u}", timeout=300)
    except subprocess.TimeoutExpired:
        return note + "repo sync: fast-forward timed out; run git pull --ff-only"
    if rc:
        return note + ("repo sync: %s is %d commit(s) behind %s but could not fast-forward (local edits to files "
                       "the update changes?): %s" % (branch, behind, up, out.splitlines()[-1:]))
    _rc, head = git("log", "-1", "--format=%h %s")
    return note + "repo sync: fast-forwarded %s by %d commit(s) from %s, now at %s" % (branch, behind, up, head)


if __name__ == "__main__":
    try:
        print(main())
    except Exception as e:
        print("repo sync: skipped (%s)" % e)
    sys.exit(0)
