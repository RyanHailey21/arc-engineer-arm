---
name: tooling-audit
description: Audit this repo's agent tooling (CLAUDE.md, .claude/ skills, agents, hooks and settings, MCP servers, scheduled agents, the Codex hand-off) against the latest Claude Code, Claude platform and OpenAI documentation, then land the safe improvements and list the rest as suggestions. Use daily (scheduled) or when asked to bring the agent tooling up to date.
---

# Agent tooling audit

Goal: keep this repo on the current Claude Code harness. Find documented features and changed best practices that
would make agent work here faster, safer or more reliable, land the ones that are safe, and hand the rest to the
user. One run lands at most a few related changes; nothing trivial (see "Meaningfulness").

The twice-daily tooling agent (`~/.claude/scheduled-tasks/arm-weekly-bloat-cleanup`) owns the CAD checks in
`cad/tools/` and `cad/tests/`. This audit owns the agent harness. Don't take its work. It runs daily, so most runs find nothing new: then record "no change" with the pages checked and stop, without forcing a change.

## 1. Read the current state
- `CLAUDE.md`, `.claude/settings.json`, `.claude/skills/*/SKILL.md`, `.claude/agents/` (if any), `cad/tools/hooks/`.
- `cad/docs/tooling_issues.md`: the open items and the "Docs audits" table at the end. The table's last row says
  which CLI version and doc pages the previous run covered; don't redo or undo what it records.
- `claude --version`, and `claude mcp list` (health of every server, read-only).
- The scheduled agents' prompts in `~/.claude/scheduled-tasks/*/SKILL.md`, and their recent runs: a run that
  ended after a few turns with "Request interrupted ... for tool use" was stopped by a permission prompt.
- The Codex hand-off: `.claude/skills/codex-fusion/SKILL.md` and `C:\Users\ryanh\tools\_agent\codex-fusion\`.

## 2. Read what is new (primary sources only)
- Claude Code docs MCP (`claude-code-docs`): search the changelog and the pages for skills, sub-agents, hooks,
  settings, permissions, memory, MCP, scheduled tasks, plugins, worktrees, output styles, status line. Note what
  is new since the CLI version in the last audit row. Use only features documented for the installed version.
- Claude platform docs MCP (`claude-platform-docs`): model ids, tool use, MCP connector, Agent SDK changes that
  affect how this repo drives Claude.
- OpenAI docs MCP (`openai-docs`): Codex CLI changes (config, `AGENTS.md`, MCP, approvals) that affect the Codex
  hand-off.
- `gh api repos/anthropics/skills/commits?per_page=10` and the repo's skill list: anything useful for a CAD repo.
Cite the page for every finding.

## 3. Decide, per finding
**Land it** (in a worktree, step 4) when it changes only repo-scoped agent tooling: `.claude/skills/`,
`.claude/agents/`, hooks and `env` in `.claude/settings.json`, the agent sections of `CLAUDE.md`,
`cad/tools/hooks/`, `cad/tests/test_agent_config.py` and hook tests.

**Suggest it** (step 5), never apply it, when it touches:
- permissions, permission modes or `defaultMode` (security settings stay the user's);
- user or machine config: `~/.claude.json`, `~/.claude/settings.json`, `~/.codex/config.toml`, MCP registrations;
- the scheduled tasks themselves, plugins and marketplaces, model or effort defaults;
- anything under the design or the released package.

**Meaningfulness.** A finding counts if it prevents a class of agent mistake, removes a recurring manual step or
permission stall, makes context cheaper (for example moving procedure out of CLAUDE.md into an on-demand skill),
or adopts a documented feature that replaces a workaround here. Wording-only edits, renames and churn don't count.
If nothing clears the bar, change nothing and log "no change" with the candidates you rejected.

## 4. Land (only for "land it" findings)
1. `git -C C:\Users\ryanh\light_weight_arm fetch origin`, then
   `git -C C:\Users\ryanh\light_weight_arm worktree add C:\Users\ryanh\light_weight_arm-audit -b audit/<YYYY-MM-DD> origin/main`.
   If the folder or branch exists, report it and stop. Never edit the user's checkout.
2. Make the change. Every new hook gets a test in `cad/tests/` that feeds it a matching and a non-matching event.
3. Gates, all must pass: `python -I cad/tests/test_agent_config.py`, the hook tests,
   `python -I cad/tests/test_no_checkout_paths.py`, `python -I cad/tools/validate_data.py`,
   `python -I cad/tools/bloat_report.py --counts` (no new findings). No change to geometry, params, interfaces,
   envelopes or check results.
4. Commit with `GIT_NO_AUTOPUSH=1` (the post-commit hook would push the branch), message ending
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Fast-forward main: `git push origin audit/<date>:main`
   (never force). If it is not a fast-forward, or a gate fails, leave the branch and report it.
5. Remove the worktree and the branch.

## 5. Record and report
Record every run, "no change" included, in the worktree (create it as in step 4.1 if nothing landed), and commit
and fast-forward the record through the same gates and steps 4.4 to 4.5.
- Add a row to the "Docs audits" table in `cad/docs/tooling_issues.md` (date, CLI version, pages read, landed,
  suggested). Each suggestion that needs the user becomes a TI row `open: needs the user`, with the exact change
  (file, key, value) and the doc URL, unless an open row already covers it.
- Final report, short: what landed (files, why, gate results), each suggestion with its URL and exact change,
  the rejected candidates, and whether main moved (if so: `git pull --ff-only`).
