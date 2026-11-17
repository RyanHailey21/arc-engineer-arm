# -*- coding: utf-8 -*-
"""Apply exact text edits from a spec file, all-or-nothing, with a hint when an anchor misses.

    python -I cad/tools/apply_patch.py SPEC.toml            # apply
    python -I cad/tools/apply_patch.py SPEC.toml --check    # report only, write nothing

Why (cad/docs/tooling_issues.md TI-002): patching Python through `python - <<'EOF'` heredocs and `sed`
failed repeatedly on this project. Bash rejected the heredoc ("unexpected EOF while looking for matching"),
`s.replace` anchors silently missed or tripped an assert after other edits had already landed, and `sed -i`
changed nothing without saying so. Write the spec with the Write tool (no shell quoting at all), then run
this script.

Spec (TOML; use '''literal''' strings so backslashes and quotes need no escaping):

    [[edit]]
    file = "cad/arm/grippers/fourbar.py"   # relative to the repo root, or absolute
    find = '''L = 47.0'''                   # exact text; must occur `count` times (default 1)
    replace = '''L = 42.0'''
    # count = 2                             # or count = "all"

    [[edit]]                                # replace a block between two anchors
    file = "cad/tools/quick_check.py"
    start = '''def old_block('''             # the span starts at this anchor ...
    end = '''def next_function('''           # ... and stops before this one (kept)
    replace_file = "C:/.../scratchpad/new_block.py"   # replacement text from a file (or `replace`)
    # include_end = true                    # also replace the end anchor

    [[edit]]
    file = "cad/docs/notes.md"
    after = '''## Log\n'''                   # insert after (or `before`) an anchor
    insert = '''- new line\n'''

    [[create]]                              # new file; refuses to overwrite
    file = "cad/tools/new_tool.py"
    text_file = "C:/.../scratchpad/new_tool.py"   # or text = '''...'''

`'''` cannot appear inside a TOML literal string: put such text in a file (replace_file / text_file).
A spec may also be JSON with the same keys.

Behaviour:
- Every edit is matched before anything is written. One miss: nothing is written, exit 1.
- A miss reports the closest lines in the file (line numbers, and whether only whitespace or line
  endings differ).
- CRLF files: anchors written with LF still match; the file keeps its line endings.
- Edited .py files must still compile, or nothing is written (`--no-syntax-check` turns this off).
- Prints one line per edit plus a short diff (`--quiet` prints only the summary).
Exit codes: 0 applied (or would apply with --check), 1 an edit failed, 2 bad spec or usage.
"""
import argparse
import difflib
import json
import os
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SpecError(Exception):
    pass


class EditError(Exception):
    pass


def _say(msg=""):
    # cp1252 consoles crash on characters such as U+27C2 (TI-003); never let output kill the run.
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "backslashreplace").decode("ascii"))


def load_spec(path):
    raw = open(path, "rb").read()
    if path.lower().endswith(".json"):
        return json.loads(raw.decode("utf-8"))
    if tomllib is None:
        raise SpecError("TOML specs need Python 3.11+; use a .json spec")
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise SpecError("%s: %s (if the text contains ''' put it in a file and use replace_file)" % (path, e))


def resolve(p, base):
    p = os.path.expandvars(os.path.expanduser(p))
    if len(p) > 2 and p[0] == "/" and p[2] == "/" and p[1].isalpha():  # Git Bash style /c/Users/...
        p = p[1] + ":" + p[2:]
    return os.path.normpath(p if os.path.isabs(p) else os.path.join(base, p))


def _text_of(entry, key, file_key, spec_dir, where):
    if key in entry and file_key in entry:
        raise SpecError("%s: give `%s` or `%s`, not both" % (where, key, file_key))
    if file_key in entry:
        f = resolve(entry[file_key], spec_dir)
        if not os.path.isfile(f):
            raise SpecError("%s: %s not found: %s" % (where, file_key, f))
        return open(f, encoding="utf-8", newline="").read()
    if key in entry:
        if not isinstance(entry[key], str):
            raise SpecError("%s: `%s` must be a string" % (where, key))
        return entry[key]
    return None


def _hint(text, needle):
    """Closest lines in `text` to the first non-blank line of `needle`."""
    first = next((ln for ln in needle.splitlines() if ln.strip()), needle)
    lines = text.splitlines()
    exact_ws = [i for i, ln in enumerate(lines) if ln.split() == first.split() and ln.split()]
    if exact_ws:
        return "  same words, different whitespace at line %s" % ", ".join(str(i + 1) for i in exact_ws[:5])
    scored = sorted(((difflib.SequenceMatcher(None, first.strip(), ln.strip()).ratio(), i)
                     for i, ln in enumerate(lines)), reverse=True)[:3]
    out = ["  closest lines to %r:" % first.strip()[:80]]
    out += ["    %5d (%.0f%%) %s" % (i + 1, 100 * r, lines[i].strip()[:100]) for r, i in scored if r > 0.5]
    return "\n".join(out) if len(out) > 1 else "  no similar line in the file"


def _find_all(text, needle):
    out, i = [], text.find(needle)
    while i >= 0:
        out.append(i)
        i = text.find(needle, i + max(1, len(needle)))
    return out


def _norm(s, crlf):
    s = s.replace("\r\n", "\n")
    return s.replace("\n", "\r\n") if crlf else s


