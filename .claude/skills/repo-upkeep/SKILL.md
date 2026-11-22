---
name: repo-upkeep
description: Daily upkeep of this repo's tooling in two phases. (A) Audit the agent harness (CLAUDE.md, .claude/ skills, agents, hooks and settings, MCP servers, scheduled agents, the Codex hand-off) against the latest Claude Code, Claude platform and OpenAI docs. (B) Land one CAD-tooling improvement (open tooling issues, check gaps, check speed, real dead code). Use for the scheduled daily run, or when asked to bring the tooling up to date.
disable-model-invocation: true
---

# Repo upkeep (daily)

One run, two phases, one worktree, one gate pass, one record row. Each phase lands at most ONE meaningful
change, or none. "No change" is a fine result; padding is not. Most days the docs have nothing new, so phase A
records the pages checked and stops.

Repo: `C:\Users\ryanh\light_weight_arm`, branch `main`, pushed to the PUBLIC GitHub repo
RyanHailey21/arc-engineer-arm (never put secrets or the user's email anywhere). The user works on `main` and wants
fast-forward merges, not pull requests. `*.FCStd` files are in Git LFS. Run FreeCAD scripts with
`python -I cad/tools/run.py SCRIPT` (shows tracebacks). FOURBAR is the only gripper; `BASE_DRIVE=DIRECT` selects
the direct-drive base (fingerprint `fourbar_direct`).

## 0. Worktree and context
1. `git -C C:\Users\ryanh\light_weight_arm fetch origin`, then
   `git -C C:\Users\ryanh\light_weight_arm worktree add C:\Users\ryanh\light_weight_arm-upkeep -b upkeep/<YYYY-MM-DD> origin/main`.
   If the folder or branch exists from an earlier run, report it and stop. Work only there: never edit, check out,
   stash or clean the user's checkout, and never delete their untracked files.
2. The post-commit hook auto-pushes every commit, and the worktree shares it: make EVERY commit with
   `GIT_NO_AUTOPUSH=1`. Only the fast-forward in step 3 publishes anything.
3. Read `CLAUDE.md`, `cad/MAP.md`, `cad/tools/bloat_keep.toml` (deliberate survivors; never touch them) and
   `cad/docs/tooling_issues.md`: the open TI items and the last 10 rows of its "Upkeep runs" table at the end.
   Don't redo or undo what those rows record.

## Phase A: agent harness, against the latest docs
**Read the state.** `.claude/settings.json`, `.claude/skills/*/SKILL.md`, `.claude/agents/` (if any),
`cad/tools/hooks/`; `claude --version`; `claude mcp list` (read-only); the scheduled tasks' prompts in
`~/.claude/scheduled-tasks/*/SKILL.md` and their recent runs (a run that ended after a few turns with "Request
interrupted ... for tool use" was stopped by a permission prompt); the Codex hand-off
(`.claude/skills/codex-fusion/SKILL.md`, `C:\Users\ryanh\tools\_agent\codex-fusion\`).

**Check the standing best practices, every run, not only what changed.** A repo can fall behind without anything
new being published.
- Re-read `/en/best-practices` in the `claude-code-docs` MCP and check the repo against it: CLAUDE.md holds only
  what Claude can't find in the repo (exact check commands, decisions, gotchas; no layout tours); procedures are in
  skills, and skills with side effects have `disable-model-invocation: true`; rules with zero exceptions are hooks or
  deny rules rather than CLAUDE.md lines; rules for one area are path-scoped in `.claude/rules/`; the unattended run
  answers the five questions under "Let Claude run without you" (done, self-check, what it may touch, what stops
  it, who signs off).
- Run the instruction audit headless, read-only:
  `MSYS_NO_PATHCONV=1 claude -p "/doctor prompt-audit" --permission-mode plan` (without the variable, Git Bash
  rewrites the leading `/` into a path). Check each finding against the files before acting on it.

**Read what is new, primary sources only, citing the page for every finding.**
- `claude-code-docs` MCP: the changelog, and the pages for skills, sub-agents, hooks, settings, permissions,
  memory, MCP, scheduled tasks, plugins, worktrees, output styles, status line. What is new since the CLI version
  in the last row? Use only features documented for the installed version.
- `claude-platform-docs` MCP: model ids, tool use, MCP connector, Agent SDK changes that affect this repo.
- `openai-docs` MCP: Codex CLI changes (config, `AGENTS.md`, MCP, approvals) that affect the Codex hand-off.
- `gh api repos/anthropics/skills/commits?per_page=10` and its skill list: anything useful for a CAD repo.

**Decide.** *Land* it only if it changes repo-scoped agent tooling: `.claude/skills/`, `.claude/agents/`, hooks and
`env` in `.claude/settings.json`, the agent sections of `CLAUDE.md`, `cad/tools/hooks/`,
`cad/tests/test_agent_config.py` and hook tests. Every new hook gets a test feeding it a matching and a
non-matching event. *Suggest* it, never apply it, when it touches permissions or permission modes, user or machine
config (`~/.claude.json`, `~/.claude/settings.json`, `~/.codex/config.toml`, MCP registrations), the scheduled
tasks, plugins and marketplaces, or model and effort defaults. A suggestion becomes a TI row `open: needs the
user` with the exact change (file, key, value) and the doc URL, unless an open row covers it.

**Bar.** It prevents a class of agent mistake, removes a recurring manual step or permission stall, makes context
cheaper (for example procedure moved from CLAUDE.md into an on-demand skill), or adopts a documented feature that
replaces a workaround here.

## Phase B: CAD tooling
Run `python -I cad/tools/bloat_report.py` (read `cad/out/bloat_report.md`) and `cad/tools/quick_check.py`, noting
each step's time. Choose ONE target, the highest on this list you can finish and verify in this run:
1. An `open` TI item in `cad/docs/tooling_issues.md` fixable in code in this repo. Skip items whose status says
   they need the user, a settings change, a plugin or another repo (read the status column; don't trust IDs named here).
2. A check gap: a check in `cad/tools/` with no negative test in `cad/tests/` (a test that breaks the geometry in
   memory and proves the check flags it), or a defect class nothing checks.
3. Speed: `quick_check` keeps its documented budget; make a slow step faster with identical results.
4. Bloat that needs real work: duplicates consolidated into one behaviour-identical helper; orphan params wired to
   the literal they should drive (no geometry change) or removed.
5. Dead code with zero references in `cad/` and `sim/`, grepping the bare name too (strings, BODY_FUNCS, GRIPPERS,
   getattr). Only counts if it removes about 30 lines or 3 items.

**Bar.** It prevents a real class of defect, makes a check or the workflow measurably faster, or removes real dead
weight.

**Hard limits.** No geometry change; never re-record fingerprints. Don't change the semantics of `cad/interfaces/`
or `cad/envelopes/`. Never touch the released package (`cad/fab/`, `cad/fea/out/`, `cad/render/`), the release
generators (`export_fab.py`, `fea/run_fea.py`, `render/export_render.py`) or anything only they use. A new or
stricter check that FAILs on the current design is a finding, not something to tune away: commit it with the
failure recorded in tooling_issues.md, and do NOT fast-forward main (a red main blocks the user).

## Not results, in either phase
Comment, docstring or wording edits; whitespace, formatting or import order; renames; a single unused import; type
hints; moving code without changing behaviour. These may only ride along with a meaningful change in the same files.

## 1. Gates (in the worktree; all must pass)
Always: `python -I cad/tools/validate_data.py`; `python -I cad/tests/test_agent_config.py`;
`python -I cad/tests/test_no_checkout_paths.py`; `python -I cad/tools/bloat_report.py --counts` (no new findings).
If anything outside `.claude/`, `CLAUDE.md`, `cad/docs/` and `cad/tools/hooks/` changed, also:
- `cad/tools/quick_check.py` as is and with `BASE_DRIVE=DIRECT`: no FAIL, fingerprint MATCH for both (CHANGED
  means you changed geometry: revert it);
- every test in `cad/tests/`, each as its docstring says, including new ones. A new check needs a negative test you
  watched fail with the defect injected;
- `cad/check_interference.py` (about 4 min, in the background): 0 overlaps.

## 2. Record
Add one row to the "Upkeep runs" table in `cad/docs/tooling_issues.md`, "no change" runs included: date, CLI
version, docs pages read, phase A result, phase B result (category, what changed, what it prevents or speeds up,
with numbers), suggestions, gate results. Add or update a TI row for any issue fixed or found.

## 3. Publish
Commit with `GIT_NO_AUTOPUSH=1`, message ending with the attribution line the session gives (else `Co-Authored-By: Claude <noreply@anthropic.com>`). Then
fast-forward main: `git push origin upkeep/<date>:main` (never force, never rewrite history). If a gate failed or
it is not a fast-forward, leave the branch and worktree and record the run as "blocked" with the reason.
Otherwise remove the worktree and the local branch.

## 4. Report (short)
What landed in each phase (files as file:function, why, numbers), each suggestion with its URL and exact change,
rejected candidates, bloat counts before and after, scratch files the user could delete (`*.bak`, `*.FCBak`, with
sizes; list only, never delete), gate results, and whether main moved (if so: `git pull --ff-only`).
