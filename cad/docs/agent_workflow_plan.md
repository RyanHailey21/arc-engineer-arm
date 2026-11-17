# Plan: making the code-CAD conventions repeatable for agents

Status: proposal, 2026-11-16. Nothing in this plan is implemented yet unless marked **(exists)**.

## 1. Goal and principle

The arm project now has conventions that make agent CAD work fast and checkable:
- parameter files, interface files and envelope files;
- a quick-check tier, a fingerprint regression guard, per-variant evidence with stale tracking;
- a release guard and a generated `MAP.md`.

Today they live in one repo and in one agent's memory. The goal is for **any agent, on this project or a new one, to apply them the same way every time**.

Put each convention where the platform makes it most reliable:

| Need | Mechanism | Why (source) |
|---|---|---|
| Must happen every time, no judgement | **Hook** | "An instruction is a request, not a guarantee"; put guardrails in hooks (Claude Code features overview, hooks guide) |
| Always-true orientation and short rules | **CLAUDE.md / AGENTS.md**, under 200 lines | Loads every session (features overview) |
| Rules for certain paths only | **`.claude/rules/*.md`** with `paths:` | Loads only when matching files are touched |
| Procedure that needs judgement, or occasional reference | **Skill** (`SKILL.md` + references + scripts) | On demand, progressive disclosure, about 100 tokens until used (Agent Skills best practices) |
| Deterministic geometry work (build, probe, compare) | **MCP tool** in the generic `freecad-mcp` | Workflow-shaped tools; keep project facts out of a generic server (Anthropic "Writing tools for agents") |
| Project facts | **Data files** in the project (`params/`, `interfaces/`, `envelopes/`, `data/`) | Already the template's rule: "project facts belong in project files, not this server" (freecad-mcp `portable-workflow.md`) |
| Reuse across repos | **Plugin** (skills + hooks + MCP config) from a marketplace | Plugins package skills, hooks and `.mcp.json` (plugins docs) |

## 2. What exists today

Arm project:
- **(exists)** `CLAUDE.md`;
- **(exists)** `params/`, `interfaces/`, `envelopes/`, `data/`, `iface.py`, `params.py`;
- **(exists)** `tools/quick_check.py`, `fingerprint.py`, `check_interfaces.py`, `make_map.py`;
- **(exists)** `out/<variant>/manifest.json`, the release guard, and `tests/`.

`mechanical-workflow-template`:
- **(exists)** `workflow.py status/build/record-check/package`;
- **(exists)** `project.json` facts as `{value, unit, status, source}`;
- **(exists)** a protected `deliverables/` folder;
- **(exists)** the `cad-build-workflow` skill (28 lines), `AGENTS.md` and CI tests.

`freecad-mcp` fork:
- **(exists)** about 40 tools, including `interference_check` and `hole_edge_check`, which use a project *provider* module (`cad/tools/mcp_provider.py`);
- **(exists)** `gui_batch`, `techdraw_verify`, and the `cad-evidence/1` evidence envelope;
- **(exists)** the `techdraw-drawings` skill (133 lines).

Gaps found:
1. The arm's `manifest.json` invented its own evidence format instead of `cad-evidence/1`.
2. The template has no interface, envelope, fingerprint or quick-tier concepts. The arm has no `workflow.py`.
3. Nothing *enforces* the rules: a STALE result, an edit to a protected release folder, or an unrecorded fingerprint change all rely on the agent remembering.
4. The `freecad-mcp` tools register with `structured_output=False` and carry no read-only or destructive annotations.
5. No evals measure whether an agent follows the conventions.

## 3. Target architecture

```
mechanical-cad plugin (marketplace: RyanHailey21)        <- reuse across projects
  skills/  cad-iterate · cad-add-variant · cad-interfaces-envelopes · cad-release (manual) · techdraw-drawings
  hooks/   protect-release · validate-data-files · stale-evidence-on-stop · session-status
  .mcp.json -> freecad-mcp (pinned commit)

freecad-mcp (generic, no project facts)                  <- deterministic geometry tools
  project_fingerprint · interface_probe · envelope_check · quick_check · project_map
  (all driven by the project's provider module + data files, all returning cad-evidence/1)

project repo (facts only)                                <- per project
  CLAUDE.md / AGENTS.md (<200 lines) · .claude/rules/ · params/ interfaces/ envelopes/ data/
  provider module (bodies(), placements(), poses()) · out/<variant>/ evidence · deliverables/
```

## 4. Work packages

