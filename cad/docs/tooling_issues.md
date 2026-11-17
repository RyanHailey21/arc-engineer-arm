# Tooling issues (observed friction → fix)

Kept by the tooling-observer session. Each entry: what happened (with transcript evidence), root cause, fix or
plan, status (`open`, `fixed`, `wontfix`). Transcript = `~/.claude/projects/C--Users-ryanh-light-weight-arm/
95cc053c-….jsonl`; "L1234" is a line number in it. Scan method: every `tool_result` with `is_error`, timed
against its `tool_use` (142 errors in 19,040 lines up to 2026-11-17 04:30Z).

| ID | Date | Summary | Status |
|---|---|---|---|
| TI-001 | 2026-11-16 | MCP client cuts every freecad-mcp call at ~60 s; long results lost | fixed (server restart needed) |
| TI-002 | 2026-11-16 | Patching Python through heredocs / `s.replace` / `sed` fails or misses silently | fixed |
| TI-003 | 2026-11-16 | `print()` crashes on cp1252 console (UnicodeEncodeError) | open: settings change proposed |
| TI-004 | 2026-11-16 | Auto-mode classifier can't review commands that start with `cd`; `sleep N; cat` blocked | open: CLAUDE.md line proposed |
| TI-005 | 2026-11-16 | Quick tier misses hole-wall and thread-engagement defects (found only in the full run) | open: plan |
| TI-006 | 2026-11-16 | Status tools (`get_rpc_status`, `get_async_status`) hang when FreeCAD is stuck | open: plan |
| TI-007 | 2026-11-16 | Eval case YAML frontmatter colon bug | open: needs a check in the plugin |
| TI-008 | 2026-11-16 | `claude` CLI too old for `plugin eval` | fixed (2.1.326) |
| TI-009 | 2026-11-16 | Fingerprint misses a hole moved inside a generic-Shape part (bbox-centre "com") | fixed; baselines re-recorded |
| TI-010 | 2026-11-16 | freecadcmd given a short script by path printed nothing (test "passed" silently) | open: workaround in use |
| TI-011 | 2026-11-16 | Eval graders regex the tool *listing* in `trace`: false FAIL (readme) and false PASS (pole clash) | fixed; verification run |
| TI-012 | 2026-11-16 | Eval graders needing plugin tools scored in the no-plugin arm (no Bash there): inflated Δ | fixed (`arm: with-only`) |
| TI-013 | 2026-11-16 | Quick-check mock contradicted the fingerprint mock (CHANGED vs MATCH) on the refactor case | fixed |
| TI-014 | 2026-11-16 | Ceiling cases (drawings, stale) pass in both arms: they test the fixture's CLAUDE.md, not the plugin | open: plan |
| TI-015 | 2026-11-17 | No check compares purchased-part mass with the catalogue (DM-J4340 counted twice; GT2 belt weighs 0 g) | fixed: test; belt entry is the main session's |

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

## TI-003: `print()` crashes on the cp1252 console  (open: settings change proposed)

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

## TI-004: classifier "no verdict" on `cd …` commands; blocked `sleep`  (open: convention proposed)

**What happened.** Five Bash calls were refused with "auto mode reviewed this call without its leading cd, and
the shell has moved since" (L5847, L6286, L6293, L6373, L6476), and each was re-sent. `sleep 60; cat …` was
blocked twice (L7478, L12053).

**Root cause.** The harness reviews commands that start with `cd` without the `cd`, so it refuses them when the
working directory has changed since. Foreground `sleep` is disallowed by design.

**Proposed CLAUDE.md line (needs the user's OK):** "Bash: use absolute paths instead of a leading `cd`; wait on
long jobs with `run_in_background` or Monitor, never `sleep`." With TI-001 fixed, MCP jobs are polled through
`job_status`.

## TI-005: quick tier misses hole walls and thread engagement  (open: plan)

**What happened** (main-session report). Hole-wall and thread-engagement defects appeared only in the full run.
`quick_check.py` lists `holes` and `engagement` evidence as FRESH/STALE but doesn't run them. `check_holes.py`
takes about 2–3 minutes for all made parts.

**Plan.** Add a `--changed` hole and engagement pass to `quick_check.py`:
1. Take the per-part fingerprint diff (fingerprint g2 already hashes each part).
2. Run `check_holes` and `check_engagement` on the changed made parts only, usually 1–5 parts and a few seconds.
3. Write `holes`/`engagement` evidence scoped to those parts, so FRESH means "checked since the change".

Acceptance: a seeded thin wall in one gripper part FAILs in the quick tier in under 40 s total, on both variants.
This needs the per-part diff API in `fingerprint.py` (my area) and a call from `quick_check.py`. Next item.

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
- The catalogue is a design input, so the entry is the main session's to add. **Plan:** once it's added, run this
  test as a `catalogue` line in `quick_check.py`. It needs no extra build, about 0.1 s.
