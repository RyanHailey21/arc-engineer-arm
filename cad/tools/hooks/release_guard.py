# -*- coding: utf-8 -*-
"""PreToolUse hook (.claude/settings.json): ask before a hand edit to the released package.

The released package (cad/fab/, cad/fea/out/, cad/render/out/) changes only on request (CLAUDE.md, Guard rails).
The release generators rewrite it through Bash and are not affected; this hook only sees Edit, Write and
NotebookEdit. A matching edit returns permissionDecision "ask", so the user confirms it; everything else passes
through silently. Never blocks on its own errors (exit 0, no output).

    echo '{"tool_input": {"file_path": "cad/fab/bom.csv"}}' | python -I cad/tools/hooks/release_guard.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RELEASED = ("cad/fab/", "cad/fea/out/", "cad/render/out/")


def decide(event):
    ti = event.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not path:
        return None
    full = os.path.normcase(os.path.abspath(os.path.join(ROOT, path)))
    rel = os.path.relpath(full, os.path.normcase(ROOT)).replace("\\", "/")
    if rel.startswith("..") or not rel.startswith(RELEASED):
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            "%s is in the released package, which changes only on request (CLAUDE.md Guard rails). "
            "Regenerate it with its release generator instead of editing by hand, unless the user asked for "
            "this edit." % rel)}}


if __name__ == "__main__":
    try:
        out = decide(json.load(sys.stdin))
        if out:
            print(json.dumps(out))
    except Exception:
        pass
    sys.exit(0)
