---
name: verify
description: Pick and run the checks a pending change in this repo needs before it is committed (code-CAD inputs, Fusion snapshots, docs, tooling). Use before every commit, and when asked whether a change is safe or verified.
---

# Verify a change before committing

Choose checks from what changed. Run nothing that the change cannot affect.

## 1. See what changed

```
git -C "$CLAUDE_PROJECT_DIR" status --short
git -C "$CLAUDE_PROJECT_DIR" diff --stat HEAD
```

## 2. Run the checks those paths need

| Changed paths | Run | Pass means |
|---|---|---|
| `cad/arm/`, `cad/params/`, `cad/interfaces/`, `cad/envelopes/`, `cad/data/`, `cad/hardware.py`, `cad/iface.py`, `cad/params.py`, `cad/vendor/` | `python -I cad/tools/run.py cad/tools/quick_check.py` (about 90 s; in the background) | `QUICK fourbar: PASS`, fingerprint MATCH |
| the same, when the base or a shared module changed | the same with `BASE_DRIVE=DIRECT` | `QUICK fourbar_direct: PASS` |
| an intended geometry change | `FP_MODE=record` fingerprint after the quick check, then name the parts that changed in the commit message | |
| `fusion/snapshot/` | `SNAP_REV=rev_b python -I cad/tools/run.py fusion/checks/mass_torque.py`, and rev A with `BASE_DRIVE=DIRECT` | the 5 % torque agreement still holds |
| `cad/docs/paper/` or any check result the paper reads | `python -I cad/docs/paper/make_paper.py` | the PDF rebuilds; look at the pages that changed |
| `cad/tools/`, `cad/tests/`, `.claude/` | each test in `cad/tests/` that covers the file (its docstring gives the command), `python -I cad/tools/validate_data.py`, `python -I cad/tools/bloat_report.py --counts` | 0 FAIL, no new bloat findings |
| `cad/fab/`, `cad/fea/out/`, `cad/render/out/` | stop: the released package changes only on request (CLAUDE.md Guard rails) | |

Milestones (a design step, not every commit) also need `cad/check_interference.py` (about 4 min, background).

## 3. Report

Say which checks ran and their result lines, and which you skipped and why. A FAIL is a finding: fix it or report
it, never tune the check to pass.
