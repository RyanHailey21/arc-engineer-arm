# -*- coding: utf-8 -*-
"""The repo's Claude Code configuration loads as written (plain Python, no FreeCAD):

    python -I cad/tests/test_agent_config.py          (exit 1 on FAIL)

Claude Code does not report a broken skill: frontmatter that fails to parse loads the skill with no fields, and
an unknown field is ignored (code.claude.com/docs/en/skills). So this checks, for .claude/:
  - settings.json is valid JSON, and every hook command that names a repo script names one that exists;
  - the deny rules hold force-push, `git reset --hard` and `git clean`, and every `Bash(...)` deny has the same
    `PowerShell(...)` deny: on Windows a Bash deny rule alone turns the PowerShell tool off without a warning
    (code.claude.com/docs/en/tools-reference#bash-deny-rules-also-turn-off-the-powershell-tool);
  - every skill and agent file has a frontmatter block of simple `key: value` lines, a `name` equal to its folder
    (skills) or file (agents), a non-empty description of at most 1,536 characters (the listing cut-off), only
    documented keys, and a body under 500 lines that names `${CLAUDE_PROJECT_DIR}`-style variables only in the
    braced form Claude Code substitutes (the bare `$CLAUDE_PROJECT_DIR` is empty in the Bash tool).
It runs on the real files, then on broken copies in memory to prove each rule fires.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLAUDE = os.path.join(ROOT, ".claude")
SKILL_KEYS = {"name", "description", "when_to_use", "argument-hint", "arguments", "disable-model-invocation",
              "user-invocable", "allowed-tools", "disallowed-tools", "model", "effort", "context", "agent",
              "background", "hooks", "paths", "shell", "metadata", "license", "compatibility"}
AGENT_KEYS = {"name", "description", "tools", "disallowedTools", "model", "permissionMode", "maxTurns",
              "autoCompactWindow", "skills", "mcpServers", "hooks", "memory", "background", "omitClaudeMd",
              "effort", "isolation", "color", "initialPrompt"}
MAX_DESC = 1536
REQUIRED_DENY = ("Bash(git push --force*)", "Bash(git push -f*)", "Bash(git reset --hard*)", "Bash(git clean *)")
MAX_LINES = 500
# code.claude.com/docs/en/skills#available-string-substitutions: ${CLAUDE_PROJECT_DIR} / ${CLAUDE_SKILL_DIR} are
# filled in in the skill's text; the Bash tool does not export them, so the bare $NAME form expands to "" there
UNBRACED = re.compile(r"\$(CLAUDE_PROJECT_DIR|CLAUDE_SKILL_DIR|CLAUDE_SESSION_ID|CLAUDE_EFFORT)(?!\w)")


def frontmatter(text):
    """(fields, body) from a `---` block of top-level `key: value` lines; nested YAML values are kept as text."""
    if not text.startswith("---"):
        raise ValueError("no frontmatter block")
    end = text.find("\n---", 3)
    if end < 0:
        raise ValueError("frontmatter block not closed")
    fields, key = {}, None
    for i, line in enumerate(text[3:end].strip("\n").splitlines(), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t-" and key:                       # continuation of a nested value
            fields[key] += "\n" + line
            continue
        m = re.match(r"^([A-Za-z][\w-]*):(?:\s+(.*))?$", line)
        if not m:
            raise ValueError("line %d is not `key: value`: %r" % (i, line))
        key, val = m.group(1), (m.group(2) or "").strip()
        if val[:1] not in "\"'|>[{" and ": " in val:
            raise ValueError("line %d: unquoted ': ' in the value of %s (YAML reads it as a mapping)" % (i, key))
        fields[key] = val
    return fields, text[end + 4:]


def check_doc(path, text, expect_name, allowed):
    try:
        f, body = frontmatter(text)
    except ValueError as e:
        return ["%s: %s" % (path, e)]
    errs = []
    if f.get("name", expect_name) != expect_name:
        errs.append("%s: name %r is not %r" % (path, f.get("name"), expect_name))
    desc = f.get("description", "").strip("\"'")
    if not desc:
        errs.append("%s: no description" % path)
    if len(desc) + len(f.get("when_to_use", "")) > MAX_DESC:
        errs.append("%s: description over %d characters" % (path, MAX_DESC))
    for k in sorted(set(f) - allowed):
        errs.append("%s: undocumented key %r (ignored by Claude Code)" % (path, k))
    if body.count("\n") > MAX_LINES:
        errs.append("%s: body over %d lines" % (path, MAX_LINES))
    for v in sorted(set(UNBRACED.findall(body))):
        errs.append("%s: $%s in the body: only ${%s} is substituted in skill text; the shell leaves it empty"
                    % (path, v, v))
    return errs


def check_settings(text, path="settings.json"):
    try:
        s = json.loads(text)
    except ValueError as e:
        return ["%s: invalid JSON (%s)" % (path, e)]
    errs = []
    deny = set((s.get("permissions") or {}).get("deny", []))
    for rule in REQUIRED_DENY:
        if rule not in deny:
            errs.append("%s: missing deny rule %s" % (path, rule))
    for rule in sorted(r for r in deny if r.startswith("Bash(")):
        if "PowerShell(" + rule[5:] not in deny:
            errs.append("%s: %s has no PowerShell twin (the PowerShell tool would be turned off)" % (path, rule))
    for event, groups in (s.get("hooks") or {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                for rel in re.findall(r"\$\{?CLAUDE_PROJECT_DIR\}?/([\w./-]+\.\w+)", h.get("command", "")):
                    if not os.path.exists(os.path.join(ROOT, rel)):
                        errs.append("%s: %s hook names a missing script %s" % (path, event, rel))
    return errs


def audit():
    errs = []
    sp = os.path.join(CLAUDE, "settings.json")
    if os.path.exists(sp):
        errs += check_settings(open(sp, encoding="utf-8").read())
    sk = os.path.join(CLAUDE, "skills")
    for d in sorted(os.listdir(sk)) if os.path.isdir(sk) else []:
        p = os.path.join(sk, d, "SKILL.md")
        if os.path.isfile(p):
            errs += check_doc("skills/%s/SKILL.md" % d, open(p, encoding="utf-8").read(), d, SKILL_KEYS)
        elif os.path.isdir(os.path.join(sk, d)):
            errs.append("skills/%s: no SKILL.md" % d)
    ag = os.path.join(CLAUDE, "agents")
    for fn in sorted(os.listdir(ag)) if os.path.isdir(ag) else []:
        if fn.endswith(".md"):
            errs += check_doc("agents/" + fn, open(os.path.join(ag, fn), encoding="utf-8").read(), fn[:-3],
                              AGENT_KEYS)
    return errs


def negatives():
    """Each rule must fire on a broken copy."""
    good = "---\nname: x\ndescription: Does a thing.\n---\nbody\n"
    cases = {
        "no block": "name: x\n",
        "unclosed": "---\nname: x\ndescription: d\n",
        "colon value": "---\nname: x\ndescription: Use when: things break\n---\n",
        "wrong name": good.replace("name: x", "name: y"),
        "no description": "---\nname: x\n---\n",
        "long description": good.replace("Does a thing.", "a" * (MAX_DESC + 1)),
        "unknown key": good.replace("name: x", "name: x\nallowed_tools: Bash"),
        "long body": good + "line\n" * (MAX_LINES + 1),
        "unbraced variable": good + 'git -C "$CLAUDE_PROJECT_DIR" status\n',
    }
    missed = [k for k, t in cases.items() if not check_doc("case", t, "x", SKILL_KEYS)]
    if check_doc("good", good + 'git -C "${CLAUDE_PROJECT_DIR}" status\n', "x", SKILL_KEYS):
        missed.append("good case flagged")
    full = {"permissions": {"deny": [r for b in REQUIRED_DENY for r in (b, "PowerShell(" + b[5:])]}}
    if check_settings(json.dumps(full)):
        missed.append("good settings flagged")
    if not check_settings(json.dumps({"permissions": {"deny": list(REQUIRED_DENY)}})):
        missed.append("Bash deny with no PowerShell twin")
    if not check_settings(json.dumps({"permissions": {"deny": full["permissions"]["deny"][2:]}})):
        missed.append("missing force-push deny")
    if not check_settings("{not json"):
        missed.append("bad JSON")
    if not check_settings(json.dumps({**full, "hooks": {"PreToolUse": [{"hooks": [
            {"command": 'python "$CLAUDE_PROJECT_DIR/cad/tools/hooks/missing.py"'}]}]}})):
        missed.append("missing hook script")
    return missed


def main():
    errs, missed = audit(), negatives()
    for e in errs:
        print("  FAIL " + e)
    for m in missed:
        print("  FAIL negative case not caught: " + m)
    print("test_agent_config: %s" % ("FAIL" if errs or missed else "PASS"))
    return 1 if errs or missed else 0


if __name__ == "__main__":
    sys.exit(main())
