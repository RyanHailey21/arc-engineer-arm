# Tooling issues (observed friction → fix)

Kept by the tooling-observer session. Each entry: what happened (with transcript evidence), root cause, fix or
plan, status (`open`, `fixed`, `wontfix`). Transcript = `~/.claude/projects/C--Users-ryanh-light-weight-arm/
95cc053c-….jsonl`; "L1234" is a line number in it. Scan method: every `tool_result` with `is_error`, timed
against its `tool_use` (142 errors in 19,040 lines up to 2026-11-17 04:30Z).

| ID | Date | Summary | Status |
|---|---|---|---|
| TI-001 | 2026-11-16 | MCP client cuts every freecad-mcp call at ~60 s; long results lost | fixed (server restart needed) |
| TI-002 | 2026-11-16 | Patching Python through heredocs / `s.replace` / `sed` fails or misses silently | fixed |
| TI-003 | 2026-11-16 | `print()` crashes on cp1252 console (UnicodeEncodeError) | fixed 2026-11-21: `PYTHONUTF8=1` in `.claude/settings.json` `env` |
| TI-004 | 2026-11-16 | Auto-mode classifier can't review commands that start with `cd`; `sleep N; cat` blocked | fixed 2026-11-21: CLAUDE.md line |
| TI-005 | 2026-11-16 | Quick tier misses hole-wall and thread-engagement defects (found only in the full run) | fixed 2026-11-21: quick_check `holes/eng` step on the changed parts + test |
| TI-006 | 2026-11-16 | Status tools (`get_rpc_status`, `get_async_status`) hang when FreeCAD is stuck | open: plan |
| TI-007 | 2026-11-16 | Eval case YAML frontmatter colon bug | open: needs a check in the plugin |
| TI-008 | 2026-11-16 | `claude` CLI too old for `plugin eval` | fixed (2.1.326) |
| TI-009 | 2026-11-16 | Fingerprint misses a hole moved inside a generic-Shape part (bbox-centre "com") | fixed; baselines re-recorded |
| TI-010 | 2026-11-16 | freecadcmd given a short script by path printed nothing (test "passed" silently) | fixed with TI-018 (tools/run.py) |
| TI-011 | 2026-11-16 | Eval graders regex the tool *listing* in `trace`: false FAIL (readme) and false PASS (pole clash) | fixed; verification run |
| TI-012 | 2026-11-16 | Eval graders needing plugin tools scored in the no-plugin arm (no Bash there): inflated Δ | fixed (`arm: with-only`) |
| TI-013 | 2026-11-16 | Quick-check mock contradicted the fingerprint mock (CHANGED vs MATCH) on the refactor case | fixed |
| TI-014 | 2026-11-16 | Ceiling cases (drawings, stale) pass in both arms: they test the fixture's CLAUDE.md, not the plugin | open: plan |
| TI-015 | 2026-11-17 | No check compares purchased-part mass with the catalogue (DM-J4340 counted twice; GT2 belt weighs 0 g) | fixed: quick_check `catalogue` line + test |
| TI-016 | 2026-11-17 | Moved standoffs left their plate holes behind; interference passed (pocket), no check caught it | fixed: tools/check_seated.py; 6 dowel findings triaged 2026-11-18 (DM rotor split) |
| TI-017 | 2026-11-17 | check_engagement skipped SB5 shoulder screws (exact name match), then SetScrew_* (case) | fixed: match by catalogue key + test |
| TI-018 | 2026-11-17 | freecadcmd swallows tracebacks (exit 1, no output) and prints nothing for short scripts | fixed: tools/run.py |
| TI-019 | 2026-11-17 | quick_check doesn't run the new level-keeping linkage check | fixed 2026-11-18 |
| TI-020 | 2026-11-18 | No detector for dead code, orphan params/catalogue keys or scratch files for a periodic cleanup agent | fixed: tools/bloat_report.py + keep-list + hook installer + test |
| TI-021 | 2026-11-18 | manifest.json `files` for level_keeping and working_doc point outside the job folder (paths relative to the cwd) | fixed: absolute paths |
| TI-022 | 2026-11-18 | Tests and quick_static hard-code the main checkout path: from a worktree they test and write the user's checkout | fixed: `__file__` + test; worktrees git-ignored, skipped by bloat_report |
| TI-023 | 2026-11-18 | test_validate_data `param_typo_type` hard-codes TOML line 17; ZL0 is on line 18, so it FAILs on main | fixed: line found from the file |
| TI-024 | 2026-11-18 | `params.inputs_hash` hashes raw bytes: a CRLF checkout (worktree, `core.autocrlf=true`) gets another hash, all evidence STALE | fixed: EOL-neutral input digests + test (staled evidence once) |
| TI-025 | 2026-11-20 | Rev B servo case screws floated 13 mm off their holes in the GUI working doc; check_seated skipped PAN screws, had no head-contact rule, and nothing compared the open document with the model | fixed: check_seated rule 2 (head/washer bearing) + PAN screws + test; tools/check_working_doc.py |
| TI-026 | 2026-11-21 | The twice-daily tooling agent has stopped at its first Bash call in every run since 2026-11-20 ("Request interrupted ... for tool use"): a permission prompt with nobody to answer it | fixed 2026-11-21: both arm tasks replaced by `arm-repo-upkeep`, saved in Bypass mode (the user can lower it to Auto in the app) |
| TI-027 | 2026-11-21 | The tooling agent's prompt still named the removed SCREW variant, drawings, TDP and build_assembly, so gate 7b could never pass | fixed: prompt updated |
| TI-028 | 2026-11-21 | Nothing stopped a hand edit to the released package (`cad/fab/`, `cad/fea/out/`, `cad/render/out/`); only CLAUDE.md said so | fixed: PreToolUse hook `cad/tools/hooks/release_guard.py` (asks) + test |
| TI-029 | 2026-11-21 | A skill whose frontmatter doesn't parse loads silently with no fields; nothing checked `.claude/` | fixed: `cad/tests/test_agent_config.py` |
| TI-030 | 2026-11-21 | The unattended daily run is in Bypass mode with no deny rules; code.claude.com/docs/en/best-practices says bypassPermissions only suits a disposable container, and "never" rules belong in deny rules (they hold in every mode) | deny rules fixed 2026-11-22 (`.claude/settings.json`: force-push, `reset --hard`, `clean`, each as Bash and PowerShell, checked by test_agent_config); Auto mode: needs the user (desktop app, Scheduled, arm-repo-upkeep, permission mode; no tool sets it) |
| TI-031 | 2026-11-21 | About ten user-scope MCP servers unrelated to this repo (KiCad, LTspice, MATLAB, Creo, slicer, shopping) load their tool names and instructions into every session here; best-practices: turn off the ones you don't need | fixed 2026-11-22: ltspice, creo, konnect, pcbparts, claude.ai FeatureScript MCP in `disabledMcpServers` for this project in `~/.claude.json` (MATLAB kept at the user's request; re-enable via /mcp). The desktop app's own connectors (EasyEDA, Solderable, reMarkable) are not in that list |
| TI-032 | 2026-11-21 | CLAUDE.md gave script paths relative to `cad/` (`tools/quick_check.py`), put `arm_model.py` under `cad/arm/`, toured the layout and repeated the Fusion procedure; `repo-upkeep` (pushes to main) could be started by the model | fixed: CLAUDE.md rewritten to commands, decisions and gotchas (42 to 34 lines); `disable-model-invocation: true`; the daily run now re-checks best practices and runs `/doctor prompt-audit` |
| TI-033 | 2026-11-22 | `check_interfaces` (quick tier) had no negative test: nothing proved it flags a part moved off its mate's bolt pattern, the defect class of the UA standoffs | fixed: `cad/tests/test_interfaces_moved_part.py` (both variants); `check_interfaces.main(bodies, write)` |
| TI-034 | 2026-11-22 | creality-slicer MCP (RyanHailey21/creality-slicer) handed OrcaSlicer system preset files whose `inherits` its CLI ignores: every inherited value fell back to Orca defaults (all slices at 200 C nozzle / 45 C bed; the Ender-3 S1 Pro refused to slice because its G92 E0 layer reset is inherited), and failures came back as a bare exit code (Orca logs to 00000.log in its working folder) | fixed 2026-11-22 in the server (6073a85, 4c39ee7): presets flattened before slicing, `settings` overrides, compatibility check, Orca log in the error. The running server needs a reconnect (/mcp) to load it |