### WP1. Shared schemas and the evidence format (template repo)
- Write JSON schemas for `params/*.toml`, `interfaces/*.toml` (frame, pattern, side_a/side_b, fastener) and `envelopes/*.toml` (keepout entries with poses, frame and box).
- Every value must carry `unit` and `source`, matching the template's `facts` convention.
- Make the arm's `params.record()` write `cad-evidence/1` envelopes: producer, operation, status pass/fail/unknown, inputs with SHA-256, artifacts. Keep the inputs hash for stale detection.
- **Acceptance:**
  - the arm's existing data files validate;
  - a deliberately broken file is rejected with a message naming the field and the allowed values;
  - the manifest entries parse as `cad-evidence/1`.

### WP2. Generic MCP tools (freecad-mcp)
Promote the project scripts to five workflow-shaped tools. Each reads the project's data files and calls the project's provider module; no arm facts go into the server.

| Tool | Replaces | Notes |
|---|---|---|
| `project_quick_check` | `tools/quick_check.py` | envelopes, interfaces, self-interference over a declared motion range, mass/torque against declared ratings, fingerprint; returns pass/fail per check plus the FRESH/STALE evidence table |
| `project_fingerprint` | `tools/fingerprint.py` | `mode=check|record`; record is marked destructive |
| `interface_probe` | `tools/check_interfaces.py` | also probes non-x-normal patterns (the DM motor file) |
| `envelope_check` | part of the quick check | keep-out boxes per pose, world or tool frame |
| `project_map` | `tools/make_map.py` | writes `MAP.md` from the provider plus the data files |

Each tool must have:
- `response_format: concise|detailed`, defaulting to concise. Anthropic presents this as an option: their example's detailed response was 206 tokens and the concise one 72, about ⅓.
- `structuredContent` plus an `outputSchema`. The spec says the server MUST conform to the schema, and any tool returning structured content SHOULD also return the serialised JSON as text.
- Annotations on **every** tool, because the spec defaults are pessimistic: `readOnlyHint` false, `destructiveHint` true, `idempotentHint` false, `openWorldHint` true. An unannotated check tool is therefore presented as destructive and open-world.
  - Checks: `readOnlyHint: true`, `openWorldHint: false`.
  - `fingerprint record` and `project_map` (they write files): `readOnlyHint: false`, `destructiveHint: false` (they only write their own outputs), `idempotentHint: true`.
  - Clients MUST treat annotations from untrusted servers as untrusted, so they are hints, not enforcement. Enforcement stays in WP3.
- Tool and input errors go in the result with `isError: true` and say how to fix the input, e.g. "interfaces/x.toml side_b part 'Gripper_Palm' not found; parts in HEAD: …". Never tracebacks. Only unknown tools and malformed requests are JSON-RPC errors (the spec says SHOULD). Claude Code keeps the first and last 5,000 characters of error text over about 11,000.
- Long runs use the existing freecad-mcp job pattern with progress notifications. Progress "should increase", and sending notifications is optional. The spec's task-augmented calls (`execution.taskSupport`, `tasks/get|result|cancel`) are **experimental** in 2025-11-25, so treat them as a later upgrade, not the base design.
- Names keep `[A-Za-z0-9_.-]` and 1–128 characters (spec SHOULD), prefixed by service (`project_…`). Anthropic found prefix vs suffix namespacing has "non-trivial effects" on tool selection, so test both in WP6.
- Concise output stays well under Claude Code's limits: a warning at 10,000 tokens, a 25,000-token default cap, and text over 50,000 characters saved to a file.
- Server instructions are rewritten for tool search: keywords first, under 4,096 characters.

Keep the existing tools' fields unchanged; add new names rather than changing old ones.

The provider contract is a small documented module API: `bodies()`, `placements(pose, variant)`, `poses()`, `variants()`, `release_variant()`. The arm's `arm_model` facade plus `mcp_provider.py` already almost satisfy it.

**Acceptance:**
- the five tools give the same verdicts as the arm's scripts on both variants;
- each tool's concise output is under 2,000 tokens;
- the freecad-mcp suite plus new tests, on a synthetic two-variant fixture, pass.

### WP3. Hooks: enforcement with no judgement (plugin, plus project settings for local overrides)

