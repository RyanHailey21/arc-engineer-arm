# -*- coding: utf-8 -*-
"""
Keep this checkout (and the tool repos it depends on) in step with GitHub, so a second machine or another agent's
pushes are never missed.

    python -I cad/tools/sync_on_open.py            SessionStart hook: sync now, always print one line per repo
    python -I cad/tools/sync_on_open.py --prompt   UserPromptSubmit hook: sync each repo at most every PROMPT_EVERY
                                                   seconds; print only when something changed or needs a hand

Repos: this one, plus each existing path in ARM_SYNC_REPOS (os.pathsep- or ';'-separated; set in
.claude/settings.json env, e.g. the creality-slicer MCP server's clone). Missing paths are skipped (other machines).

What it does, never blocking the session (always exits 0; 20 s network cap per repo, 8 s in --prompt mode):
  1. installs this repo's git hooks if the clone lacks them (auto-push after every commit, bloat counts);
  2. git fetch; if the branch is behind its upstream, fast-forwards it (git merge --ff-only, which also pulls the
     Git LFS files).  It never merges, rebases, stashes or discards anything: a diverged branch, or local edits
     to files the update would change, are reported and left alone;
  3. prints a status line, which Claude Code adds to the session's context.
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NET_TIMEOUT = 20
PROMPT_TIMEOUT = 8
PROMPT_EVERY = 300            # s between fetches of one repo in --prompt mode


def git(root, *args, timeout=10):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def ensure_hooks():
    rc, hooks = git(ROOT, "rev-parse", "--git-path", "hooks")
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


def repos():
    out = [ROOT]
    for p in os.environ.get("ARM_SYNC_REPOS", "").replace(";", os.pathsep).split(os.pathsep):
        p = os.path.normpath(os.path.expandvars(os.path.expanduser(p.strip()))) if p.strip() else ""
        if p and os.path.isdir(os.path.join(p, ".git")) and os.path.normcase(p) != os.path.normcase(ROOT):
            out.append(p)
    return out


def due(root):
    """--prompt throttle: True (and restamp) when this repo was last fetched PROMPT_EVERY s ago or more."""
    rc, gd = git(root, "rev-parse", "--git-dir")
    if rc:
        return False
    stamp = os.path.join(gd if os.path.isabs(gd) else os.path.join(root, gd), "sync_on_open.stamp")
    try:
        if time.time() - os.path.getmtime(stamp) < PROMPT_EVERY:
            return False
    except OSError:
        pass
    with open(stamp, "w") as f:
        f.write(str(time.time()))
    return True


def sync(root, net_timeout):
    """(changed, line): changed is True when the branch moved or needs a hand."""
    name = os.path.basename(root)
    rc, branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if rc:
        return False, "%s: detached HEAD, not synced" % name
    rc, up = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if rc:
        return False, "%s: %s has no upstream, not synced" % (name, branch)
    try:
        rc, out = git(root, "fetch", "--quiet", timeout=net_timeout)
    except subprocess.TimeoutExpired:
        return False, "%s: fetch timed out (offline?); %s not checked against %s" % (name, branch, up)
    if rc:
        return False, "%s: fetch failed (%s); %s not checked" % (name, out.splitlines()[-1:] or ["?"], branch)
    _rc, counts = git(root, "rev-list", "--left-right", "--count", "HEAD...@{u}")
    ahead, behind = (int(x) for x in counts.split())
    if behind == 0:
        return False, "%s: %s is up to date with %s%s" % (
            name, branch, up, (" (%d local commit(s) not pushed yet)" % ahead) if ahead else "")
    if ahead:
        return True, ("%s: %s has DIVERGED from %s (%d local, %d remote commits). Not merged; reconcile by hand "
                      "(git pull --rebase or a merge)." % (name, branch, up, ahead, behind))
    _rc, new = git(root, "log", "--format=%h %s", "HEAD..@{u}")
    try:
        rc, out = git(root, "merge", "--ff-only", "--quiet", "@{u}", timeout=300)
    except subprocess.TimeoutExpired:
        return True, "%s: fast-forward timed out; run git pull --ff-only" % name
    if rc:
        return True, ("%s: %s is %d commit(s) behind %s but could not fast-forward (local edits to files the update "
                      "changes?): %s" % (name, branch, behind, up, out.splitlines()[-1:]))
    shown = new.splitlines()[:8]
    more = " (+%d more)" % (behind - len(shown)) if behind > len(shown) else ""
    return True, "%s: fast-forwarded %s by %d commit(s) from %s: %s%s" % (
        name, branch, behind, up, "; ".join(shown), more)


def main(prompt_mode=False):
    note = ""
    try:
        note = ensure_hooks()
    except Exception as e:                       # never block the session
        note = "hook install failed (%s); " % e
    lines = []
    for root in repos():
        if prompt_mode and not due(root):
            continue
        try:
            changed, line = sync(root, PROMPT_TIMEOUT if prompt_mode else NET_TIMEOUT)
        except Exception as e:
            changed, line = False, "%s: skipped (%s)" % (os.path.basename(root), e)
        if changed or not prompt_mode:
            lines.append(line)
    if prompt_mode:
        if not lines and not note:
            return ""
        return note + "repo sync (new pushes from another machine or agent): " + " | ".join(lines)
    return note + "repo sync: " + " | ".join(lines)


if __name__ == "__main__":
    try:
        msg = main("--prompt" in sys.argv[1:])
        if msg:
            print(msg)
    except Exception as e:
        print("repo sync: skipped (%s)" % e)
    sys.exit(0)