---

## TI-001: MCP calls die at ~60 s whatever `timeout` they pass  (fixed; needs an MCP server restart)

**What happened.** 57 freecad-mcp calls returned `Error: Request timed out`: 48 `execute_code`, 4
`execute_code_headless`, 2 `job_status`, plus `execute_code_async`, `get_async_status` and `get_rpc_status`.
Every one ended 60–93 s after it started, including calls that passed `timeout: 1800` (24 of them), 1200, 900
and 300. Examples: L2207–L2345 (render stills, 5 in a row), L12039–L12172 (drawing batch), L13339 and L14246
(`export_fab.py` headless, `timeout: 900`). The work usually *finished* in FreeCAD. The result was lost, and the
agent re-ran the call or polled files with `sleep`, which was blocked (L7478, L12053). Reproduced from this
session on 2026-11-16: `execute_code_headless` with `time.sleep(80)` and `timeout: 200` → `Request timed out`.

**Root cause.** The MCP *client* gives up on a request at about 60 s. The server's `timeout` arguments (90 s
default, capped at 1800) only bound the server's own wait, so they can never take effect. The server sends no
progress notifications. The Claude Code docs say stdio servers have no per-request timer and `MCP_TOOL_TIMEOUT`
defaults to ~28 h, but the observed behaviour in the desktop app is a hard ~60 s. So don't rely on client config.
`job_status(wait_s=60)` was itself at the limit (L7240, L7340).

**Fix (freecad-mcp, branch `feat/techdraw-asme-layout`, uncommitted).**
- `jobs.run_with_deadline` and the shared `tool` wrapper in `server.py`: every tool call runs under a sync
  budget, `FREECAD_MCP_SYNC_BUDGET_S` (default 50 s; 0 turns it off). A call still running at the budget
  becomes a background job. The reply is `{"status": "running", "job_id": …, "note": "… call
  job_status(job_id, wait_s=45) … Do not re-run the call"}`. Calls that finish in time are unchanged, exceptions
  included, and leave no job history.
- `job_status`: `wait_s` is capped at 45 s (`WAIT_CAP_S` = budget − 5) so polling itself can't time out. A
  handed-off tool's original reply (text and screenshots) is returned after the summary.
- The `execute_code` docstring now says this instead of "the result is lost".
- Tests: `tests/test_sync_handoff.py` (7). Full suite: 356 passed, 2 skipped.

**How to work now (after the restart):** a long call returns a `job_id` at ~50 s. Poll
`job_status(job_id, wait_s=45)`; don't re-run the call. `job_cancel` only drops the result. It cannot stop GUI
work already running.

**Restart caveat.** The server is an editable install, so the change loads only after the freecad-mcp server
restarts (`/mcp` reconnect). A restart kills in-flight FreeCAD jobs, so the main session chooses when.

## TI-002: patch scripts via heredoc / `s.replace` / `sed` fail or miss  (fixed)

**What happened.**
- Bash rejected multi-line `python - <<'EOF'` patch scripts with `unexpected EOF while looking for matching
  ''` at L1324 (arm_model roll patch), L3058 (blender_render, 152-line heredoc), L5697 (make_drawings) and
  L17545 (fourbar block).
- `s.replace`/`index` anchors missed after earlier edits or on a non-ASCII character: L7142 (`±` in
  `TOL_LIN1`), L17195 (patch_tdp), L18701, L18878 (eval cases). The patch half-applied or aborted.
- The main session reported that `sed -i` patches changed nothing without any error.