def apply_edit(text, e, crlf, where):
    """Return the edited text or raise EditError."""
    def anchor(key):
        a = _norm(e[key], crlf)
        hits = _find_all(text, a)
        if not hits:
            raise EditError("%s: `%s` not found\n%s" % (where, key, _hint(text, e[key])))
        return a, hits

    if "find" in e:
        a, hits = anchor("find")
        want = e.get("count", 1)
        if want != "all" and len(hits) != want:
            raise EditError("%s: `find` occurs %d times, expected %s (set count = %d or \"all\", or add context)"
                            % (where, len(hits), want, len(hits)))
        return text.replace(a, e["_new"])
    if "start" in e:
        a, hits = anchor("start")
        if len(hits) != 1:
            raise EditError("%s: `start` occurs %d times; it must be unique" % (where, len(hits)))
        s0 = hits[0]
        b = _norm(e["end"], crlf)
        j = text.find(b, s0 + len(a))
        if j < 0:
            raise EditError("%s: `end` not found after `start`\n%s" % (where, _hint(text[s0:], e["end"])))
        j2 = j + len(b) if e.get("include_end") else j
        return text[:s0] + e["_new"] + text[j2:]
    key = "after" if "after" in e else "before"
    a, hits = anchor(key)
    if len(hits) != 1:
        raise EditError("%s: `%s` occurs %d times; it must be unique" % (where, key, len(hits)))
    k = hits[0] + (len(a) if key == "after" else 0)
    return text[:k] + e["_new"] + text[k:]


def plan(spec, spec_dir):
    """Validate the spec and compute every new file text. Returns {path: (old_or_None, new)}."""
    edits, creates = spec.get("edit", []), spec.get("create", [])
    unknown = set(spec) - {"edit", "create"}
    if unknown or not (edits or creates):
        raise SpecError("spec needs [[edit]] and/or [[create]] tables%s"
                        % (" (unknown keys: %s)" % ", ".join(sorted(unknown)) if unknown else ""))
    files, errors = {}, []
    for n, e in enumerate(edits, 1):
        where = "edit %d (%s)" % (n, e.get("file", "?"))
        modes = [k for k in ("find", "start", "after", "before") if k in e]
        if "file" not in e or len(modes) != 1:
            raise SpecError("%s: needs `file` and exactly one of find / start+end / after / before" % where)
        if modes == ["start"] and "end" not in e:
            raise SpecError("%s: `start` needs `end`" % where)
        new = _text_of(e, "insert" if modes[0] in ("after", "before") else "replace",
                       "insert_file" if modes[0] in ("after", "before") else "replace_file", spec_dir, where)
        if new is None:
            raise SpecError("%s: missing the replacement text" % where)
        path = resolve(e["file"], ROOT)
        if path not in files:
            if not os.path.isfile(path):
                errors.append("%s: file not found: %s" % (where, path))
                continue
            old = open(path, encoding="utf-8", newline="").read()
            files[path] = [old, old]
        cur = files[path][1]
        crlf = "\r\n" in cur
        e = dict(e, _new=_norm(new, crlf))
        try:
            files[path][1] = apply_edit(cur, e, crlf, where)
        except EditError as x:
            errors.append(str(x))
    for n, c in enumerate(creates, 1):
        where = "create %d (%s)" % (n, c.get("file", "?"))
        if "file" not in c:
            raise SpecError("%s: needs `file`" % where)
        text = _text_of(c, "text", "text_file", spec_dir, where)
        if text is None:
            raise SpecError("%s: needs `text` or `text_file`" % where)
        path = resolve(c["file"], ROOT)
        if os.path.exists(path) or path in files:
            errors.append("%s: already exists; use [[edit]] to change it" % where)
            continue
        files[path] = [None, text]
    return files, errors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    ap.add_argument("--quiet", action="store_true", help="no diff output")
    ap.add_argument("--no-syntax-check", action="store_true")
    a = ap.parse_args(argv)
    spec_path = resolve(a.spec, os.getcwd())
    try:
        files, errors = plan(load_spec(spec_path), os.path.dirname(spec_path))
    except (SpecError, OSError, ValueError) as x:
        _say("SPEC ERROR %s" % x)
        return 2
    if not a.no_syntax_check:
        for path, (old, new) in files.items():
            if path.endswith(".py") and not errors:
                try:
                    compile(new, path, "exec")
                except SyntaxError as x:
                    errors.append("%s: result does not compile: line %s: %s" % (path, x.lineno, x.msg))
    if errors:
        for x in errors:
            _say("FAIL " + x)
        _say("nothing written (%d problem%s)" % (len(errors), "" if len(errors) == 1 else "s"))
        return 1
    for path, (old, new) in files.items():
        rel = os.path.relpath(path, ROOT) if path.startswith(ROOT) else path
        if old == new:
            _say("SAME   %s (edits produced no change)" % rel)
            continue
        _say("%s %s" % ("NEW   " if old is None else "EDIT  ", rel))
        if not a.quiet and old is not None:
            diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=1))[2:]
            for ln in diff[:60]:
                _say("    " + ln)
            if len(diff) > 60:
                _say("    ... %d more diff lines" % (len(diff) - 60))
        if not a.check:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".apply_patch.tmp"
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            os.replace(tmp, path)
    _say("%s %d file(s)" % ("would change" if a.check else "changed", len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
