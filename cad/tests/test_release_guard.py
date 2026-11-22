# -*- coding: utf-8 -*-
"""The release-guard hook asks before hand edits to the released package and stays silent elsewhere.

    python -I cad/tests/test_release_guard.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "cad", "tools", "hooks", "release_guard.py")


def run(event):
    r = subprocess.run([sys.executable, "-I", HOOK], input=json.dumps(event), capture_output=True, text=True,
                       timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


def main():
    cases = [
        ({"tool_input": {"file_path": "cad/fab/bom.csv"}}, True),
        ({"tool_input": {"file_path": os.path.join(ROOT, "cad", "fea", "out", "report.md")}}, True),
        ({"tool_input": {"file_path": os.path.join(ROOT, "cad", "render", "out", "hero_stow.png")}}, True),
        ({"tool_input": {"file_path": "cad/params/arm.toml"}}, False),
        ({"tool_input": {"file_path": "cad/fabric/x.py"}}, False),             # prefix, not the folder
        ({"tool_input": {"file_path": "../elsewhere/cad/fab/x"}}, False),       # outside the repo
        ({"tool_input": {}}, False),
        ({}, False),
    ]
    bad = []
    for ev, expect in cases:
        out = run(ev)
        asked = bool(out) and out["hookSpecificOutput"]["permissionDecision"] == "ask"
        if asked != expect:
            bad.append((ev, out))
    r = subprocess.run([sys.executable, "-I", HOOK], input="not json", capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or r.stdout.strip():
        bad.append(("garbage input", r.stdout))
    print("test_release_guard: %s (%d cases)" % ("FAIL %s" % bad if bad else "PASS", len(cases) + 1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