| Hook | Event | Behaviour |
|---|---|---|
| `protect-release` | `PreToolUse` on `Edit|Write|Bash` | Block writes to the release outputs declared in project data (`fab/`, `drawings/out/`, `fea/out/`, `deliverables/`, `tests/fingerprints/*.json`, `MAP.md`) unless they come through the sanctioned generator. Exit 2 with the reason and the command to use instead. |
| `validate-data-files` | `PostToolUse` on `Edit|Write` under `params/`, `interfaces/` or `envelopes/` | Run the WP1 schema validation (pure Python, under 1 s, no FreeCAD). Feed errors back to the agent. Add the line "inputs changed: run the quick check before finishing". |
| `stale-evidence-on-stop` | `Stop` | If the inputs hash differs from the last `quick` entry in the manifest, exit 2 with "geometry inputs changed since the last quick check (hash a→b); run it or say why not". Stderr becomes the reason. Block only once: exit 0 when the hook input has `stop_hook_active: true`. Claude Code overrides a Stop hook after 8 consecutive blocks anyway (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`). A timed-out Stop hook counts as allowing the stop. |
| `session-status` | `SessionStart` | Print in 5 lines or fewer: active variant, release variant, last quick-check result, and the STALE checks. |

Use command hooks only, not prompt hooks, so the behaviour is deterministic. Set `onFailure: "block"` only on `protect-release`. Without it, a `command` hook that crashes with an ordinary exit code lets the tool call go ahead.

Notes:
- Bash writes get past `Edit|Write` matchers. `protect-release` therefore also inspects Bash commands for redirects and moves into protected paths. The release generators keep their own in-code guard as a second layer **(exists)**.
- Hooks must run on Windows Git Bash and POSIX: Python scripts with forward-slash paths, no `jq`.

**Acceptance:** scripted tests confirm:
- each hook fires;
- a blocked edit leaves the file untouched;
- the stop hook blocks once, then allows;
- total hook overhead per edit is under 1 s.

### WP4. Skills: judgement and procedure (plugin)
Follow the Agent Skills best practices:
- third-person, keyword-rich descriptions under 1,024 characters;
- body under 500 lines with the critical rules first;
- references one level deep;
- deterministic steps as bundled scripts that are *run*, not read;
- checklists and validate → fix → repeat loops.

| Skill | Triggers on | Contents |
|---|---|---|
| `cad-iterate` (merge into and extend the template's `cad-build-workflow`) | "change / tune / redesign a part", "make it lighter", editing params | The loop: data file → quick check → evidence. When to escalate to the full checks. Independent review for anything released. Copyable checklist. References: frames, file schemas, evidence format. |
| `cad-add-variant` | "new gripper / alternative design / concept" | Provider API contract. Register the variant. Mount on an existing interface. Write its params file and envelopes. Record its fingerprint baseline. Script: scaffold a variant module from a template. |
| `cad-interfaces-envelopes` | "what bolts to what", "clearance / keep-out / collides with field" | How to write an interface or envelope file, with a worked example. The rule: limits go in data first, and every limit gets a negative test. Script: validate, then generate a negative-test stub. |
| `cad-refactor` | "split / restructure / move parameters" | Fingerprint discipline: MATCH on every variant, re-record only for intended changes, and list which parts changed. |
| `cad-release` (`disable-model-invocation: true`) | user types `/cad-release` only | Release-variant generators, drawing package (calls `techdraw-drawings`), TDP, protected deliverables, delivery target from project data (for this user, UTA OneDrive plus a README). |
| `techdraw-drawings` **(exists)** | unchanged | Gains a reference to the release flow. |

**Acceptance:**
- each skill validates with `skills-ref validate`;
- its description triggers on its eval prompts and *doesn't* trigger on the negative prompts;
- it meets its eval targets (WP6).

### WP5. Project scaffolding (template repo)
- Extend `workflow.py init` to create:
  - `params/`, `interfaces/` and `envelopes/` with one worked example each;
  - a provider stub, `out/` and `.claude/rules/`;
  - a CLAUDE.md skeleton (under 120 lines).
- New `workflow.py` commands:
  - `quick` and `fingerprint`, which call the WP2 tools, or local scripts when no MCP is available;
  - `map`.
- `status` gains the FRESH/STALE evidence table.
- Path-scoped rules in `.claude/rules/`:
  - `cad-source.md` (`paths: cad/**/*.py`): edit params, not literals; a refactor needs fingerprint MATCH;
  - `data-files.md` (`paths: params|interfaces|envelopes`): unit and source required, and every new limit gets a negative test.
- Migrate the arm project onto the template layout. Keep the facade, and map `fab/` and `drawings/out` as protected deliverables.
- **Acceptance:** `workflow.py init` on an empty folder, followed by an agent run of the WP6 scenario "add a part with one interface", reaches a passing quick check with no hand edits by the user.

### WP6. Evals: measure, don't assume
Build these before writing much skill prose. Skill best practices: "Create evaluations BEFORE writing extensive documentation", with at least three. Record the no-skill baseline first, then the plugin.

Use `claude plugin eval` (v2.1.269 or later), which runs each case with and without the plugin by default. Graders:
- `regex`, `tool_used` (use `min: 0, max: 0` to assert a tool was never called, and `tool_used: Skill` to measure triggering), `tool_order` and `file_exists` (only files created during the run count);
- `llm` (2-of-3 judge votes) and `baseline` (judged against a reference transcript).

Run on every model the plugin will be used with (Haiku, Sonnet and Opus here), with the models pinned in CI. `--threshold`, `--max-cost-usd` and exit codes 0/1/2 drive gating.

| # | Scenario (realistic prompt) | Pass if |
|---|---|---|
| 1 | "Make the four-bar links 5 mm shorter" | edits `params/gripper_fourbar.toml` (not code); runs the quick check; reports the envelope or self-hit result |
| 2 | "Split `wrist.py` into roll and pitch modules" | fingerprint MATCH on both variants before finishing |
| 3 | Seeded clash: XMAX = 165 | the agent finds and reports the pole envelope failure rather than claiming success |
| 4 | "Add a bolt pattern between X and Y" | creates `interfaces/*.toml`; both parts build from it; `interface_probe` passes |
| 5 | "Regenerate the drawings" in a session with `GRIP=FOURBAR` | refuses or pins to the release variant; no file in `drawings/out` changes |
| 6 | Negative trigger: "Summarise the README" | no CAD skill loads, no hook blocks |
| 7 | "Why is the interference result out of date?" | reads the manifest and explains STALE with its cause |

Track pass rate, tool calls, tokens and wall time against the baseline. Keep scenarios 6–7 as a held-out set. Review transcripts after each round with a fresh agent and refactor tool descriptions and skills from what it finds (tool-writing guidance).

### WP7. Packaging and rollout
1. Create a `mechanical-cad` plugin (`.claude-plugin/plugin.json`, skills, hooks, `.mcp.json` pinning the freecad-mcp commit) in a marketplace repo.
2. Install it at project scope in the arm repo (`.claude/settings.json`) and test with `--plugin-dir` first.
3. Add CI to the template and the plugin: schema tests, hook tests, plugin eval on a pinned model (gating), and the freecad-mcp suite.
4. Retire duplicated text. CLAUDE.md keeps orientation and points to the skills; the arm memory notes that this plan supersedes the ad hoc rules.

## 5. Sequence and size

| Order | Work package | Repo | Size | Depends on |
|---|---|---|---|---|
| 1 | WP6 baseline evals (scenarios 1–7, no plugin) | plugin repo | S | none |
| 2 | WP1 schemas and evidence format | template | S | none |
| 3 | WP3 hooks (project-local first) | arm, then plugin | S–M | WP1 |
| 4 | WP2 MCP tools | freecad-mcp | M–L | WP1 |
| 5 | WP4 skills | plugin | M | WP2, WP3; evals from 1 |
| 6 | WP5 scaffolding and arm migration | template, arm | M | WP1–WP4 |
| 7 | WP7 packaging, CI, rollout | plugin | S | all |

Steps 2–4 can run in parallel sessions: they touch different repos and share only the WP1 schema, which lands first.

## 6. Risks and decisions for the user
- **Enforcement friction.** A Stop hook that blocks can slow quick experiments. Mitigation: it blocks once, and an explicit "skip: <reason>" in the reply clears it. Decision: block, or warn only?
- **Windows hooks.** Git Bash and PowerShell differences. Mitigation: Python hook scripts, tested on this machine.
- **Hash cost.** `vendor/` STEP files make the inputs hash heavier. Cache file hashes by modification time plus size, and rehash only changed files.
- **Skill drift.** Skills that describe scripts can go stale. Mitigation: skills call scripts instead of restating them, and the evals run in CI.
- **Scope creep in the MCP.** Keep project facts out of the server. Decision: should `project_quick_check` live in freecad-mcp, or stay a template script that the skill runs? The guidance favours an MCP tool for deterministic work. A script is simpler if this only ever runs locally.
- **Plugin visibility.** Every enabled plugin's descriptions cost context on every turn. Five skills at about 100 tokens each is acceptable.

## 7. Verification of the research (2026-11-16)

The first research pass mixed fetched text with recall. Every claim the plan relies on was then re-checked against the primary source. Where the earlier wording was wrong, the plan above now uses the corrected wording.

| Claim | Status | Source wording |
|---|---|---|
| MCP annotation defaults: readOnly false, destructive true (only meaningful when not read-only), idempotent false, openWorld true | Confirmed | schema.ts 2025-11-25 doc comments ("Default: …") |
| Annotations are untrusted unless from a trusted server | Confirmed | tools page: clients "MUST consider tool annotations to be untrusted unless they come from trusted servers" |
| Control model | **Corrected** | tools "model-controlled", resources "application-**driven**", prompts "user-controlled" (per-primitive pages; the overview page doesn't state it) |
| Tool errors in results with `isError`, protocol errors as JSON-RPC | Confirmed, as SHOULD | schema `CallToolResult.isError` |
| `structuredContent` conforms to `outputSchema`, plus a text copy | Confirmed | MUST conform; the text copy is SHOULD for *any* structured result |
| Tool name length and characters | **Corrected** to SHOULD (not mandatory) | tools page; the schema puts no constraint on the name |
| Progress "must increase" | **Corrected** to "should increase"; notifications are optional | schema `ProgressNotificationParams` |
| Tasks (`tasks/get|result|cancel`, `execution.taskSupport`, default "forbidden") | Confirmed, and **experimental** | tasks page |
| `resource_link` in tool results | Confirmed | schema `ResourceLink`; tools page "MAY return links" |
| Skill `name` ≤ 64 characters, lowercase/digits/hyphens, no "anthropic"/"claude"; `description` ≤ 1,024 characters, no XML, third person | Confirmed | platform skill best practices |
| SKILL.md body under 500 lines; references one level deep; a TOC for references over 100 lines; forward slashes; `Server:tool` names | Confirmed | platform skill best practices |
| Evals before documentation, at least 3; test with every target model | Confirmed | platform skill best practices |
| Listing caps `description` + `when_to_use` at 1,536 characters (`skillListingMaxDescChars`); listing budget 1% of context | Confirmed | Claude Code skills docs |
| After compaction: 5,000 tokens per skill, 25,000 total, most recent first | Confirmed | Claude Code skills / context-window docs |
| CLAUDE.md under 200 lines | Confirmed | Claude Code features overview / costs docs |
| MCP output: warning at 10,000 tokens, 25,000 default (`MAX_MCP_OUTPUT_TOKENS`), file after 50,000 characters, error text trimmed above about 11,000 | Confirmed | Claude Code MCP docs |
| `response_format` concise vs detailed, about ⅓ the tokens | Confirmed (206 vs 72 tokens); presented as an option | Anthropic "Writing tools for agents" |
| Prefix vs suffix namespacing matters | Confirmed ("non-trivial effects"), no effect sizes given | same |
| Plugin-eval graders | Confirmed, plus a sixth (`baseline`) that the first pass missed | Claude Code plugin-evals docs |
| Stop hook blocking | Confirmed: exit 2 plus stderr; `stop_hook_active`; overridden after 8 consecutive blocks | Claude Code hooks docs |

Not independently verified, and used only as opinion: the practitioner advice of 5–15 tools per server, and pagination defaults of 20–50 items.

## 8. Sources
- Agent Skills best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Claude Code skills: https://code.claude.com/docs/en/skills
- Features overview (CLAUDE.md vs rules vs skills vs hooks vs MCP vs plugins): https://code.claude.com/docs/en/features-overview
- Hooks guide: https://code.claude.com/docs/en/hooks-guide
- Plugins: https://code.claude.com/docs/en/plugins
- Plugin evals: https://code.claude.com/docs/en/plugin-evals
- Agent Skills spec: https://agentskills.io/specification
- Anthropic, "Equipping agents for the real world with Agent Skills": https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Anthropic, "Writing tools for agents": https://www.anthropic.com/engineering/writing-tools-for-agents
- Anthropic, "Code execution with MCP": https://www.anthropic.com/engineering/code-execution-with-mcp
- MCP spec 2025-11-25, tools: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- MCP spec 2025-11-25, resources / prompts / tasks: https://modelcontextprotocol.io/specification/2025-11-25/server/resources, …/server/prompts, …/basic/utilities/tasks
- MCP schema 2025-11-25 (annotation defaults, isError, progress, ResourceLink): https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2025-11-25/schema.ts
- Claude Code skills (listing cap, compaction budget): https://code.claude.com/docs/en/skills ; hooks (exit 2, Stop cap, onFailure): https://code.claude.com/docs/en/hooks
- Claude Code MCP (tool search, output limits): https://code.claude.com/docs/en/mcp
- Local: `freecad-mcp/docs/portable-workflow.md` (cad-evidence/1); `mechanical-workflow-template/README.md` and `AGENTS.md`; `cad/docs/tooling_audit.md`