**Root cause.** Patch text goes through two quoting layers (the Bash tool's `bash -c` wrapper, then the heredoc).
Python source with `'''`, backslashes and quotes breaks that. `str.replace` returns the text unchanged on a miss,
and `sed` exits 0 when nothing matched.

**Fix.** `cad/tools/apply_patch.py`. Write a TOML or JSON spec with the **Write tool** (no shell quoting at all),
then run `python -I cad/tools/apply_patch.py SPEC.toml [--check]`.
- Edit types: `find`/`replace` (exact count), `start`/`end` block replace, `after`/`before` insert, `[[create]]`.
  Replacement text can come from a file (`replace_file`), so `'''` is never a problem.
- All-or-nothing: every edit is matched before anything is written.
- A miss names the closest lines, with line numbers, and says when only whitespace differs.
- CRLF files keep their line endings.
- An edited `.py` must compile, or nothing is written.
- The output is a short diff.
- Tests: `cad/tests/test_apply_patch.py` (11/11).
- For a single exact replacement the Edit tool is still the simplest. Use `apply_patch` for multi-anchor or
  multi-file patches, where the heredoc scripts were used.

## TI-003: `print()` crashes on the cp1252 console  (fixed 2026-11-21: `env` `PYTHONUTF8=1` in `.claude/settings.json`)

**What happened.** `UnicodeEncodeError: 'charmap' codec` at L711, L6123–L6133 (`lint_pdf.py` printing `⟂`),
L8773, L10724, L16455 and L15738. Some runs succeeded on a second try with `PYTHONIOENCODING=utf-8`, but not all
(L6128 still failed).

**Root cause.** Python 3.14 on Windows uses the console code page (cp1252) for stdout when it is a pipe. PDF text
and GD&T symbols are outside it. The freecad MCP server already sets `PYTHONUTF8=1` in its own env
(`~/.claude.json`), but Bash and PowerShell tool commands don't.

**Proposed fix (needs the user's OK; settings are off-limits to this session):** add
`"env": {"PYTHONUTF8": "1"}` to the arm repo's `.claude/settings.json`. Every python run by the Bash tool then
uses UTF-8 for stdio and `open()`. New tools in `cad/tools/` already print safely (`apply_patch._say`).
`cad/drawings/lint_pdf.py` belongs to the main session and is not changed here.

## TI-004: classifier "no verdict" on `cd …` commands; blocked `sleep`  (fixed 2026-11-21: the line is in CLAUDE.md)

**What happened.** Five Bash calls were refused with "auto mode reviewed this call without its leading cd, and
the shell has moved since" (L5847, L6286, L6293, L6373, L6476), and each was re-sent. `sleep 60; cat …` was
blocked twice (L7478, L12053).

**Root cause.** The harness reviews commands that start with `cd` without the `cd`, so it refuses them when the
working directory has changed since. Foreground `sleep` is disallowed by design.

**Proposed CLAUDE.md line (needs the user's OK):** "Bash: use absolute paths instead of a leading `cd`; wait on
long jobs with `run_in_background` or Monitor, never `sleep`." With TI-001 fixed, MCP jobs are polled through
`job_status`.

## TI-005: quick tier misses hole walls and thread engagement  (fixed 2026-11-21)

**What happened** (main-session report). Hole-wall and thread-engagement defects appeared only in the full run.
`quick_check.py` lists `holes` and `engagement` evidence as FRESH/STALE but doesn't run them. `check_holes.py`
takes about 2–3 minutes for all made parts.

**Plan.** Add a `--changed` hole and engagement pass to `quick_check.py`:
1. Take the per-part fingerprint diff (fingerprint g2 already hashes each part).
2. Run `check_holes` and `check_engagement` on the changed made parts only, usually 1–5 parts and a few seconds.
3. Write `holes`/`engagement` evidence scoped to those parts, so FRESH means "checked since the change".

Acceptance: a seeded thin wall in one gripper part FAILs in the quick tier in under 40 s total, on both variants.
This needs the per-part diff API in `fingerprint.py` (my area) and a call from `quick_check.py`. Next item.

**Fix (upkeep 2026-11-21).** `quick_check.py` step 10 `holes/eng`: `changed_parts()` takes the parts whose
fingerprint entry (kind, chk, vis) is new or differs from the baseline; `changed_holes()` runs
`check_holes.scan_part()` on the changed made parts and `check_engagement.scan(only=...)` on tapped holes in a
changed part or under a changed screw. FAIL/BROKEN and screw-past-thread fail the quick check; WARN rows are left to
the full run. Both checks were split into those functions with full-mode results identical to the committed reports
(43 hole rows, 18 engagement rows), and `check_holes.py` no longer runs on import. Deviation from the plan: the step
writes no `holes`/`engagement` evidence (a partial pass must not mark the full check FRESH); its result is
`holes_changed` in `quick.json`. Cost: 0 s when the fingerprint matches; about 1 s per changed part.
Negative test `tests/test_quick_holes_changed.py`: a hole drilled 0.5 mm beside a Jaw_Block_L hole and the screw of
the first blind tapped hole pushed 1 mm past its thread both FAIL on both variants, and both parts pass before the
edit. The plan's < 40 s total is not
reachable here: the model build alone is about 31 s and the whole quick check about 72 s on this machine.

## TI-006: status tools hang when FreeCAD is stuck  (open: plan)

**What happened.** `get_rpc_status` and `get_async_status` timed out or reported "Server freecad unavailable"
at L11614–L11940 and L15241–L15268. Those are the tools meant to diagnose a stuck GUI.

**Root cause.** Each one makes an XML-RPC call with the connection's 150 s socket timeout. When the addon's RPC
thread is blocked, the call waits longer than the client allows.

**Plan.** In freecad-mcp, give status tools their own connection with a 5 s timeout, the same as
`toolchain_status(probe_freecad)`. A timeout then returns `{"freecad_rpc": "unresponsive", "hint": …}` instead
of hanging. TI-001's hand-off already keeps them from losing the session in the meantime.

## TI-007: eval case YAML frontmatter colon bug  (open)

Reported by the main session. Related evidence at L18878: the case-writing script's own `s.replace` assert
failed on the `value-in-params` regex grader (the same TI-002 pattern). I haven't confirmed the exact YAML
failure from the transcript. Plan: a plugin test that parses every `evals/*/case.md` frontmatter with a real YAML
parser and checks the grader types. To be done with the baseline-eval analysis.

## TI-008: CLI too old for `plugin eval`  (fixed)

Reported by the main session. `claude` is now 2.1.326, and the baseline run started 2026-11-16 22:41 with it.

## TI-009: fingerprint misses holes moved inside a generic Shape  (fixed; both baselines re-recorded)

**What happened** (main-session report, 2026-11-16). The rear standoff hole in Finger_L/R_bot_CF3 and
Jaw_Block moved from (XT+16, o+20) to (XT+12, o+18). The fingerprint showed no change, although `check_holes`
showed the move: the 1.33 mm wall warning disappeared.

**Root cause.** `shape_fp` used `s.CenterOfMass if hasattr(...) else BoundBox.Center`. `makeFillet` returns a
generic Shape with no `CenterOfMass`, so "com" was the bounding-box centre. A hole that moves inside the outline
changes neither the volume nor the bounding box. The re-record showed this affected far more than fillets:
422 of 628 screw shapes and 280 of 484 fourbar shapes (chk + vis) had a bbox-centre "com".

**Fix** (`cad/tools/fingerprint.py`):
- `centre_of_mass()` computes the volume-weighted centre of `s.Solids`.
- New per-shape `fdig`: a sorted digest of every face's surface type, area and centroid, so a moved hole always
  shows even when the mass centre shift rounds away.
- Regression test `cad/tests/test_fingerprint_moved_hole.py` (a filleted plate with the real hole move) PASSes.
  It reports com and fdig changes with identical volume and bbox.

**Re-record (measurement change only).** A guarded script allowed only `com` diffs and new `fdig` keys, and
found 0 other diffs on both variants before recording: screw.json 23:10:29, fourbar.json 23:12:14. Both then
MATCH. The main session's later edits (params 23:12:40, fourbar.py 23:13:14) show as CHANGED. That is their
work to re-record. Backups of the old baselines are in this session's scratchpad (`fp_backup/`).

## TI-010: freecadcmd given a short script by path printed nothing  (open: workaround)

**What happened.** `freecadcmd cad/tests/test_fingerprint_moved_hole.py` printed only the banner and exited 0.
So did a two-line `print("hello")` script from the scratchpad, and a copy under `cad/tools/`, with output piped
or redirected. The same tests ran through `freecadcmd -c "exec(open(r'…').read())"` and printed normally.
`fingerprint.py` and `quick_check.py` print fine by path. Cause not found yet. A test that prints PASS/FAIL can
therefore "pass" by printing nothing.

**Workaround.** Run short FreeCAD scripts through `-c "exec(open(...).read())"`. The new test's docstring says
so. **Plan:** find the cause (FreeCAD 1.1.4 `freecadcmd` file handling vs `-c`), then add a
`tools/run_fc_tests.py` runner that treats "no TEST line" as FAIL.

## TI-011: eval graders regex the tool listing in `trace`  (fixed; verification run pending)

**What happened** (baseline-v0.0.1).
- `readme-summary` WITH scored 0.75 in all 3 runs on `no-checks: pattern found`. Yet every one of those runs
  shows `mocks.calls.total: 0`, and `no-edit`/`no-write` passed. No CAD tool was called and nothing was edited,
  contrary to the first reading that the tool descriptions over-trigger.
- `seeded-pole-clash/ran-a-check` used the same pattern, so in the with-arm it passed whether or not a check ran.

**Root cause.** `target: trace` is the whole session, including the init record that lists every available tool
(plugin-evals docs, "What a grader can look at"). A tool-name regex over it is always true in the with-arm.

**Fix (verified with 1-run cases, $1.34 in all).**
- `ran-a-check` uses `target: mock_calls` and the pattern `project_quick_check|envelope_check`. It is with-only
  automatically, because the mocked server is the plugin's. Verified: it matched 3 real calls and shows as an
  indicator.
- `no-checks` was first moved to `mock_calls`. That errored in the no-plugin arm ("no mock stand-ins were
  active"), a new false FAIL, so it is now five `tool_used` graders (`no-call-<tool>.md`, `min: 0, max: 0`,
  weight 0.2 each, `arm: both`). Verified: readme-summary 1.00 WITH and 1.00 W/OUT, all scored.
- Rule for new graders: never regex `trace` for a tool name. Use `tool_used`, or `mock_calls` for with-only
  indicators.

## TI-012: plugin-only graders scored in the no-plugin arm  (fixed)

**What happened.** The W/OUT failures were almost all `tool_used`/`tool_order` graders on
`mcp__plugin_mechanical-cad_cad__*`. The without-arm has neither those tools nor Bash (the run grants only Edit
and Write), so it cannot run any check at all. Those graders pushed W/OUT down by construction (for example,
split-wrist W/OUT 0.33 = only `writes-new-module` and `never-records` passing).

**Fix.** `probes-it`, `ran-quick-check`, `check-after-edit`, `fingerprint-after-edits`, `fingerprint-fourbar`
and `fingerprint-screw` are now `arm: with-only`: plugin-fired indicators, not scored in either arm (docs: "Score
against the no-plugin baseline"). The scored graders are the outcome checks (params value, honest report, no
literal edit, no re-record), which both arms can pass or fail. Δ will shrink, and that is the honest number.

## TI-013: quick-check mock contradicted the fingerprint mock  (fixed)

**What happened.** split-wrist-module WITH runs 1 and 2 failed `reports-match`. The agents saw
`project_fingerprint` → MATCH but `project_quick_check` → "fingerprint CHANGED (re-record if intended)" without
a count, in an output labelled "synthetic eval fixture". They correctly refused to call the refactor verified.
The mock was wrong, not the agent.

**Fix.**
- split-wrist-module has its own quick-check mock with `fingerprint PASS MATCH (0 differences)`.
- The shared and seeded-pole-clash mocks use the real output format ("CHANGED (N differences; re-record if
  intended)").
- The "(synthetic eval fixture)" labels are removed from every mock.

## TI-014: ceiling cases test the fixture's CLAUDE.md, not the plugin  (open: plan)

`regenerate-drawings-concept` and `explain-stale-evidence` score 1.0 in both arms.
- The fixture is the real project, and its `CLAUDE.md` states the release guard and points to the manifest.
- Neither arm has Bash or a generator, so "regenerating" can't happen at all.

They stay as guard cases (a regression would show). They say nothing about the plugin.

**Plan (WP6, with the skills in WP4):** add a `fixture_bare` variant of each case. Same project with the
conventions section of `CLAUDE.md` removed, so the conventions can only come from the plugin's skills and hooks.
For the drawings case, add a mocked generator tool, so a real overwrite becomes possible and gradable.

## TI-015: no purchased-part mass check against the catalogue  (fixed: test added; one defect handed over)

**What happened** (main-session report, 2026-11-17).
- Each DM-J4340 is modelled as a stator part plus a rotor part, and `part_mass_g` counted the full 330 g for both.
- No check caught it; it surfaced while building the BOM. The main session fixed it with a 70/30 split
  (`ROTOR_SHARE` in `arm/kinematics.py`) and re-recorded both baselines.

**Root cause.** Mass and torque checks compare totals with ratings. Nothing compares the modelled mass of each
purchased item with its catalogue figure. Also, a CAT part whose `src` isn't a catalogue key silently weighs 0 g
(`CAT[p.src]["mass"] if p.src in CAT else 0`).

**Fix.** `cad/tests/test_catalogue_mass.py` checks, per variant:
1. every CAT `src` is a catalogue key;
2. summed `part_mass_g` per key = units × catalogue mass (within 0.5 %), with units counted by the BOM's
   split-motor rule (a name containing "rotor" is the same unit);
3. every rotor part has a stator sibling.

Run with `freecadcmd -c "exec(open(r'cad/tests/test_catalogue_mass.py').read())"` under `GRIP=SCREW` and
`GRIP=FOURBAR`.
- Negative check: with the pre-fix `part_mass_g` restored, it FAILs with "DM-J4340-2EC: modelled 1320.0 g over 4
  parts, expected 2 unit(s) x 330 g = 660.0 g".
- Current result, both variants: FAIL on one real defect. `FOREARM/GT2_Belt_9mm_Stage2` (`arm/forearm.py:72`)
  has `src = "GT2-BELT"`, which isn't in `data/catalogue.toml`, so the belt weighs 0 g in mass and torques.
  Everything else matches (SCREW 32 keys / 241 units, FOURBAR 27 / 173).
- The catalogue is a design input, so the main session added the `GT2-BELT` entry (5.5 g, commit f7b35f2).
- **Done 2026-11-17:** the check lives in `cad/tools/catalogue_mass.py`. `quick_check.py` runs it as check 5,
  `catalogue` (under 0.1 s). The test calls the same function and also asserts that the old double count is
  still reported. Results: SCREW 33 keys / 242 units PASS, FOURBAR 28 / 174 PASS. quick_check PASSes and both
  fingerprints MATCH.

## TI-016: a moved standoff left its plate holes behind and no check caught it  (fixed: new check; findings triaged)

**What happened** (main session, 2026-11-17).
- The upper-arm standoffs were moved through `UA_CLIP_X`, but the UA plate holes and pocket layout stayed
  hard-coded at L2/3 and 2L2/3 in `arm/upper_arm.py`.
- The standoffs sat over lightening pockets and the old holes were empty. The user caught it.
- `check_interference` passed: zero overlap, because there was no material.
- The main session fixed it by formalising `interfaces/ua_plate__ua_standoff.toml` (new `[stations]` row pattern
  and optional `[spacer]` side).

**Root cause.** Every check looks for overlap, which a fastener over a pocket doesn't have. Only mates written
into `interfaces/` are probed for holes, so a mate nobody formalised isn't checked at all.

**Fix: `cad/tools/check_seated.py`.** At STOW, on the vis shapes:
- For every SHCS/BHCS/CSK/SB5 screw, the point 0.5 mm past the head bearing face must lie in a coaxial hole of
  another part.
- For every pin or dowel, both points 1 mm in from its ends must.
- "Coaxial hole": a concave cylinder, axis parallel within 1° and within 0.3 mm of the fastener axis, radius at
  least the local fastener radius − 0.15 mm, the point inside its axial extent.
- Tips are not judged. Tips stick out of through-tapped holes and nuts, and vendor models lack tapped bores
  (the first draft flagged 52 tips); `check_engagement` covers tapped holes.
- Writes `out/<variant>/seated_report.txt` and a `seated` evidence record. About 20 s.
- Negative test `cad/tests/test_seated_moved_screw.py`: moves the 4 UA standoff screws 6 mm sideways in memory.
  All 4 are flagged, and nothing else changes. PASS.

**Findings (same on both variants; for the main session to triage).**
- `Dowel_4x5_J1_Output_Hub_0..2`: end A is inside the J1 DM-J4340 stator solid, with no hole.
- `Dowel_4x5_J2_Output_Hub_Journal_0..2`: end B finds no hole and no material.

Either the dowel positions are off, or the vendor motor model lacks its dowel holes (and the J2 journal side has a
gap). If they are intended, the check needs a reviewed exemption list in data, with a reason per entry, not a
silent skip.

**Triage (2026-11-18): modelling gap, fixed; no checker exemption.**
- Not a checker limitation and not a dowel position error. The vendor STEP (`DM-J4340-2EC-V1.1.stp`) does have
  all three D4 dowel holes at PCD24, at 90°, −30° and −150°, matching `interfaces/dm_j4340__hub_tower.toml`.
  They run 1–6 mm behind the output face.
- Cause: the STEP fuses the output flange into the housing solid (one solid, y −0.05…42.45, `isValid()` False).
  `dm_split()` looked for whole solids in front of the face, found none, and returned an empty rotor. The
  flange, with its dowel and M3 holes, stayed on the stator in GROUND. The hubs turn with UPPER and CRANK, so at
  STOW their dowels were ~50° away from the holes. J1's probe landed in housing material; J2's landed in the
  1 mm face recess, hence the two different messages.
- Fix: `dm_split()` cuts the rotor out of the solid that carries the output face, the D35 boss (`DM.rotor_r`
  17.45) down to the dowel-hole bottom (`DM.rotor_depth` 6.0). Both values are in the interface file. The
  J1/J2 rotor parts now carry the holes, and check_seated reports 0 FAIL on FOURBAR and SCREW.
- Geometry change: vis shapes of `J1/J2_Motor_DM-J4340_stator` and `..._rotor` only. chk shapes, mass
  (catalogue × `ROTOR_SHARE`) and the hubs are unchanged. Fingerprints re-recorded for both variants.

**Open design note (not changed; rev A BOM).** The output face is recessed 1 mm between R6.5 and R16.5. The
4×5 dowel (hub hole 2.5 deep) crosses that 1 mm gap and engages only 1.5 mm of the 5 mm motor hole, less than
1×D. A 4×8 dowel (ISO 8734) in the same hub hole would engage 4.5 mm. That changes the released rev A
purchased-parts list, so it is the user's call; if taken, the dowel length should come from the interface file.

**Plan.** After triage, run it as a quick_check line. It reuses the built bodies but needs the vis placement, about
5–8 s. That brings quick_check back over its 30 s target, so the plan is to cache the vis placement shared with
the envelope check.

## TI-017: check_engagement skipped screws by name  (fixed)

**What happened.** Screws were matched by `name.split('_')[0] in SCREWS`, so `SB5x6_…` and `SB5x12_…` shoulder
screws were never checked. The main session changed it to `startswith`. The new regression test then found that
`SetScrew_M3x3_drum`, `SetScrew_M3x3_screwgear` and `SetScrew_M3_motorgear` (SCREW variant) were still missed:
the prefix is `SETSCREW`, the names are mixed case.

**Fix.**
- `check_engagement.is_screw(p)` now matches by catalogue key (`p.src in SHCS/BHCS/CSK/SETSCREW/SB5`), not by name.
- `main()` is guarded by `QC_IMPORT`, so it can be imported.
- Test `cad/tests/test_engagement_screws.py` cross-checks it against the names in any case, and requires an SB5
  part. PASS on both variants: SCREW 153 screws (SB5 6, SETSCREW 3), FOURBAR 98.

**Not re-run here:** `check_engagement.py` on SCREW. For the release variant it also writes
`cad/fab/engagement_report.txt`, a release output. The 3 set screws are now judged there, so the main session
should re-run it. FOURBAR has no set screws, so its result is unchanged.

## TI-018: freecadcmd swallows tracebacks and short-script output  (fixed)

**What happened.** The main session saw a script that raised exit 1 with no output, and used a runpy wrapper to
see the traceback. Same family as TI-010, where short scripts printed nothing.

**Fix: `cad/tools/run.py`**, a plain-Python launcher: `python -I cad/tools/run.py [--grip G] [--timeout S]
SCRIPT [args]`.
- It starts freecadcmd with `-c` code that runs the script through runpy, with a real `__file__` and `sys.argv`.
- It prints any traceback, flushes, and exits with the script's own code (124 on timeout).
- It drops the FreeCAD banner and ends with `RUN <script>: OK|FAIL (exit N) in S s`.
- Test `cad/tests/test_run.py` (5/5): short print shown, traceback shown with exit 1, exit code kept, `__file__`
  and GRIP set, FreeCAD imports work.
- The FreeCAD tests in `cad/tests/` now exit 1 on FAIL, so run.py reports FAIL rather than OK.
- **Proposed CLAUDE.md line (needs the user's OK):** "Run FreeCAD scripts with `python -I cad/tools/run.py
  [--grip G] SCRIPT`, not `freecadcmd SCRIPT`."

## TI-019: quick_check doesn't run the level-keeping check  (fixed 2026-11-18)

`tools/check_level_keeping.py` (closure, dead-point margins, elbow and wrist sweeps) takes about 4 minutes and
had a single `main()`.

**Fix** (after the main session said the file was final):
- Checks 1 + 2 moved into `closure_margins() -> (ok, lines, summary)`. They are kinematic only (placements and
  pin positions, no booleans) and take well under 1 s. `main()` calls it first, then runs the sweep as before;
  the standalone output and the `level_keeping` evidence record are unchanged.
- `main()` runs only when `QC_IMPORT` is unset, like the other checks quick_check imports.
- quick_check check 6 `level-keep` prints closure, the worst dead-point margin and where, and the margin at the
  elbow limits, with any FAIL line. The sweep's FRESH/STALE shows in the evidence list as `level_keeping`.
- One function, not separate `closure()` and `margins()` as planned: both walk the same sample list.

## TI-020: no bloat detector for the periodic cleanup agent  (fixed 2026-11-18)

**Request** (user-approved, via the main session): a deterministic report that a scheduled cleanup agent consumes.

**Fix.** `tools/bloat_report.py`, plain Python, about 1.5 s, always exits 0.
- Kinds: unused-import, unused-variable, dead-def (ast names, attributes and words in string literals across every
  tracked `*.py`, docstrings excluded), duplicate (6 identical significant lines, or 8 after blanking names, numbers
  and strings), orphan-param, orphan-catalogue (string literals plus the CAT `src` column of
  `out/<variant>/map_parts.md`, because some keys are built at run time), orphan-interface, orphan-envelope,
  out-unindexed (not in the manifest and no tool names the file), scratch (`*.bak*`, `*.FCBak`, ...).
- `tools/bloat_keep.toml`: `[[path]]` globs (rev A package, release generators) and `[[item]]` entries, each with a
  reason. Kept in `tools/`, not `data/`, so editing it does not change `params.inputs_hash()` and stale every check.
  A name that only frozen code uses is reported as kept ("used only by frozen/release code: ..."), e.g. GT2-BELT.
  Unmatched `[[item]]` entries without `guard = true` are listed so the keep-list does not rot.
- Outputs: `cad/out/bloat_report.md` + `.json` (stable ids `kind:path:name`, new/resolved since the last run,
  deterministic so re-runs don't churn git) and a `bloat` evidence record. `--counts` prints one line, writes nothing.
- quick_check line `bloat` (informational, never fails). `tools/install_hooks.py` writes a non-blocking
  `.git/hooks/pre-commit` that prints the counts; it refuses to replace a hook it did not write. **Not installed**:
  installing a hook is the user's call (`python -I cad/tools/install_hooks.py`).
- `tests/test_bloat_report.py`: planted dead function, unused import, unused local and orphan param are found; a
  keep-listed planted function is kept; nothing in the rev A package or a release generator is a finding.
- Limits: names built at run time (`getattr(H, "gt2_" + x)`) are invisible; a TOML key read by iterating its table
  shows as an orphan. The report says to check both before deleting. Stale part maps are noted in the report.

## TI-021: manifest `files` paths escape the job folder  (fixed 2026-11-18)

`out/fourbar/manifest.json` listed `../level_keeping.txt` (level_keeping) and
`../../../../Windows/System32/ARC_Arm_Fourbar.FCStd` (working_doc): both tools passed a bare file name to
`params.record`, which resolved it against the cwd (System32 in the FreeCAD GUI). Found while reading the
manifest for bloat_report. Fix: both pass the absolute path. The entries correct themselves on the next run of each tool.

## TI-022: hard-coded checkout path breaks worktree isolation  (fixed 2026-11-18)

**What happened.** The new tooling observer works in its own git worktree (`.claude/worktrees/tooling-observer/`).
Its baseline found `CAD = r"C:\Users\ryanh\light_weight_arm\cad"` as a bare assignment in
`tests/test_catalogue_mass.py`, `tests/test_envelope_catches_pole.py`, `tests/test_params_flow.py` and
`tools/quick_static.py` (`sys.path.insert`). From a worktree those imported the main checkout's model and tools,
so they tested someone else's files and could write into the user's `cad/out/`. The tools themselves were safe:
they resolve `CAD` from `__file__` and fall back to the literal only without one. The main session also reported
that the worktree showed as untracked in the user's checkout, and asked that `bloat_report` never scan `.claude/`.

**Fix.**
- The four files resolve the repo from `__file__`. `tests/test_fingerprint_moved_hole.py` drops its fallback,
  because tests always run through `tools/run.py`, which sets `__file__`.
- `.gitignore`: `.claude/worktrees/`.
- `bloat_report.py`: `.claude` in `SKIP_DIRS` (scratch walk, no-git walk) and `.claude/` in `SKIP_PREFIX` (git
  file list). Without this, a worktree's untracked copy of every `.py` would be scanned in the main checkout.
- New `tests/test_no_checkout_paths.py` (plain Python). Rule: for every live `.py` (bloat_report's file list,
  minus the frozen `[[path]]` globs in `bloat_keep.toml`), a string constant holding a home path that leads into
  this repo is a finding: `X:\Users\…\<repo>`, `/c/Users/…`, `/home/…`, raw or escaped, f-strings included.
  The repo name is the main checkout's folder, taken from `git rev-parse --git-common-dir`. Allowed:
  docstrings (usage examples), and a statement with the `if "__file__" in globals() else r"…"` GUI-exec
  fallback. Paths to other tools (the `MWT_DIR` default in `test_evidence.py`) and synthetic test data are not
  this hazard and are not flagged; a first, broader rule over every home path flagged exactly those two.
  Negative part: 8 planted bad forms are flagged and 7 allowed forms are not.
- The pre-fix HEAD copies of the four files are flagged at their `CAD`/`sys.path` lines; the old
  `test_fingerprint_moved_hole.py` (fallback form) is not.
- `tests/test_bloat_report.py` case 4: a `.py` and a `.bak` planted under `.claude/` are invisible to
  `py_files()` and `scratch()`, and found once the skip is removed.

**Left as is.**
- Frozen code (release generators, `drawings/`, `render/`) still has bare paths, e.g. `drawings/make_drawings.py:31`
  and `render/fc_render.py:26`. Release generators must be run from the main checkout anyway.
- The `__file__` fallbacks in the tools still name the main checkout. They apply only when code is exec'd in the
  FreeCAD GUI, which is the user's session on the main checkout.
- `tools/mcp_provider.py`'s docstring example names the main checkout. A worktree session must pass its own path
  to the MCP tools.

## TI-023: test_validate_data hard-codes a TOML line number  (fixed 2026-11-18)

Found by the TI-022 gate: `param_typo_type` expected `:17: FB.ZL0: …`, but `ZL0` is on line 18 of
`params/gripper_fourbar.toml`, so the test FAILed at d45ee2e (11 passed, 1 failed). The validator was right. Fix:
the test finds the `ZL0 = [23.5, 26.5]` line in the file and asserts that both of its anchors still exist, so a
silent `str.replace` miss (TI-002) can't pass either. 12/12 PASS.

## TI-024: inputs hash depends on line endings  (fixed 2026-11-18)

**What happened.** At the same commit (d45ee2e), the main checkout's inputs hash is `d7e43ee0e386a980` and the
observer worktree's is `60fe32915db51fb3`, so every evidence record from one checkout reads STALE in the other.
**Root cause.** `git config core.autocrlf` is `true`. Git checked the worktree out with CRLF, while the main
checkout's files were written LF by the tools. `params.inputs_hash()` hashes raw bytes, and all 22 `.py`/`.toml`
inputs differ only in CRLF vs LF; the vendor files match. The same thing happens in the main checkout whenever
git re-writes a file (checkout, merge, pull).
**Fix (fix A, chosen by the main session).**
- `params.input_sha(path)` hashes `.py`/`.toml`/`.json`/`.md` with `\r\n` → `\n`, the same convention as the urdf
  sha in `cad/sim/gz_check.py` and `build_robot.py`. Vendor inputs (`.brep`, STEP) stay raw.
- `inputs_hash()` and the per-file list in `evidence/<check>.inputs.json` use it.
- `_sha` stays raw for evidence artifacts, the implementation and the snapshot file, because the
  template's `verify_report` re-hashes those files byte for byte.
- `params.py` is itself a hashed input, so every recorded check went STALE once (new hash `25e790bf621fca4f` at
  this commit). It is the same in an LF and a CRLF checkout.
- Test `tests/test_inputs_hash_eol.py` (plain Python):
  - CRLF and LF copies of each text type hash the same, a content change is still seen, and a `.brep` with
    CRLF bytes is not normalised;
  - the real 32 inputs, copied all-LF and all-CRLF, give one `inputs_hash`;
  - negative: the old raw-byte hash gives two different values on those trees;
  - `record()`'s snapshot uses `input_sha`.
Not done: a `.gitattributes` `eol=lf` (fix B), which is a repo-wide line-ending change and not needed for the hash.

## TI-025: floating screws in the working document  (fixed 2026-11-20)
**Symptom.** The user saw the rev B STS3215 bottom-cap screws (PAN-M2x12, 16 of them) hanging in the air in the
FreeCAD GUI's ARC_Arm_Fourbar document, 12-33 mm from their holes.
**Root cause, two gaps.**
- The coloured GUI build was made while `hardware.pan_screw` returned one object as both vis and chk, so
  `sts_case_screws` translated it twice by the screw-pattern offset.  The bug was fixed and the file on disk was
  rebuilt headless, but the document left open in the GUI was never rebuilt, and no check looks at it.
- `check_seated` would not have caught the bug in the model either: it judged only SHCS/BHCS/CSK/SB5 (not the
  `PAN-*` keys), and it only asked whether the point under the head lies in a coaxial hole, never whether the head
  actually bears on anything.
**Fix.**
- `tools/check_seated.py`: `PAN-*` screws are judged; new rule 2: the head's bearing face (an annulus between
  shank and rim; the cone for countersunk heads) and both faces of every washer must touch another part within
  0.2 mm, else FAIL "floating" with the distance to the nearest part.  It now runs inside `quick_check`
  (`seating`, ~3-6 s).  FOURBAR 119 and SCREW 154 fasteners: 0 FAIL.
- `tests/test_seated_floating_head.py`: every PAN screw pulled 2 mm off its floor (rule 2 only) and shifted
  13.2 mm sideways (the original bug) must be flagged, and nothing else may start failing.  PASS (16/16, 16/16).
- `tools/check_working_doc.py`: compares every part of the working document (the open GUI document when run in the
  GUI, else the saved file) with the model at STOW by exact bounding box (`optimalBoundingBox`: the plain box
  tightens once the GUI has meshed a shape, ~1.3 mm on button heads) and volume.  Before the rebuild: 96 FAIL in
  the open document; after: 0.  It is a standalone check (its evidence goes STALE like the others), not part of
  quick_check: opening the document costs ~15 s and quick_check cannot see the GUI anyway.

## TI-026: scheduled tooling agent stalls on a permission prompt  (fixed 2026-11-21)

**What happened.** Runs of `arm-weekly-bloat-cleanup` on 2026-11-20 14:13Z, 11-21 02:13Z, 14:13Z and 11-22 02:13Z
each ended after 4 turns: the first Bash call (`git fetch` / `worktree add`) raised a permission prompt, nobody was
there, and the run ended "interrupted ... for tool use". The app still lists them as succeeded. The MCP
maintenance task runs fine, so it is the task's permission mode, not the prompt.

**Fix (the user's decision; permissions stay with the user).** In the Claude app, Scheduled, open the task and
set its permission mode to Auto (code.claude.com/docs/en/desktop-scheduled-tasks: the mode is set per task).
The same applies to `arm-repo-upkeep`, which replaced both arm tasks on 2026-11-21 (created in the default mode). Alternative: click "Run now"
on the task's page and approve its tools once; the app stores those approvals on the task for later runs.

**Resolution.** `arm-repo-upkeep` was created from a turn typed in the desktop app, so it kept this session's
Bypass mode. It needs no prompt answered. Bypass reviews nothing; Auto would still run unattended with the
classifier checking each action.

## Upkeep runs

Kept by the daily `repo-upkeep` skill (`.claude/skills/repo-upkeep/SKILL.md`, scheduled task `arm-repo-upkeep`), one row per run, "no change" included. It replaced the twice-daily tooling agent and the docs audit on 2026-11-21.

Phase A is the agent harness against the latest docs; phase B is one CAD-tooling improvement.

| Date | CLI | Docs pages read | Phase A (harness) | Phase B (CAD tooling) | Suggested | Gates |
|---|---|---|---|---|---|---|
| 2026-11-21 | 2.1.326 | code.claude.com/docs: skills, sub-agents, hooks, settings, permissions, memory, mcp, scheduled-tasks, desktop-scheduled-tasks, routines, plugins, worktrees, checkpointing, sandboxing; platform.claude.com/docs/mcp; developers.openai.com/learn/docs-mcp; github.com/anthropics/skills | docs MCPs `claude-platform-docs` and `openai-docs` (user scope); `PYTHONUTF8` env (TI-003); release-guard hook (TI-028); skills `verify`, `fusion-change`, `codex-fusion`, `tooling-audit`; `test_agent_config.py` (TI-029); CLAUDE.md agent section (TI-004); tooling-agent prompt (TI-027); daily upkeep task | none (manual session; repo cleanup landed: 77cd101) | task permission mode (TI-026) | tests, validate_data, bloat 0 |
| 2026-11-21 (scheduled) | 2.1.326 | code.claude.com/docs: changelog, hooks (Monitor matchers, v2.1.314), skills, settings, sub-agents, permissions, desktop-scheduled-tasks, worktrees; platform.claude.com/docs/en/models/overview; learn.chatgpt.com/docs/developer-commands, developers.openai.com/learn/docs-mcp; github.com/anthropics/skills commits (Office/MCP-builder skills only) | no change: same CLI as the morning row, nothing new for this repo (docs features past 2.1.326, e.g. v2.1.328/330, not adopted); release guard left Edit/Write-only as designed (TI-028) | TI-005 fixed: quick_check step 10 `holes/eng` runs check_holes/check_engagement on the parts the fingerprint says changed (0 s on MATCH); check_holes `scan_part`, check_engagement `scan(only=)`, results identical to the full reports (43/18 rows); test_quick_holes_changed (both variants) | none | validate_data, agent_config, no_checkout_paths, bloat 0 -> 0, all 21 tests incl. DIRECT, quick_check PASS + MATCH both variants (71.5 / 72.7 s), interference 0 overlaps (376 s) |
| 2026-11-21 (manual, best practices) | 2.1.326 | /en/best-practices, /en/skills (verify, invocation control, prompt-audit); `/doctor prompt-audit` run headless | CLAUDE.md, repo-upkeep and codex-fusion fixes (TI-032) | none | TI-030, TI-031 | test_agent_config, paths in CLAUDE.md exist |
| 2026-11-22 (scheduled) | 2.1.326 | code.claude.com/docs: changelog (to v2.1.330: 30-day scheduled tasks, prompt-hook model aliases; past the installed CLI, not adopted), best-practices; `/doctor prompt-audit` headless; developers.openai.com changelog search (nothing for the Codex hand-off); github.com/anthropics/skills commits (Office skills only, 11-16) | repo-upkeep phase B step 1 no longer names TI-005 (fixed 11-21) or fixed IDs as examples; it now reads the status column (prompt-audit finding 1, checked against the TI table). Audit's other findings report-only (plugin wording, paths that resolve) | TI-033 check gap: `cad/tests/test_interfaces_moved_part.py` moves one PASSing part per bolt-pattern interface 3 mm off its normal in memory: 4/4 flagged GEARED, 5/5 DIRECT, unmoved rows unchanged; `check_interfaces.main(bodies=None, write=True)` (quick_check call unchanged) | none new (TI-030, TI-031 still open) | validate_data, agent_config, no_checkout_paths, bloat 0 -> 0, all 22 tests incl. DIRECT, quick_check PASS + MATCH both variants (77.8 / 80.6 s), interference 0 overlaps (403 s) |
| 2026-11-22 (manual, user-approved) | 2.1.326 | /en/permissions, /en/tools-reference (Bash deny turns PowerShell off), /en/mcp (disable per project), /en/auto-mode-config | deny rules + test (TI-030); five MCP servers off for this project (TI-031) | none | Auto mode for the daily run (user, in the app) | test_agent_config, test_release_guard, test_no_checkout_paths; force-push dry run denied |
